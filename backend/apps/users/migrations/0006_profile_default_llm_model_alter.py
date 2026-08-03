from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_profile_ai_relevance_threshold"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="default_llm_model",
            field=models.CharField(default="gemini-3.5-flash-lite", max_length=50),
        ),
    ]
