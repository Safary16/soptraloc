# Core views for frontend pages
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD


def home(request):
    """Dashboard principal con estadísticas"""
    today = timezone.now().date()
    
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
        'total_conductores': Driver.objects.count(),
        'conductores_disponibles': Driver.objects.filter(activo=True, presente=True).count(),
    }
    
    return render(request, 'home.html', {'stats': stats})


def asignacion(request):
    """Sistema de asignación de conductores"""
    return render(request, 'asignacion.html')


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