from django.core.management.base import BaseCommand

from api.models import Prenda

PRENDAS_INICIALES = [
    {
        "talla": "S",
        "color": "NEGRO",
        "detalles": "TRAJE NEGRO LISO",
        "marca": "ANTONIO UOMO",
        "saco": "36R",
        "chaleco": "36R",
        "pantalon": "30R",
        "codigo_old": "103",
        "codigo_new": "N-0103",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "S",
        "color": "NEGRO",
        "detalles": "TUX NEGRO SS",
        "marca": "BELLIO",
        "saco": "36S",
        "chaleco": "X",
        "pantalon": "30S",
        "codigo_old": "113",
        "codigo_new": "N-0113",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "S",
        "color": "NEGRO",
        "detalles": "TRAJE NEGRO LISO METALICO",
        "marca": "RIZZA",
        "saco": "38R",
        "chaleco": "X",
        "pantalon": "X",
        "codigo_old": "109",
        "codigo_new": "N-0109",
        "estatus": Prenda.Estatus.MANTENIMIENTO,
    },
    {
        "talla": "M",
        "color": "NEGRO",
        "detalles": "TRAJE NEGRO LISO",
        "marca": "RETRO PARIS",
        "saco": "38R",
        "chaleco": "38R",
        "pantalon": "32R",
        "codigo_old": "104",
        "codigo_new": "N-0104",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "M",
        "color": "NEGRO",
        "detalles": "TUX NEGRO SS",
        "marca": "GINO VITALE",
        "saco": "40R",
        "chaleco": "40R",
        "pantalon": "34R",
        "codigo_old": "114",
        "codigo_new": "N-0114",
        "estatus": Prenda.Estatus.RENTADO,
    },
    {
        "talla": "M",
        "color": "NEGRO",
        "detalles": "TRAJE NEGRO LISO METALICO",
        "marca": "FERRECCI",
        "saco": "40R",
        "chaleco": "X",
        "pantalon": "34W",
        "codigo_old": "110",
        "codigo_new": "N-0110",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "L",
        "color": "NEGRO",
        "detalles": "TRAJE NEGRO LISO",
        "marca": "GQ",
        "saco": "42R",
        "chaleco": "42R",
        "pantalon": "36R",
        "codigo_old": "105",
        "codigo_new": "N-0105",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "L",
        "color": "NEGRO",
        "detalles": "TUX NEGRO SS",
        "marca": "ANTONIO UOMO",
        "saco": "44R",
        "chaleco": "X",
        "pantalon": "38R",
        "codigo_old": "115",
        "codigo_new": "N-0115",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "L",
        "color": "NEGRO",
        "detalles": "TRAJE NEGRO LISO METALICO",
        "marca": "BELLIO",
        "saco": "44R",
        "chaleco": "44R",
        "pantalon": "AJUST 36-40",
        "codigo_old": "111",
        "codigo_new": "N-0111",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
    {
        "talla": "L",
        "color": "NEGRO",
        "detalles": "TUX NEGRO METALICO",
        "marca": "RIZZA",
        "saco": "46R",
        "chaleco": "X",
        "pantalon": "40R",
        "codigo_old": "112",
        "codigo_new": "N-0112",
        "estatus": Prenda.Estatus.DISPONIBLE,
    },
]


class Command(BaseCommand):
    help = "Carga prendas de ejemplo en el inventario (solo si está vacío)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Borra el inventario existente y vuelve a cargar.",
        )

    def handle(self, *args, **options):
        if Prenda.objects.exists():
            if not options["force"]:
                self.stdout.write(
                    self.style.WARNING(
                        "Ya hay prendas en la base de datos. Usa --force para reemplazar."
                    )
                )
                return
            count = Prenda.objects.count()
            Prenda.objects.all().delete()
            self.stdout.write(f"Eliminadas {count} prendas existentes.")

        creadas = Prenda.objects.bulk_create([Prenda(**p) for p in PRENDAS_INICIALES])
        self.stdout.write(self.style.SUCCESS(f"Se cargaron {len(creadas)} prendas de ejemplo."))
