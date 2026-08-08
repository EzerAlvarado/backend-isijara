from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0041_renta_fecha_evento"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cliente", models.CharField(max_length=255)),
                (
                    "tipo_pedido",
                    models.CharField(
                        choices=[
                            ("tuxedo", "Tuxedo"),
                            ("noche", "Noche"),
                            ("xv", "XV"),
                            ("novia", "Novia"),
                        ],
                        default="tuxedo",
                        max_length=16,
                    ),
                ),
                (
                    "estatus",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("en_proceso", "En proceso"),
                            ("en_boutique", "En boutique"),
                            ("en_camino", "En camino"),
                            ("con_kayla", "Con Kayla"),
                            ("no_hay", "No hay"),
                            ("entregado", "Entregado"),
                            ("cancelado", "Cancelado"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("estilo_piezas", models.TextField(blank=True, default="")),
                (
                    "servicio",
                    models.CharField(
                        choices=[
                            ("venta", "Venta"),
                            ("premier", "Premier"),
                        ],
                        default="venta",
                        max_length=32,
                    ),
                ),
                ("fecha_entrega", models.CharField(blank=True, default="", max_length=120)),
                ("comentarios", models.TextField(blank=True, default="")),
                (
                    "mes_etiqueta",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Etiqueta de mes para agrupar (ej. JULIO). Vacío = sin grupo.",
                        max_length=40,
                    ),
                ),
                ("orden", models.PositiveIntegerField(default=0)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["mes_etiqueta", "orden", "-id"],
            },
        ),
    ]
