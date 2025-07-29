from django.contrib import admin
from .models import (
    Cliente,
    Estado,
    Factura,
    Proforma,
    LocalizacionReparacion,
    Trabajo,
    TrabajoCliente,
    Reparacion
)

admin.site.register(Cliente)
admin.site.register(Estado)
admin.site.register(Factura)
admin.site.register(Proforma)
admin.site.register(LocalizacionReparacion)
admin.site.register(Trabajo)
admin.site.register(TrabajoCliente)
admin.site.register(Reparacion)

