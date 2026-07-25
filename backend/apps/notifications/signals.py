"""Post-save signal that fires email send on Notification creation."""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def trigger_email_send(sender, instance, created, **kwargs):
    """When a new Notification is committed, enqueue email delivery.

    `transaction.on_commit` ensures the Celery worker can never pick up the
    task before the row is visible in the database. Without it, on systems
    with read-replicas or under heavy load, the worker can fetch the
    notification before the producer transaction commits and get a
    DoesNotExist.
    """
    if not created:
        return

    def _enqueue():
        try:
            from .tasks import send_notification_email

            send_notification_email.delay(instance.id)
        except Exception as e:
            logger.error(
                f"Failed to enqueue email for notification {instance.id}: {e}"
            )

    transaction.on_commit(_enqueue)
