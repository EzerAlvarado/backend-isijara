from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0040_renta_pagare"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="fecha_evento",
            field=models.CharField(
                blank=True,
                help_text="Fecha del evento (recibo). Si vacío, se usa fecha de entrega.",
                max_length=32,
            ),
        ),
    ]
