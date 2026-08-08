from django.db import migrations, models


class Migration(migrations.Migration):
    """
    1) Amplía servicio a varchar(32) con SQL directo (esquema real en Railway).
    2) Renombra faltante_boutique -> faltante (cabe en 16 y queda estable).
    """

    dependencies = [
        ("api", "0044_pedido_servicio_max_length"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="pedido",
                    name="servicio",
                    field=models.CharField(
                        choices=[
                            ("venta", "Venta"),
                            ("premier", "Premier"),
                            ("faltante", "Faltante boutique"),
                        ],
                        default="venta",
                        max_length=32,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE api_pedido
                        ALTER COLUMN servicio TYPE varchar(32);
                        UPDATE api_pedido
                        SET servicio = 'faltante'
                        WHERE servicio = 'faltante_boutique';
                    """,
                    reverse_sql="""
                        UPDATE api_pedido
                        SET servicio = 'faltante_boutique'
                        WHERE servicio = 'faltante';
                        ALTER TABLE api_pedido
                        ALTER COLUMN servicio TYPE varchar(16);
                    """,
                ),
            ],
        ),
    ]
