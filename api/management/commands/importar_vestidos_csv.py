import csv
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from api.models import Pieza, LineaNegocio


class Command(BaseCommand):
    help = "Importa vestidos desde CSV (noche, quince, boda)"

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str, help="Ruta al archivo CSV")
        parser.add_argument(
            "--tipo",
            type=str,
            choices=["noche", "quince", "boda"],
            default="noche",
            help="Tipo de vestido (noche, quince, boda)",
        )
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina vestidos del tipo especificado antes de importar",
        )

    def handle(self, *args, **options):
        archivo = options["archivo"]
        tipo = options["tipo"]
        limpiar = options["limpiar"]

        if limpiar:
            count, _ = Pieza.objects.filter(
                linea_negocio=LineaNegocio.VESTIDOS,
                tipo=tipo,
            ).delete()
            self.stdout.write(self.style.WARNING(f"Eliminados {count} vestidos de {tipo}"))

        importados = 0
        errores = 0

        with open(archivo, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    codigo = (row.get("CODIGO") or "").strip()
                    color_mero = (row.get("COLOR_MERO") or "").strip()
                    marca = (row.get("MARCA") or "").strip()
                    color_desc = (row.get("COLOR") or "").strip()
                    talla = (row.get("TALLA") or "").strip()
                    precio_raw = (row.get("PRECIO") or "").strip()

                    if not codigo and not color_desc:
                        continue

                    # Parsear precio (puede ser "1700" o "1700-1400", tomar el primero)
                    precio = Decimal("0")
                    if precio_raw:
                        # Remover espacios y tomar primer número
                        precio_match = re.match(r"(\d+)", precio_raw.replace(" ", ""))
                        if precio_match:
                            precio = Decimal(precio_match.group(1))

                    Pieza.objects.create(
                        tipo=tipo,
                        color=color_mero or "SIN COLOR",
                        color_vestido=color_desc,
                        talla=talla or "ÚNICA",
                        marca=marca,
                        detalles="",
                        codigo_old="",
                        codigo_new=codigo,
                        conjunto="",
                        estatus=Pieza.Estatus.DISPONIBLE,
                        precio_renta=precio,
                        precio_venta=Decimal("0"),
                        precio_premier=Decimal("0"),
                        ubicacion="",
                        linea_negocio=LineaNegocio.VESTIDOS,
                    )
                    importados += 1

                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error en fila: {row} — {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completada: {importados} vestidos de {tipo} importados, {errores} errores"
            )
        )
