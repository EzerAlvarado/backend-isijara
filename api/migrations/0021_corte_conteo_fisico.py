from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0020_renta_tipo_operacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="cortedia",
            name="conteo_fisico",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
