from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    numero = models.IntegerField()
    cp = models.IntegerField()
    localidad = models.CharField(max_length=255)
    cif = models.CharField(max_length=50)
    email = models.EmailField()

    def __str__(self):
        return self.nombre
    
class Estado(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
    
class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero_factura = models.CharField(max_length=100, editable=False, unique=True)
    # Archivo PDF generado de la factura
    pdf_file = models.FileField(upload_to='facturas_pdfs/', null=True, blank=True)
    fecha = models.DateField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        from datetime import date
        if not self.numero_factura:
            current_year = date.today().year
            last_factura = Factura.objects.filter(fecha__year=current_year).order_by('-numero_factura').first()
            if last_factura and last_factura.numero_factura:
                try:
                    last_number = int(last_factura.numero_factura.split('/')[0])
                except Exception:
                    last_number = 0
            else:
                last_number = 0
            next_number = str(last_number + 1).zfill(4)
            self.numero_factura = f"{next_number}/{current_year}"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Solo permitir eliminar la última factura creada (número más alto)
        from django.core.exceptions import ValidationError
        current_year = self.fecha.year
        # Buscar la última factura del año de esta factura
        last_factura = Factura.objects.filter(fecha__year=current_year).order_by('-numero_factura').first()
        if not last_factura or last_factura.pk != self.pk:
            raise ValidationError("Solo se puede eliminar la última factura creada.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_factura}, {self.cliente}"

class Proforma(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True)
    numero_proforma = models.CharField(max_length=100, editable=False, unique=True)
    # Archivo PDF generado de la proforma
    pdf_file = models.FileField(upload_to='proformas_pdfs/', null=True, blank=True)
    def save(self, *args, **kwargs):
        from datetime import date
        if not self.numero_proforma:
            current_year = date.today().year
            last_proforma = Proforma.objects.filter(fecha__year=current_year).order_by('-numero_proforma').first()
            if last_proforma and last_proforma.numero_proforma:
                try:
                    # extract the numeric sequence part, which is the second segment
                    last_number = int(last_proforma.numero_proforma.split('/')[1])
                except Exception:
                    last_number = 0
            else:
                last_number = 0
            next_number = str(last_number + 1).zfill(4)
            self.numero_proforma = f"PF/{next_number}/{current_year}"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Solo permitir eliminar la última proforma creada (número más alto)
        from django.core.exceptions import ValidationError
        current_year = self.fecha.year
        last_proforma = Proforma.objects.filter(fecha__year=current_year).order_by('-numero_proforma').first()
        if not last_proforma or last_proforma.pk != self.pk:
            raise ValidationError("Solo se puede eliminar la última proforma creada.")
        super().delete(*args, **kwargs)
    fecha = models.DateField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)


class Trabajo(models.Model):
    nombre_reparacion = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    especial = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre_reparacion}"

class TrabajoCliente(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    def __str__(self):
        return f"A {self.cliente} se le cobra {self.precio} por {self.trabajo}"
    


class LocalizacionReparacion(models.Model):
    direccion = models.CharField(max_length=255)
    numero = models.IntegerField()
    ascensor = models.CharField(max_length=20, default=1, blank=True)
    escalera = models.CharField(max_length=20, null=True, blank=True)
    localidad = models.CharField(max_length=50)

    def __str__(self):
        partes = []
        if self.direccion:
            partes.append(str(self.direccion))
        if self.numero:
            partes.append(str(self.numero))
        if hasattr(self, 'escalera') and self.escalera:
            partes.append(f"Esc {self.escalera}")
        if hasattr(self, 'ascensor') and self.ascensor:
            partes.append(f"Asc {self.ascensor}")
        return ', '.join(partes)



class Reparacion(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True)
    proforma = models.ForeignKey(Proforma, on_delete=models.SET_NULL, null=True, blank=True)
    localizacion = models.ForeignKey(LocalizacionReparacion, on_delete=models.CASCADE)
    fecha = models.DateField()
    num_reparacion = models.CharField(max_length=100, null=True, blank=True)
    num_pedido = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(null=True, blank=True)

    def __str__(self):
        factura_str = self.factura.numero_factura if self.factura else "Sin factura"
        proforma_str = self.proforma.numero_proforma if self.proforma else "Sin proforma"
        trabajos_str = ", ".join([tr.trabajo.nombre_reparacion for tr in self.trabajos_reparaciones.all()])
        return f"{trabajos_str} en factura/proforma {factura_str}/{proforma_str} realizado en {self.localizacion} el {self.fecha}"


# Modelo intermedio para relacionar Reparaciones con Trabajos (many-to-many)
class TrabajosReparaciones(models.Model):
    reparacion = models.ForeignKey(Reparacion, related_name='trabajos_reparaciones', on_delete=models.CASCADE)
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('reparacion', 'trabajo')

    def __str__(self):
        return f"{self.trabajo.nombre_reparacion} - Reparación {self.reparacion.id}"
    

# Modelo para almacenar múltiples fotos de una reparación
class ReparacionFoto(models.Model):
    reparacion = models.ForeignKey(Reparacion, related_name='fotos', on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='fotos_reparacion/')

    def __str__(self):
        return f"Foto {self.id} de Reparacion {self.reparacion.id}"




# MODELOS DE FACTURAS DE GASTOS

class Gasto(models.Model):
    nombre = models.CharField(max_length=255)
    TIPOS_DEFAULT = [
        'Suministros',
        'Materiales',
        'Servicios',
        'Impuestos',
        'Otros',
    ]
    tipo = models.CharField(max_length=50, choices=[(t, t) for t in TIPOS_DEFAULT])
    ESTADOS_DEFAULT = [
        'Pagada',
        'Enviada',
        'Pendiente de pago',
    ]
    estado = models.CharField(max_length=20, choices=[(e, e) for e in ESTADOS_DEFAULT], default='pendiente de pago')
    fecha = models.DateField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True, null=True)
    archivo = models.FileField(upload_to='gastos_archivos/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo}) - {self.fecha}"
