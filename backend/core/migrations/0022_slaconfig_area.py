from django.db import migrations, models


def duplicate_sla_configs_by_area(apps, schema_editor):
    SLAConfig = apps.get_model("core", "SLAConfig")
    existing = list(SLAConfig.objects.all().values("prioridade", "horas", "area"))
    if not existing:
        return

    priorities_with_infra = {
        row["prioridade"]
        for row in existing
        if row.get("area") == "Infra"
    }

    for row in existing:
        if row.get("area") != "Dev":
            continue
        if row["prioridade"] in priorities_with_infra:
            continue
        SLAConfig.objects.create(
            area="Infra",
            prioridade=row["prioridade"],
            horas=row["horas"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_whatsappmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="slaconfig",
            name="area",
            field=models.CharField(default="Dev", max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="slaconfig",
            name="prioridade",
            field=models.CharField(max_length=20),
        ),
        migrations.RunPython(duplicate_sla_configs_by_area, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="slaconfig",
            options={"ordering": ["area", "id"]},
        ),
        migrations.AddConstraint(
            model_name="slaconfig",
            constraint=models.UniqueConstraint(
                fields=("area", "prioridade"),
                name="uniq_sla_area_prioridade",
            ),
        ),
    ]
