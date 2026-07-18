from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0025_corte_turno"),
    ]

    operations = [
        migrations.AddField(
            model_name="cortedia",
            name="empleado_corte",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Nombre del empleado que realizó el cierre de caja.",
                max_length=120,
            ),
        ),
    ]
