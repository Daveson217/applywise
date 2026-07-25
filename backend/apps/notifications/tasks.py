"""Celery tasks for sending notifications."""

import html
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_notification_email(self, notification_id: int):
    """Send an email for a Notification, with the right template per type.

    SECURITY: For job_alert, we look up the related JobPosting via the
    notification's `metadata` JSON (set by the producer), not by parsing
    free-text. We additionally verify the posting belongs to a watchlist
    company owned by the notification recipient — defense in depth against
    a bug elsewhere creating a Notification for user A pointing at user B's
    posting.
    """
    from apps.watchlist.models import JobPosting

    from .email import send_email, send_job_alert
    from .models import Notification

    try:
        notification = Notification.objects.select_related("user").get(pk=notification_id)
    except Notification.DoesNotExist:
        return

    user = notification.user

    if notification.type == "job_alert":
        posting_id = (notification.metadata or {}).get("posting_id")
        posting = None
        if isinstance(posting_id, int):
            posting = (
                JobPosting.objects.select_related("company")
                .filter(pk=posting_id, company__user=user)  # ownership check
                .first()
            )
        if posting:
            sent = send_job_alert(user, posting)
        else:
            # Fall through to plain email — but escape body since it might
            # contain user-controlled content from a different code path
            sent = send_email(
                user.email,
                notification.title,
                f"<p>{html.escape(notification.body)}</p>",
                notification.body,
            )
    else:
        sent = send_email(
            user.email,
            notification.title,
            f"<p>{html.escape(notification.body)}</p>",
            notification.body,
        )

    if not sent:
        logger.warning(f"Failed to send notification {notification_id} to {user.email}")
        raise self.retry()
