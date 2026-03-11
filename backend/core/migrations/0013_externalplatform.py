# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_infralocationconfig_ticket_localizacao_problema'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalPlatform',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=150, unique=True)),
                ('responsavel', models.CharField(max_length=150)),
            ],
            options={
                'ordering': ['nome', 'id'],
            },
        ),
    ]
