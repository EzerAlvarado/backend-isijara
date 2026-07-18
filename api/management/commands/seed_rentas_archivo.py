from datetime import date, timedelta
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Renta
from api.models.linea_negocio import LineaNegocio
from api.models.metodo_pago import MetodoPago

DEMO_TAG = "DEMO-ARCHIVO"

CLIENTES_TRAJES = [
    "GARCIA MARTINEZ",
    "LOPEZ HERNANDEZ",
    "RODRIGUEZ PEREZ",
    "MARTINEZ SANCHEZ",
    "HERNANDEZ LOPEZ",
    "PEREZ GONZALEZ",
    "SANCHEZ RAMIREZ",
    "GONZALEZ TORRES",
    "RAMIREZ FLORES",
    "TORRES MORALES",
    "FLORES CASTRO",
    "MORALES VARGAS",
]

CLIENTES_VESTIDOS = [
    "SOFIA ALVARADO",
    "VALENTINA REYES",
    "CAMILA NAVARRO",
    "ISABELLA CRUZ",
    "MARIANA ORTEGA",
    "REGINA SILVA",
    "DANIELA ROMERO",
    "FERNANDA GUZMAN",
    "PAULA MEDINA",
    "ANDREA DELGADO",
]

COLORES_TRAJES = ["NEGRO", "AZUL MARINO", "GRIS", "CAFE", "BURGUNDY"]
MARCAS_TRAJES = ["CHAPS", "CALVIN KLEIN", "KENNETH COLE", "MICHAEL KORS", "IZOD"]
COLORES_VESTIDOS = ["ROSA", "DORADO", "AZUL REY", "VINO", "CHAMPAGNE"]
MARCAS_VESTIDOS = ["MORI LEE", "ALYCE", "JOVANI", "SHERI HILL", "MAC DUGGAL"]

CATEGORIAS_VESTIDO = [
    Renta.CategoriaVestido.NOCHE,
    Renta.CategoriaVestido.QUINCE,
    Renta.CategoriaVestido.BODA,
]

TIPOS_OPERACION = [
    Renta.TipoOperacion.RENTA,
    Renta.TipoOperacion.RENTA,
    Renta.TipoOperacion.RENTA,
    Renta.TipoOperacion.PREMIER,
    Renta.TipoOperacion.VENTA,
]


def celda(valor: str) -> dict:
    return {"valor": valor}


def inicio_semana_lun(d: date) -> date:
    return d - timedelta(days=d.weekday())


def fmt_mx(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def regreso(fecha_salida: date) -> str:
    return fmt_mx(fecha_salida + timedelta(days=3))


class Command(BaseCommand):
    help = "Inserta rentas genéricas de archivo (últimos meses) para probar el archivero."

    def add_arguments(self, parser):
        parser.add_argument("--meses", type=int, default=4)
        parser.add_argument("--por-mes", type=int, default=12)
        parser.add_argument(
            "--linea",
            choices=("trajes", "vestidos", "ambas"),
            default="ambas",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Borra rentas demo anteriores (detalles=DEMO-ARCHIVO).",
        )

    def handle(self, *args, **options):
        meses_atras: int = options["meses"]
        por_mes: int = options["por_mes"]
        linea_opt: str = options["linea"]

        if options["force"]:
            borradas, _ = Renta.objects.filter(detalles__valor=DEMO_TAG).delete()
            self.stdout.write(f"Eliminadas {borradas} rentas demo.")

        hoy = timezone.localdate()
        inicio_semana_actual = inicio_semana_lun(hoy)

        lineas = []
        if linea_opt in ("trajes", "ambas"):
            lineas.append(LineaNegocio.TRAJES)
        if linea_opt in ("vestidos", "ambas"):
            lineas.append(LineaNegocio.VESTIDOS)

        creadas = 0
        random.seed(42)

        for mes_offset in range(1, meses_atras + 1):
            year = hoy.year
            month = hoy.month - mes_offset
            while month <= 0:
                month += 12
                year -= 1

            ultimo_dia = self._ultimo_dia_mes(year, month)
            dias_muestra = sorted(
                random.sample(range(1, ultimo_dia + 1), min(por_mes, ultimo_dia))
            )

            for linea in lineas:
                clientes = CLIENTES_TRAJES if linea == LineaNegocio.TRAJES else CLIENTES_VESTIDOS
                for i, dia in enumerate(dias_muestra):
                    fecha = date(year, month, dia)
                    if fecha >= inicio_semana_actual:
                        continue

                    tipo_op = random.choice(TIPOS_OPERACION)
                    cliente = clientes[i % len(clientes)]
                    empleado = random.choice(["ANA", "LUIS", "KAREN", "JOSE", "MARIA"])
                    semana = inicio_semana_lun(fecha)
                    fecha_s = fmt_mx(fecha)
                    tipo_entrega = (
                        Renta.TipoEntrega.PREMIER
                        if tipo_op == Renta.TipoOperacion.PREMIER
                        else Renta.TipoEntrega.RECOGER
                    )
                    base = dict(
                        linea_negocio=linea,
                        tipo_entrega=tipo_entrega,
                        tipo_operacion=tipo_op,
                        empleado=celda(empleado),
                        cliente=celda(cliente),
                        telefono="6531000000",
                        fecha_cita=celda(fecha_s),
                        horario=celda(random.choice(["17:00", "17:30", "18:00", "19:00"])),
                        detalles=celda(DEMO_TAG),
                        semana_inicio=semana,
                        fecha_salida=fecha_s,
                        fecha_regreso=regreso(fecha),
                        multa=Decimal("0"),
                        metodo_pago=MetodoPago.PESOS,
                    )

                    if linea == LineaNegocio.TRAJES:
                        renta = Renta(
                            **base,
                            color=celda(random.choice(COLORES_TRAJES)),
                            saco=celda(random.choice(["40R", "42R", "44L", "38S"])),
                            chaleco=celda(random.choice(["40", "42", "44"])),
                            pantalon=celda(random.choice(["32", "34", "36"])),
                            camisa=celda(random.choice(["M", "L", "16.5"])),
                            corbata_mono=celda(random.choice(["NEGRO", "VINO", "AZUL"])),
                            cinto=celda("NEGRO"),
                            accesorio=celda(""),
                            marca=random.choice(MARCAS_TRAJES),
                            fondo=Decimal(random.choice([1200, 1400, 1600, 1800, 2000])),
                            anticipo=Decimal(random.choice([0, 300, 500, 700])),
                        )
                    else:
                        renta = Renta(
                            **base,
                            categoria_vestido=random.choice(CATEGORIAS_VESTIDO),
                            color=celda(random.choice(COLORES_VESTIDOS)),
                            chaleco=celda(random.choice(["DORADO", "PLATA", "NUDE"])),
                            saco=celda(f"V-{100 + i}"),
                            pantalon=celda(random.choice(["6", "8", "10", "12"])),
                            camisa=celda(tipo_op.upper()),
                            accesorio=celda(random.choice(["", "VELO", "TOCADO"])),
                            marca=random.choice(MARCAS_VESTIDOS),
                            fondo=Decimal(random.choice([900, 1200, 1500, 3500, 4500])),
                            anticipo=Decimal(random.choice([0, 400, 800])),
                        )

                    renta.save()
                    creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Se crearon {creadas} rentas demo de archivo "
                f"({meses_atras} meses, hasta {por_mes}/mes por línea)."
            )
        )

    @staticmethod
    def _ultimo_dia_mes(year: int, month: int) -> int:
        if month == 12:
            ultimo = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo = date(year, month + 1, 1) - timedelta(days=1)
        return ultimo.day
