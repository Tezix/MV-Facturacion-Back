from api.models import Gasto
from rest_framework import serializers
class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = '__all__'
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
    # Nombre del cliente para mostrar en dashboard
    cliente_nombre = serializers.SerializerMethodField(read_only=True)
    cliente_email = serializers.SerializerMethodField(read_only=True)
    pdf_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Factura
        fields = '__all__'
        extra_fields = ['cliente_nombre', 'cliente_email', 'pdf_url']
        # Evitar escritura de archivos PDF desde cliente
        read_only_fields = ['pdf_file', 'pdf_url']

    def get_total(self, obj):
        # Obtener todas las reparaciones asociadas a esta factura
        reparaciones = obj.reparacion_set.all()
        total = 0
        for reparacion in reparaciones:
            # Buscar el precio personalizado para este cliente y trabajo
            try:
                trabajo_cliente = TrabajoCliente.objects.get(
                    cliente=obj.cliente,
                    trabajo=reparacion.trabajo
                )
                total += float(trabajo_cliente.precio)
            except TrabajoCliente.DoesNotExist:
                # Si no hay trabajo personalizado, usar el precio del trabajo
                if reparacion.trabajo and hasattr(reparacion.trabajo, 'precio'):
                    total += float(reparacion.trabajo.precio or 0)
        return total

    def get_cliente_nombre(self, obj):
        # Retorna el nombre del cliente asociado
        return obj.cliente.nombre if obj.cliente else None
    
    def get_cliente_email(self, obj):
        # Retorna el email del cliente asociado
        return obj.cliente.email if obj.cliente and hasattr(obj.cliente, 'email') else None
    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file:
            url = obj.pdf_file.url
            return request.build_absolute_uri(url) if request else url
        return None

class ProformaSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all()
    )
    total = serializers.SerializerMethodField(read_only=True)
    # Nombre del cliente para mostrar en dashboard
    cliente_nombre = serializers.SerializerMethodField(read_only=True)
    # Email del cliente y URL para descargar PDF de la proforma
    cliente_email = serializers.SerializerMethodField(read_only=True)
    pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proforma
        fields = '__all__'
        extra_fields = ['cliente_nombre', 'cliente_email', 'pdf_url']
        # Evitar escritura de campos de PDF desde cliente
        read_only_fields = ['cliente_email', 'pdf_url', 'pdf_file']

    def get_total(self, obj):
        # Obtener todas las reparaciones asociadas a esta proforma
        reparaciones = obj.reparacion_set.all()
        total = 0
        for reparacion in reparaciones:
            # Buscar el precio personalizado para este cliente y trabajo
            try:
                trabajo_cliente = TrabajoCliente.objects.get(
                    cliente=obj.cliente,
                    trabajo=reparacion.trabajo
                )
                total += float(trabajo_cliente.precio)
            except TrabajoCliente.DoesNotExist:
                # Si no hay trabajo personalizado, usar el precio del trabajo
                if reparacion.trabajo and hasattr(reparacion.trabajo, 'precio'):
                    total += float(reparacion.trabajo.precio or 0)
        return total

    def get_cliente_nombre(self, obj):
        # Retorna el nombre del cliente asociado
        return obj.cliente.nombre if obj.cliente else None
    def get_cliente_email(self, obj):
        # Retorna el email del cliente asociado
        return obj.cliente.email if obj.cliente and hasattr(obj.cliente, 'email') else None
    def get_pdf_url(self, obj):
        """Retorna la URL absoluta al archivo PDF de la proforma"""
        request = self.context.get('request')
        if obj.pdf_file:
            url = obj.pdf_file.url
            return request.build_absolute_uri(url) if request else url
        return None

class LocalizacionReparacionSerializer(serializers.ModelSerializer):
    ascensor = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    escalera = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    class Meta:
        model = LocalizacionReparacion
        fields = '__all__'

class TrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trabajo
        fields = '__all__'

class TrabajoClienteSerializer(serializers.ModelSerializer):
    trabajo = serializers.PrimaryKeyRelatedField(
        queryset=Trabajo.objects.all()
    )

    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all()
    )

    cliente_nombre = serializers.SerializerMethodField(read_only=True)
    trabajo_nombre = serializers.SerializerMethodField(read_only=True)

    def get_cliente_nombre(self, obj):
        return obj.cliente.nombre if obj.cliente else None

    def get_trabajo_nombre(self, obj):
        return obj.trabajo.nombre_reparacion if obj.trabajo else None
    class Meta:
        model = TrabajoCliente
        fields = '__all__'
        extra_fields = ['cliente_nombre', 'trabajo_nombre']

class ReparacionFotoSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ReparacionFoto
        fields = ['id', 'foto_url']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto:
            url = obj.foto.url
            return request.build_absolute_uri(url) if request else url
        return None

class ReparacionSerializer(serializers.ModelSerializer):
    # Permitir formatos de fecha personalizados (dd/MM/yyyy y ISO)
    fecha = serializers.DateField(input_formats=['%d/%m/%Y', 'iso-8601'])
    localizacion = LocalizacionReparacionSerializer(read_only=True)
    trabajo = TrabajoSerializer(read_only=True)
    fotos = ReparacionFotoSerializer(many=True, read_only=True)
    localizacion_id = serializers.PrimaryKeyRelatedField(
        queryset=LocalizacionReparacion.objects.all(),
        source='localizacion',
        write_only=True,
        required=False
    )
    trabajo_id = serializers.PrimaryKeyRelatedField(
        queryset=Trabajo.objects.all(),
        source='trabajo',
        write_only=True,
        required=False
    )
    comentarios = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    class Meta:
        model = Reparacion
        fields = '__all__'
        extra_fields = ['localizacion_id', 'trabajo_id', 'comentarios', 'fotos']
        # Para que DRF acepte los campos *_id en POST/PUT
        read_only_fields = []