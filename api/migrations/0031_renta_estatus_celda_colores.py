from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0030_renta_fecha_salio_real"),
    ]

    operations = [
        migrations.AlterField(
            model_name="renta",
            name="estatus_fila",
            field=models.CharField(
                blank=True,
                choices=[
                    ("normal", "Normal"),
                    ("arrugado", "Arrugado"),
                    ("listo_empacar", "Listo para empacar"),
                    ("sucio", "Sucio"),
                    ("salio", "Fuera / Salió"),
                    ("mojado", "Mojado"),
                    ("listo_para_entregar", "Listo para entregar"),
                    ("en_ajustes", "Ajustes"),
                    ("otra_situacion", "Otra situación"),
                ],
                max_length=24,
            ),
        ),
    ]
