from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_profile_job_preferences"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="ai_relevance_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
