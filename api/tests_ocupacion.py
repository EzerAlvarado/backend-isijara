from datetime import date

from django.test import TestCase

from api.models import LineaNegocio, Pieza, Renta
from api.services.ocupacion import alertas_reuso_vestido, conteo_piezas_anio


def _renta(**kwargs):
    defaults = {
        "linea_negocio": LineaNegocio.VESTIDOS,
        "categoria_vestido": Renta.CategoriaVestido.NOCHE,
        "tipo_operacion": Renta.TipoOperacion.RENTA,
        "semana_inicio": date(2025, 10, 27),
        "fecha_salida": "31/10/2025",
        "fecha_regreso": "03/11/2025",
        "saco": {"valor": "VN100"},
        "color": {"valor": "NEGRO"},
        "cliente": {"valor": "ANA"},
    }
    defaults.update(kwargs)
    return Renta.objects.create(**defaults)


class ConteoPiezasAnioTests(TestCase):
    def test_cuenta_por_mes_y_rubro_y_compara_anio(self):
        for _ in range(2):
            _renta()
        _renta(
            categoria_vestido=Renta.CategoriaVestido.NOCHE,
            semana_inicio=date(2026, 10, 26),
            fecha_salida="31/10/2026",
            fecha_regreso="03/11/2026",
        )
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            semana_inicio=date(2025, 8, 25),
            fecha_salida="29/08/2025",
            fecha_regreso="01/09/2025",
            saco={"valor": "DQ1892"},
        )
        _renta(
            tipo_operacion=Renta.TipoOperacion.VENTA,
            semana_inicio=date(2025, 10, 27),
            fecha_salida="30/10/2025",
        )
        _renta(cancelada=True)

        data = conteo_piezas_anio(2026)
        octubre = next(m for m in data["meses"] if m["mes"] == 10)
        noche = next(r for r in octubre["rubros"] if r["id"] == "noche")
        agosto = next(m for m in data["meses"] if m["mes"] == 8)
        xv_rubro = next(r for r in agosto["rubros"] if r["id"] == "xv")

        self.assertEqual(noche["anterior"], 2)
        self.assertEqual(noche["actual"], 1)
        self.assertEqual(noche["diferencia"], -1)
        self.assertEqual(xv_rubro["anterior"], 1)
        self.assertEqual(data["anioAnterior"], 2025)

    def test_no_cuenta_trajes_como_noche(self):
        _renta(
            linea_negocio=LineaNegocio.TRAJES,
            categoria_vestido="",
            semana_inicio=date(2026, 5, 4),
            fecha_salida="08/05/2026",
            fecha_regreso="11/05/2026",
        )
        data = conteo_piezas_anio(2026)
        mayo = next(m for m in data["meses"] if m["mes"] == 5)
        self.assertEqual(next(r for r in mayo["rubros"] if r["id"] == "trajes")["actual"], 1)
        self.assertEqual(next(r for r in mayo["rubros"] if r["id"] == "noche")["actual"], 0)


class AlertasReusoTests(TestCase):
    def setUp(self):
        self.pieza = Pieza.objects.create(
            linea_negocio=LineaNegocio.VESTIDOS,
            tipo=Pieza.Tipo.QUINCE,
            color="ROSA",
            color_vestido="ROSA BRILLOS",
            talla="M",
            codigo_new="DQ1892",
        )

    def test_marca_reuso_cercano_del_mismo_vestido(self):
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            pieza_saco=self.pieza,
            saco={"valor": "DQ1892"},
            color={"valor": "ROSA"},
            semana_inicio=date(2026, 8, 24),
            fecha_salida="29/08/2026",
            fecha_regreso="01/09/2026",
            cliente={"valor": "MARIA"},
        )
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            pieza_saco=self.pieza,
            saco={"valor": "DQ1892"},
            color={"valor": "ROSA"},
            semana_inicio=date(2026, 8, 31),
            fecha_salida="05/09/2026",
            fecha_regreso="08/09/2026",
            cliente={"valor": "LUCIA"},
        )
        data = alertas_reuso_vestido(
            dias_alerta=10,
            categoria="quince",
            hoy=date(2026, 8, 15),
        )
        self.assertEqual(len(data["alertas"]), 1)
        alerta = data["alertas"][0]
        self.assertEqual(alerta["codigo"], "DQ1892")
        self.assertEqual(alerta["color"], "ROSA")
        self.assertEqual(alerta["diasEntre"], 4)
        self.assertFalse(alerta["traslape"])
        self.assertEqual(alerta["vecesRentado"], 2)
        self.assertEqual(data["masRentados"][0]["veces"], 2)

    def test_no_alerta_si_hay_holgura(self):
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            pieza_saco=self.pieza,
            semana_inicio=date(2026, 8, 24),
            fecha_salida="29/08/2026",
            fecha_regreso="01/09/2026",
        )
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            pieza_saco=self.pieza,
            semana_inicio=date(2026, 9, 21),
            fecha_salida="25/09/2026",
            fecha_regreso="28/09/2026",
        )
        data = alertas_reuso_vestido(
            dias_alerta=10,
            categoria="quince",
            hoy=date(2026, 8, 15),
        )
        self.assertEqual(data["alertas"], [])
        self.assertEqual(data["masRentados"][0]["veces"], 2)

    def test_traslape_es_alerta_alta(self):
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            pieza_saco=self.pieza,
            semana_inicio=date(2026, 8, 24),
            fecha_salida="29/08/2026",
            fecha_regreso="05/09/2026",
        )
        _renta(
            categoria_vestido=Renta.CategoriaVestido.QUINCE,
            pieza_saco=self.pieza,
            semana_inicio=date(2026, 8, 31),
            fecha_salida="03/09/2026",
            fecha_regreso="06/09/2026",
        )
        data = alertas_reuso_vestido(
            dias_alerta=10,
            categoria="quince",
            hoy=date(2026, 8, 15),
        )
        self.assertEqual(data["alertas"][0]["severidad"], "alta")
        self.assertTrue(data["alertas"][0]["traslape"])
