from decimal import Decimal

from django.db import migrations, models


FONDO_FERIA_DEFAULT = Decimal("2732.00")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0022_corte_conteo_fondo"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionsistema",
            name="fondo_feria",
            field=models.DecimalField(
                decimal_places=2,
                default=FONDO_FERIA_DEFAULT,
                help_text="Fondo de feria (cambio) en caja, en MXN",
                max_digits=10,
            ),
        ),
    ]
