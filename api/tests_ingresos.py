from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, override_settings

from api.services.ingresos import inicio_dia_local


@override_settings(TIME_ZONE="America/Hermosillo", USE_TZ=True)
class InicioDiaLocalTests(SimpleTestCase):
    def test_hoy_no_incluye_la_tarde_de_ayer(self):
        utc = ZoneInfo("UTC")
        # 15:25 en Hermosillo = 22:25 UTC
        ahora = datetime(2026, 8, 15, 22, 25, tzinfo=utc)
        inicio = inicio_dia_local(ahora)

        self.assertEqual(inicio.astimezone(utc), datetime(2026, 8, 15, 7, 0, tzinfo=utc))

        ayer_tarde = datetime(2026, 8, 15, 3, 0, tzinfo=utc)  # 20:00 del 14 en Hermosillo
        hoy_manana = datetime(2026, 8, 15, 17, 0, tzinfo=utc)  # 10:00 del 15 en Hermosillo
        self.assertLess(ayer_tarde, inicio)
        self.assertGreaterEqual(hoy_manana, inicio)
