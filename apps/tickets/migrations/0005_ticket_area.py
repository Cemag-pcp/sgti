from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0004_whatsappconversation'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='area',
            field=models.CharField(
                blank=True,
                choices=[
                    ('DEVELOPMENT', 'Desenvolvimento'),
                    ('INFRASTRUCTURE', 'Infraestrutura'),
                ],
                max_length=20,
                verbose_name='Área',
            ),
        ),
    ]
