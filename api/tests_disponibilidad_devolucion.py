from datetime import date

from django.test import TestCase

from api.models import Devolucion, Pieza, Renta
from api.models.linea_negocio import LineaNegocio
from api.services.inventario_renta import (
    conflicto_pieza_en_rentas,
    renta_bloquea_disponibilidad,
)


class DisponibilidadTrasDevolucionTests(TestCase):
    def setUp(self):
        self.pieza = Pieza.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            tipo=Pieza.Tipo.SACO,
            color="NEGRO",
            talla="38R",
            marca="TEST",
            estatus=Pieza.Estatus.SUCIO,
        )
        self.renta = Renta.objects.create(
            linea_negocio=LineaNegocio.TRAJES,
            semana_inicio=date(2026, 8, 4),
            fecha_salida="07/08/2026",
            fecha_regreso="10/08/2026",
            pieza_saco=self.pieza,
            color={"valor": "NEGRO"},
            saco={"valor": "38R"},
            cliente={"valor": "CARLOS CINCO"},
        )
        self.devolucion = Devolucion.objects.create(
            renta=self.renta,
            cliente="CARLOS CINCO",
            prenda_nombre="SACO NEGRO 38R",
            fecha_limite=date(2026, 8, 10),
            estatus=Devolucion.Estatus.AFUERA,
        )

    def test_renta_regresada_no_bloquea_disponibilidad(self):
        self.devolucion.estatus = Devolucion.Estatus.REGRESADO
        self.devolucion.save(update_fields=["estatus"])
        self.renta.refresh_from_db()

        self.assertFalse(renta_bloquea_disponibilidad(self.renta))
        conflicto = conflicto_pieza_en_rentas(
            self.pieza.pk,
            "07/08/2026",
            LineaNegocio.TRAJES,
        )
        self.assertIsNone(conflicto)

    def test_renta_afuera_si_bloquea_disponibilidad(self):
        self.assertTrue(renta_bloquea_disponibilidad(self.renta))
        conflicto = conflicto_pieza_en_rentas(
            self.pieza.pk,
            "07/08/2026",
            LineaNegocio.TRAJES,
        )
        self.assertEqual(conflicto["estado"], "ocupada_misma_semana")
