from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0036_perfil_usuario_vestido"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="cortedia",
            name="unique_corte_fecha_linea_turno",
        ),
        migrations.AddField(
            model_name="cortedia",
            name="categoria_vestido",
            field=models.CharField(
                blank=True,
                choices=[
                    ("noche", "Noche"),
                    ("quince", "XV / Quinceañera"),
                    ("boda", "Novia"),
                ],
                db_index=True,
                help_text="Solo vestidos: noche, quince o boda. Null para trajes.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="cortedia",
            constraint=models.UniqueConstraint(
                fields=["fecha", "linea_negocio", "turno", "categoria_vestido"],
                name="unique_corte_fecha_linea_turno_categoria",
            ),
        ),
        migrations.AddField(
            model_name="transaccion",
            name="categoria_vestido",
            field=models.CharField(
                blank=True,
                choices=[
                    ("noche", "Noche"),
                    ("quince", "XV / Quinceañera"),
                    ("boda", "Novia"),
                ],
                db_index=True,
                help_text="Solo vestidos: noche, quince o boda.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="vale",
            name="categoria_vestido",
            field=models.CharField(
                blank=True,
                choices=[
                    ("noche", "Noche"),
                    ("quince", "XV / Quinceañera"),
                    ("boda", "Novia"),
                ],
                db_index=True,
                help_text="Solo vestidos: noche, quince o boda.",
                max_length=20,
                null=True,
            ),
        ),
    ]
