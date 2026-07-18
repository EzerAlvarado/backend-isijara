from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_configuracion_sistema"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionsistema",
            name="multa_por_dia",
            field=models.DecimalField(
                decimal_places=2,
                default="15.00",
                help_text="Multa en MXN por cada día de retraso en devolución",
                max_digits=8,
            ),
        ),
    ]
