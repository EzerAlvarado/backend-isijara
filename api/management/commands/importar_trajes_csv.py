import csv
from django.core.management.base import BaseCommand
from api.models import Prenda, LineaNegocio


class Command(BaseCommand):
    help = "Importa trajes desde un archivo CSV"

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str, help="Ruta al archivo CSV")
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina todas las prendas de trajes antes de importar",
        )

    def handle(self, *args, **options):
        archivo = options["archivo"]
        limpiar = options["limpiar"]

        if limpiar:
            count, _ = Prenda.objects.filter(linea_negocio=LineaNegocio.TRAJES).delete()
            self.stdout.write(self.style.WARNING(f"Eliminadas {count} prendas existentes"))

        importadas = 0
        errores = 0

        with open(archivo, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    detalles = (row.get("detalles") or "").strip()
                    marca = (row.get("marca") or "").strip()
                    color_saco = (row.get("color saco") or "").strip()
                    saco = (row.get("saco") or "").strip()
                    color_chaleco = (row.get("color chaleco") or "").strip()
                    chaleco = (row.get("chaleco") or "").strip()
                    color_pantalon = (row.get("color pantalon") or "").strip()
                    pantalon = (row.get("pantalon") or "").strip()
                    codigo_old = (row.get("codigo old") or "").strip()
                    codigo_new = (row.get("codigo new") or "").strip()

                    if not detalles:
                        continue

                    # Determinar color principal (prioridad: saco > chaleco > pantalon)
                    color = color_saco or color_chaleco or color_pantalon or "SIN COLOR"
                    
                    # Determinar talla principal (del saco si existe)
                    talla = saco or chaleco or pantalon or "ÚNICA"

                    # Construir campos de prendas con color + talla
                    saco_completo = f"{color_saco} {saco}".strip() if saco else ""
                    chaleco_completo = f"{color_chaleco} {chaleco}".strip() if chaleco else ""
                    pantalon_completo = f"{color_pantalon} {pantalon}".strip() if pantalon else ""

                    Prenda.objects.create(
                        detalles=detalles,
                        marca=marca,
                        color=color,
                        talla=talla,
                        saco=saco_completo,
                        chaleco=chaleco_completo,
                        pantalon=pantalon_completo,
                        codigo_old=codigo_old,
                        codigo_new=codigo_new,
                        estatus=Prenda.Estatus.DISPONIBLE,
                        linea_negocio=LineaNegocio.TRAJES,
                    )
                    importadas += 1

                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error en fila: {row} — {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Importación completada: {importadas} prendas importadas, {errores} errores")
        )
