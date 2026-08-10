from datetime import date

from django.test import TestCase

from api.models import Devolucion, Pieza, Renta
from api.models.linea_negocio import LineaNegocio
from api.services.inventario_renta import (
    renta_requiere_devolucion,
    sincronizar_devolucion,
    sincronizar_renta_inventario,
)


def _celda(valor: str) -> dict:
    return {"valor": valor}


class DevolucionVentaTests(TestCase):
    def setUp(self):
        self.pieza_saco = Pieza.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            tipo=Pieza.Tipo.SACO,
            color="NEGRO",
            talla="40R",
            marca="TEST",
            estatus=Pieza.Estatus.DISPONIBLE,
        )
        self.pieza_chaleco = Pieza.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            tipo=Pieza.Tipo.CHALECO,
            color="NEGRO",
            talla="40R",
            marca="TEST",
            estatus=Pieza.Estatus.DISPONIBLE,
        )
        self.pieza_pantalon = Pieza.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            tipo=Pieza.Tipo.PANTALON,
            color="NEGRO",
            talla="34R",
            marca="TEST",
            estatus=Pieza.Estatus.DISPONIBLE,
        )

    def _crear_renta(self, tipo_operacion: str) -> Renta:
        return Renta.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            semana_inicio=date(2026, 7, 27),
            fecha_salida="27/07/2026",
            fecha_regreso="30/07/2026",
            tipo_operacion=tipo_operacion,
            pieza_saco=self.pieza_saco,
            pieza_chaleco=self.pieza_chaleco,
            pieza_pantalon=self.pieza_pantalon,
            color=_celda("NEGRO"),
            saco=_celda("40R"),
            chaleco=_celda("40R"),
            pantalon=_celda("34R"),
            cliente=_celda("CLIENTE TEST"),
        )

    def test_venta_no_requiere_devolucion(self):
        renta = self._crear_renta(Renta.TipoOperacion.VENTA)
        self.assertFalse(renta_requiere_devolucion(renta))

    def test_renta_si_requiere_devolucion(self):
        renta = self._crear_renta(Renta.TipoOperacion.RENTA)
        self.assertTrue(renta_requiere_devolucion(renta))

    def test_sincronizar_no_crea_devolucion_para_venta(self):
        renta = self._crear_renta(Renta.TipoOperacion.VENTA)
        sincronizar_renta_inventario(renta)
        self.assertEqual(Devolucion.objects.filter(renta=renta).count(), 0)

    def test_sincronizar_crea_devolucion_para_renta(self):
        renta = self._crear_renta(Renta.TipoOperacion.RENTA)
        sincronizar_renta_inventario(renta)
        self.assertEqual(Devolucion.objects.filter(renta=renta).count(), 1)

    def test_cambiar_renta_a_venta_elimina_devolucion(self):
        renta = self._crear_renta(Renta.TipoOperacion.RENTA)
        sincronizar_devolucion(renta)
        self.assertEqual(Devolucion.objects.filter(renta=renta).count(), 1)

        renta.tipo_operacion = Renta.TipoOperacion.VENTA
        renta.save(update_fields=["tipo_operacion"])
        sincronizar_devolucion(renta)
        self.assertEqual(Devolucion.objects.filter(renta=renta).count(), 0)
