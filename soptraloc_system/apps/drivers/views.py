from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Driver, Assignment, Alert, TimeMatrix, Location
from apps.containers.models import Container
import json


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
            
            # Verificar que el conductor esté disponible
            if not driver.esta_disponible:
                return JsonResponse({
                    'success': False, 
                    'message': f'El conductor {driver.nombre} no está disponible'
                })
            
            # Crear asignación
            if container.scheduled_date and container.scheduled_time:
                fecha_programada = timezone.make_aware(
                    timezone.datetime.combine(container.scheduled_date, container.scheduled_time)
                )
            else:
                fecha_programada = timezone.now()
                
            assignment = Assignment.objects.create(
                container=container,
                driver=driver,
                fecha_programada=fecha_programada,
                estado='PENDIENTE',
                origen_legacy=driver.get_ubicacion_actual_display() if hasattr(driver, 'get_ubicacion_actual_display') else str(driver.ubicacion_actual),
                destino_legacy=container.cd_location or 'CD No definido',
                created_by=request.user
            )
            
            # Actualizar relaciones
            driver.contenedor_asignado = container
            driver.save()
            
            # Actualizar container status y asignar conductor
            container.status = 'ASIGNADO'
            container.conductor_asignado = driver
            container.save()
            
            # Resolver alerta si existe
            Alert.objects.filter(
                tipo='CONTENEDOR_SIN_ASIGNAR',
                container=container,
                is_active=True
            ).update(
                is_active=False,
                fecha_resolucion=timezone.now(),
                resuelto_por=request.user
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Contenedor {container.container_number} asignado a {driver.nombre}'
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
        
        # Determinar tipo de conductor necesario basado en destino
        if container.cd_location and 'CD' in container.cd_location:
            # Para CD se necesitan localeros
            tipo_requerido = 'LOCALERO'
        else:
            # Para puertos se pueden usar troncales
            tipo_requerido = 'TRONCO'
        
        # Obtener la fecha/hora programada
        scheduled_datetime = None
        if container.scheduled_date and container.scheduled_time:
            scheduled_datetime = timezone.datetime.combine(
                container.scheduled_date, 
                container.scheduled_time
            ).replace(tzinfo=timezone.get_current_timezone())
        
        # Obtener conductores disponibles del tipo adecuado
        available_drivers = Driver.objects.filter(
            estado='OPERATIVO',
            contenedor_asignado__isnull=True,
            tipo_conductor=tipo_requerido,
            is_active=True
        )
        
        # Si hay fecha programada, verificar conflictos de horario
        if scheduled_datetime:
            # Buscar conductores que NO tienen asignaciones conflictivas
            conflicted_drivers = Assignment.objects.filter(
                fecha_programada__date=scheduled_datetime.date(),
                estado__in=['PENDIENTE', 'EN_CURSO']
            ).values_list('driver_id', flat=True)
            
            available_drivers = available_drivers.exclude(id__in=conflicted_drivers)
        
        available_drivers = available_drivers.order_by('nombre')
        
        drivers_data = []
        for driver in available_drivers:
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
            today = timezone.now().date()
            tomorrow = today + timedelta(days=1)
            
            # Obtener contenedores sin asignar
            unassigned_containers = Container.objects.filter(
                status='PROGRAMADO',
                conductor_asignado__isnull=True,
                scheduled_date__in=[today, tomorrow]
            ).order_by('scheduled_date', 'scheduled_time')
            
            # Obtener conductores disponibles
            available_drivers = Driver.objects.filter(
                is_active=True,
                estado='OPERATIVO',
                contenedor_asignado__isnull=True,
                ultimo_registro_asistencia=today  # Solo conductores presentes
            )
            
            assigned_count = 0
            
            for container in unassigned_containers[:available_drivers.count()]:
                # Determinar tipo de conductor necesario
                if container.cd_location and 'CD' in container.cd_location:
                    tipo_requerido = 'LOCALERO'
                else:
                    tipo_requerido = 'TRONCO'
                
                # Buscar conductor del tipo adecuado
                suitable_driver = available_drivers.filter(
                    tipo_conductor=tipo_requerido
                ).first()
                
                if not suitable_driver:
                    # Si no hay del tipo específico, usar cualquier disponible
                    suitable_driver = available_drivers.first()
                
                if suitable_driver:
                    # Crear asignación
                    if container.scheduled_date and container.scheduled_time:
                        fecha_programada = timezone.make_aware(
                            timezone.datetime.combine(container.scheduled_date, container.scheduled_time)
                        )
                    else:
                        fecha_programada = timezone.now()
                    
                    Assignment.objects.create(
                        container=container,
                        driver=suitable_driver,
                        fecha_programada=fecha_programada,
                        estado='PENDIENTE',
                        origen_legacy=suitable_driver.get_ubicacion_actual_display(),
                        destino_legacy=container.cd_location or 'CD No definido',
                        created_by=request.user
                    )
                    
                    # Actualizar relaciones
                    suitable_driver.contenedor_asignado = container
                    suitable_driver.save()
                    
                    container.status = 'ASIGNADO'
                    container.conductor_asignado = suitable_driver
                    container.save()
                    
                    # Remover de disponibles
                    available_drivers = available_drivers.exclude(id=suitable_driver.id)
                    assigned_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Asignación automática completada',
                'assigned_count': assigned_count
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            container_id = data.get('container_id')
            
            if not container_id:
                return JsonResponse({'success': False, 'message': 'ID de contenedor requerido'})
            
            # Obtener el contenedor
            from apps.containers.models import Container
            try:
                container = Container.objects.get(id=container_id, status='PROGRAMADO')
            except Container.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Contenedor no encontrado o no disponible'})
            
            # Obtener conductores disponibles hoy
            available_drivers = Driver.objects.filter(
                is_active=True,
                contenedor_asignado__isnull=True,
                hora_ingreso_hoy__isnull=False  # Solo conductores que han marcado asistencia
            ).select_related('ubicacion_actual')
            
            if not available_drivers.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'No hay conductores disponibles. Asegúrate de que hayan marcado asistencia.'
                })
            
            # Buscar el mejor conductor considerando tipo de vehículo y ubicación
            best_driver = None
            min_time = float('inf')
            
            for driver in available_drivers:
                # Verificar tipo de vehículo compatible
                if container.container_type in ['20ft', '20st']:
                    if driver.tipo_vehiculo not in ['SIMPLE', 'DOBLE']:
                        continue
                elif container.container_type in ['40ft', '40hc', '40hr', '40hn']:
                    if driver.tipo_vehiculo != 'DOBLE':
                        continue
                
                # Calcular tiempo estimado basado en ubicación
                if driver.ubicacion_actual and container.terminal:
                    try:
                        time_matrix = TimeMatrix.objects.get(
                            origin=driver.ubicacion_actual,
                            destination=container.terminal
                        )
                        estimated_time = time_matrix.travel_time
                    except TimeMatrix.DoesNotExist:
                        estimated_time = 60  # Tiempo por defecto si no hay matriz
                else:
                    estimated_time = 45  # Tiempo por defecto
                
                if estimated_time < min_time:
                    min_time = estimated_time
                    best_driver = driver
            
            if not best_driver:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró un conductor compatible para este tipo de contenedor'
                })
            
            # Crear la asignación
            assignment = Assignment.objects.create(
                driver=best_driver,
                container=container,
                origen_programado=container.terminal.name if container.terminal else 'Terminal',
                destino_programado=container.cd_location or 'CD',
                destino_legacy=container.cd_location or 'CD',
                created_by=request.user
            )
            
            # Calcular tiempo estimado
            assignment.calculate_estimated_time()
            assignment.save()
            
            # Actualizar contenedor
            container.status = 'ASIGNADO'
            container.conductor_asignado = best_driver
            container.tiempo_asignacion = timezone.now()
            container.save()
            
            # Actualizar conductor
            best_driver.contenedor_asignado = container
            best_driver.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Contenedor asignado automáticamente a {best_driver.nombre} ({best_driver.ppu})'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en asignación automática: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})