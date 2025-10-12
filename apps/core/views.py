from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.programaciones.models import Programacion


def home(request):
    """Vista principal del dashboard"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Get today's date range
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    stats = {
        # Métricas principales
        'contenedores_total': Container.objects.count(),
        'conductores': Driver.objects.count(),
        'cds': CD.objects.count(),
        
        # Métricas específicas requeridas
        'programados_hoy': Container.objects.filter(
            estado='programado',
            fecha_programacion__date=today
        ).count(),
        
        'con_demurrage': Container.objects.filter(
            fecha_demurrage__isnull=False,
            estado__in=['liberado', 'programado', 'asignado']
        ).exclude(estado='devuelto').count(),
        
        'liberados': Container.objects.filter(estado='liberado').count(),
        'en_ruta': Container.objects.filter(estado='en_ruta').count(),
        
        # Alertas de no asignados
        'sin_asignar': Container.objects.filter(
            estado='programado',
            fecha_programacion__lte=timezone.now() + timedelta(hours=48)
        ).count(),
        
        # Totales por estado (excluyendo devueltos)
        'por_arribar': Container.objects.filter(estado='por_arribar').count(),
        'programados': Container.objects.filter(estado='programado').count(),
        'vacios': Container.objects.filter(estado__in=['vacio', 'vacio_en_ruta']).count(),
        
        # Total excluyendo devueltos
        'total_activos': Container.objects.exclude(estado='devuelto').count(),
    }
    return render(request, 'home.html', {'stats': stats})


def asignacion(request):
    """Vista de asignación de conductores"""
    return render(request, 'asignacion.html')


def importar(request):
    """Vista de importación de archivos Excel"""
    stats = {
        'contenedores': Container.objects.count(),
        'conductores': Driver.objects.count(),
        'cds': CD.objects.count(),
        'programaciones': Programacion.objects.count(),
    }
    return render(request, 'importar.html', {'stats': stats})


def estados(request):
    """Vista de estados de contenedores - ciclo de vida completo"""
    return render(request, 'estados.html')


def container_detail(request, container_id):
    """Vista de detalle de un contenedor específico"""
    from apps.containers.models import Container
    from django.shortcuts import get_object_or_404
    
    container = get_object_or_404(Container, container_id=container_id)
    return render(request, 'container_detail.html', {'container': container})


def containers_list(request):
    """Vista de listado de contenedores con filtros"""
    return render(request, 'containers_list.html')


def drivers_list(request):
    """Vista de listado de conductores con filtros"""
    return render(request, 'drivers_list.html')


def operaciones(request):
    """Vista del panel de operaciones"""
    return render(request, 'operaciones.html')


def driver_login(request):
    """Vista de login para conductores"""
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir al dashboard
        try:
            driver = request.user.driver_profile
            return redirect('driver_dashboard')
        except:
            # Si no tiene perfil de conductor, logout
            logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar que el usuario tiene perfil de conductor
            try:
                driver = user.driver_profile
                login(request, user)
                return redirect('driver_dashboard')
            except:
                messages.error(request, 'Este usuario no tiene un perfil de conductor asociado.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'driver_login.html')


def driver_logout(request):
    """Vista de logout para conductores"""
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('driver_login')


@login_required(login_url='/driver/login/')
def driver_dashboard(request):
    """Vista del dashboard móvil para conductores"""
    try:
        driver = request.user.driver_profile
    except:
        messages.error(request, 'No tiene un perfil de conductor asociado.')
        return redirect('driver_login')
    
    return render(request, 'driver_dashboard.html', {
        'driver': driver
    })


def monitoring(request):
    """Vista de monitoreo en tiempo real de conductores"""
    from django.conf import settings
    return render(request, 'monitoring.html', {
        'MAPBOX_API_KEY': settings.MAPBOX_API_KEY
    })


def executive_dashboard(request):
    """Vista del dashboard ejecutivo con reportes y analíticas"""
    return render(request, 'executive_dashboard.html')
