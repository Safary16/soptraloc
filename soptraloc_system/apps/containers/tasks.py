"""
Tareas programadas de Celery para el módulo de containers.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


@shared_task
def generate_demurrage_alerts():
    """
    Genera alertas automáticas de demurrage para contenedores en riesgo.
    Ejecutar cada hora con Celery Beat.
    
    Returns:
        dict: Estadísticas de alertas generadas
    """
    from apps.containers.models import Container
    from apps.drivers.models import Alert
    
    now = timezone.now().date()
    
    # Contenedores cerca de demurrage (3 días antes)
    warning_date = now + timedelta(days=3)
    
    containers_at_risk = Container.objects.filter(
        demurrage_date__lte=warning_date,
        demurrage_date__gt=now,
        status__in=['LIBERADO', 'PROGRAMADO', 'ASIGNADO', 'EN_RUTA', 'ARRIBADO', 'DESCARGADO_CD']
    ).select_related('client', 'conductor_asignado')
    
    warnings_created = 0
    
    for container in containers_at_risk:
        days_remaining = (container.demurrage_date - now).days
        
        # Verificar si ya existe alerta activa
        existing_alert = Alert.objects.filter(
            container=container,
            tipo='DEMURRAGE_PROXIMO',
            is_active=True
        ).exists()
        
        if not existing_alert:
            Alert.objects.create(
                container=container,
                driver=container.conductor_asignado,
                tipo='DEMURRAGE_PROXIMO',
                prioridad='ALTA' if days_remaining <= 1 else 'MEDIA',
                titulo=f'Demurrage próximo: {container.container_number}',
                mensaje=f'Contenedor {container.container_number} tiene {days_remaining} día(s) hasta demurrage'
            )
            warnings_created += 1
    
    # Contenedores ya en demurrage (CRÍTICO)
    containers_overdue = Container.objects.filter(
        demurrage_date__lt=now,
        status__in=['LIBERADO', 'PROGRAMADO', 'ASIGNADO', 'EN_RUTA', 'ARRIBADO', 'DESCARGADO_CD']
    ).select_related('client', 'conductor_asignado')
    
    overdue_created = 0
    
    for container in containers_overdue:
        days_overdue = (now - container.demurrage_date).days
        
        existing_alert = Alert.objects.filter(
            container=container,
            tipo='DEMURRAGE_VENCIDO',
            is_active=True
        ).exists()
        
        if not existing_alert:
            Alert.objects.create(
                container=container,
                driver=container.conductor_asignado,
                tipo='DEMURRAGE_VENCIDO',
                prioridad='CRITICA',
                titulo=f'URGENTE: Demurrage vencido - {container.container_number}',
                mensaje=f'⚠️ CRÍTICO: Contenedor {container.container_number} lleva {days_overdue} día(s) en demurrage. '
                        f'Cliente: {container.client.name if container.client else "N/A"}. '
                        f'Estado: {container.get_status_display()}'
            )
            overdue_created += 1
    
    return {
        'timestamp': timezone.now().isoformat(),
        'warnings_generated': warnings_created,
        'overdue_alerts': overdue_created,
        'total_at_risk': containers_at_risk.count(),
        'total_overdue': containers_overdue.count()
    }


@shared_task
def check_delayed_deliveries():
    """
    Detecta asignaciones que están retrasadas respecto al tiempo estimado.
    Ejecutar cada 30 minutos.
    
    Returns:
        dict: Estadísticas de alertas por retrasos
    """
    from apps.drivers.models import Assignment, Alert
    
    now = timezone.now()
    
    # Assignments en curso que excedieron tiempo estimado
    delayed_assignments = Assignment.objects.filter(
        estado='EN_CURSO',
        fecha_inicio__isnull=False
    ).select_related('container', 'driver', 'origen', 'destino')
    
    alerts_created = 0
    
    for assignment in delayed_assignments:
        elapsed_minutes = (now - assignment.fecha_inicio).total_seconds() / 60
        
        # Si excede 50% del tiempo estimado, generar alerta
        if elapsed_minutes > (assignment.tiempo_estimado * 1.5):
            existing_alert = Alert.objects.filter(
                container=assignment.container,
                tipo='ENTREGA_RETRASADA',
                is_active=True
            ).exists()
            
            if not existing_alert:
                delay_percentage = int(((elapsed_minutes - assignment.tiempo_estimado) / assignment.tiempo_estimado) * 100)
                
                Alert.objects.create(
                    container=assignment.container,
                    driver=assignment.driver,
                    tipo='ENTREGA_RETRASADA',
                    prioridad='ALTA',
                    titulo=f'Entrega retrasada: {assignment.container.container_number}',
                    mensaje=f'Conductor {assignment.driver.nombre} lleva {int(elapsed_minutes)} minutos en ruta '
                            f'(estimado: {assignment.tiempo_estimado} min). Retraso: {delay_percentage}%. '
                            f'Ruta: {assignment.origen.name} → {assignment.destino.name}'
                )
                alerts_created += 1
    
    # Contenedores en estado ASIGNADO pero que deberían haber salido
    from apps.containers.models import Container
    
    stuck_containers = Container.objects.filter(
        status='ASIGNADO',
        tiempo_asignacion__isnull=False,
        tiempo_asignacion__lt=now - timedelta(hours=2)  # Más de 2 horas sin iniciar
    ).select_related('conductor_asignado')
    
    stuck_alerts = 0
    
    for container in stuck_containers:
        existing_alert = Alert.objects.filter(
            container=container,
            tipo='ASIGNACION_PENDIENTE',
            is_active=True
        ).exists()
        
        if not existing_alert:
            hours_stuck = int((now - container.tiempo_asignacion).total_seconds() / 3600)
            
            Alert.objects.create(
                container=container,
                driver=container.conductor_asignado,
                tipo='ASIGNACION_PENDIENTE',
                prioridad='MEDIA',
                titulo=f'Asignación sin iniciar: {container.container_number}',
                mensaje=f'Contenedor asignado hace {hours_stuck} hora(s) pero no ha iniciado ruta. '
                        f'Conductor: {container.conductor_asignado.nombre if container.conductor_asignado else "N/A"}'
            )
            stuck_alerts += 1
    
    return {
        'timestamp': timezone.now().isoformat(),
        'delayed_alerts_created': alerts_created,
        'stuck_alerts_created': stuck_alerts,
        'total_delayed': delayed_assignments.count(),
        'total_stuck': stuck_containers.count()
    }


@shared_task
def auto_resolve_old_alerts():
    """
    Marca automáticamente como inactivas las alertas antiguas (más de 7 días).
    Ejecutar diariamente.
    
    Returns:
        dict: Número de alertas desactivadas
    """
    from apps.drivers.models import Alert
    
    now = timezone.now()
    threshold = now - timedelta(days=7)
    
    old_alerts = Alert.objects.filter(
        is_active=True,
        fecha_creacion__lt=threshold
    )
    
    count = old_alerts.count()
    
    old_alerts.update(
        is_active=False,
        fecha_resolucion=now
    )
    
    return {
        'timestamp': now.isoformat(),
        'alerts_resolved': count
    }


@shared_task
def generate_daily_summary():
    """
    Genera un resumen diario del estado del sistema.
    Ejecutar diariamente a las 7 AM.
    
    Returns:
        dict: Resumen de métricas del día
    """
    from apps.containers.models import Container
    from apps.drivers.models import Assignment, Driver, Alert
    
    now = timezone.now()
    today = now.date()
    
    summary = {
        'date': today.isoformat(),
        'containers': {
            'total_active': Container.objects.filter(is_active=True).count(),
            'in_demurrage': Container.objects.filter(
                demurrage_date__lt=today,
                status__in=['LIBERADO', 'PROGRAMADO', 'ASIGNADO']
            ).count(),
            'by_status': {}
        },
        'assignments': {
            'completed_today': Assignment.objects.filter(
                fecha_completada__date=today,
                estado='COMPLETADA'
            ).count(),
            'in_progress': Assignment.objects.filter(estado='EN_CURSO').count(),
            'pending': Assignment.objects.filter(estado='PENDIENTE').count()
        },
        'drivers': {
            'total_active': Driver.objects.filter(is_active=True).count(),
            'available': Driver.objects.filter(
                is_active=True,
                estado='OPERATIVO',
                contenedor_asignado__isnull=True
            ).count(),
            'with_assignment': Driver.objects.filter(
                contenedor_asignado__isnull=False
            ).count()
        },
        'alerts': {
            'critica': Alert.objects.filter(is_active=True, prioridad='CRITICA').count(),
            'alta': Alert.objects.filter(is_active=True, prioridad='ALTA').count(),
            'media': Alert.objects.filter(is_active=True, prioridad='MEDIA').count(),
            'baja': Alert.objects.filter(is_active=True, prioridad='BAJA').count()
        }
    }
    
    # Contar por estado
    from django.db.models import Count
    status_counts = Container.objects.filter(is_active=True).values('status').annotate(count=Count('id'))
    for item in status_counts:
        summary['containers']['by_status'][item['status']] = item['count']
    
    return summary
