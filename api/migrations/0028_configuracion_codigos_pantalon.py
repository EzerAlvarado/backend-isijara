from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0027_renta_pago_mixto"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionsistema",
            name="usar_codigos_nuevos_pantalon",
            field=models.BooleanField(
                default=False,
                help_text="Si es falso, en pantalones se prefiere código viejo; si es verdadero, código nuevo",
            ),
        ),
    ]
