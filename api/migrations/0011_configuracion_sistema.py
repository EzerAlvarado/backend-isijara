from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_renta_metodo_pago"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfiguracionSistema",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo_cambio_usd",
                    models.DecimalField(
                        decimal_places=2,
                        default="18.50",
                        help_text="Pesos mexicanos por 1 USD",
                        max_digits=8,
                    ),
                ),
                ("precios_referencia", models.JSONField(blank=True, default=list)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "configuración del sistema",
                "verbose_name_plural": "configuración del sistema",
            },
        ),
    ]
