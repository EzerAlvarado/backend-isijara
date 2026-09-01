from datetime import date, datetime, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from api.models import CorteDia, LineaNegocio, MetodoPago, Renta, Transaccion, TurnoCorte
from api.services.corte import (
    mover_transaccion_a_turno,
    registrar_transaccion_multa_renta,
    sincronizar_transacciones_dia,
    transacciones_del_corte,
)


def _celda(valor: str) -> dict:
    return {"valor": valor}


class CorteTurnoMultaTests(TestCase):
    fecha = date(2026, 8, 31)

    def _renta_xv(self, cargo: Decimal) -> Renta:
        return Renta.objects.create(
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            semana_inicio=self.fecha,
            fecha_salida="31/08/2026",
            fecha_regreso="01/09/2026",
            cargo_danos=cargo,
            cliente=_celda("YARELIA"),
        )

    def test_sincronizar_no_cambia_hora_de_multa_existente(self):
        renta = self._renta_xv(Decimal("2500.00"))
        registrar_transaccion_multa_renta(renta)
        tx = Transaccion.objects.get(referencia=f"MR{renta.pk}")
        hora_manana = timezone.make_aware(datetime(2026, 8, 31, 10, 15))
        tx.timestamp = hora_manana
        tx.save(update_fields=["timestamp"])

        sincronizar_transacciones_dia(self.fecha, LineaNegocio.VESTIDOS)
        tx.refresh_from_db()

        self.assertEqual(tx.timestamp, hora_manana)
        self.assertEqual(tx.monto, Decimal("2500.00"))

    def test_sincronizar_actualiza_monto_sin_mover_hora(self):
        renta = self._renta_xv(Decimal("2500.00"))
        registrar_transaccion_multa_renta(renta)
        tx = Transaccion.objects.get(referencia=f"MR{renta.pk}")
        hora_manana = timezone.make_aware(datetime(2026, 8, 31, 11, 0))
        tx.timestamp = hora_manana
        tx.save(update_fields=["timestamp"])

        renta.cargo_danos = Decimal("3000.00")
        renta.save(update_fields=["cargo_danos"])
        sincronizar_transacciones_dia(self.fecha, LineaNegocio.VESTIDOS)
        tx.refresh_from_db()

        self.assertEqual(tx.timestamp, hora_manana)
        self.assertEqual(tx.monto, Decimal("3000.00"))

    def test_mover_multa_de_tarde_a_manana_cerrada(self):
        tz = timezone.get_current_timezone()
        cerrado_en = timezone.make_aware(datetime(2026, 8, 31, 14, 0), tz)
        manana = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.MANANA,
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            cerrado=True,
            cerrado_en=cerrado_en,
        )
        tarde = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.TARDE,
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            cerrado=False,
        )
        tx = Transaccion.objects.create(
            timestamp=cerrado_en + timedelta(hours=2),
            referencia="MR99",
            cliente="MULTA TARDE",
            pago=MetodoPago.PESOS,
            monto=Decimal("2500.00"),
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
        )

        mover_transaccion_a_turno(tarde, tx, TurnoCorte.MANANA)
        tx.refresh_from_db()

        self.assertLess(tx.timestamp, cerrado_en)
        ids_manana = set(transacciones_del_corte(manana).values_list("pk", flat=True))
        ids_tarde = set(transacciones_del_corte(tarde).values_list("pk", flat=True))
        self.assertIn(tx.pk, ids_manana)
        self.assertNotIn(tx.pk, ids_tarde)

    def test_mover_en_corte_cerrado_falla(self):
        tarde = CorteDia.objects.create(
            fecha=self.fecha,
            turno=TurnoCorte.TARDE,
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            cerrado=True,
            cerrado_en=timezone.now(),
        )
        tx = Transaccion.objects.create(
            timestamp=timezone.now(),
            referencia="MR100",
            cliente="MULTA",
            pago=MetodoPago.PESOS,
            monto=Decimal("2500.00"),
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
        )
        with self.assertRaises(ValueError):
            mover_transaccion_a_turno(tarde, tx, TurnoCorte.MANANA)
