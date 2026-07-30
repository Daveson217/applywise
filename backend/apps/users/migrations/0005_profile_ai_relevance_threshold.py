from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_profile_ai_relevance_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="ai_relevance_threshold",
            field=models.FloatField(default=0.6),
        ),
    ]
