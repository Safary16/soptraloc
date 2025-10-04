"""
Vistas adicionales para el flujo de devolución de contenedores
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.containers.models import Container, ContainerMovement
from apps.core.models import MovementCode
from apps.drivers.models import Driver, Assignment
import logging

logger = logging.getLogger(__name__)


@login_required
def mark_ready_for_return(request):
    """
    Marca un contenedor como disponible para devolución.
    Transición: ARRIBADO o DESCARGADO_CD → DISPONIBLE_DEVOLUCION
    """
    if request.method == 'POST':
        try:
            container_id = request.POST.get('container_id')
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
            container.save(update_fields=['status'])
            
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
            container_id = request.POST.get('container_id')
            driver_id = request.POST.get('driver_id')
            return_location = request.POST.get('return_location', 'CCTI')  # CCTI por defecto
            
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
            
            # Crear asignación de devolución
            assignment = Assignment.objects.create(
                container=container,
                driver=driver,
                fecha_asignacion=timezone.now(),
                estado='PENDIENTE',
                tipo_asignacion='DEVOLUCION',
                # origen será el CD actual, destino será el return_location
                created_by=request.user
            )
            
            # Actualizar contenedor y conductor
            container.conductor_asignado = driver
            container.status = 'ASIGNADO'  # Vuelve a ASIGNADO para la devolución
            container.save(update_fields=['conductor_asignado', 'status'])
            
            driver.contenedor_asignado = container
            driver.save(update_fields=['contenedor_asignado'])
            
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
            
            logger.info(
                "Conductor %s asignado para devolver contenedor %s a %s",
                driver.nombre,
                container.container_number,
                return_location
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Conductor {driver.nombre} asignado para devolución'
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
            container_id = request.POST.get('container_id')
            container = get_object_or_404(Container, id=container_id)
            
            if container.status != 'ASIGNADO' or not container.conductor_asignado:
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor debe tener conductor asignado para devolución'
                })
            
            # Cambiar estado
            container.status = 'EN_RUTA_DEVOLUCION'
            container.current_position = 'EN_RUTA'
            now = timezone.now()
            container.tiempo_inicio_ruta = now
            container.save(update_fields=['status', 'current_position', 'tiempo_inicio_ruta'])
            
            # Actualizar assignment
            assignment = Assignment.objects.filter(
                container=container,
                driver=container.conductor_asignado,
                estado='PENDIENTE'
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
            container_id = request.POST.get('container_id')
            has_eir = request.POST.get('has_eir', 'false').lower() == 'true'
            
            container = get_object_or_404(Container, id=container_id)
            
            if container.status != 'EN_RUTA_DEVOLUCION':
                return JsonResponse({
                    'success': False,
                    'message': 'El contenedor debe estar en ruta de devolución'
                })
            
            # Finalizar contenedor
            now = timezone.now()
            container.status = 'FINALIZADO'
            container.current_position = 'DEPOSITO_DEVOLUCION'
            container.return_date = now.date()
            container.has_eir = has_eir
            
            # Calcular tiempo total del ciclo
            if container.tiempo_asignacion:
                delta = now - container.tiempo_asignacion
                container.duracion_total = int(delta.total_seconds() / 60)
            
            container.save(update_fields=[
                'status', 'current_position', 'return_date', 'has_eir', 'duracion_total'
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
                    estado='EN_CURSO'
                ).first()
                
                if assignment:
                    assignment.estado = 'COMPLETADA'
                    assignment.fecha_completada = now
                    if assignment.fecha_inicio:
                        elapsed = now - assignment.fecha_inicio
                        assignment.tiempo_real = int(elapsed.total_seconds() / 60)
                    assignment.save(update_fields=['estado', 'fecha_completada', 'tiempo_real'])
                
                container.conductor_asignado = None
                container.save(update_fields=['conductor_asignado'])
            
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
            
            logger.info(
                "Contenedor %s finalizado. Ciclo completo. EIR: %s",
                container.container_number,
                has_eir
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Contenedor {container.container_number} finalizado exitosamente',
                'cycle_duration_minutes': container.duracion_total
            })
            
        except Exception as e:
            logger.exception("Error al finalizar contenedor")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
