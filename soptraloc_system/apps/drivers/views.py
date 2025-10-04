from datetime import datetime, timedelta, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.containers.models import Container
from apps.containers.services.status_utils import normalize_status

from .models import Alert, Assignment, Driver, Location, TimeMatrix
import json

# Configuración auxiliar para asignaciones automáticas
DEFAULT_ASSIGNMENT_TIME = time(hour=8, minute=0)
CD_NAME_TO_CODE = {
    'CD QUILICURA': 'CD_QUILICURA',
    'CD CAMPOS': 'CD_CAMPOS',
    'CD CAMPOS DE CHILE - PUDAHUEL': 'CD_CAMPOS',
    'CD PUERTO MADERO': 'CD_MADERO',
    'CD PUERTO MADERO - PUDAHUEL': 'CD_MADERO',
    'CD EL PEÑÓN': 'CD_PENON',
    'CD EL PEÑON': 'CD_PENON',
}

SCHEDULE_BUFFER_MINUTES = 30
DEFAULT_ASSIGNMENT_DURATION = 120


def _compute_scheduled_datetime(container):
    """Obtiene la fecha/hora efectiva para programar una asignación."""
    if container.scheduled_date:
        scheduled_time = container.scheduled_time or DEFAULT_ASSIGNMENT_TIME
        naive_datetime = datetime.combine(container.scheduled_date, scheduled_time)
        if timezone.is_naive(naive_datetime):
            return timezone.make_aware(naive_datetime)
        return naive_datetime
    return timezone.now()


def _resolve_assignment_locations(driver, container):
    """Busca ubicaciones origen/destino compatibles con la asignación."""
    origin = Location.objects.filter(code=driver.ubicacion_actual).first()

    destination = None
    if container.cd_location:
        normalized_cd = container.cd_location.strip()
        destination_code = CD_NAME_TO_CODE.get(normalized_cd.upper())
        if destination_code:
            destination = Location.objects.filter(code=destination_code).first()
        if not destination:
            destination = Location.objects.filter(name__iexact=normalized_cd).first()
        if not destination:
            destination = Location.objects.filter(name__icontains=normalized_cd).first()

    return origin, destination


def _preferred_driver_types(container):
    """Determina los tipos de conductor preferidos según destino."""
    cd_location = (container.cd_location or '').upper()
    if cd_location.startswith('CD'):
        return ['LOCALERO', 'LEASING']
    return ['TRONCO', 'TRONCO_PM', 'LEASING']


def _estimate_assignment_duration_minutes(origin, destination, assignment_type, scheduled_datetime):
    if origin and destination:
        try:
            from apps.drivers.services.duration_predictor import DriverDurationPredictor
        except ImportError:
            DriverDurationPredictor = None

        if DriverDurationPredictor is not None:
            prediction = DriverDurationPredictor().predict(
                origin=origin,
                destination=destination,
                assignment_type=assignment_type,
                scheduled_datetime=scheduled_datetime,
            )
            if prediction and prediction.minutes:
                return prediction.minutes

        try:
            time_matrix = TimeMatrix.objects.get(from_location=origin, to_location=destination)
            return time_matrix.get_total_time()
        except TimeMatrix.DoesNotExist:
            pass
    return DEFAULT_ASSIGNMENT_DURATION


def _has_schedule_conflict(driver, start_datetime, duration_minutes):
    if start_datetime is None:
        start_datetime = timezone.now()
    if duration_minutes is None or duration_minutes <= 0:
        duration_minutes = DEFAULT_ASSIGNMENT_DURATION

    buffer = timedelta(minutes=SCHEDULE_BUFFER_MINUTES)
    window_start = start_datetime - buffer
    window_end = start_datetime + timedelta(minutes=duration_minutes) + buffer

    active_assignments = Assignment.objects.filter(
        driver=driver,
        estado__in=['PENDIENTE', 'EN_CURSO']
    )

    for assignment in active_assignments:
        assign_start = assignment.fecha_programada or assignment.fecha_inicio or timezone.now()
        if assignment.estado == 'EN_CURSO' and assignment.fecha_inicio:
            assign_start = assignment.fecha_inicio

        assign_duration = assignment.tiempo_estimado or DEFAULT_ASSIGNMENT_DURATION
        assign_end = assign_start + timedelta(minutes=assign_duration)

        if (assign_start - buffer) < window_end and window_start < (assign_end + buffer):
            return True

    return False


