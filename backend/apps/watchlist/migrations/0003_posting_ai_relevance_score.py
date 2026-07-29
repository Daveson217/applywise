from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("watchlist", "0002_rule_matching_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobposting",
            name="ai_relevance_score",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
