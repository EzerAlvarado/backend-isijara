from django.db import migrations, models


def migrar_categoria_desde_pieza(apps, schema_editor):
    Renta = apps.get_model("api", "Renta")
    Pieza = apps.get_model("api", "Pieza")
    for renta in Renta.objects.filter(linea_negocio="vestidos"):
        if renta.categoria_vestido:
            continue
        pieza_id = renta.pieza_saco_id
        if not pieza_id:
            continue
        pieza = Pieza.objects.filter(pk=pieza_id).first()
        if pieza and pieza.tipo in ("noche", "quince", "boda"):
            renta.categoria_vestido = pieza.tipo
            renta.save(update_fields=["categoria_vestido"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_pieza_vestidos_categorias_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="categoria_vestido",
            field=models.CharField(
                blank=True,
                choices=[
                    ("noche", "Noche"),
                    ("quince", "15 / Quinceañera"),
                    ("boda", "Boda"),
                ],
                db_index=True,
                help_text="Solo vestidos: noche, quince o boda",
                max_length=12,
            ),
        ),
        migrations.RunPython(migrar_categoria_desde_pieza, migrations.RunPython.noop),
    ]
