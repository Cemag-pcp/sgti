# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_externalplatform'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalplatform',
            name='data_implantacao',
            field=models.DateField(blank=True, null=True),
        ),
    ]
