from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_password_reset_requested_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="excluded_keywords",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="target_job_types",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