def _assign_driver_to_container(container, driver, user, scheduled_datetime=None, assignment_type='ENTREGA'):
    """Centraliza la creación de asignaciones y la actualización de estados."""
    scheduled_datetime = scheduled_datetime or _compute_scheduled_datetime(container)
    origin_location, destination_location = _resolve_assignment_locations(driver, container)

    today = timezone.localdate()
    if driver.ultimo_registro_asistencia != today or not driver.hora_ingreso_hoy:
        raise ValueError(f'El conductor {driver.nombre} no ha registrado asistencia hoy')

    duration_minutes = _estimate_assignment_duration_minutes(
        origin_location,
        destination_location,
        assignment_type,
        scheduled_datetime,
    )
    if _has_schedule_conflict(driver, scheduled_datetime, duration_minutes):
        raise ValueError(
            f'El conductor {driver.nombre} tiene otra asignación en horario conflictivo'
        )

    assignment = Assignment.objects.create(
        container=container,
        driver=driver,
        fecha_programada=scheduled_datetime,
        estado='PENDIENTE',
        origen=origin_location,
        destino=destination_location,
        origen_legacy=driver.get_ubicacion_actual_display() if hasattr(driver, 'get_ubicacion_actual_display') else driver.ubicacion_actual,
        destino_legacy=container.cd_location or 'CD No definido',
        created_by=user,
        tiempo_estimado=duration_minutes,
        tipo_asignacion=assignment_type
    )

    assignment.calculate_estimated_time(refresh=False)
    assignment.save(update_fields=['tiempo_estimado'])

    driver.contenedor_asignado = container
    driver.save(update_fields=['contenedor_asignado', 'updated_at'])

    now = timezone.now()
    container.status = 'ASIGNADO'
    container.conductor_asignado = driver
    container.tiempo_asignacion = now
    container.save(update_fields=['status', 'conductor_asignado', 'tiempo_asignacion', 'updated_at'])

    Alert.objects.filter(
        tipo='CONTENEDOR_SIN_ASIGNAR',
        container=container,
        is_active=True
    ).update(
        is_active=False,
        fecha_resolucion=now,
        resuelto_por=user
    )

    return assignment


def _pick_driver_for_container(container, drivers, excluded_driver_ids=None):
    """Selecciona y extrae el conductor más adecuado desde una lista mutable."""
    if not drivers:
        return None

    if excluded_driver_ids is None:
        excluded_driver_ids = set()

    preferred_types = _preferred_driver_types(container)
    for index, driver in enumerate(drivers):
        if driver.id in excluded_driver_ids:
            continue
        if driver.tipo_conductor in preferred_types:
            return drivers.pop(index)

    for index, driver in enumerate(drivers):
        if driver.id in excluded_driver_ids:
            continue
        return drivers.pop(index)

    return None


