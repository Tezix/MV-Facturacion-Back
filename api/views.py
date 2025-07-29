from rest_framework.decorators import action
from api.models import Reparacion, Factura
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from api.models import *
from api.serializers import (
    ClienteSerializer,
    EstadoSerializer,
    FacturaSerializer,
    ProformaSerializer,
    LocalizacionReparacionSerializer,
    TrabajoSerializer,
    TrabajoClienteSerializer,
    ReparacionSerializer
)

from rest_framework.permissions import IsAuthenticated

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    permission_classes = [IsAuthenticated]

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='asignar-reparaciones')
    def asignar_reparaciones(self, request, pk=None):
        factura = self.get_object()
        reparaciones_ids = request.data.get('reparaciones', [])
        reparaciones = Reparacion.objects.filter(id__in=reparaciones_ids)
        reparaciones.update(factura=factura)
        # Opcional: devolver las reparaciones actualizadas
        from api.serializers import ReparacionSerializer
        reparaciones_actualizadas = ReparacionSerializer(reparaciones, many=True).data
        return Response({'success': True, 'reparaciones_actualizadas': reparaciones_actualizadas})

    @action(detail=False, methods=['get'], url_path='con-reparaciones')
    def con_reparaciones(self, request):
        facturas = Factura.objects.all()
        data = []
        for factura in facturas:
            reparaciones = Reparacion.objects.filter(factura=factura)
            # Usar el serializer para obtener el total calculado
            serializer = FacturaSerializer(factura)
            total = serializer.data.get('total', 0)
            data.append({
                'id': factura.id,
                'numero_factura': factura.numero_factura,
                'cliente': factura.cliente.id,
                'cliente_nombre': factura.cliente.nombre,
                'fecha': factura.fecha,
                'estado': factura.estado.id,
                'estado_nombre': factura.estado.nombre,
                'total': total,
                'reparaciones': [
                    {
                        'id': r.id,
                        'fecha': r.fecha,
                        'localizacion': str(r.localizacion),
                        'trabajo': str(r.trabajo),
                    } for r in reparaciones
                ]
            })
        return Response(data)

class ProformaViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'], url_path='convertir-a-factura')
    def convertir_a_factura(self, request, pk=None):
        from api.models import Factura, Reparacion
        from api.serializers import FacturaSerializer
        proforma = self.get_object()
        # Crear la nueva factura con los datos de la proforma
        factura = Factura.objects.create(
            cliente=proforma.cliente,
            fecha=proforma.fecha,
            estado=proforma.estado
        )
        # Asociar la nueva factura a las reparaciones relacionadas con la proforma
        reparaciones = Reparacion.objects.filter(proforma=proforma)
        reparaciones.update(factura=factura)
        # No desasociar la proforma de las reparaciones, mantener ambas relaciones
        # Asociar la factura creada a la proforma
        proforma.factura = factura
        proforma.save()
        # Serializar la nueva factura
        factura_data = FacturaSerializer(factura).data
        return Response({
            'success': True,
            'factura': factura_data,
            'reparaciones_actualizadas': [r.id for r in reparaciones]
        })
    queryset = Proforma.objects.all()
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='asignar-reparaciones')
    def asignar_reparaciones(self, request, pk=None):
        proforma = self.get_object()
        reparaciones_ids = request.data.get('reparaciones', [])
        reparaciones = Reparacion.objects.filter(id__in=reparaciones_ids)
        reparaciones.update(proforma=proforma)
        from api.serializers import ReparacionSerializer
        reparaciones_actualizadas = ReparacionSerializer(reparaciones, many=True).data
        return Response({'success': True, 'reparaciones_actualizadas': reparaciones_actualizadas})

    @action(detail=False, methods=['get'], url_path='con-reparaciones')
    def con_reparaciones(self, request):
        proformas = Proforma.objects.all()
        data = []
        for proforma in proformas:
            reparaciones = Reparacion.objects.filter(proforma=proforma)
            serializer = ProformaSerializer(proforma)
            total = serializer.data.get('total', 0)
            data.append({
                'id': proforma.id,
                'numero_proforma': proforma.numero_proforma,
                'factura': proforma.factura.id if proforma.factura else None,
                'factura_numero': proforma.factura.numero_factura if proforma.factura else None,
                'cliente': proforma.cliente.id if proforma.cliente else None,
                'cliente_nombre': proforma.cliente.nombre if proforma.cliente else None,
                'fecha': proforma.fecha,
                'estado': proforma.estado.id if proforma.estado else None,
                'estado_nombre': proforma.estado.nombre if proforma.estado else None,
                'total': total,
                'reparaciones': [
                    {
                        'id': r.id,
                        'fecha': r.fecha,
                        'localizacion': str(r.localizacion),
                        'trabajo': str(r.trabajo),
                    } for r in reparaciones
                ]
            })
        return Response(data)

class LocalizacionReparacionViewSet(viewsets.ModelViewSet):
    queryset = LocalizacionReparacion.objects.all()
    serializer_class = LocalizacionReparacionSerializer
    permission_classes = [IsAuthenticated]

class TrabajoViewSet(viewsets.ModelViewSet):
    queryset = Trabajo.objects.all()
    serializer_class = TrabajoSerializer
    permission_classes = [IsAuthenticated]

class TrabajoClienteViewSet(viewsets.ModelViewSet):
    queryset = TrabajoCliente.objects.all()
    serializer_class = TrabajoClienteSerializer
    permission_classes = [IsAuthenticated]




class ReparacionViewSet(viewsets.ModelViewSet):
    queryset = Reparacion.objects.all()
    serializer_class = ReparacionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        trabajos = request.data.get('trabajos')
        if trabajos and isinstance(trabajos, list):
            reparaciones = []
            errors = []
            for trabajo_id in trabajos:
                data = request.data.copy()
                data['trabajo_id'] = trabajo_id
                data.pop('trabajos', None)
                serializer = self.get_serializer(data=data)
                if serializer.is_valid():
                    self.perform_create(serializer)
                    reparaciones.append(serializer.data)
                else:
                    errors.append(serializer.errors)
            if errors:
                return Response({'errors': errors}, status=400)
            return Response(reparaciones, status=201)
        else:
            return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='agrupados')
    def agrupados(self, request):
        # Agrupar reparaciones por fecha y localizacion
        reparaciones = Reparacion.objects.all().select_related('localizacion', 'trabajo')
        grupos = {}
        for r in reparaciones:
            key = (str(r.fecha), r.localizacion.id)
            if key not in grupos:
                grupos[key] = {
                    'fecha': r.fecha,
                    'localizacion': LocalizacionReparacionSerializer(r.localizacion).data,
                    'num_reparacion': r.num_reparacion,
                    'num_pedido': r.num_pedido,
                    'factura': r.factura.id if r.factura else None,
                    'factura_numero': r.factura.numero_factura if r.factura else None,
                    'proforma': r.proforma.id if r.proforma else None,
                    'proforma_numero': r.proforma.numero_proforma if r.proforma else None,
                    'trabajos': [],
                    'reparacion_ids': [],
                }
            grupos[key]['trabajos'].append(TrabajoSerializer(r.trabajo).data)
            grupos[key]['reparacion_ids'].append(r.id)
        return Response(list(grupos.values()))


# ---------- LOGIN / LOGOUT ----------

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # Obtener o crear el token
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "success": True,
                "token": token.key,
                "username": user.username,
                "user_id": user.id
            })

        return Response({"success": False}, status=401)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"success": True})