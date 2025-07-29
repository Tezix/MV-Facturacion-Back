from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import *

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'estados', EstadoViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'proformas', ProformaViewSet)
router.register(r'localizaciones_reparaciones', LocalizacionReparacionViewSet)
router.register(r'tarifas', TarifaViewSet)
router.register(r'tarifas_clientes', TarifaClienteViewSet)
router.register(r'reparaciones', ReparacionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
]