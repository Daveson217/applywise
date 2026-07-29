from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("watchlist", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="watchlistrule",
            name="exclude_keywords",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="watchlistrule",
            name="search_description",
            field=models.BooleanField(default=False),
        ),
    ]
