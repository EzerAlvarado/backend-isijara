from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0047_renta_excluir_corte"),
    ]

    operations = [
        migrations.AlterField(
            model_name="renta",
            name="creado_en",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                help_text="Fecha y hora en que se registró la renta (editable).",
            ),
        ),
    ]
