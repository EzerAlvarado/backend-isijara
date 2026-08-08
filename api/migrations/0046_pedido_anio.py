from django.db import migrations, models


def asignar_anio_2026(apps, schema_editor):
    Pedido = apps.get_model("api", "Pedido")
    Pedido.objects.all().update(anio=2026)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0045_pedido_servicio_varchar32_sql"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="anio",
            field=models.PositiveIntegerField(
                default=2026,
                help_text="Año del grupo (ej. 2026, 2027).",
            ),
        ),
        migrations.RunPython(asignar_anio_2026, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="pedido",
            options={"ordering": ["anio", "mes_etiqueta", "orden", "-id"]},
        ),
    ]
