from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_profile_default_llm_model_alter"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="watchlist_digest_frequency",
            field=models.CharField(
                choices=[("off", "Off"), ("daily", "Daily"), ("weekly", "Weekly")],
                default="daily",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="watchlist_digest_last_sent",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
