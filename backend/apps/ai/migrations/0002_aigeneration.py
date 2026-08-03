from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AIGeneration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "feature",
                    models.CharField(
                        choices=[
                            ("qa", "Question Answer"),
                            ("fit_score", "Fit Score"),
                            ("ats_score", "ATS Score"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=255)),
                ("input", models.JSONField(blank=True, default=dict)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("provider", models.CharField(blank=True, max_length=20)),
                ("model", models.CharField(blank=True, max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="ai_generations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["user", "feature", "-created_at"],
                        name="ai_aigenera_user_id_feature_idx",
                    )
                ],
            },
        ),
    ]
