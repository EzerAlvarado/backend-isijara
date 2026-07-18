from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_renta_categoria_vestido"),
    ]

    operations = [
        migrations.AddField(
            model_name="pieza",
            name="precio_premier",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Precio de renta Premier / a domicilio (vestidos)",
                max_digits=10,
            ),
        ),
    ]
