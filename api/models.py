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

    def __str__(self):
        return f"{self.numero_factura}, {self.cliente}"

class Proforma(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True)
    numero_proforma = models.CharField(max_length=100, editable=False, unique=True)
    def save(self, *args, **kwargs):
        from datetime import date
        if not self.numero_proforma:
            current_year = date.today().year
            last_proforma = Proforma.objects.filter(fecha__year=current_year).order_by('-numero_proforma').first()
            if last_proforma and last_proforma.numero_proforma:
                try:
                    last_number = int(last_proforma.numero_proforma.split('/')[0])
                except Exception:
                    last_number = 0
            else:
                last_number = 0
            next_number = str(last_number + 1).zfill(4)
            self.numero_proforma = f"{next_number}/{current_year}"
        super().save(*args, **kwargs)
    fecha = models.DateField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)


class Trabajo(models.Model):
    nombre_reparacion = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

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
    localidad = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.direccion}, {self.numero}, {self.localidad}"
    


class Reparacion(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True)
    proforma = models.ForeignKey(Proforma, on_delete=models.SET_NULL, null=True, blank=True)
    localizacion = models.ForeignKey(LocalizacionReparacion, on_delete=models.CASCADE)
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE)
    fecha = models.DateField()
    num_reparacion = models.CharField(max_length=100, null=True, blank=True)
    num_pedido = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        factura_str = self.factura.numero_factura if self.factura else "Sin factura"
        proforma_str = self.proforma.numero_proforma if self.proforma else "Sin proforma"
        return f"{self.trabajo} en factura/proforma {factura_str}/{proforma_str} realizado en {self.localizacion} el {self.fecha}"