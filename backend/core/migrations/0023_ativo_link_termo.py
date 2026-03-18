from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_slaconfig_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="ativo",
            name="link_termo",
            field=models.URLField(blank=True, default=""),
        ),
    ]
