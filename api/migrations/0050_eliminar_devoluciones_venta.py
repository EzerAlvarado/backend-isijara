from django.db import migrations


def eliminar_devoluciones_venta(apps, schema_editor):
    Devolucion = apps.get_model("api", "Devolucion")
    Devolucion.objects.filter(renta__tipo_operacion="venta").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0049_transaccion_anulada"),
    ]

    operations = [
        migrations.RunPython(eliminar_devoluciones_venta, migrations.RunPython.noop),
    ]
