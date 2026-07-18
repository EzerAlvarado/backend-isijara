from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0033_vestidos_estatus_sesion_fotos"),
    ]

    operations = [
        migrations.AddField(
            model_name="cortedia",
            name="conteo_caja",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
