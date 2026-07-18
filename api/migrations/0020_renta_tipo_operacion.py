from django.db import migrations, models


def _valor_celda(celda) -> str:
    if isinstance(celda, dict):
        return str(celda.get("valor", "")).strip().upper()
    return ""


def rellenar_tipo_operacion(apps, schema_editor):
    Renta = apps.get_model("api", "Renta")
    for renta in Renta.objects.all().iterator():
        if renta.linea_negocio == "vestidos":
            v = _valor_celda(renta.camisa)
            if v == "VENTA":
                tipo = "venta"
            elif v == "PREMIER":
                tipo = "premier"
            else:
                tipo = "renta"
        elif renta.tipo_entrega == "premier":
            tipo = "premier"
        else:
            tipo = "renta"
        Renta.objects.filter(pk=renta.pk).update(tipo_operacion=tipo)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0019_renta_cancelada"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="tipo_operacion",
            field=models.CharField(
                choices=[("renta", "Renta"), ("venta", "Venta"), ("premier", "Premier")],
                db_index=True,
                default="renta",
                max_length=10,
            ),
        ),
        migrations.RunPython(rellenar_tipo_operacion, migrations.RunPython.noop),
    ]
