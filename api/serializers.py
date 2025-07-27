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
    class Meta:
        model = Factura
        fields = '__all__'

class ProformaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proforma
        fields = '__all__'

class LocalizacionTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalizacionTrabajo
        fields = '__all__'

class TarifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifa
        fields = '__all__'

class TarifaClienteSerializer(serializers.ModelSerializer):
    tarifa = serializers.SlugRelatedField(
        slug_field='nombre_trabajo',
        queryset=Tarifa.objects.all()
    )

    class Meta:
        model = TarifaCliente
        fields = '__all__'

class TrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trabajo
        fields = '__all__'