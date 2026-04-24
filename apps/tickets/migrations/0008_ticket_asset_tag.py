from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0007_browserpushsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='asset_tag',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Tombamento informado'),
            preserve_default=False,
        ),
    ]
