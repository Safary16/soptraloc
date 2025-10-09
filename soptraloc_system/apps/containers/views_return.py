"""Vistas adicionales para el flujo de devolución de contenedores."""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.containers.models import Container, ContainerMovement
from apps.containers.services.demurrage import (
    create_demurrage_alert_if_needed,
    resolve_demurrage_alerts,
)
from apps.core.models import MovementCode
from apps.drivers.models import Driver, Assignment, Location
from apps.drivers.views import _has_schedule_conflict, _estimate_assignment_duration_minutes

logger = logging.getLogger(__name__)


def _extract_payload(request):
    """Obtiene el payload desde JSON o formulario clásico."""
    if request.content_type and 'application/json' in request.content_type:
        try:
            raw_body = request.body.decode('utf-8').strip() if request.body else ''
            return json.loads(raw_body) if raw_body else {}
        except (ValueError, UnicodeDecodeError):
            logger.warning("Payload JSON inválido en solicitud de devolución")
            return {}
    if request.method == 'POST':
        return request.POST
    return {}


def _fetch_or_create_location(value: str | None) -> Location | None:
    """Busca una Location por código/nombre y la crea si es necesario."""
    if not value:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    code_candidate = normalized.upper().replace(' ', '_')[:20]

    location = Location.objects.filter(code=code_candidate).first()
    if location:
        return location

    location = Location.objects.filter(name__iexact=normalized).first()
    if location:
        return location

    # Crear una nueva ubicación si no existe (evita duplicados con sufijo incremental)
    base_code = code_candidate or 'RETORNO'
    final_code = base_code
    suffix = 1
    while Location.objects.filter(code=final_code).exists():
        suffix += 1
        final_code = f"{base_code[:17]}_{suffix}"[:20]

    return Location.objects.create(
        name=normalized[:100],
        code=final_code,
        address=''
    )


def _resolve_return_locations(container: Container, return_location_label: str) -> tuple[Location | None, Location | None]:
    origin = None
    if container.current_position:
        origin = _fetch_or_create_location(container.current_position)
    if origin is None and container.cd_location:
        origin = _fetch_or_create_location(container.cd_location)

    destination = _fetch_or_create_location(return_location_label)
    return origin, destination


