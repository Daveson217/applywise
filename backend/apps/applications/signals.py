from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Application, ApplicationActivity


@receiver(pre_save, sender=Application)
def log_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Application.objects.get(pk=instance.pk)
    except Application.DoesNotExist:
        return

    if old_instance.status != instance.status:
        ApplicationActivity.objects.create(
            application=instance,
            event_type="status_change",
            old_value=old_instance.status,
            new_value=instance.status,
        )
