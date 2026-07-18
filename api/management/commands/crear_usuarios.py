from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from api.models import LineaNegocio, PerfilUsuario
from api.models.renta import Renta
from api.services.finanzas import obtener_configuracion


USUARIOS = [
    {"username": "trajes", "password": "trajes123", "linea": LineaNegocio.TRAJES},
    {
        "username": "noche",
        "password": "noche123",
        "linea": LineaNegocio.VESTIDOS,
        "perfil_vestido": Renta.CategoriaVestido.NOCHE,
    },
    {
        "username": "xv",
        "password": "xv123",
        "linea": LineaNegocio.VESTIDOS,
        "perfil_vestido": Renta.CategoriaVestido.QUINCE,
    },
    {
        "username": "novia",
        "password": "novia123",
        "linea": LineaNegocio.VESTIDOS,
        "perfil_vestido": Renta.CategoriaVestido.BODA,
    },
]


class Command(BaseCommand):
    help = "Crea usuarios trajes, noche, xv y novia con su perfil de negocio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Actualiza contraseña si el usuario ya existe.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        for datos in USUARIOS:
            user, created = User.objects.get_or_create(
                username=datos["username"],
                defaults={"is_staff": False, "is_superuser": False},
            )
            if created or force:
                user.set_password(datos["password"])
                user.save()
                accion = "creado" if created else "actualizado"
            else:
                accion = "ya existía"

            perfil_defaults = {"linea_negocio": datos["linea"]}
            if datos.get("perfil_vestido"):
                perfil_defaults["perfil_vestido"] = datos["perfil_vestido"]

            perfil, _ = PerfilUsuario.objects.update_or_create(
                user=user,
                defaults=perfil_defaults,
            )
            obtener_configuracion(datos["linea"])

            extra = ""
            if perfil.perfil_vestido:
                extra = f" · {perfil.get_perfil_vestido_display()}"

            self.stdout.write(
                self.style.SUCCESS(
                    f"Usuario '{user.username}' ({perfil.get_linea_negocio_display()}{extra}) — {accion}"
                )
            )

        self.stdout.write("")
        self.stdout.write("Credenciales por defecto:")
        self.stdout.write("  trajes / trajes123")
        self.stdout.write("  noche  / noche123")
        self.stdout.write("  xv     / xv123")
        self.stdout.write("  novia  / novia123")
