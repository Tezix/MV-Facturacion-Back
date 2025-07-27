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
    numero_factura = models.CharField(max_length=100)
    fecha = models.DateField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.numero_factura}, {self.cliente}"

class Proforma(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True)
    numero_proforma = models.CharField(max_length=100)
    fecha = models.DateField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class Tarifa(models.Model):
    nombre_trabajo = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre_trabajo}"

class TarifaCliente(models.Model):
    tarifa = models.ForeignKey(Tarifa, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    def __str__(self):
        return f"A {self.cliente} se le cobra {self.precio} por {self.tarifa}"
    

class LocalizacionTrabajo(models.Model):
    direccion = models.CharField(max_length=255)
    numero = models.IntegerField()
    localidad = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.direccion}, {self.numero}, {self.localidad}"
    

class Trabajo(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True)
    proforma = models.ForeignKey(Proforma, on_delete=models.SET_NULL, null=True, blank=True)
    localizacion = models.ForeignKey(LocalizacionTrabajo, on_delete=models.CASCADE)
    tarifa = models.ForeignKey(Tarifa, on_delete=models.CASCADE)
    fecha = models.DateField()
    num_reparacion = models.CharField(max_length=100, null=True, blank=True)
    num_pedido = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        factura_str = self.factura.numero_factura if self.factura else "Sin factura"
        proforma_str = self.proforma.numero_proforma if self.proforma else "Sin proforma"
        return f"{self.tarifa} en factura/proforma {factura_str}/{proforma_str} realizado en {self.localizacion} el {self.fecha}"