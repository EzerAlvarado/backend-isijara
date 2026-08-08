from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0048_renta_creado_en_editable"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaccion",
            name="anulada",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Si es True, no cuenta en el corte (caso excepcional).",
            ),
        ),
        migrations.AddField(
            model_name="transaccion",
            name="anulada_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
