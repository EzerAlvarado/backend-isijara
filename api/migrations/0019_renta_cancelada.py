from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0018_pieza_estatus_pintura"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="cancelada",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
