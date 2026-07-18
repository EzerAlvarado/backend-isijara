from django.db import migrations, models


def renombrar_vestidos_a_noche(apps, schema_editor):
    User = apps.get_model("auth", "User")
    PerfilUsuario = apps.get_model("api", "PerfilUsuario")

    if User.objects.filter(username="noche").exists():
        return

    try:
        user = User.objects.get(username="vestidos")
    except User.DoesNotExist:
        return

    user.username = "noche"
    user.save(update_fields=["username"])

    perfil = PerfilUsuario.objects.filter(user=user).first()
    if perfil:
        perfil.perfil_vestido = "noche"
        perfil.save(update_fields=["perfil_vestido"])


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0035_renta_tipo_patrocinio"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="perfil_vestido",
            field=models.CharField(
                blank=True,
                choices=[
                    ("noche", "Noche"),
                    ("quince", "XV / Quinceañera"),
                    ("boda", "Novia"),
                ],
                help_text="Solo línea vestidos: categoría asignada al usuario.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(renombrar_vestidos_a_noche, migrations.RunPython.noop),
    ]
