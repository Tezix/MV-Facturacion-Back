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
    LocalizacionTrabajoSerializer,
    TarifaSerializer,
    TarifaClienteSerializer,
    TrabajoSerializer
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

class ProformaViewSet(viewsets.ModelViewSet):
    queryset = Proforma.objects.all()
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]

class LocalizacionTrabajoViewSet(viewsets.ModelViewSet):
    queryset = LocalizacionTrabajo.objects.all()
    serializer_class = LocalizacionTrabajoSerializer
    permission_classes = [IsAuthenticated]

class TarifaViewSet(viewsets.ModelViewSet):
    queryset = Tarifa.objects.all()
    serializer_class = TarifaSerializer
    permission_classes = [IsAuthenticated]

class TarifaClienteViewSet(viewsets.ModelViewSet):
    queryset = TarifaCliente.objects.all()
    serializer_class = TarifaClienteSerializer
    permission_classes = [IsAuthenticated]

class TrabajoViewSet(viewsets.ModelViewSet):
    queryset = Trabajo.objects.all()
    serializer_class = TrabajoSerializer
    permission_classes = [IsAuthenticated]


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