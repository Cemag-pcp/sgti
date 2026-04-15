from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_device_ticket_device'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BrowserPushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.TextField(unique=True, verbose_name='Endpoint')),
                ('p256dh', models.CharField(max_length=255, verbose_name='Chave p256dh')),
                ('auth', models.CharField(max_length=255, verbose_name='Chave auth')),
                ('user_agent', models.CharField(blank=True, max_length=255, verbose_name='User-Agent')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_success_at', models.DateTimeField(blank=True, null=True, verbose_name='Último envio com sucesso')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_subscriptions', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Inscrição de push',
                'verbose_name_plural': 'Inscrições de push',
                'ordering': ['-updated_at'],
            },
        ),
    ]
