from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_ativo_link_termo"),
    ]

    operations = [
        migrations.CreateModel(
            name="AtivoMaintenance",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("descricao", models.TextField()),
                ("custo", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("data_manutencao", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ativo", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="manutencoes", to="core.ativo")),
            ],
            options={
                "ordering": ["-data_manutencao", "-id"],
            },
        ),
    ]