@login_required
def drivers_view(request):
    """Vista principal de conductores"""
    # Filtros
    tipo_filter = request.GET.get('tipo', '')
    estado_filter = request.GET.get('estado', '')
    ubicacion_filter = request.GET.get('ubicacion', '')
    
    # Obtener conductores
    drivers = Driver.objects.filter(is_active=True)
    
    if tipo_filter:
        drivers = drivers.filter(tipo_conductor=tipo_filter)
    if estado_filter:
        drivers = drivers.filter(estado=estado_filter)
    if ubicacion_filter:
        drivers = drivers.filter(ubicacion_actual=ubicacion_filter)
    
    drivers = drivers.order_by('nombre')
    
    # Estadísticas
    stats = {
        'total': Driver.objects.filter(is_active=True).count(),
        'operativos': Driver.objects.filter(estado='OPERATIVO', is_active=True).count(),
        'disponibles': Driver.objects.filter(estado='OPERATIVO', contenedor_asignado__isnull=True, is_active=True).count(),
        'asignados': Driver.objects.filter(contenedor_asignado__isnull=False, is_active=True).count(),
        'localeros': Driver.objects.filter(tipo_conductor='LOCALERO', is_active=True).count(),
        'troncales': Driver.objects.filter(tipo_conductor='TRONCO', is_active=True).count(),
    }
    
    context = {
        'title': 'Gestión de Conductores',
        'drivers': drivers,
        'stats': stats,
        'tipo_filter': tipo_filter,
        'estado_filter': estado_filter,
        'ubicacion_filter': ubicacion_filter,
        'tipo_choices': Driver.TIPO_CONDUCTOR_CHOICES,
        'estado_choices': Driver.ESTADO_CHOICES,
        'ubicacion_choices': Driver.UBICACION_CHOICES,
    }
    
    return render(request, 'drivers/drivers.html', context)


@login_required
def update_driver_location(request, driver_id):
    """Actualizar ubicación de conductor"""
    if request.method == 'POST':
        driver = get_object_or_404(Driver, id=driver_id)
        nueva_ubicacion = request.POST.get('ubicacion')
        
        if nueva_ubicacion in dict(Driver.UBICACION_CHOICES):
            driver.ubicacion_actual = nueva_ubicacion
            driver.tiempo_en_ubicacion = timezone.now()
            driver.save()
            
            messages.success(request, f'Ubicación de {driver.nombre} actualizada a {driver.get_ubicacion_actual_display()}')
        else:
            messages.error(request, 'Ubicación no válida')
    
    return redirect('drivers')


