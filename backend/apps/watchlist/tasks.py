import asyncio
import logging

from celery import shared_task
from django.utils import timezone

from ats_adapters.registry import get_adapter

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def monitor_company(self, company_id: int):
    from .models import JobPosting, WatchlistCompany

    try:
        company = WatchlistCompany.objects.get(pk=company_id)
    except WatchlistCompany.DoesNotExist:
        return

    if company.scrape_status == "paused" or not company.ats_provider:
        return

    adapter = get_adapter(company.ats_provider)
    if not adapter:
        company.scrape_status = "error"
        company.last_error = f"No adapter for provider: {company.ats_provider}"
        company.save()
        return

    try:
        jobs = asyncio.run(adapter.fetch_jobs(company.ats_company_slug))

        seen_ids = set()
        for job_data in jobs:
            seen_ids.add(job_data.external_id)

            posting, created = JobPosting.objects.update_or_create(
                company=company,
                external_id=job_data.external_id,
                defaults={
                    "title": job_data.title,
                    "url": job_data.url,
                    "location": job_data.location,
                    "description_text": job_data.description_text,
                    "is_active": True,
                    "last_seen_at": timezone.now(),
                },
            )

            if not created and not posting.is_active:
                posting.is_reposted = True
                posting.is_active = True
                posting.save()

            if created:
                _check_rules(posting, company)

        stale = JobPosting.objects.filter(company=company, is_active=True).exclude(
            external_id__in=seen_ids
        )
        stale.update(is_active=False)

        company.last_checked_at = timezone.now()
        company.last_error = ""
        company.consecutive_failures = 0
        company.scrape_status = "active"
        company.save()

        logger.info(f"Monitored {company.name}: {len(jobs)} jobs found, {len(seen_ids)} active")

    except Exception as exc:
        company.consecutive_failures += 1
        company.last_error = str(exc)[:500]
        if company.consecutive_failures >= 5:
            company.scrape_status = "error"
        company.save()
        logger.error(f"Failed to monitor {company.name}: {exc}")
        raise self.retry(exc=exc) from exc


def _check_rules(posting, company):
    """Check posting against active rules; create Notification on match.

    Creating the Notification fires a post_save signal that enqueues the
    email-send task. One notification per posting (first matching rule wins).
    """
    from apps.notifications.models import Notification

    for rule in company.rules.filter(is_active=True):
        title_lower = posting.title.lower()
        location_lower = posting.location.lower()

        keyword_match = not rule.keywords or any(kw.lower() in title_lower for kw in rule.keywords)
        location_match = not rule.locations or any(
            loc.lower() in location_lower for loc in rule.locations
        )

        if keyword_match and location_match:
            posting.matched_rules = True
            posting.save()

            # Structured metadata lets the email task look up the posting
            # safely (no free-text parsing).
            Notification.objects.create(
                user=company.user,
                type="job_alert",
                title=f"New role at {company.name}: {posting.title}"[:255],
                body=f"Matched your alert rules for {company.name}.",
                link=posting.url,
                metadata={"posting_id": posting.id, "company_id": company.id},
            )
            break


@shared_task
def monitor_all_companies():
    """Tier-aware monitoring dispatcher.

    Runs hourly via Celery Beat. Filters per-company based on the owner's
    subscription tier so Free users get daily checks, Pro every 4h,
    Premium every hour.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.billing.permissions import get_user_limits

    from .models import WatchlistCompany

    companies = (
        WatchlistCompany.objects.filter(
            scrape_status="active",
            ats_provider__isnull=False,
        )
        .exclude(ats_provider="")
        .exclude(ats_provider="manual")
        .select_related("user")
    )

    queued = 0
    now = timezone.now()
    for company in companies:
        # Determine interval based on owner's tier
        limits = get_user_limits(company.user)
        interval_hours = limits.get("monitoring_interval_hours", 24)
        cutoff = now - timedelta(hours=interval_hours)

        # Skip if checked too recently for this tier
        if company.last_checked_at and company.last_checked_at > cutoff:
            continue

        monitor_company.delay(company.id)
        queued += 1

    logger.info(f"Queued monitoring for {queued}/{companies.count()} companies")
