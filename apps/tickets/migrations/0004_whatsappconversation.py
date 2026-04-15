from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_location_ticket_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsAppConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=30, unique=True, verbose_name='Telefone')),
                ('state', models.CharField(choices=[('AWAITING_COMMAND', 'Aguardando comando'), ('AWAITING_MATRICULA', 'Aguardando matricula'), ('AWAITING_NAME', 'Aguardando nome'), ('AWAITING_TITLE', 'Aguardando titulo'), ('AWAITING_DESCRIPTION', 'Aguardando descricao'), ('COMPLETED', 'Concluida')], default='AWAITING_COMMAND', max_length=30, verbose_name='Estado')),
                ('context', models.JSONField(blank=True, default=dict, verbose_name='Contexto')),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Conversa do WhatsApp',
                'verbose_name_plural': 'Conversas do WhatsApp',
                'ordering': ['-last_message_at'],
            },
        ),
    ]
