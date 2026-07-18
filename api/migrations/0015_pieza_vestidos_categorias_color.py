from django.db import migrations, models


def migrar_categorias_vestidos(apps, schema_editor):
    Pieza = apps.get_model("api", "Pieza")
    Pieza.objects.filter(linea_negocio="vestidos", tipo="vestido").update(tipo="quince")
    Pieza.objects.filter(linea_negocio="vestidos", tipo="accesorio").update(tipo="quince")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_pieza_vestidos_inventario"),
    ]

    operations = [
        migrations.AddField(
            model_name="pieza",
            name="color_vestido",
            field=models.CharField(
                blank=True,
                help_text="Descripción del vestido (ej. VERDE SAGE CON BRILLOS)",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="pieza",
            name="color",
            field=models.CharField(
                help_text="Color mero (ej. VERDE, ROSA)",
                max_length=120,
            ),
        ),
        migrations.AlterField(
            model_name="pieza",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("saco", "Saco"),
                    ("chaleco", "Chaleco"),
                    ("pantalon", "Pantalón"),
                    ("quince", "15 / Quinceañera"),
                    ("boda", "Boda"),
                    ("noche", "Noche"),
                    ("vestido", "Vestido"),
                    ("accesorio", "Accesorio"),
                ],
                max_length=12,
            ),
        ),
        migrations.RunPython(migrar_categorias_vestidos, migrations.RunPython.noop),
    ]
