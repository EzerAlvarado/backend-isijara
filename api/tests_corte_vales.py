from datetime import date
from decimal import Decimal

from django.test import TestCase

from api.models import CorteDia, LineaNegocio, TurnoCorte
from api.services.conteo_caja import CONTEO_VACIO, aplicar_vale_a_conteo_fondo, normalizar_conteo
from api.services.corte import (
    _preservar_vales_conteo_fondo,
    _propagar_fondo_tras_cierre,
    _sincronizar_fondo_feria,
    calcular_resumen,
    cerrar_corte,
    vales_esperados_fondo,
)
from api.services.vales import registrar_gasto_fondo


class CorteValesPropagationTests(TestCase):
    fecha = date(2026, 6, 19)

    def _conteo_fondo_con_vales(self, vales: int, billetes: int = 2000) -> dict:
        conteo = normalizar_conteo(CONTEO_VACIO)
        conteo["mxnBilletes"]["1000"] = billetes // 1000
        resto = billetes % 1000
        if resto:
            conteo["mxnBilletes"]["500"] = resto // 500
        conteo["valesMxn"] = vales
        return conteo

    def test_vales_esperados_usa_max_pendientes_y_conteo(self):
        conteo = self._conteo_fondo_con_vales(732)
        self.assertEqual(vales_esperados_fondo(conteo, Decimal("0")), Decimal("732"))
        self.assertEqual(vales_esperados_fondo(conteo, Decimal("500")), Decimal("732"))
        self.assertEqual(vales_esperados_fondo({}, Decimal("200")), Decimal("200"))

    def test_preservar_vales_al_cerrar_sin_fila_vales(self):
        anterior = self._conteo_fondo_con_vales(732)
        enviado = normalizar_conteo(anterior)
        enviado["valesMxn"] = 0
        resultado = _preservar_vales_conteo_fondo(enviado, anterior, Decimal("0"))
        self.assertEqual(resultado["valesMxn"], 732)

    def test_preservar_vales_desde_pendientes_si_no_hay_conteo_previo(self):
        enviado = normalizar_conteo(CONTEO_VACIO)
        enviado["mxnBilletes"]["1000"] = 2
        resultado = _preservar_vales_conteo_fondo(enviado, {}, Decimal("732"))
        self.assertEqual(resultado["valesMxn"], 732)

    def test_propaga_conteo_fondo_con_vales_manana_a_tarde(self):
        manana = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.MANANA,
            linea_negocio=LineaNegocio.TRAJES,
            fondo_inicial=Decimal("2732"),
            conteo_fondo=self._conteo_fondo_con_vales(732, billetes=2000),
            cerrado=True,
        )
        _propagar_fondo_tras_cierre(manana)

        tarde = CorteDia.objects.get(
            fecha=self.fecha,
            turno=TurnoCorte.TARDE,
            linea_negocio=LineaNegocio.TRAJES,
        )
        self.assertEqual(tarde.conteo_fondo["valesMxn"], 732)
        self.assertEqual(tarde.fondo_inicial, Decimal("2732"))

    def test_sincroniza_vales_heredados_en_tarde_abierto(self):
        manana = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.MANANA,
            linea_negocio=LineaNegocio.TRAJES,
            fondo_inicial=Decimal("2732"),
            conteo_fondo=self._conteo_fondo_con_vales(732, billetes=2000),
            cerrado=True,
        )
        tarde = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.TARDE,
            linea_negocio=LineaNegocio.TRAJES,
            fondo_inicial=Decimal("2732"),
            conteo_fondo=normalizar_conteo(CONTEO_VACIO),
        )
        _sincronizar_fondo_feria(tarde)
        tarde.refresh_from_db()
        self.assertEqual(tarde.conteo_fondo["valesMxn"], manana.conteo_fondo["valesMxn"])

    def test_calcular_resumen_incluye_vales_esperados_desde_conteo(self):
        corte = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.TARDE,
            linea_negocio=LineaNegocio.TRAJES,
            fondo_inicial=Decimal("2732"),
            conteo_fondo=self._conteo_fondo_con_vales(732, billetes=2000),
        )
        resumen = calcular_resumen(corte)
        self.assertEqual(resumen["fondoFisico"], 2000.0)
        self.assertEqual(resumen["valesPendientesTotal"], 0.0)
        self.assertEqual(resumen["valesEsperadosFondo"], 732.0)

    def test_cerrar_manana_preserva_vales_en_conteo_y_propaga(self):
        manana = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.MANANA,
            linea_negocio=LineaNegocio.TRAJES,
            fondo_inicial=Decimal("2732"),
            conteo_fondo=self._conteo_fondo_con_vales(732, billetes=2000),
        )
        conteo_caja = normalizar_conteo(CONTEO_VACIO)
        conteo_enviado = normalizar_conteo(manana.conteo_fondo)
        conteo_enviado["valesMxn"] = 0

        cerrar_corte(
            self.fecha,
            LineaNegocio.TRAJES,
            turno=TurnoCorte.MANANA,
            conteo_fondo=conteo_enviado,
            conteo_caja=conteo_caja,
            empleado="ANA",
        )

        manana.refresh_from_db()
        self.assertEqual(manana.conteo_fondo["valesMxn"], 732)

        tarde = CorteDia.objects.get(
            fecha=self.fecha,
            turno=TurnoCorte.TARDE,
            linea_negocio=LineaNegocio.TRAJES,
        )
        self.assertEqual(tarde.conteo_fondo["valesMxn"], 732)

    def test_registrar_gasto_actualiza_vales_en_conteo(self):
        corte = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.MANANA,
            linea_negocio=LineaNegocio.VESTIDOS,
            fondo_inicial=Decimal("2732"),
            conteo_fondo=normalizar_conteo(CONTEO_VACIO),
        )
        conteo = corte.conteo_fondo
        conteo["mxnBilletes"]["1000"] = 2
        conteo["mxnBilletes"]["500"] = 1
        conteo["mxnBilletes"]["200"] = 1
        conteo["mxnBilletes"]["20"] = 1
        conteo["mxnBilletes"]["2"] = 1
        corte.conteo_fondo = conteo
        corte.save()

        registrar_gasto_fondo(corte, "INSUMOS", Decimal("732"), "pesos")
        corte.refresh_from_db()
        self.assertEqual(corte.conteo_fondo["valesMxn"], 732)
