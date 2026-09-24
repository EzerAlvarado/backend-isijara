from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0054_metodo_pago_tarjeta"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionsistema",
            name="tinta_recibo",
            field=models.CharField(
                choices=[("negra", "Negra"), ("azul", "Azul marino")],
                default="negra",
                help_text="Color de impresión de recibos (usar azul si no hay tinta negra).",
                max_length=12,
            ),
        ),
    ]
