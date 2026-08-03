from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("watchlist", "0003_posting_ai_relevance_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobposting",
            name="matched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobposting",
            name="match_dismissed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="jobposting",
            name="match_notified",
            field=models.BooleanField(default=False),
        ),
    ]
