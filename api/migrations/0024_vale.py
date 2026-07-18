from decimal import Decimal

from django.db import migrations, models

import api.models.linea_negocio
import api.models.metodo_pago


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0023_configuracion_fondo_feria"),
    ]

    operations = [
        migrations.CreateModel(
            name="Vale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateField()),
                ("concepto", models.CharField(max_length=200)),
                ("monto", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "pago",
                    models.CharField(
                        choices=api.models.metodo_pago.MetodoPago.choices,
                        default="pesos",
                        max_length=20,
                    ),
                ),
                ("monto_mxn", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "estatus",
                    models.CharField(
                        choices=[("pendiente", "Pendiente"), ("repuesto", "Repuesto")],
                        db_index=True,
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                (
                    "linea_negocio",
                    models.CharField(
                        choices=api.models.linea_negocio.LineaNegocio.choices,
                        db_index=True,
                        default="trajes",
                        max_length=20,
                    ),
                ),
                ("repuesto_en", models.DateTimeField(blank=True, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "transaccion",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=models.CASCADE,
                        related_name="vale",
                        to="api.transaccion",
                    ),
                ),
            ],
            options={
                "verbose_name": "vale",
                "verbose_name_plural": "vales",
                "ordering": ["-fecha", "-creado_en"],
            },
        ),
    ]
