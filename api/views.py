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
    TarifaSerializer,
    TarifaClienteSerializer,
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
                        'tarifa': str(r.tarifa),
                    } for r in reparaciones
                ]
            })
        return Response(data)

class ProformaViewSet(viewsets.ModelViewSet):
    queryset = Proforma.objects.all()
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]

class LocalizacionReparacionViewSet(viewsets.ModelViewSet):
    queryset = LocalizacionReparacion.objects.all()
    serializer_class = LocalizacionReparacionSerializer
    permission_classes = [IsAuthenticated]

class TarifaViewSet(viewsets.ModelViewSet):
    queryset = Tarifa.objects.all()
    serializer_class = TarifaSerializer
    permission_classes = [IsAuthenticated]

class TarifaClienteViewSet(viewsets.ModelViewSet):
    queryset = TarifaCliente.objects.all()
    serializer_class = TarifaClienteSerializer
    permission_classes = [IsAuthenticated]




class ReparacionViewSet(viewsets.ModelViewSet):
    queryset = Reparacion.objects.all()
    serializer_class = ReparacionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tarifas = request.data.get('tarifas')
        if tarifas and isinstance(tarifas, list):
            reparaciones = []
            errors = []
            for tarifa_id in tarifas:
                data = request.data.copy()
                data['tarifa_id'] = tarifa_id
                data.pop('tarifas', None)
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
        reparaciones = Reparacion.objects.all().select_related('localizacion', 'tarifa')
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
                    'tarifas': [],
                    'reparacion_ids': [],
                }
            grupos[key]['tarifas'].append(TarifaSerializer(r.tarifa).data)
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