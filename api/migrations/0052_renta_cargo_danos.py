from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0051_renta_paquete_premium"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="cargo_danos",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Multa por daños agregada después (p. ej. ya marcada como entregada).",
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="renta",
            name="nota_danos",
            field=models.TextField(blank=True),
        ),
    ]
