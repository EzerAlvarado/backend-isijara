from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0038_renta_deposito_reembolsable"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="detalles_saco",
            field=models.CharField(
                blank=True,
                help_text="Nombre/descripción del saco (ej: TRAJE AZUL INDIGO)",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="renta",
            name="detalles_chaleco",
            field=models.CharField(
                blank=True,
                help_text="Nombre/descripción del chaleco",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="renta",
            name="detalles_pantalon",
            field=models.CharField(
                blank=True,
                help_text="Nombre/descripción del pantalón",
                max_length=255,
            ),
        ),
    ]
