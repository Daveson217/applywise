from django.db import migrations, models


class Migration(migrations.Migration):
    """Rename the AIGeneration index to a deterministic name that matches the
    model, so makemigrations stops detecting a phantom change."""

    dependencies = [
        ("ai", "0002_aigeneration"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="aigeneration",
            name="ai_aigenera_user_id_feature_idx",
        ),
        migrations.AddIndex(
            model_name="aigeneration",
            index=models.Index(
                fields=["user", "feature", "-created_at"],
                name="ai_gen_user_feat_created_idx",
            ),
        ),
    ]
