from django.contrib import admin
from .models import (
    Cliente,
    Estado,
    Factura,
    Proforma,
    LocalizacionTrabajo,
    Tarifa,
    TarifaCliente,
    Trabajo
)

admin.site.register(Cliente)
admin.site.register(Estado)
admin.site.register(Factura)
admin.site.register(Proforma)
admin.site.register(LocalizacionTrabajo)
admin.site.register(Tarifa)
admin.site.register(TarifaCliente)
admin.site.register(Trabajo)

