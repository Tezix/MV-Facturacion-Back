from rest_framework import serializers
from api.models import *

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = '__all__'

class FacturaSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all()
    )
    total = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Factura
        fields = '__all__'

    def get_total(self, obj):
        # Obtener todas las reparaciones asociadas a esta factura
        reparaciones = obj.reparacion_set.all()
        total = 0
        for reparacion in reparaciones:
            # Buscar el precio de la tarifa para este cliente
            try:
                tarifa_cliente = TarifaCliente.objects.get(
                    cliente=obj.cliente,
                    tarifa=reparacion.tarifa
                )
                total += float(tarifa_cliente.precio)
            except TarifaCliente.DoesNotExist:
                pass  # Si no hay tarifa personalizada, no suma nada
        return total

class ProformaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proforma
        fields = '__all__'

class LocalizacionReparacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalizacionReparacion
        fields = '__all__'

class TarifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifa
        fields = '__all__'

class TarifaClienteSerializer(serializers.ModelSerializer):
    tarifa = serializers.PrimaryKeyRelatedField(
        queryset=Tarifa.objects.all()
    )

    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all()
    )

    cliente_nombre = serializers.SerializerMethodField(read_only=True)
    tarifa_nombre = serializers.SerializerMethodField(read_only=True)

    def get_cliente_nombre(self, obj):
        return obj.cliente.nombre if obj.cliente else None

    def get_tarifa_nombre(self, obj):
        return obj.tarifa.nombre_reparacion if obj.tarifa else None
    class Meta:
        model = TarifaCliente
        fields = '__all__'
        extra_fields = ['cliente_nombre', 'tarifa_nombre']

class ReparacionSerializer(serializers.ModelSerializer):
    localizacion = LocalizacionReparacionSerializer(read_only=True)
    tarifa = TarifaSerializer(read_only=True)
    localizacion_id = serializers.PrimaryKeyRelatedField(
        queryset=LocalizacionReparacion.objects.all(),
        source='localizacion',
        write_only=True,
        required=False
    )
    tarifa_id = serializers.PrimaryKeyRelatedField(
        queryset=Tarifa.objects.all(),
        source='tarifa',
        write_only=True,
        required=False
    )
    class Meta:
        model = Reparacion
        fields = '__all__'
        extra_fields = ['localizacion_id', 'tarifa_id']
        # Para que DRF acepte los campos *_id en POST/PUT
        read_only_fields = []