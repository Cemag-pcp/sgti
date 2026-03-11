from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_notificationrecipient_telefone"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsappMessage",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("numero", models.CharField(db_index=True, max_length=50)),
                ("ticket_id", models.CharField(blank=True, default="", max_length=50)),
                ("direcao", models.CharField(choices=[("in", "Entrada"), ("out", "Saida")], max_length=10)),
                (
                    "origem",
                    models.CharField(
                        choices=[("usuario", "Usuario"), ("bot", "Bot"), ("tecnico", "Tecnico")],
                        default="bot",
                        max_length=20,
                    ),
                ),
                ("texto", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "session",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="messages",
                        to="core.whatsappsession",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="whatsapp_messages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
    ]
