from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0043_pedido_servicio_faltante_boutique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pedido",
            name="servicio",
            field=models.CharField(
                choices=[
                    ("venta", "Venta"),
                    ("premier", "Premier"),
                    ("faltante_boutique", "Faltante boutique"),
                ],
                default="venta",
                max_length=32,
            ),
        ),
    ]