@login_required
def mark_ready_for_return(request):
    """
    Marca un contenedor como disponible para devolución.
    Transición: ARRIBADO o DESCARGADO_CD → DISPONIBLE_DEVOLUCION
    """
    if request.method == 'POST':
        try:
            data = _extract_payload(request)
            container_id = data.get('container_id')
            container = get_object_or_404(Container, id=container_id)
            
            # Validar que el contenedor esté en estado apropiado
            valid_statuses = ['ARRIBADO', 'DESCARGADO_CD']
            if container.status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': f'El contenedor debe estar en estado ARRIBADO o DESCARGADO_CD. Estado actual: {container.status}'
                })
            
            # Cambiar estado
            old_status = container.status
            container.status = 'DISPONIBLE_DEVOLUCION'
            container.save(update_fields=['status', 'updated_at'])
            
            # Registrar movimiento
            movement_code = MovementCode.generate_code('transfer')
            movement_code.created_by = request.user
            movement_code.save()
            
            ContainerMovement.objects.create(
                container=container,
                movement_type='TRANSFER',
                movement_code=movement_code,
                movement_date=timezone.now(),
                notes=f'Marcado como disponible para devolución (de {old_status})',
                created_by=request.user
            )

            create_demurrage_alert_if_needed(container, resolved_by=request.user)
            
            logger.info(
                "Contenedor %s marcado como disponible para devolución por usuario %s",
                container.container_number,
                request.user.username
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Contenedor {container.container_number} listo para devolución'
            })
            
        except Exception as e:
            logger.exception("Error al marcar contenedor para devolución")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def assign_return_driver(request):
    """
    Asigna conductor para devolución de contenedor.
    Similar a asignación normal pero para devolución.
    """
    if request.method == 'POST':
        try:
            data = _extract_payload(request)
            container_id = data.get('container_id')
            driver_id = data.get('driver_id')
            return_location = data.get('return_location', 'CCTI')  # CCTI por defecto
            
            container = get_object_or_404(Container, id=container_id)
            driver = get_object_or_404(Driver, id=driver_id)
            
            # Validar estado
            if container.status != 'DISPONIBLE_DEVOLUCION':
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor debe estar en estado DISPONIBLE_DEVOLUCION'
                })
            
            # Validar que conductor esté disponible
            if driver.contenedor_asignado:
                return JsonResponse({
                    'success': False,
                    'message': f'El conductor ya tiene asignado el contenedor {driver.contenedor_asignado.container_number}'
                })
            
            scheduled_datetime = timezone.now()
            origin_location, destination_location = _resolve_return_locations(container, return_location)

            duration_minutes = _estimate_assignment_duration_minutes(
                origin_location,
                destination_location,
                'DEVOLUCION',
                scheduled_datetime,
            )

            if _has_schedule_conflict(driver, scheduled_datetime, duration_minutes):
                return JsonResponse({
                    'success': False,
                    'message': f'El conductor {driver.nombre} tiene otra asignación en curso en ese horario'
                })

            assignment = Assignment.objects.create(
                container=container,
                driver=driver,
                fecha_programada=scheduled_datetime,
                estado='PENDIENTE',
                origen=origin_location,
                destino=destination_location,
                origen_legacy=(origin_location.name if origin_location else container.current_position or 'Origen no definido'),
                destino_legacy=destination_location.name if destination_location else return_location,
                tipo_asignacion='DEVOLUCION',
                created_by=request.user,
                tiempo_estimado=duration_minutes,
            )

            assignment.calculate_estimated_time(refresh=False)
            assignment.save(update_fields=['tiempo_estimado'])

            container.conductor_asignado = driver
            container.save(update_fields=['conductor_asignado', 'updated_at'])
            
            driver.contenedor_asignado = container
            driver.save(update_fields=['contenedor_asignado', 'updated_at'])
            
            # Registrar movimiento
            movement_code = MovementCode.generate_code('load')
            movement_code.created_by = request.user
            movement_code.save()
            
            ContainerMovement.objects.create(
                container=container,
                movement_type='LOAD_CHASSIS',
                movement_code=movement_code,
                movement_date=timezone.now(),
                notes=f'Asignado a {driver.nombre} para devolución a {return_location}',
                created_by=request.user
            )

            create_demurrage_alert_if_needed(container, resolved_by=request.user)
            
            logger.info(
                "Conductor %s asignado para devolver contenedor %s a %s",
                driver.nombre,
                container.container_number,
                return_location
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Conductor {driver.nombre} asignado para devolución',
                'assignment_id': assignment.id,
            })
            
        except Exception as e:
            logger.exception("Error al asignar conductor para devolución")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def start_return_route(request):
    """
    Marca inicio de ruta de devolución.
    Transición: ASIGNADO → EN_RUTA_DEVOLUCION
    """
    if request.method == 'POST':
        try:
            data = _extract_payload(request)
            container_id = data.get('container_id')
            container = get_object_or_404(Container, id=container_id)

            if container.status not in ['DISPONIBLE_DEVOLUCION', 'ASIGNADO'] or not container.conductor_asignado:
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor debe tener conductor asignado para devolución'
                })
            
            now = timezone.now()
            container.status = 'EN_RUTA_DEVOLUCION'
            container.current_position = 'EN_RUTA'
            container.position_status = 'chassis'
            if not container.tiempo_inicio_devolucion:
                container.tiempo_inicio_devolucion = now
            container.save(update_fields=['status', 'current_position', 'position_status', 'tiempo_inicio_devolucion', 'updated_at'])
            
            # Actualizar assignment
            assignment = Assignment.objects.filter(
                container=container,
                driver=container.conductor_asignado,
                estado='PENDIENTE',
                tipo_asignacion='DEVOLUCION'
            ).first()
            
            if assignment:
                assignment.estado = 'EN_CURSO'
                assignment.fecha_inicio = now
                assignment.save(update_fields=['estado', 'fecha_inicio'])
            
            # Registrar movimiento
            movement_code = MovementCode.generate_code('transfer')
            movement_code.created_by = request.user
            movement_code.save()
            
            ContainerMovement.objects.create(
                container=container,
                movement_type='TRANSFER',
                movement_code=movement_code,
                movement_date=now,
                notes='Inicio de ruta de devolución',
                created_by=request.user
            )

            create_demurrage_alert_if_needed(container, resolved_by=request.user)
            
            logger.info(
                "Contenedor %s inició ruta de devolución con conductor %s",
                container.container_number,
                container.conductor_asignado.nombre
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Ruta de devolución iniciada'
            })
            
        except Exception as e:
            logger.exception("Error al iniciar ruta de devolución")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def finalize_container(request):
    """
    Finaliza el ciclo del contenedor tras devolverlo.
    Transición: EN_RUTA_DEVOLUCION → FINALIZADO
    """
    if request.method == 'POST':
        try:
            data = _extract_payload(request)
            container_id = data.get('container_id')
            has_eir = str(data.get('has_eir', 'false')).lower() == 'true'
            final_position = data.get('final_position', 'DEPOSITO_DEVOLUCION')
            
            container = get_object_or_404(Container, id=container_id)
            
            if container.status != 'EN_RUTA_DEVOLUCION':
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor debe estar en ruta de devolución'
                })
            
            # Finalizar contenedor
            now = timezone.now()
            container.status = 'FINALIZADO'
            container.current_position = final_position or 'DEPOSITO_DEVOLUCION'
            container.position_status = 'warehouse'
            container.return_date = now.date()
            container.has_eir = has_eir

            if container.tiempo_inicio_devolucion:
                delta_dev = now - container.tiempo_inicio_devolucion
                container.duracion_devolucion = int(delta_dev.total_seconds() / 60)

            if not container.tiempo_arribo_devolucion:
                container.tiempo_arribo_devolucion = now

            if not container.tiempo_finalizacion:
                container.tiempo_finalizacion = now

            if container.tiempo_asignacion and not container.duracion_total:
                delta = now - container.tiempo_asignacion
                container.duracion_total = int(delta.total_seconds() / 60)

            container.save(update_fields=[
                'status',
                'current_position',
                'position_status',
                'return_date',
                'has_eir',
                'duracion_total',
                'duracion_devolucion',
                'tiempo_arribo_devolucion',
                'tiempo_finalizacion',
                'updated_at'
            ])
            
            # Liberar conductor
            if container.conductor_asignado:
                driver = container.conductor_asignado
                driver.contenedor_asignado = None
                driver.save(update_fields=['contenedor_asignado'])
                
                # Actualizar assignment
                assignment = Assignment.objects.filter(
                    container=container,
                    driver=driver,
                    estado__in=['PENDIENTE', 'EN_CURSO'],
                    tipo_asignacion='DEVOLUCION'
                ).first()
                
                if assignment:
                    if assignment.fecha_inicio:
                        total_minutes = int((now - assignment.fecha_inicio).total_seconds() / 60)
                    else:
                        total_minutes = container.duracion_devolucion or container.duracion_total or 0

                    assignment.record_actual_times(
                        total_minutes=total_minutes,
                        route_minutes=container.duracion_devolucion,
                    )
                
                container.conductor_asignado = None
                container.save(update_fields=['conductor_asignado', 'updated_at'])
            
            # Registrar movimiento final
            movement_code = MovementCode.generate_code('unload')
            movement_code.created_by = request.user
            movement_code.save()
            
            ContainerMovement.objects.create(
                container=container,
                movement_type='UNLOAD_CHASSIS',
                movement_code=movement_code,
                movement_date=now,
                notes=f'Contenedor devuelto y finalizado. EIR: {has_eir}',
                created_by=request.user
            )

            resolve_demurrage_alerts(container, resolved_by=request.user)
            
            logger.info(
                "Contenedor %s finalizado. Ciclo completo. EIR: %s",
                container.container_number,
                has_eir
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Contenedor {container.container_number} finalizado exitosamente',
                'cycle_duration_minutes': container.duracion_total,
                'return_duration_minutes': container.duracion_devolucion
            })
            
        except Exception as e:
            logger.exception("Error al finalizar contenedor")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
