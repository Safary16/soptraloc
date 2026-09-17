# Core views for frontend pages
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.containers.models import Container
from apps.drivers.models import Driver
from django.contrib.admin.views.decorators import staff_member_required


def inicio(request):
    """Página inicial: portada con logo SAFARY y tarjetas de acceso por rol"""
    return render(request, 'inicio.html')


def home(request):
    """Dashboard principal con estadísticas"""
    today = timezone.now().date()
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
    """Sistema inteligente de asignación de conductores"""
    from django.middleware.csrf import get_token
    get_token(request)
    return render(request, 'asignacion.html')


def estados(request):
    """Visualización de estados de contenedores"""
    # Estados del ciclo de vida (sin arribado)
    estados = [
        'por_arribar', 'liberado', 'secuenciado', 'programado', 
        'asignado', 'en_ruta', 'entregado', 'descargado', 
        'vacio', 'vacio_en_ruta', 'en_ccti', 'devuelto'
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
    from apps.containers.models import Container
    from apps.programaciones.models import Programacion
    # Clientes conocidos (para sugerir en el campo de embarque)
    clientes = set()
    for c in Container.objects.exclude(cliente__isnull=True).exclude(cliente='').values_list('cliente', flat=True):
        if c and c.strip():
            clientes.add(c.strip())
    for c in Programacion.objects.exclude(cliente__isnull=True).exclude(cliente='').values_list('cliente', flat=True):
        if c and c.strip():
            clientes.add(c.strip())
    return render(request, 'importar.html', {
        'clientes_conocidos': sorted(clientes),
    })


def gestion(request):
    """Panel de Gestión / Control (Customer Service):
    - Visión de todo el stock (todas las unidades, con filtros)
    - Liberar, programar y modificar unidades manualmente desde la misma vista
    - Carga masiva (importación) accesible desde aquí
    """
    from django.middleware.csrf import get_token
    from apps.containers.models import Container
    from apps.programaciones.models import Programacion
    get_token(request)
    clientes = set()
    for c in Container.objects.exclude(cliente__isnull=True).exclude(cliente='').values_list('cliente', flat=True):
        if c and c.strip():
            clientes.add(c.strip())
    for c in Programacion.objects.exclude(cliente__isnull=True).exclude(cliente='').values_list('cliente', flat=True):
        if c and c.strip():
            clientes.add(c.strip())
    return render(request, 'gestion.html', {
        'clientes_conocidos': sorted(clientes),
        'estados': [e[0] for e in Container.ESTADOS],
    })


@staff_member_required
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
    """Visión operacional del día: reloj, servicios programados, vacíos y asignación"""
    from django.middleware.csrf import get_token
    get_token(request)
    from django.utils import timezone as _tz
    return render(request, 'vision_operativa.html', {'hoy': _tz.now()})


def operaciones_panel(request):
    """Panel operativo completo (liberación, ciclo de vida, preasignación)"""
    from django.middleware.csrf import get_token
    get_token(request)
    return render(request, 'operaciones.html')


@staff_member_required
def drivers_list(request):
    """Listado de conductores con filtros"""
    return render(request, 'drivers_list.html')


@staff_member_required
def cds_list(request):
    """CRUD visible de centros de distribución."""
    return render(request, 'cds_list.html')


def executive_dashboard(request):
    """Dashboard ejecutivo con métricas y análisis"""
    return render(request, 'executive_dashboard.html')


def operaciones_diarias(request):
    """Vista de operaciones diarias con horarios completos"""
    return render(request, 'operaciones_diarias.html')


def cliente_portal(request):
    """Portal separado del cliente: stock liberado disponible para programar.
    El cliente ve las unidades liberadas (sus o todas) y programa; ese cambio
    lleva el contenedor de 'liberado' a 'programado', igual que en Operaciones.
    """
    from django.middleware.csrf import get_token
    get_token(request)  # CSRF listo para las llamadas fetch
    return render(request, 'cliente_portal.html')


@staff_member_required
def auditoria(request):
    """Panel de auditoría: trazabilidad de eventos del sistema."""
    return render(request, 'auditoria.html')
