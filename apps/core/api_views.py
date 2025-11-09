"""
API Views para el core del sistema
Endpoints de dashboard y estadísticas
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Q

from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.programaciones.models import Programacion, TiempoOperacion, TiempoViaje
from apps.notifications.models import Notification


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def dashboard_stats(request):
    """
    Estadísticas generales para el dashboard
    """
    today = timezone.now().date()
    
    stats = {
        # Métricas principales
        'contenedores_total': Container.objects.count(),
        'conductores': Driver.objects.count(),
        'conductores_disponibles': Driver.objects.filter(esta_disponible=True).count(),
        
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
        'asignados': Container.objects.filter(estado='asignado').count(),
        'entregados': Container.objects.filter(estado='entregado').count(),
        'descargados': Container.objects.filter(estado='descargado').count(),
        'vacios': Container.objects.filter(estado__in=['vacio', 'vacio_en_ruta']).count(),
        
        # Total excluyendo devueltos
        'total_activos': Container.objects.exclude(estado='devuelto').count(),
        
        # Notificaciones activas
        'notificaciones_activas': Notification.objects.filter(
            estado__in=['pendiente', 'enviada']
        ).count(),
    }
    
    return Response({
        'success': True,
        'stats': stats
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def dashboard_alertas(request):
    """
    Lista de alertas activas para el dashboard
    """
    alertas = []
    
    # Alertas de demurrage
    fecha_limite = timezone.now() + timedelta(days=2)
    containers_riesgo = Container.objects.filter(
        fecha_demurrage__isnull=False,
        fecha_demurrage__lte=fecha_limite,
        estado__in=['liberado', 'programado', 'asignado']
    ).select_related('cd_entrega')
    
    for container in containers_riesgo:
        dias_restantes = (container.fecha_demurrage - timezone.now()).days
        alertas.append({
            'tipo': 'demurrage',
            'prioridad': 'critica' if dias_restantes < 0 else 'alta',
            'container_id': container.container_id,
            'mensaje': f'Demurrage vence en {dias_restantes} días' if dias_restantes >= 0 else 'Demurrage vencido',
            'dias_restantes': dias_restantes
        })
    
    # Alertas de programaciones sin conductor
    programaciones_sin_conductor = Programacion.objects.filter(
        driver__isnull=True,
        fecha_programada__lte=timezone.now() + timedelta(hours=48)
    ).select_related('container')
    
    for prog in programaciones_sin_conductor:
        horas_restantes = (prog.fecha_programada - timezone.now()).total_seconds() / 3600
        alertas.append({
            'tipo': 'sin_conductor',
            'prioridad': 'critica' if horas_restantes < 24 else 'alta',
            'container_id': prog.container.container_id,
            'mensaje': f'Sin conductor asignado - Faltan {int(horas_restantes)} horas',
            'horas_restantes': int(horas_restantes)
        })
    
    # Ordenar por prioridad
    prioridad_orden = {'critica': 0, 'alta': 1, 'media': 2, 'baja': 3}
    alertas.sort(key=lambda x: prioridad_orden.get(x['prioridad'], 9))
    
    return Response({
        'success': True,
        'total': len(alertas),
        'alertas': alertas
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def analytics_conductores(request):
    """
    Analíticas de rendimiento de conductores
    """
    drivers = Driver.objects.all()
    
    analytics = []
    for driver in drivers:
        # Calcular estadísticas
        programaciones_completadas = Programacion.objects.filter(
            driver=driver,
            container__estado__in=['descargado', 'devuelto']
        ).count()
        
        analytics.append({
            'driver_id': driver.id,
            'nombre': driver.nombre,
            'esta_disponible': driver.esta_disponible,
            'entregas_dia': driver.num_entregas_dia,
            'max_entregas_dia': driver.max_entregas_dia,
            'total_entregas': driver.total_entregas,
            'entregas_a_tiempo': driver.entregas_a_tiempo,
            'cumplimiento_porcentaje': float(driver.cumplimiento_porcentaje),
            'ocupacion_porcentaje': float(driver.ocupacion_porcentaje),
            'programaciones_completadas': programaciones_completadas
        })
    
    # Ordenar por cumplimiento
    analytics.sort(key=lambda x: x['cumplimiento_porcentaje'], reverse=True)
    
    return Response({
        'success': True,
        'total': len(analytics),
        'conductores': analytics
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def analytics_eficiencia(request):
    """
    Métricas de eficiencia operacional
    """
    # Calcular tiempo promedio de operación
    tiempos_operacion = TiempoOperacion.objects.filter(
        anomalia=False
    ).aggregate(
        tiempo_promedio=Avg('tiempo_real_min')
    )
    
    # Calcular tiempo promedio de viaje
    tiempos_viaje = TiempoViaje.objects.filter(
        anomalia=False
    ).aggregate(
        tiempo_promedio=Avg('tiempo_real_min')
    )
    
    # Calcular tasa de cumplimiento general
    drivers = Driver.objects.all()
    if drivers.exists():
        tasa_cumplimiento = sum(float(d.cumplimiento_porcentaje) for d in drivers) / drivers.count()
    else:
        tasa_cumplimiento = 0
    
    # Entregas completadas últimos 7 días
    fecha_inicio = timezone.now() - timedelta(days=7)
    entregas_recientes = Container.objects.filter(
        estado__in=['descargado', 'devuelto'],
        fecha_descarga__gte=fecha_inicio
    ).count()
    
    # Contenedores por estado (para análisis de flujo)
    estados_count = Container.objects.values('estado').annotate(
        count=Count('id')
    )
    
    return Response({
        'success': True,
        'tiempo_promedio_operacion_min': tiempos_operacion['tiempo_promedio'] or 0,
        'tiempo_promedio_viaje_min': tiempos_viaje['tiempo_promedio'] or 0,
        'tasa_cumplimiento_porcentaje': round(tasa_cumplimiento, 2),
        'entregas_ultimos_7_dias': entregas_recientes,
        'distribucion_estados': list(estados_count)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def analytics_tendencias(request):
    """
    Tendencias y patrones históricos
    """
    dias = int(request.query_params.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    # Entregas por día
    entregas_por_dia = []
    for i in range(dias):
        fecha = (timezone.now() - timedelta(days=dias-i-1)).date()
        count = Container.objects.filter(
            estado__in=['descargado', 'devuelto'],
            fecha_descarga__date=fecha
        ).count()
        
        entregas_por_dia.append({
            'fecha': fecha.isoformat(),
            'entregas': count
        })
    
    # Promedio de entregas por día de la semana
    from collections import defaultdict
    entregas_por_dia_semana = defaultdict(int)
    contenedores_completados = Container.objects.filter(
        fecha_descarga__gte=fecha_inicio,
        estado__in=['descargado', 'devuelto']
    )
    
    for container in contenedores_completados:
        dia_semana = container.fecha_descarga.weekday()  # 0=Monday, 6=Sunday
        entregas_por_dia_semana[dia_semana] += 1
    
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    entregas_semana = [
        {'dia': dias_semana[i], 'entregas': entregas_por_dia_semana.get(i, 0)}
        for i in range(7)
    ]
    
    return Response({
        'success': True,
        'periodo_dias': dias,
        'entregas_por_dia': entregas_por_dia,
        'entregas_por_dia_semana': entregas_semana
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def ml_learning_stats(request):
    """
    Estadísticas de aprendizaje del sistema de Machine Learning
    
    Muestra:
    - Datos recolectados para entrenamiento
    - Precisión del modelo
    - Estadísticas de asignación automática
    - Progreso del aprendizaje
    """
    from apps.cds.models import CD
    
    # Estadísticas de datos de entrenamiento
    fecha_30_dias = timezone.now() - timedelta(days=30)
    fecha_7_dias = timezone.now() - timedelta(days=7)
    
    # Tiempos de operación
    total_tiempos_operacion = TiempoOperacion.objects.count()
    tiempos_operacion_recientes = TiempoOperacion.objects.filter(
        fecha__gte=fecha_30_dias
    ).count()
    tiempos_operacion_validos = TiempoOperacion.objects.filter(
        anomalia=False
    ).count()
    
    # Tiempos de viaje
    total_tiempos_viaje = TiempoViaje.objects.count()
    tiempos_viaje_recientes = TiempoViaje.objects.filter(
        fecha__gte=fecha_30_dias
    ).count()
    tiempos_viaje_validos = TiempoViaje.objects.filter(
        anomalia=False
    ).count()
    
    # Estadísticas por CD
    cds_con_datos = []
    for cd in CD.objects.all():
        tiempos_cd = TiempoOperacion.objects.filter(
            cd=cd,
            anomalia=False
        ).count()
        
        if tiempos_cd > 0:
            # Calcular precisión promedio (diferencia entre estimado y real)
            tiempos_cd_obj = TiempoOperacion.objects.filter(
                cd=cd,
                anomalia=False,
                fecha__gte=fecha_30_dias
            )
            
            if tiempos_cd_obj.exists():
                total_diff = 0
                count = 0
                for tiempo in tiempos_cd_obj:
                    diff_abs = abs(tiempo.tiempo_real_min - tiempo.tiempo_estimado_min)
                    total_diff += diff_abs
                    count += 1
                
                error_promedio_min = total_diff / count if count > 0 else 0
                precision = max(0, 100 - (error_promedio_min / 60 * 100))  # Precisión basada en error
            else:
                precision = 0
            
            cds_con_datos.append({
                'cd_nombre': cd.nombre,
                'datos_recolectados': tiempos_cd,
                'precision_porcentaje': round(precision, 1),
                'estado_aprendizaje': 'Excelente' if tiempos_cd > 50 else 'Bueno' if tiempos_cd > 20 else 'Inicial'
            })
    
    # Estadísticas de asignación automática
    total_programaciones = Programacion.objects.count()
    programaciones_asignadas = Programacion.objects.filter(
        driver__isnull=False
    ).count()
    
    programaciones_recientes = Programacion.objects.filter(
        created_at__gte=fecha_7_dias
    )
    asignaciones_recientes = programaciones_recientes.filter(
        driver__isnull=False
    ).count()
    
    tasa_asignacion = (asignaciones_recientes / programaciones_recientes.count() * 100) if programaciones_recientes.count() > 0 else 0
    
    # Resumen del estado del ML
    datos_minimos_operacion = 20  # Mínimo de datos para considerar el ML "entrenado"
    datos_minimos_viaje = 10
    
    ml_operacion_estado = 'Entrenado' if tiempos_operacion_validos >= datos_minimos_operacion else 'En entrenamiento'
    ml_viaje_estado = 'Entrenado' if tiempos_viaje_validos >= datos_minimos_viaje else 'En entrenamiento'
    
    # Calcular progreso general
    progreso_operacion = min(100, (tiempos_operacion_validos / datos_minimos_operacion * 100))
    progreso_viaje = min(100, (tiempos_viaje_validos / datos_minimos_viaje * 100))
    progreso_general = (progreso_operacion + progreso_viaje) / 2
    
    return Response({
        'success': True,
        'resumen': {
            'estado_general': 'Activo' if progreso_general > 50 else 'Inicial',
            'progreso_porcentaje': round(progreso_general, 1),
            'datos_total': total_tiempos_operacion + total_tiempos_viaje,
            'datos_ultimos_30_dias': tiempos_operacion_recientes + tiempos_viaje_recientes,
        },
        'tiempos_operacion': {
            'total': total_tiempos_operacion,
            'validos': tiempos_operacion_validos,
            'recientes_30d': tiempos_operacion_recientes,
            'anomalos': total_tiempos_operacion - tiempos_operacion_validos,
            'estado': ml_operacion_estado,
            'progreso_porcentaje': round(progreso_operacion, 1)
        },
        'tiempos_viaje': {
            'total': total_tiempos_viaje,
            'validos': tiempos_viaje_validos,
            'recientes_30d': tiempos_viaje_recientes,
            'anomalos': total_tiempos_viaje - tiempos_viaje_validos,
            'estado': ml_viaje_estado,
            'progreso_porcentaje': round(progreso_viaje, 1)
        },
        'asignacion_automatica': {
            'total_programaciones': total_programaciones,
            'total_asignadas': programaciones_asignadas,
            'asignaciones_ultimos_7d': asignaciones_recientes,
            'tasa_asignacion_porcentaje': round(tasa_asignacion, 1)
        },
        'aprendizaje_por_cd': cds_con_datos,
        'recomendaciones': [
            'Sistema aprendiendo continuamente de operaciones reales',
            f'Se han recolectado {tiempos_operacion_recientes} datos de operación en los últimos 30 días',
            f'Se han recolectado {tiempos_viaje_recientes} datos de viaje en los últimos 30 días',
            'Continúa operando normalmente para mejorar la precisión del sistema'
        ]
    })
