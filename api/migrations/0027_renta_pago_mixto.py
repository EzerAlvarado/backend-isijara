from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0026_corte_empleado"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="feria_mxn",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Cambio entregado al cliente en pesos.",
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="renta",
            name="pago_efectivo_mxn",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Efectivo recibido en pesos (pago mixto o contado).",
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="renta",
            name="pago_efectivo_usd",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Efectivo recibido en dólares.",
                max_digits=10,
            ),
        ),
    ]
