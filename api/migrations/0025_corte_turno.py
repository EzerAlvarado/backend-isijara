from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0024_vale"),
    ]

    operations = [
        migrations.AddField(
            model_name="cortedia",
            name="turno",
            field=models.CharField(
                choices=[("manana", "Mañana"), ("tarde", "Tarde")],
                db_index=True,
                default="manana",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="cortedia",
            name="omitido",
            field=models.BooleanField(
                default=False,
                help_text="Turno de mañana cerrado automáticamente al hacer corte de tarde.",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="cortedia",
            name="unique_corte_fecha_linea",
        ),
        migrations.AddConstraint(
            model_name="cortedia",
            constraint=models.UniqueConstraint(
                fields=("fecha", "linea_negocio", "turno"),
                name="unique_corte_fecha_linea_turno",
            ),
        ),
    ]
