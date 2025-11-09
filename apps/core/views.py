# Core views for frontend pages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD


def home(request):
    """Dashboard principal con estadísticas"""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    two_days_from_now = today + timedelta(days=2)
    ahora = timezone.now()
    
    # Calculate stats for dashboard
    from apps.programaciones.models import Programacion
    
    # Mejorar cálculo de sin_asignar: programaciones sin conductor donde la fecha programada está en las próximas 72 horas
    # Esto da más tiempo para preparar pero sigue siendo urgente
    stats = {
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
        'conductores': Driver.objects.filter(activo=True).count(),
        'por_arribar': Container.objects.filter(estado='por_arribar').count(),
        'programados': Container.objects.filter(estado='programado').count(),
        'vacios': Container.objects.filter(estado__in=['vacio', 'vacio_en_ruta']).count(),
        # Programaciones sin conductor asignado que requieren atención urgente (< 72h)
        'sin_asignar': Programacion.objects.filter(
            fecha_programada__gt=ahora,  # Solo futuras
            fecha_programada__lte=ahora + timedelta(hours=72),  # Dentro de 72 horas
            driver__isnull=True  # Sin conductor asignado
        ).count(),
    }
    
    return render(request, 'home.html', {'stats': stats})


def asignacion(request):
    """Sistema de asignación de conductores - redirige a operaciones"""
    return redirect('operaciones')


def estados(request):
    """Visualización de estados de contenedores"""
    # Estados del ciclo de vida (sin arribado)
    estados = [
        'por_arribar', 'liberado', 'secuenciado', 'programado', 
        'asignado', 'en_ruta', 'entregado', 'descargado', 
        'vacio', 'vacio_en_ruta', 'devuelto'
    ]
    
    # Contar contenedores por estado
    containers_por_estado = {}
    for estado in estados:
        containers_por_estado[estado] = Container.objects.filter(estado=estado).count()
    
    return render(request, 'estados.html', {
        'estados': estados,
        'containers_por_estado': containers_por_estado
    })


def importar(request):
    """Página de importación de Excel"""
    return render(request, 'importar.html')


def containers_list(request):
    """Listado de contenedores con filtros"""
    # Filtros desde query params
    estado = request.GET.get('estado', '')
    urgencia = request.GET.get('urgencia', '')
    search = request.GET.get('search', '')
    
    containers = Container.objects.all().select_related('cd_entrega').order_by('-created_at')
    
    if estado:
        containers = containers.filter(estado=estado)
    
    if urgencia:
        containers = containers.filter(urgencia_demurrage=urgencia)
    
    if search:
        containers = containers.filter(
            container_id__icontains=search
        ) | containers.filter(
            nave__icontains=search
        ) | containers.filter(
            vendor__icontains=search
        )
    
    return render(request, 'containers_list.html', {
        'containers': containers[:100],  # Limitar a 100 para performance
        'estado_filter': estado,
        'urgencia_filter': urgencia,
        'search_query': search
    })


def container_detail(request, container_id):
    """Detalle completo de un contenedor"""
    container = get_object_or_404(Container, container_id=container_id)
    
    return render(request, 'container_detail.html', {
        'container': container
    })


def operaciones(request):
    """Panel de operaciones para asignación y gestión de ciclo de vida"""
    # Ensure CSRF token is in context for the template
    from django.middleware.csrf import get_token
    get_token(request)
    return render(request, 'operaciones.html')


def drivers_list(request):
    """Listado de conductores con filtros"""
    return render(request, 'drivers_list.html')


def executive_dashboard(request):
    """Dashboard ejecutivo con métricas y análisis"""
    return render(request, 'executive_dashboard.html')


def operaciones_diarias(request):
    """Vista de operaciones diarias con horarios completos"""
    return render(request, 'operaciones_diarias.html')