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


def _get_profile_defaults(user):
    """Pull job-preference defaults off UserProfile. Returns a dict of the
    four fields the matcher understands. Missing profile = all empty lists."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return {
            "keywords": [],
            "exclude_keywords": [],
            "locations": [],
            "job_types": [],
        }
    return {
        "keywords": list(profile.target_roles or []),
        "exclude_keywords": list(profile.excluded_keywords or []),
        "locations": list(profile.preferred_locations or []),
        "job_types": list(profile.target_job_types or []),
    }


def _merge_rule_with_defaults(rule, defaults):
    """Rule field wins if non-empty; otherwise fall back to profile default.
    Exclusions are unioned so profile-level excludes ALWAYS apply."""
    merged = {
        "keywords": rule.keywords if rule.keywords else defaults["keywords"],
        "locations": rule.locations if rule.locations else defaults["locations"],
        "job_types": rule.job_types if rule.job_types else defaults["job_types"],
        # Union: rule-level + profile-level excludes both apply.
        "exclude_keywords": list({*(rule.exclude_keywords or []), *defaults["exclude_keywords"]}),
        "search_description": rule.search_description,
    }
    return merged


def _check_rules(posting, company):
    """Check posting against active rules; create Notification on match.

    Order of precedence:
      1. Per-company WatchlistRule fields (if set) — override profile defaults.
      2. UserProfile job-preference fields — fallback when a rule field is empty.
      3. If the company has no active rules at all, match against the raw
         profile defaults (auto-alert mode).

    Exclusions from the profile ALWAYS apply, even when a rule sets its own
    excludes — safer default.

    Flags the posting as matched (for the in-app Matched Jobs feed) and sets
    matched_at. It does NOT send an email — a scheduled digest task
    (send_watchlist_digests) batches new matches into one summary per user,
    so a company with 400 postings can't flood the inbox.
    """
    from django.utils import timezone

    from .ai_scoring import RELEVANCE_THRESHOLD, score_posting, should_score
    from .matching import matches

    defaults = _get_profile_defaults(company.user)
    active_rules = list(company.rules.filter(is_active=True))

    # No rules: match against profile defaults directly. Skip entirely if the
    # profile has nothing configured (avoid spamming the user with everything).
    if not active_rules:
        if not any(defaults.values()):
            return
        candidates = [{**defaults, "search_description": False}]
    else:
        candidates = [_merge_rule_with_defaults(r, defaults) for r in active_rules]

    for filters in candidates:
        if not matches(
            title=posting.title,
            location=posting.location,
            description=posting.description_text,
            **filters,
        ):
            continue

        # Second-pass AI relevance gate (Pro / opt-in). Fail-open: if the
        # scorer returns None (LLM error, no prefs, etc.), we still match.
        if should_score(company.user):
            score = score_posting(posting=posting, user=company.user)
            if score is not None:
                posting.ai_relevance_score = score
                posting.save(update_fields=["ai_relevance_score"])
                profile = getattr(company.user, "profile", None)
                threshold = (
                    profile.ai_relevance_threshold if profile is not None else RELEVANCE_THRESHOLD
                )
                if score < threshold:
                    return

        # Flag for the feed + digest. No per-job email.
        posting.matched_rules = True
        posting.matched_at = timezone.now()
        posting.save(update_fields=["matched_rules", "matched_at", "ai_relevance_score"])
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


# Minimum hours between digests per frequency tier. Beat runs the digest
# dispatcher daily; each user is only sent one if enough time has elapsed.
_DIGEST_MIN_HOURS = {"daily": 20, "weekly": 24 * 7 - 4}
_DIGEST_MAX_JOBS = 50  # cap rows per email so the digest stays readable


@shared_task
def send_watchlist_digests():
    """Batch newly-matched jobs into one summary email per user.

    Replaces per-job emails. For each user whose digest is enabled and due,
    gather matched/undismissed/unnotified active postings, send a single
    email with links, mark them notified, and drop one in-app notification.
    """
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from .models import JobPosting

    user_model = get_user_model()
    now = timezone.now()

    users = user_model.objects.filter(
        profile__watchlist_digest_frequency__in=["daily", "weekly"]
    ).select_related("profile")

    sent = 0
    for user in users:
        profile = user.profile
        freq = profile.watchlist_digest_frequency
        min_hours = _DIGEST_MIN_HOURS.get(freq)
        if min_hours is None:
            continue
        # Respect the per-user cadence.
        if profile.watchlist_digest_last_sent and profile.watchlist_digest_last_sent > (
            now - timedelta(hours=min_hours)
        ):
            continue

        pending = list(
            JobPosting.objects.filter(
                company__user=user,
                matched_rules=True,
                match_notified=False,
                match_dismissed=False,
                is_active=True,
            )
            .select_related("company")
            .order_by("-ai_relevance_score", "-matched_at")[:_DIGEST_MAX_JOBS]
        )
        if not pending:
            continue

        _send_digest_email(user, pending)

        JobPosting.objects.filter(id__in=[p.id for p in pending]).update(match_notified=True)
        profile.watchlist_digest_last_sent = now
        profile.save(update_fields=["watchlist_digest_last_sent"])

        # Single in-app notification pointing at the Matched Jobs feed.
        # bulk_create deliberately bypasses the post_save signal so it does
        # NOT trigger the per-notification email path (we already sent the
        # digest email above) — the bell badge still updates.
        from apps.notifications.models import Notification

        Notification.objects.bulk_create(
            [
                Notification(
                    user=user,
                    type="job_alert",
                    title=f"{len(pending)} new job match{'es' if len(pending) != 1 else ''}",
                    body="New roles matching your alerts are in your watchlist.",
                    link="/watchlist",
                    metadata={"digest": True, "count": len(pending)},
                )
            ]
        )
        sent += 1

    logger.info(f"Sent {sent} watchlist digest(s)")


def _send_digest_email(user, postings):
    """Compose and send the digest email. Values are HTML-escaped."""
    from django.conf import settings
    from django.utils.html import escape

    from apps.notifications.email import send_email

    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
    feed_url = f"{frontend}/watchlist"

    # Plain-text body
    text_lines = [
        f"Hi {user.first_name or 'there'},",
        "",
        f"We found {len(postings)} new job(s) matching your alerts:",
        "",
    ]
    for p in postings:
        score = f" (relevance {round(p.ai_relevance_score * 100)}%)" if p.ai_relevance_score else ""
        text_lines.append(f"- {p.title} @ {p.company.name} — {p.location or 'N/A'}{score}")
        text_lines.append(f"  {p.url}")
    text_lines += ["", f"See all matches: {feed_url}", "", "— Applywise"]
    text = "\n".join(text_lines)

    # HTML body
    rows = []
    for p in postings:
        score = (
            f'<span style="color:#666">· {round(p.ai_relevance_score * 100)}% match</span>'
            if p.ai_relevance_score
            else ""
        )
        rows.append(
            f'<li style="margin:0 0 10px">'
            f'<a href="{escape(p.url)}" style="color:#3B82F6;font-weight:500;text-decoration:none">'
            f"{escape(p.title)}</a><br>"
            f'<span style="color:#444">{escape(p.company.name)} — '
            f"{escape(p.location or 'Location N/A')}</span> {score}</li>"
        )
    html_body = (
        f"<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        f'max-width:560px;margin:24px auto;color:#111">'
        f'<h2 style="margin:0 0 12px">{len(postings)} new job match'
        f"{'es' if len(postings) != 1 else ''}</h2>"
        f'<p>Hi {escape(user.first_name or "there")}, here are the latest roles '
        f"matching your watchlist alerts:</p>"
        f'<ul style="list-style:none;padding:0">{"".join(rows)}</ul>'
        f'<p><a href="{escape(feed_url)}" style="display:inline-block;background:#3B82F6;'
        f'color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:500">'
        f"View all matches</a></p>"
        f'<p style="color:#666;font-size:13px">You can change digest frequency in '
        f"Settings → Job Preferences.</p></div>"
    )

    subject = f"{len(postings)} new job match{'es' if len(postings) != 1 else ''} — Applywise"
    try:
        send_email(user.email, subject, html_body, text)
    except Exception as e:
        logger.error(f"Failed to send watchlist digest to {user.email}: {e}")
