from rest_framework.decorators import api_view
from rest_framework.response import Response

# Endpoint para exponer los choices de tipo y estado de Gasto
@api_view(['GET'])
def gasto_choices(request):
    from .models import Gasto
    tipos = [t[0] for t in Gasto._meta.get_field('tipo').choices]
    estados = [e[0] for e in Gasto._meta.get_field('estado').choices]
    return Response({
        'tipos': tipos,
        'estados': estados,
    })
from api.models import Gasto
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
# --- CRUD de Gastos ---
from .serializers import GastoSerializer

class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer
    permission_classes = [IsAuthenticated]
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
from api.models import ReparacionFoto
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from api.serializers import (
    ClienteSerializer,
    EstadoSerializer,
    FacturaSerializer,
    ProformaSerializer,
    LocalizacionReparacionSerializer,
    TrabajoSerializer,
    TrabajoClienteSerializer,
    ReparacionSerializer,
    ReparacionFotoSerializer,
    GastoSerializer,
)

from rest_framework.permissions import IsAuthenticated
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML, CSS
import os, base64
from django.conf import settings
from django.core.files.base import ContentFile

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
            reparaciones = Reparacion.objects.filter(factura=factura).select_related('localizacion', 'trabajo')
            # Agrupar reparaciones por (num_reparacion, localizacion)
            grupos = {}
            for r in reparaciones:
                key = (r.num_reparacion, r.localizacion.id)
                if key not in grupos:
                    grupos[key] = {
                        'id': r.id,
                        'fecha': r.fecha,
                        'num_reparacion': r.num_reparacion,
                        'num_pedido': r.num_pedido,
                        'localizacion': str(r.localizacion),
                        'localizacion_obj': {
                            'id': r.localizacion.id,
                            'direccion': r.localizacion.direccion,
                            'numero': r.localizacion.numero,
                            'escalera': getattr(r.localizacion, 'escalera', None),
                            'ascensor': getattr(r.localizacion, 'ascensor', None),
                            'localidad': r.localizacion.localidad,
                        },
                        'trabajos': [],
                    }
                # Buscar precio personalizado para el cliente y trabajo
                precio = None
                try:
                    from api.models import TrabajoCliente
                    trabajo_cliente = TrabajoCliente.objects.get(cliente=factura.cliente, trabajo=r.trabajo)
                    precio = float(trabajo_cliente.precio)
                except TrabajoCliente.DoesNotExist:
                    precio = float(r.trabajo.precio)
                grupos[key]['trabajos'].append({
                    'id': r.trabajo.id,
                    'nombre_reparacion': r.trabajo.nombre_reparacion,
                    'precio': precio,
                })
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
                'reparaciones': list(grupos.values())
            })
        return Response(data)
    
    @action(detail=True, methods=['get'], url_path='exportar')
    def exportar(self, request, pk=None):
        factura = self.get_object()
        reparaciones = Reparacion.objects.filter(factura=factura)
        # Agrupar por (num_reparacion, localizacion)
        grupos = {}
        for r in reparaciones:
            key = (r.num_reparacion, r.localizacion)
            if key not in grupos:
                grupos[key] = {
                    'num_reparacion': r.num_reparacion,
                    'num_pedido': r.num_pedido,
                    'localizacion': str(r.localizacion),
                    'trabajos': [],
                    'total': 0,
                }
            grupos[key]['trabajos'].append(r.trabajo)
            grupos[key]['total'] += float(r.trabajo.precio)
        reparaciones_agrupadas = list(grupos.values())
        # Detectar si hay algún num_pedido no vacío
        tiene_num_pedido = any(g.get('num_pedido') for g in reparaciones_agrupadas)
        # Calcular total general
        total = sum(g['total'] for g in reparaciones_agrupadas)
        # Cargar logo e incrustar como base64
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.webp')
        try:
            with open(logo_path, 'rb') as img_f:
                logo_data = 'data:image/webp;base64,' + base64.b64encode(img_f.read()).decode('utf-8')
        except FileNotFoundError:
            logo_data = None
        # Renderizar plantilla HTML
        html_string = render_to_string('factura.html', {
            'factura': factura,
            'reparaciones_agrupadas': reparaciones_agrupadas,
            'total': total,
            'logo_data': logo_data,
            'tiene_num_pedido': tiene_num_pedido,
        })
        # Generar PDF con WeasyPrint
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        css_path = os.path.join(settings.BASE_DIR, 'static/css/factura.css')
        pdf = html.write_pdf(stylesheets=[CSS(filename=css_path)])
        # Devolver como respuesta descargable
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero_factura}.pdf"'
        return response
    
    @action(detail=True, methods=['post'], url_path='generar-pdf')
    def generar_pdf(self, request, pk=None):
        """
        Genera el PDF de la factura, lo guarda en el campo pdf_file, y devuelve los datos actualizados.
        """
        factura = self.get_object()
        # Agrupar reparaciones como en exportar
        reparaciones = Reparacion.objects.filter(factura=factura)
        grupos = {}
        for r in reparaciones:
            key = (r.num_reparacion, r.localizacion)
            if key not in grupos:
                grupos[key] = {
                    'num_reparacion': r.num_reparacion,
                    'num_pedido': r.num_pedido,
                    'localizacion': str(r.localizacion),
                    'trabajos': [],
                    'total': 0,
                }
            grupos[key]['trabajos'].append(r.trabajo)
            grupos[key]['total'] += float(r.trabajo.precio)
        reparaciones_agrupadas = list(grupos.values())
        tiene_num_pedido = any(g.get('num_pedido') for g in reparaciones_agrupadas)
        total = sum(g['total'] for g in reparaciones_agrupadas)
        # Cargar logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.webp')
        try:
            with open(logo_path, 'rb') as img_f:
                logo_data = 'data:image/webp;base64,' + base64.b64encode(img_f.read()).decode('utf-8')
        except FileNotFoundError:
            logo_data = None
        # Renderizar HTML
        html_string = render_to_string('factura.html', {
            'factura': factura,
            'reparaciones_agrupadas': reparaciones_agrupadas,
            'total': total,
            'logo_data': logo_data,
            'tiene_num_pedido': tiene_num_pedido,
        })
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        css_path = os.path.join(settings.BASE_DIR, 'static/css/factura.css')
        pdf_bytes = html.write_pdf(stylesheets=[CSS(filename=css_path)])
        # Guardar PDF en el campo
        filename = f"factura_{factura.numero_factura}.pdf"
        factura.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        # Devolver datos actualizados (pasar request para construir URL completa)
        serializer = FacturaSerializer(factura, context={'request': request})
        return Response(serializer.data)

class ProformaViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['get'], url_path='exportar')
    def exportar(self, request, pk=None):
        proforma = self.get_object()
        reparaciones = Reparacion.objects.filter(proforma=proforma)
        # Agrupar por (num_reparacion, localizacion)
        grupos = {}
        for r in reparaciones:
            key = (r.num_reparacion, r.localizacion)
            if key not in grupos:
                grupos[key] = {
                    'num_reparacion': r.num_reparacion,
                    'num_pedido': r.num_pedido,
                    'localizacion': str(r.localizacion),
                    'trabajos': [],
                    'total': 0,
                }
            grupos[key]['trabajos'].append(r.trabajo)
            grupos[key]['total'] += float(r.trabajo.precio)
        reparaciones_agrupadas = list(grupos.values())
        # Detectar si hay algún num_pedido no vacío
        tiene_num_pedido = any(g.get('num_pedido') for g in reparaciones_agrupadas)
        # Calcular total general
        total = sum(g['total'] for g in reparaciones_agrupadas)
        # Cargar logo e incrustar como base64
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.webp')
        try:
            with open(logo_path, 'rb') as img_f:
                logo_data = 'data:image/webp;base64,' + base64.b64encode(img_f.read()).decode('utf-8')
        except FileNotFoundError:
            logo_data = None
        # Renderizar plantilla HTML
        html_string = render_to_string('factura.html', {
            'factura': proforma,  # reutilizamos la plantilla, pero es una proforma
            'reparaciones_agrupadas': reparaciones_agrupadas,
            'total': total,
            'logo_data': logo_data,
            'es_proforma': True,  # para distinguir en la plantilla
            'tiene_num_pedido': tiene_num_pedido,
        })
        # Generar PDF con WeasyPrint
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        css_path = os.path.join(settings.BASE_DIR, 'static/css/factura.css')
        pdf = html.write_pdf(stylesheets=[CSS(filename=css_path)])
        # Devolver como respuesta descargable
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="proforma_{proforma.numero_proforma}.pdf"'
        return response
    @action(detail=True, methods=['post'], url_path='generar-pdf')
    def generar_pdf(self, request, pk=None):
        """
        Genera el PDF de la proforma, lo guarda en el campo pdf_file, y devuelve los datos actualizados.
        """
        proforma = self.get_object()
        reparaciones = Reparacion.objects.filter(proforma=proforma)
        grupos = {}
        for r in reparaciones:
            key = (r.num_reparacion, r.localizacion)
            if key not in grupos:
                grupos[key] = {
                    'num_reparacion': r.num_reparacion,
                    'num_pedido': r.num_pedido,
                    'localizacion': str(r.localizacion),
                    'trabajos': [],
                    'total': 0,
                }
            grupos[key]['trabajos'].append(r.trabajo)
            grupos[key]['total'] += float(r.trabajo.precio)
        reparaciones_agrupadas = list(grupos.values())
        tiene_num_pedido = any(g.get('num_pedido') for g in reparaciones_agrupadas)
        total = sum(g['total'] for g in reparaciones_agrupadas)
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.webp')
        try:
            with open(logo_path, 'rb') as img_f:
                logo_data = 'data:image/webp;base64,' + base64.b64encode(img_f.read()).decode('utf-8')
        except FileNotFoundError:
            logo_data = None
        html_string = render_to_string('factura.html', {
            'factura': proforma,
            'reparaciones_agrupadas': reparaciones_agrupadas,
            'total': total,
            'logo_data': logo_data,
            'es_proforma': True,
            'tiene_num_pedido': tiene_num_pedido,
        })
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        css_path = os.path.join(settings.BASE_DIR, 'static/css/factura.css')
        pdf_bytes = html.write_pdf(stylesheets=[CSS(filename=css_path)])
        filename = f"proforma_{proforma.numero_proforma}.pdf"
        proforma.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        serializer = ProformaSerializer(proforma, context={'request': request})
        return Response(serializer.data)
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
            reparaciones = Reparacion.objects.filter(proforma=proforma).select_related('localizacion', 'trabajo')
            grupos = {}
            for r in reparaciones:
                key = (r.num_reparacion, r.localizacion.id)
                if key not in grupos:
                    grupos[key] = {
                        'id': r.id,
                        'fecha': r.fecha,
                        'num_reparacion': r.num_reparacion,
                        'num_pedido': r.num_pedido,
                        'localizacion': str(r.localizacion),
                        'localizacion_obj': {
                            'id': r.localizacion.id,
                            'direccion': r.localizacion.direccion,
                            'numero': r.localizacion.numero,
                            'escalera': getattr(r.localizacion, 'escalera', None),
                            'ascensor': getattr(r.localizacion, 'ascensor', None),
                            'localidad': r.localizacion.localidad,
                        },
                        'trabajos': [],
                    }
                # Buscar precio personalizado para el cliente y trabajo
                precio = None
                try:
                    from api.models import TrabajoCliente
                    trabajo_cliente = TrabajoCliente.objects.get(cliente=proforma.cliente, trabajo=r.trabajo)
                    precio = float(trabajo_cliente.precio)
                except TrabajoCliente.DoesNotExist:
                    precio = float(r.trabajo.precio)
                grupos[key]['trabajos'].append({
                    'id': r.trabajo.id,
                    'nombre_reparacion': r.trabajo.nombre_reparacion,
                    'precio': precio,
                })
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
                'reparaciones': list(grupos.values())
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
    # Allow JSON and multipart/form-data uploads
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        # Obtener lista de trabajos desde JSON o multipart
        if hasattr(request.data, 'getlist'):
            trabajos_raw = request.data.getlist('trabajos')
        else:
            trabajos_raw = request.data.get('trabajos', [])
        # Asegurar lista de valores
        if isinstance(trabajos_raw, list):
            trabajos = trabajos_raw
        elif trabajos_raw is None:
            trabajos = []
        else:
            trabajos = [trabajos_raw]
        comentarios = request.data.get('comentarios', None)
        # Si hay trabajos, crear múltiples reparaciones
        if trabajos:
            reparaciones = []
            errors = []
            for trabajo_id in trabajos:
                data = request.data.copy()
                data['trabajo_id'] = trabajo_id
                data.pop('trabajos', None)
                if comentarios is not None:
                    data['comentarios'] = comentarios
                serializer = self.get_serializer(data=data)
                if serializer.is_valid():
                    self.perform_create(serializer)
                    # Attach uploaded fotos to this reparacion
                    instance = serializer.instance
                    for foto in request.FILES.getlist('fotos'):
                        ReparacionFoto.objects.create(reparacion=instance, foto=foto)
                    reparaciones.append(serializer.data)
                else:
                    errors.append(serializer.errors)
            if errors:
                return Response({'errors': errors}, status=400)
            return Response(reparaciones, status=201)
        else:
            # For single reparacion, handle photo uploads
            response = super().create(request, *args, **kwargs)
            # Attach fotos if present
            try:
                instance = self.get_queryset().get(pk=response.data.get('id'))
                for foto in request.FILES.getlist('fotos'):
                    ReparacionFoto.objects.create(reparacion=instance, foto=foto)
            except Exception:
                pass
            return response
    
    def update(self, request, *args, **kwargs):
        # Override update to handle fotos
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Perform update on Reparacion fields
        response = super().update(request, *args, **kwargs)
        # Handle uploaded photos: replace existing if new ones provided
        if 'fotos' in request.FILES:
            # Delete old fotos
            instance.fotos.all().delete()
            # Create new fotos
            for foto in request.FILES.getlist('fotos'):
                ReparacionFoto.objects.create(reparacion=instance, foto=foto)
        return response

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
                    'comentarios': r.comentarios,
                }
            grupos[key]['trabajos'].append(TrabajoSerializer(r.trabajo).data)
            grupos[key]['reparacion_ids'].append(r.id)
        # Note: the above return won't include fotos; to include fotos, rebuild response
        # Agregar fotos por grupo
        data = []
        # Para cada grupo, obtener fotos con el serializer para foto_url
        for group in grupos.values():
            all_urls = []
            for rid in group['reparacion_ids']:
                fotos_qs = ReparacionFoto.objects.filter(reparacion_id=rid)
                fotos_serialized = ReparacionFotoSerializer(fotos_qs, many=True, context={'request': request}).data
                # Extraer foto_url de cada serializador
                for item in fotos_serialized:
                    if item.get('foto_url'):
                        all_urls.append(item['foto_url'])
            group['fotos'] = all_urls
            data.append(group)
        return Response(data)


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