@login_required
def assign_container(request):
    """Asignar contenedor a conductor"""
    if request.method == 'POST':
        container_id = request.POST.get('container_id')
        driver_id = request.POST.get('driver_id')
        
        try:
            container = get_object_or_404(Container, id=container_id)
            driver = get_object_or_404(Driver, id=driver_id)
            
            if container.conductor_asignado_id:
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor ya cuenta con un conductor asignado'
                })

            # Verificar que el conductor esté disponible
            if not driver.esta_disponible:
                return JsonResponse({
                    'success': False, 
                    'message': f'El conductor {driver.nombre} no está disponible'
                })
            
            assignment = _assign_driver_to_container(container, driver, request.user)

            return JsonResponse({
                'success': True, 
                'message': f'Contenedor {container.container_number} asignado a {driver.nombre}',
                'assignment_id': assignment.id
            })
        except ValueError as exc:
            return JsonResponse({
                'success': False,
                'message': str(exc)
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error al asignar: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@csrf_exempt
@login_required
def unassign_driver(request):
    """Desasignar un conductor de un contenedor"""
    if request.method == 'POST':
        try:
            container_id = request.POST.get('container_id')
            container = get_object_or_404(Container, id=container_id)
            
            if not container.conductor_asignado:
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor no tiene conductor asignado'
                })
            
            # Desasignar conductor
            driver = container.conductor_asignado
            container.conductor_asignado = None
            container.status = 'PROGRAMADO'  # Volver al estado anterior
            container.save()
            
            # Actualizar estado del conductor
            driver.contenedor_asignado = None
            driver.save()
            
            # Cancelar asignación
            Assignment.objects.filter(
                container=container,
                driver=driver,
                estado__in=['PENDIENTE', 'EN_CURSO']
            ).update(
                estado='CANCELADA',
                fecha_completada=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Conductor {driver.nombre} desasignado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al desasignar conductor: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@csrf_exempt
@login_required
def check_driver_availability(request):
    """Verificar disponibilidad de un conductor para una fecha/hora específica"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            driver_id = data.get('driver_id')
            scheduled_date = data.get('scheduled_date')  # YYYY-MM-DD
            scheduled_time = data.get('scheduled_time')  # HH:MM
            duration = data.get('duration', 120)  # Duración en minutos, por defecto 2 horas
            
            driver = get_object_or_404(Driver, id=driver_id)
            
            # Convertir fecha y hora
            scheduled_datetime = timezone.datetime.strptime(
                f"{scheduled_date} {scheduled_time}", 
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=timezone.get_current_timezone())
            
            end_time = scheduled_datetime + timedelta(minutes=duration)
            
            # Verificar conflictos
            conflicts = Assignment.objects.filter(
                driver=driver,
                estado__in=['PENDIENTE', 'EN_CURSO'],
                fecha_programada__range=[
                    scheduled_datetime - timedelta(minutes=30),  # Buffer de 30 min
                    end_time + timedelta(minutes=30)
                ]
            )
            
            if conflicts.exists():
                conflict_list = []
                for conflict in conflicts:
                    conflict_list.append({
                        'container': conflict.container.container_number,
                        'time': conflict.fecha_programada.strftime('%H:%M'),
                        'destination': conflict.destino_legacy or conflict.destino.name if conflict.destino else 'N/A'
                    })
                
                return JsonResponse({
                    'available': False,
                    'message': f'Conductor no disponible - tiene {len(conflicts)} asignación(es) conflictiva(s)',
                    'conflicts': conflict_list
                })
            
            return JsonResponse({
                'available': True,
                'message': 'Conductor disponible',
                'driver_info': {
                    'name': driver.nombre,
                    'ppu': driver.ppu,
                    'location': driver.get_ubicacion_actual_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'available': False,
                'message': f'Error al verificar disponibilidad: {str(e)}'
            })
    
    return JsonResponse({'available': False, 'message': 'Método no permitido'})


@csrf_exempt
@login_required 
def resolve_alert(request):
    """Resolver una alerta manualmente"""
    if request.method == 'POST':
        try:
            alert_id = request.POST.get('alert_id')
            alert = get_object_or_404(Alert, id=alert_id)
            
            alert.is_active = False
            alert.fecha_resolucion = timezone.now()
            alert.resuelto_por = request.user
            alert.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Alerta resuelta exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al resolver alerta: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def get_available_drivers(request):
    """Obtener conductores disponibles para asignación con verificación de horarios"""
    container_id = request.GET.get('container_id')
    
    try:
        container = get_object_or_404(Container, id=container_id)
        today = timezone.localdate()
        
        # Determinar tipo de conductor necesario basado en destino
        if container.cd_location and 'CD' in container.cd_location:
            # Para CD se necesitan localeros
            tipo_requerido = 'LOCALERO'
        else:
            # Para puertos se pueden usar troncales
            tipo_requerido = 'TRONCO'
        
        scheduled_datetime = _compute_scheduled_datetime(container)
        container_status = normalize_status(container.status)
        assignment_type = 'DEVOLUCION' if container_status in {'DISPONIBLE_DEVOLUCION', 'EN_RUTA_DEVOLUCION'} else 'ENTREGA'
        
        # Obtener conductores disponibles del tipo adecuado y con asistencia registrada
        available_drivers = Driver.objects.filter(
            estado='OPERATIVO',
            contenedor_asignado__isnull=True,
            tipo_conductor=tipo_requerido,
            is_active=True,
            ultimo_registro_asistencia=today,
            hora_ingreso_hoy__isnull=False
        )
        candidates = available_drivers.order_by('nombre')

        drivers_data = []
        for driver in candidates:
            origin, destination = _resolve_assignment_locations(driver, container)
            duration = _estimate_assignment_duration_minutes(
                origin,
                destination,
                assignment_type,
                scheduled_datetime,
            )

            if _has_schedule_conflict(driver, scheduled_datetime, duration):
                continue

            drivers_data.append({
                'id': driver.id,
                'nombre': driver.nombre,
                'ppu': driver.ppu,
                'tipo': driver.get_tipo_conductor_display(),
                'ubicacion': driver.get_ubicacion_actual_display(),
                'tiempo_ubicacion': driver.tiempo_en_ubicacion_texto
            })
        
        return JsonResponse({
            'success': True,
            'drivers': drivers_data,
            'container': {
                'id': container.id,
                'number': container.container_number,
                'destination': container.cd_location,
                'scheduled_date': container.scheduled_date.strftime('%d/%m/%Y') if container.scheduled_date else '',
                'scheduled_time': container.scheduled_time.strftime('%H:%M') if container.scheduled_time else '',
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required 
def alerts_view(request):
    """Vista de alertas del sistema"""
    alerts = Alert.objects.filter(is_active=True).order_by('-prioridad', '-fecha_creacion')
    
    context = {
        'title': 'Alertas del Sistema',
        'alerts': alerts,
        'total_alerts': alerts.count(),
        'critical_alerts': alerts.filter(prioridad='CRITICA').count(),
        'high_alerts': alerts.filter(prioridad='ALTA').count(),
    }
    
    return render(request, 'drivers/alerts.html', context)


@login_required
def attendance_view(request):
    """Vista de pase de lista de conductores"""
    today = timezone.now().date()
    
    # Obtener conductores activos
    drivers = Driver.objects.filter(is_active=True).order_by('nombre')
    
    # Verificar quién ya registró ingreso hoy
    for driver in drivers:
        if driver.ultimo_registro_asistencia == today:
            # Ya se registró hoy, mantener hora_ingreso_hoy
            pass
        else:
            # No se ha registrado hoy, limpiar hora_ingreso_hoy
            if driver.hora_ingreso_hoy:
                driver.hora_ingreso_hoy = None
                driver.save(update_fields=['hora_ingreso_hoy'])
    
    # Estadísticas
    stats = {
        'total': drivers.count(),
        'presentes': drivers.filter(ultimo_registro_asistencia=today).count(),
        'disponibles': drivers.filter(
            estado='OPERATIVO', 
            contenedor_asignado__isnull=True,
            ultimo_registro_asistencia=today
        ).count(),
        'asignados': drivers.filter(contenedor_asignado__isnull=False).count(),
    }
    
    # Contenedores sin asignar
    unassigned_containers = Container.objects.filter(
        status='PROGRAMADO',
        conductor_asignado__isnull=True,
        scheduled_date__in=[today, today + timedelta(days=1)]
    )
    
    # Próximas salidas (próxima hora)
    next_hour = timezone.now() + timedelta(hours=1)
    next_hour_containers = Container.objects.filter(
        status__in=['ASIGNADO', 'PROGRAMADO'],
        scheduled_date=today,
        scheduled_time__lte=next_hour.time()
    )
    
    context = {
        'title': 'Pase de Lista',
        'drivers': drivers,
        'stats': stats,
        'today': today,
        'unassigned_containers': unassigned_containers,
        'next_hour_containers': next_hour_containers,
    }
    
    return render(request, 'drivers/attendance.html', context)


@login_required
def mark_present(request):
    """Marcar conductor como presente"""
    if request.method == 'POST':
        try:
            driver_id = request.POST.get('driver_id')
            driver = get_object_or_404(Driver, id=driver_id)
            
            today = timezone.now().date()
            now = timezone.now()
            
            if driver.ultimo_registro_asistencia == today:
                return JsonResponse({
                    'success': False,
                    'message': f'{driver.nombre} ya fue registrado hoy'
                })
            
            # Registrar asistencia
            driver.hora_ingreso_hoy = now
            driver.ultimo_registro_asistencia = today
            driver.estado = 'OPERATIVO'
            driver.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{driver.nombre} marcado como presente a las {now.strftime("%H:%M")}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar asistencia: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def mass_entry(request):
    """Registro masivo de ingreso"""
    if request.method == 'POST':
        try:
            today = timezone.now().date()
            now = timezone.now()
            
            # Marcar como presentes a todos los conductores operativos que no se han registrado hoy
            drivers_to_update = Driver.objects.filter(
                is_active=True,
                estado='OPERATIVO'
            ).exclude(ultimo_registro_asistencia=today)
            
            updated_count = 0
            for driver in drivers_to_update:
                driver.hora_ingreso_hoy = now
                driver.ultimo_registro_asistencia = today
                driver.save()
                updated_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'{updated_count} conductores marcados como presentes'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en registro masivo: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def auto_assign_drivers(request):
    """Asignación automática de conductores"""
    if request.method == 'POST':
        try:
            today = timezone.localdate()
            tomorrow = today + timedelta(days=1)

            unassigned_containers = Container.objects.filter(
                conductor_asignado__isnull=True,
                status__in=['PROGRAMADO', 'EN_PROCESO', 'EN_SECUENCIA', 'SECUENCIADO'],
                scheduled_date__in=[today, tomorrow]
            ).order_by('scheduled_date', 'scheduled_time', 'container_number')

            available_drivers = list(
                Driver.objects.filter(
                    is_active=True,
                    estado='OPERATIVO',
                    contenedor_asignado__isnull=True,
                    ultimo_registro_asistencia=today,
                    hora_ingreso_hoy__isnull=False
                ).order_by('tiempo_en_ubicacion')
            )

            assigned_count = 0
            pending_containers = []

            for container in unassigned_containers:
                attempted_ids = set()
                assignment_error = None

                while available_drivers:
                    driver = _pick_driver_for_container(container, available_drivers, attempted_ids)
                    if not driver:
                        break

                    attempted_ids.add(driver.id)

                    try:
                        _assign_driver_to_container(container, driver, request.user)
                        assigned_count += 1
                        break
                    except ValueError as exc:
                        assignment_error = str(exc)
                        available_drivers.append(driver)
                        continue

                else:
                    driver = None

                if not driver or driver.id not in attempted_ids:
                    pending_containers.append({
                        'number': container.container_number,
                        'reason': assignment_error or 'Sin conductores con horario disponible'
                    })

            message = f'{assigned_count} contenedores asignados automáticamente'
            if pending_containers:
                detalles = ', '.join(
                    f"{item['number']} ({item['reason']})" for item in pending_containers[:5]
                )
                message += f". Sin conductor disponible para: {detalles}" + (
                    '...' if len(pending_containers) > 5 else ''
                )

            return JsonResponse({
                'success': True,
                'message': message,
                'assigned_count': assigned_count,
                'pending_containers': [item['number'] for item in pending_containers]
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en asignación automática: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@csrf_exempt
@login_required  
def auto_assign_single(request):
    """Asignación automática para un contenedor específico"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Formato JSON inválido'})

    container_id = data.get('container_id')
    if not container_id:
        return JsonResponse({'success': False, 'message': 'ID de contenedor requerido'})

    container = get_object_or_404(Container, id=container_id)

    if container.conductor_asignado_id:
        return JsonResponse({'success': False, 'message': 'El contenedor ya posee un conductor asignado'})

    status_code = normalize_status(container.status)
    if status_code not in {'PROGRAMADO', 'EN_PROCESO', 'EN_SECUENCIA', 'SECUENCIADO', 'LIBERADO'}:
        return JsonResponse({'success': False, 'message': f'Estado {status_code} no admite asignación automática'})

    today = timezone.localdate()

    available_drivers = list(
        Driver.objects.filter(
            is_active=True,
            estado='OPERATIVO',
            contenedor_asignado__isnull=True,
            ultimo_registro_asistencia=today,
            hora_ingreso_hoy__isnull=False
        ).order_by('tiempo_en_ubicacion')
    )

    attempted_ids = set()
    last_error = None

    while available_drivers:
        driver = _pick_driver_for_container(container, available_drivers, attempted_ids)
        if not driver:
            break

        attempted_ids.add(driver.id)

        try:
            assignment = _assign_driver_to_container(container, driver, request.user)

            return JsonResponse({
                'success': True,
                'message': f'Contenedor {container.container_number} asignado a {driver.nombre} ({driver.ppu})',
                'assignment_id': assignment.id,
                'driver': {
                    'id': driver.id,
                    'nombre': driver.nombre,
                    'tipo': driver.get_tipo_conductor_display(),
                    'ubicacion': driver.get_ubicacion_actual_display(),
                }
            })

        except ValueError as exc:
            last_error = str(exc)
            available_drivers.append(driver)
            continue

    return JsonResponse({
        'success': False,
        'message': last_error or 'No hay conductores disponibles para asignar automáticamente'
    })