from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0017_pieza_precio_premier"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pieza",
            name="estatus",
            field=models.CharField(
                choices=[
                    ("rentado", "Rentado"),
                    ("disponible", "Disponible"),
                    ("mantenimiento", "Mantenimiento"),
                    ("salio", "Fuera / Salió"),
                    ("sucio", "Sucio"),
                    ("mojado", "Mojado"),
                    ("en_ajustes", "En ajustes"),
                    ("listo_para_entregar", "Listo para entregar"),
                ],
                default="disponible",
                max_length=24,
            ),
        ),
    ]
