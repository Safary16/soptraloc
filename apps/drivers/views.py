from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Driver, DriverLocation
from .serializers import DriverSerializer, DriverDetailSerializer, DriverLocationSerializer


# ============================================
# Authentication Views (for drivers)
# ============================================

def driver_login(request):
    """Vista de login para conductores"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Verificar que el usuario tiene un driver asociado
            try:
                driver = user.driver
                login(request, user)
                return redirect('driver_dashboard')
            except Driver.DoesNotExist:
                messages.error(request, 'Este usuario no está asociado a un conductor.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'driver_login.html')


@login_required
def driver_logout(request):
    """Vista de logout para conductores"""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('driver_login')


@login_required
def driver_dashboard(request):
    """Dashboard principal para conductores"""
    try:
        driver = request.user.driver
        return render(request, 'driver_dashboard.html', {
            'driver': driver
        })
    except Driver.DoesNotExist:
        messages.error(request, 'No se encontró información del conductor.')
        return redirect('driver_login')


def monitoring(request):
    """Página de monitoreo en tiempo real de conductores"""
    return render(request, 'monitoring.html')


# ============================================
# API ViewSet for Drivers
# ============================================

class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de conductores"""
    
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = []  # Allow access without authentication for now
    
    def get_queryset(self):
        """Filtrar conductores según parámetros"""
        queryset = Driver.objects.all()
        
        # Filtros opcionales
        activo = self.request.query_params.get('activo')
        presente = self.request.query_params.get('presente')
        
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        if presente is not None:
            queryset = queryset.filter(presente=presente.lower() == 'true')
        
        return queryset.order_by('nombre')
    
    @action(detail=True, methods=['post'])
    def track_location(self, request, pk=None):
        """
        Registrar ubicación GPS del conductor
        
        POST /api/drivers/{id}/track_location/
        Body: {
            "lat": -33.4569,
            "lng": -70.6483,
            "accuracy": 10.5
        }
        """
        driver = self.get_object()
        
        # Verificar que el usuario autenticado es el conductor
        if hasattr(request.user, 'driver') and request.user.driver == driver:
            lat = request.data.get('lat')
            lng = request.data.get('lng')
            accuracy = request.data.get('accuracy')
            
            if lat is None or lng is None:
                return Response(
                    {'error': 'Se requieren lat y lng'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                driver.actualizar_posicion(lat, lng, accuracy)
                return Response({
                    'success': True,
                    'mensaje': 'Ubicación actualizada',
                    'lat': float(lat),
                    'lng': float(lng),
                    'timestamp': driver.ultima_actualizacion_posicion
                })
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {'error': 'No autorizado para actualizar esta ubicación'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=False, methods=['get'])
    def active_locations(self, request):
        """
        Obtener ubicaciones de conductores activos (últimos 30 minutos)
        
        GET /api/drivers/active_locations/
        """
        time_threshold = timezone.now() - timedelta(minutes=30)
        
        drivers = Driver.objects.filter(
            activo=True,
            ultima_actualizacion_posicion__gte=time_threshold,
            ultima_posicion_lat__isnull=False,
            ultima_posicion_lng__isnull=False
        )
        
        resultado = []
        for driver in drivers:
            resultado.append({
                'id': driver.id,
                'nombre': driver.nombre,
                'lat': float(driver.ultima_posicion_lat),
                'lng': float(driver.ultima_posicion_lng),
                'ultima_actualizacion': driver.ultima_actualizacion_posicion,
                'num_entregas_dia': driver.num_entregas_dia,
                'max_entregas_dia': driver.max_entregas_dia
            })
        
        return Response(resultado)
    
    @action(detail=True, methods=['get'])
    def my_info(self, request, pk=None):
        """
        Obtener información del conductor autenticado con programaciones
        
        GET /api/drivers/{id}/my_info/
        """
        driver = self.get_object()
        
        # Verificar que el usuario autenticado es el conductor
        if hasattr(request.user, 'driver') and request.user.driver == driver:
            serializer = DriverDetailSerializer(driver)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'No autorizado para ver esta información'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'])
    def reset_entregas_diarias(self, request, pk=None):
        """
        Resetear contador de entregas diarias
        
        POST /api/drivers/{id}/reset_entregas_diarias/
        """
        driver = self.get_object()
        driver.reset_entregas_diarias()
        
        return Response({
            'success': True,
            'mensaje': f'Entregas diarias reseteadas para {driver.nombre}',
            'num_entregas_dia': driver.num_entregas_dia
        })
    
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Obtener historial de ubicaciones del conductor
        
        GET /api/drivers/{id}/historial/?dias=7
        """
        driver = self.get_object()
        dias = int(request.query_params.get('dias', 7))
        
        fecha_desde = timezone.now() - timedelta(days=dias)
        ubicaciones = DriverLocation.objects.filter(
            driver=driver,
            timestamp__gte=fecha_desde
        ).order_by('-timestamp')[:100]
        
        serializer = DriverLocationSerializer(ubicaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='import-excel')
    def import_excel(self, request):
        """
        Importa conductores desde archivo Excel
        
        POST /api/drivers/import-excel/
        Body: multipart/form-data with 'file' field
        """
        from rest_framework.parsers import MultiPartParser, FormParser
        import tempfile
        import os
        from apps.drivers.importers import ConductorImporter
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['file']
        usuario = request.user.username if request.user.is_authenticated else None
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            # Procesar con el importador
            importer = ConductorImporter(tmp_path, usuario)
            resultados = importer.procesar()
            
            return Response({
                'success': True,
                'mensaje': f'Importación completada',
                'creados': resultados['creados'],
                'actualizados': resultados['actualizados'],
                'errores': resultados['errores'],
                'detalles': resultados['detalles']
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
