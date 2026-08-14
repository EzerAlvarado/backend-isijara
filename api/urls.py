from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, views_auth, views_corte, views_finanzas

router = DefaultRouter()
router.register("piezas", views.PiezaViewSet, basename="pieza")
router.register("prendas", views.PrendaViewSet, basename="prenda")
router.register("rentas", views.RentaViewSet, basename="renta")
router.register("pedidos", views.PedidoViewSet, basename="pedido")
router.register("devoluciones", views.DevolucionViewSet, basename="devolucion")
router.register("transacciones", views.TransaccionViewSet, basename="transaccion")

urlpatterns = [
    path("health/", views.health, name="health"),
    path("auth/login/", views_auth.login, name="auth-login"),
    path("auth/logout/", views_auth.logout, name="auth-logout"),
    path("auth/me/", views_auth.me, name="auth-me"),
    path("corte/", views_corte.corte_dia, name="corte-dia"),
    path("corte/cierre/", views_corte.corte_cierre, name="corte-cierre"),
    path("corte/gasto/", views_corte.corte_gasto, name="corte-gasto"),
    path(
        "corte/transacciones/<int:tx_id>/anular/",
        views_corte.corte_anular_transaccion,
        name="corte-anular-transaccion",
    ),
    path("corte/vales/<int:vale_id>/reponer/", views_corte.corte_reponer_vale, name="corte-reponer-vale"),
    path("finanzas/", views_finanzas.configuracion_finanzas, name="finanzas"),
    path("finanzas/ingresos/", views_finanzas.ingresos_mes, name="finanzas-ingresos"),
    path("test/limpiar/", views.limpiar_datos_test, name="limpiar-datos-test"),
    path("", include(router.urls)),
]
