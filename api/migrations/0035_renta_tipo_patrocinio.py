from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0034_corte_conteo_caja"),
    ]

    operations = [
        migrations.AlterField(
            model_name="renta",
            name="tipo_operacion",
            field=models.CharField(
                choices=[
                    ("renta", "Renta"),
                    ("venta", "Venta"),
                    ("premier", "Premier"),
                    ("sesion_fotos", "Sesión de fotos"),
                    ("patrocinio", "Patrocinio"),
                ],
                db_index=True,
                default="renta",
                max_length=15,
            ),
        ),
    ]
