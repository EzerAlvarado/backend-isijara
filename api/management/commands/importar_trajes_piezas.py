import csv
from django.core.management.base import BaseCommand
from api.models import Pieza, LineaNegocio


class Command(BaseCommand):
    help = "Importa trajes desde CSV como piezas (saco, chaleco, pantalón)"

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str, help="Ruta al archivo CSV")
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina todas las piezas de trajes antes de importar",
        )

    def handle(self, *args, **options):
        archivo = options["archivo"]
        limpiar = options["limpiar"]

        if limpiar:
            count, _ = Pieza.objects.filter(linea_negocio=LineaNegocio.TRAJES).delete()
            self.stdout.write(self.style.WARNING(f"Eliminadas {count} piezas existentes"))

        sacos = 0
        chalecos = 0
        pantalones = 0
        errores = 0

        with open(archivo, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    detalles = (row.get("detalles") or "").strip()
                    marca = (row.get("marca") or "").strip()
                    color_saco = (row.get("color saco") or "").strip()
                    talla_saco = (row.get("saco") or "").strip()
                    color_chaleco = (row.get("color chaleco") or "").strip()
                    talla_chaleco = (row.get("chaleco") or "").strip()
                    color_pantalon = (row.get("color pantalon") or "").strip()
                    talla_pantalon = (row.get("pantalon") or "").strip()
                    codigo_old = (row.get("codigo old") or "").strip()
                    codigo_new = (row.get("codigo new") or "").strip()

                    if not detalles:
                        continue

                    # El conjunto agrupa las piezas del mismo traje
                    conjunto = codigo_new or codigo_old or ""

                    # Crear SACO si tiene datos
                    if talla_saco:
                        Pieza.objects.create(
                            tipo=Pieza.Tipo.SACO,
                            color=color_saco or "SIN COLOR",
                            talla=talla_saco,
                            marca=marca,
                            detalles=detalles,
                            codigo_old=codigo_old,
                            codigo_new=codigo_new,
                            conjunto=conjunto,
                            estatus=Pieza.Estatus.DISPONIBLE,
                            linea_negocio=LineaNegocio.TRAJES,
                        )
                        sacos += 1

                    # Crear CHALECO si tiene datos
                    if talla_chaleco:
                        Pieza.objects.create(
                            tipo=Pieza.Tipo.CHALECO,
                            color=color_chaleco or "SIN COLOR",
                            talla=talla_chaleco,
                            marca=marca,
                            detalles=detalles,
                            codigo_old=codigo_old,
                            codigo_new=codigo_new,
                            conjunto=conjunto,
                            estatus=Pieza.Estatus.DISPONIBLE,
                            linea_negocio=LineaNegocio.TRAJES,
                        )
                        chalecos += 1

                    # Crear PANTALÓN si tiene datos
                    if talla_pantalon:
                        Pieza.objects.create(
                            tipo=Pieza.Tipo.PANTALON,
                            color=color_pantalon or "SIN COLOR",
                            talla=talla_pantalon,
                            marca=marca,
                            detalles=detalles,
                            codigo_old=codigo_old,
                            codigo_new=codigo_new,
                            conjunto=conjunto,
                            estatus=Pieza.Estatus.DISPONIBLE,
                            linea_negocio=LineaNegocio.TRAJES,
                        )
                        pantalones += 1

                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error en fila: {row} — {e}")
                    )

        total = sacos + chalecos + pantalones
        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completada: {total} piezas ({sacos} sacos, {chalecos} chalecos, {pantalones} pantalones), {errores} errores"
            )
        )
