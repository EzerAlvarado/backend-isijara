from datetime import date

from django.test import TestCase

from api.models import Renta
from api.models.linea_negocio import LineaNegocio
from api.services.inventario_renta import marcar_prendas_arrugado_renta


def _celda(valor: str, estatus: str = "normal") -> dict:
    data = {"valor": valor}
    if estatus != "normal":
        data["estatus"] = estatus
    return data


class MarcarEstatusDevolucionRentaTests(TestCase):
    def test_vestidos_marca_entregado_en_todas_las_celdas_y_fila(self):
        renta = Renta.objects.create(
            linea_negocio=LineaNegocio.VESTIDOS,
            semana_inicio=date(2026, 6, 15),
            fecha_salida="15/06/2026",
            fecha_regreso="18/06/2026",
            tipo_operacion=Renta.TipoOperacion.PREMIER,
            estatus_fila=Renta.EstatusCelda.PREMIER,
            color=_celda("ROSA", "salio"),
            chaleco=_celda("ROSA CLARO"),
            saco=_celda("V-101"),
            pantalon=_celda("8"),
            accesorio=_celda("TUL"),
            empleado=_celda("ANA"),
            cliente=_celda("MARIA"),
            horario=_celda("10:00"),
            detalles=_celda("AJUSTE"),
        )

        self.assertTrue(marcar_prendas_arrugado_renta(renta))
        renta.refresh_from_db()

        self.assertEqual(renta.estatus_fila, Renta.EstatusCelda.ENTREGADO)
        for field in (
            "color",
            "chaleco",
            "saco",
            "pantalon",
            "accesorio",
            "empleado",
            "cliente",
            "horario",
            "detalles",
        ):
            celda = getattr(renta, field)
            self.assertEqual(celda.get("estatus"), Renta.EstatusCelda.ENTREGADO, field)

    def test_trajes_marca_arrugado_solo_prendas_y_limpia_fila(self):
        renta = Renta.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            semana_inicio=date(2026, 6, 15),
            fecha_salida="15/06/2026",
            fecha_regreso="18/06/2026",
            estatus_fila=Renta.EstatusCelda.SALIO,
            color=_celda("NEGRO"),
            saco=_celda("40", "salio"),
            chaleco=_celda("40"),
            pantalon=_celda("34"),
            camisa=_celda("BLANCA"),
            empleado=_celda("LUIS"),
            cliente=_celda("PEDRO"),
        )

        self.assertTrue(marcar_prendas_arrugado_renta(renta))
        renta.refresh_from_db()

        self.assertEqual(renta.estatus_fila, "")
        for field in ("color", "saco", "chaleco", "pantalon", "camisa"):
            celda = getattr(renta, field)
            self.assertEqual(celda.get("estatus"), Renta.EstatusCelda.ARRUGADO, field)
        self.assertNotIn("estatus", renta.empleado)
        self.assertNotIn("estatus", renta.cliente)
