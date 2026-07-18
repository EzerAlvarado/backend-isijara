from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0032_abono"),
    ]

    operations = [
        migrations.AlterField(
            model_name="renta",
            name="estatus_fila",
            field=models.CharField(
                blank=True,
                choices=[
                    ("normal", "Normal"),
                    ("arrugado", "Arrugado"),
                    ("listo_empacar", "Listo para empacar"),
                    ("sucio", "Sucio"),
                    ("salio", "Fuera / Salió"),
                    ("mojado", "Mojado"),
                    ("listo_para_entregar", "Listo para entregar"),
                    ("en_ajustes", "Ajustes"),
                    ("otra_situacion", "Otra situación"),
                    ("entregado", "Entregado"),
                    ("venta", "Venta (texto azul)"),
                    ("premier", "Premier (texto morado)"),
                    ("sesion_fotos", "Sesión de fotos"),
                ],
                max_length=24,
            ),
        ),
        migrations.AlterField(
            model_name="renta",
            name="tipo_operacion",
            field=models.CharField(
                choices=[
                    ("renta", "Renta"),
                    ("venta", "Venta"),
                    ("premier", "Premier"),
                    ("sesion_fotos", "Sesión de fotos"),
                ],
                db_index=True,
                default="renta",
                max_length=15,
            ),
        ),
    ]
