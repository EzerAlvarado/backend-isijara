from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0046_pedido_anio"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="excluir_corte",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Si True, el anticipo no genera transacción de corte (rentas de papel / cobro previo).",
            ),
        ),
    ]
