"""Importa vestidos de noche desde un CSV limpio con columnas:

COLOR MERO, MARCA, CODIGO, COLOR, TALLA, PRECIO
"""

import csv
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import LineaNegocio, Pieza

# Normalización de color mero (plurales y variantes)
COLORES_MERO = {
    "ROSAS": "ROSA",
    "NEGROS": "NEGRO",
    "VERDES": "VERDE",
    "ROJOS": "ROJO",
    "AZULES": "AZUL",
    "PLATEADOS": "PLATEADO",
    "MORADOS": "MORADO",
    "AMARILLOS": "AMARILLO",
    "BLANCOS": "BLANCO",
    "NARANJAS": "NARANJA",
    "BIEGE / DORADO": "BEIGE/DORADO",
    "BEIGE / DORADO": "BEIGE/DORADO",
}


def parsear_precio(texto: str) -> int:
    """Acepta '$1.100', '950', '1500-1400' (rangos: se toma el mayor)."""
    limpio = (texto or "").replace("$", "").replace(".", "").replace(",", "").strip()
    numeros = [int(n) for n in re.findall(r"\d+", limpio)]
    return max(numeros) if numeros else 0


class Command(BaseCommand):
    help = "Importa vestidos de noche desde un CSV limpio (COLOR MERO, MARCA, CODIGO, COLOR, TALLA, PRECIO)."

    def add_arguments(self, parser):
        parser.add_argument("ruta", help="Ruta del archivo .csv")
        parser.add_argument(
            "--borrar",
            action="store_true",
            help="Elimina las piezas de vestidos de noche existentes antes de importar.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra lo que se importaría, sin tocar la base de datos.",
        )

    def handle(self, *args, **options):
        try:
            with open(options["ruta"], newline="", encoding="utf-8-sig") as fh:
                filas = list(csv.DictReader(fh))
        except FileNotFoundError as exc:
            raise CommandError(f"No se encontró el archivo: {options['ruta']}") from exc

        columnas = {"COLOR MERO", "MARCA", "CODIGO", "COLOR", "TALLA", "PRECIO"}
        if filas and not columnas.issubset(filas[0].keys()):
            raise CommandError(
                f"El CSV debe tener las columnas: {', '.join(sorted(columnas))}"
            )

        piezas: list[dict] = []
        omitidas: list[str] = []

        for num, fila in enumerate(filas, 2):
            vals = {k: (v or "").strip() for k, v in fila.items()}
            color_mero = vals["COLOR MERO"].upper()
            codigo = vals["CODIGO"].lstrip("#").strip()
            talla = vals["TALLA"].upper()

            # Filas vacías o separadores de sección (sin talla ni código)
            if not talla and not codigo:
                if any(vals.values()):
                    omitidas.append(f"fila {num}: {vals}")
                continue

            if not color_mero or not vals["COLOR"]:
                omitidas.append(f"fila {num} incompleta: {vals}")
                continue

            piezas.append(
                {
                    "color": COLORES_MERO.get(color_mero, color_mero),
                    "color_vestido": vals["COLOR"].upper(),
                    "talla": talla,
                    "marca": vals["MARCA"].upper(),
                    "codigo_new": codigo.upper(),
                    "precio_renta": parsear_precio(vals["PRECIO"]),
                }
            )

        resumen: dict[str, int] = {}
        sin_precio = 0
        for p in piezas:
            resumen[p["color"]] = resumen.get(p["color"], 0) + 1
            if not p["precio_renta"]:
                sin_precio += 1

        self.stdout.write(f"Vestidos leídos del CSV: {len(piezas)}")
        for color, cuenta in sorted(resumen.items()):
            self.stdout.write(f"  {color}: {cuenta}")
        if sin_precio:
            self.stdout.write(self.style.WARNING(f"Sin precio (quedan en $0): {sin_precio}"))
        if omitidas:
            self.stdout.write(f"Filas omitidas (separadores/vacías): {len(omitidas)}")

        existentes = Pieza.objects.filter(
            tipo=Pieza.Tipo.NOCHE, linea_negocio=LineaNegocio.VESTIDOS
        )
        self.stdout.write(f"Piezas de noche actuales en el sistema: {existentes.count()}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run: no se modificó la base de datos."))
            for p in piezas[:5]:
                self.stdout.write(f"  ejemplo: {p}")
            return

        with transaction.atomic():
            if options["borrar"]:
                eliminadas = existentes.count()
                existentes.delete()
                self.stdout.write(f"Eliminadas {eliminadas} piezas de noche.")

            Pieza.objects.bulk_create(
                Pieza(
                    tipo=Pieza.Tipo.NOCHE,
                    linea_negocio=LineaNegocio.VESTIDOS,
                    estatus=Pieza.Estatus.DISPONIBLE,
                    **p,
                )
                for p in piezas
            )

        self.stdout.write(self.style.SUCCESS(f"Importados {len(piezas)} vestidos de noche."))
