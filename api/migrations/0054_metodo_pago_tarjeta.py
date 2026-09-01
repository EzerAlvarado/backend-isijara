from django.db import migrations, models


METODOS_PAGO = [
    ("pesos", "Pesos"),
    ("dlls", "DLLS"),
    ("mixto", "Mixto"),
    ("bbva", "BBVA"),
    ("zelle", "Zelle"),
    ("transferencia", "Transferencia"),
    ("tarjeta", "Tarjeta"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0053_metodo_pago_transferencia"),
    ]

    operations = [
        migrations.AlterField(
            model_name="renta",
            name="metodo_pago",
            field=models.CharField(
                choices=METODOS_PAGO,
                default="pesos",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="transaccion",
            name="pago",
            field=models.CharField(choices=METODOS_PAGO, max_length=20),
        ),
        migrations.AlterField(
            model_name="abono",
            name="metodo_pago",
            field=models.CharField(choices=METODOS_PAGO, max_length=20),
        ),
        migrations.AlterField(
            model_name="vale",
            name="pago",
            field=models.CharField(
                choices=METODOS_PAGO,
                default="pesos",
                max_length=20,
            ),
        ),
    ]
