from django.core.management.base import BaseCommand

from api.models import Pieza, Prenda


def _pieza_valida(valor: str) -> bool:
    v = (valor or "").strip().upper()
    return bool(v) and v not in ("X", "—", "-", "NO", "N/A")


class Command(BaseCommand):
    help = "Convierte trajes (Prenda) en piezas sueltas de inventario (Pieza)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Borra piezas existentes y vuelve a generar desde Prenda.",
        )

    def handle(self, *args, **options):
        if Pieza.objects.exists():
            if not options["force"]:
                self.stdout.write(
                    self.style.WARNING(
                        "Ya hay piezas. Usa --force para regenerar desde Prenda."
                    )
                )
                return
            count = Pieza.objects.count()
            Pieza.objects.all().delete()
            self.stdout.write(f"Eliminadas {count} piezas.")

        creadas = 0
        conjunto_id = 0
        for prenda in Prenda.objects.all():
            conjunto_id += 1
            codigo = prenda.codigo_new or prenda.codigo_old or f"P-{prenda.pk}"
            base = {
                "marca": prenda.marca,
                "detalles": prenda.detalles,
                "codigo_old": prenda.codigo_old,
                "codigo_new": prenda.codigo_new,
                "conjunto": codigo,
                "estatus": prenda.estatus,
                "ubicacion": prenda.ubicacion,
            }
            if _pieza_valida(prenda.saco):
                Pieza.objects.create(
                    tipo=Pieza.Tipo.SACO,
                    color=prenda.color.upper(),
                    talla=prenda.saco.upper(),
                    **base,
                )
                creadas += 1
            if _pieza_valida(prenda.chaleco):
                Pieza.objects.create(
                    tipo=Pieza.Tipo.CHALECO,
                    color=prenda.color.upper(),
                    talla=prenda.chaleco.upper(),
                    **base,
                )
                creadas += 1
            if _pieza_valida(prenda.pantalon):
                Pieza.objects.create(
                    tipo=Pieza.Tipo.PANTALON,
                    color=prenda.color.upper(),
                    talla=prenda.pantalon.upper(),
                    **base,
                )
                creadas += 1

        self.stdout.write(self.style.SUCCESS(f"Se crearon {creadas} piezas de inventario."))
