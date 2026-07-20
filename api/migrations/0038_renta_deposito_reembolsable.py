from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0037_corte_categoria_vestido"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="deposito_reembolsable",
            field=models.CharField(
                blank=True,
                help_text="Depósito reembolsable (texto descriptivo, ej: $500)",
                max_length=100,
            ),
        ),
    ]
