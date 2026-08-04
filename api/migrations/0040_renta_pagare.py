from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0039_renta_detalles_prendas"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="pagare",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Monto del pagaré (BUENO POR $)",
                max_digits=10,
            ),
        ),
    ]
