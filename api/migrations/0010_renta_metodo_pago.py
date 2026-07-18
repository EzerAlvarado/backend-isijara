from django.db import migrations, models


def migrar_pagos_transaccion(apps, schema_editor):
    Transaccion = apps.get_model("api", "Transaccion")
    mapping = {
        "Efectivo": "pesos",
        "Tarjeta": "bbva",
        "Transferencia": "zelle",
    }
    for old, new in mapping.items():
        Transaccion.objects.filter(pago=old).update(pago=new)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_corte_dia"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="metodo_pago",
            field=models.CharField(
                choices=[
                    ("pesos", "Pesos"),
                    ("dlls", "DLLS"),
                    ("bbva", "BBVA"),
                    ("zelle", "Zelle"),
                ],
                default="pesos",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrar_pagos_transaccion, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="transaccion",
            name="pago",
            field=models.CharField(
                choices=[
                    ("pesos", "Pesos"),
                    ("dlls", "DLLS"),
                    ("bbva", "BBVA"),
                    ("zelle", "Zelle"),
                ],
                max_length=20,
            ),
        ),
    ]
