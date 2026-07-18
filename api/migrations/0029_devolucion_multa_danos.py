from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0028_configuracion_codigos_pantalon"),
    ]

    operations = [
        migrations.AddField(
            model_name="devolucion",
            name="multa_perdonada",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devolucion",
            name="cargo_danos",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="devolucion",
            name="nota_danos",
            field=models.TextField(blank=True),
        ),
    ]
