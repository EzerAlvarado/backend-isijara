from decimal import Decimal

from django.db import migrations, models


FONDO_FERIA_DEFAULT = Decimal("2732.00")


def fondo_feria_por_defecto(apps, schema_editor):
    CorteDia = apps.get_model("api", "CorteDia")
    CorteDia.objects.filter(fondo_inicial=0).update(fondo_inicial=FONDO_FERIA_DEFAULT)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0021_corte_conteo_fisico"),
    ]

    operations = [
        migrations.AddField(
            model_name="cortedia",
            name="conteo_fondo",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="cortedia",
            name="fondo_inicial",
            field=models.DecimalField(
                decimal_places=2,
                default=FONDO_FERIA_DEFAULT,
                max_digits=10,
            ),
        ),
        migrations.RunPython(fondo_feria_por_defecto, migrations.RunPython.noop),
    ]
