from django.contrib import admin
from .models import (
    Cliente,
    Estado,
    Factura,
    Proforma,
    LocalizacionReparacion,
    Tarifa,
    TarifaCliente,
    Reparacion
)

admin.site.register(Cliente)
admin.site.register(Estado)
admin.site.register(Factura)
admin.site.register(Proforma)
admin.site.register(LocalizacionReparacion)
admin.site.register(Tarifa)
admin.site.register(TarifaCliente)
admin.site.register(Reparacion)

