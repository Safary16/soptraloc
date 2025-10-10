"""
Servicios para actualización de estados de contenedores.
FASE 3: Refactoring de funciones largas - Extraer lógica de negocio de views.
"""
from typing import Optional, Dict, Any
from datetime import datetime

from django.utils import timezone
from django.contrib.auth.models import User

from apps.containers.models import Container, ContainerMovement
from apps.core.models import MovementCode
from apps.drivers.models import Assignment
from apps.containers.services.demurrage import (
    create_demurrage_alert_if_needed,
    resolve_demurrage_alerts
)


class ContainerStatusUpdater:
    """Servicio para actualizar estados de contenedores con lógica de tiempos."""
    
    def __init__(self, container: Container, new_status: str, user: User):
        self.container = container
        self.new_status = new_status
        self.user = user
        self.old_status = container.status
        self.now = timezone.now()
    
    def update_status(self) -> Dict[str, Any]:
        """
        Actualiza el estado del contenedor y registra tiempos correspondientes.
        
        Returns:
            Dict con información de la actualización
        """
        # Actualizar estado
        self.container.status = self.new_status
        
        # Registrar tiempos según el nuevo estado
        self._update_timestamps()
        
        # Guardar cambios
        self.container.save()
        
        # Acciones post-actualización
        self._handle_driver_release()
        self._handle_assignment_completion()
        self._create_movement_record()
        self._handle_demurrage_alerts()
        
        return {
            'success': True,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'container_id': self.container.id
        }
    
    def _update_timestamps(self) -> None:
        """Actualiza timestamps según el nuevo estado."""
        if self.new_status == 'ASIGNADO' and not self.container.tiempo_asignacion:
            self.container.tiempo_asignacion = self.now
        
        elif self.new_status == 'EN_RUTA':
            if not self.container.tiempo_inicio_ruta:
                self.container.tiempo_inicio_ruta = self.now
                if self.container.tiempo_asignacion:
                    delta = self.now - self.container.tiempo_asignacion
                    self.container.duracion_ruta = int(delta.total_seconds() / 60)
        
        elif self.new_status == 'ARRIBADO':
            if not self.container.tiempo_llegada:
                self.container.tiempo_llegada = self.now
                if self.container.tiempo_inicio_ruta:
                    delta = self.now - self.container.tiempo_inicio_ruta
                    self.container.duracion_ruta = int(delta.total_seconds() / 60)
        
        elif self.new_status == 'FINALIZADO':
            if not self.container.tiempo_finalizacion:
                self.container.tiempo_finalizacion = self.now
                if self.container.tiempo_llegada:
                    delta = self.now - self.container.tiempo_llegada
                    self.container.duracion_descarga = int(delta.total_seconds() / 60)
                if self.container.tiempo_asignacion:
                    delta_total = self.now - self.container.tiempo_asignacion
                    self.container.duracion_total = int(delta_total.total_seconds() / 60)
    
    def _handle_driver_release(self) -> None:
        """Libera el conductor si el estado es final."""
        if self.new_status in ['ARRIBADO', 'DESCARGADO_CD']:
            if self.container.conductor_asignado:
                driver = self.container.conductor_asignado
                driver.contenedor_asignado = None
                if driver.estado != 'OPERATIVO':
                    driver.estado = 'OPERATIVO'
                driver.save(update_fields=['contenedor_asignado', 'estado', 'updated_at'])
                self.container.conductor_asignado = None
                self.container.save(update_fields=['conductor_asignado'])
        
        elif self.new_status == 'FINALIZADO':
            if self.container.conductor_asignado:
                driver = self.container.conductor_asignado
                driver.contenedor_asignado = None
                driver.save(update_fields=['contenedor_asignado', 'updated_at'])
                self.container.conductor_asignado = None
                self.container.save(update_fields=['conductor_asignado'])
    
    def _handle_assignment_completion(self) -> None:
        """Completa la asignación registrando tiempos reales."""
        if self.new_status in ['ARRIBADO', 'DESCARGADO_CD', 'FINALIZADO']:
            assignment = Assignment.objects.filter(
                container=self.container,
                driver=self.container.conductor_asignado,
                estado__in=['PENDIENTE', 'EN_CURSO']
            ).first()
            
            if assignment:
                if self.new_status == 'FINALIZADO':
                    self._complete_final_assignment(assignment)
                else:
                    self._complete_route_assignment(assignment)
    
    def _complete_route_assignment(self, assignment: Assignment) -> None:
        """Completa asignación para estados intermedios."""
        if assignment.fecha_inicio:
            route_minutes = self.container.duracion_ruta or int(
                (self.now - assignment.fecha_inicio).total_seconds() / 60
            )
            assignment.record_actual_times(
                total_minutes=route_minutes,
                route_minutes=route_minutes,
            )
        else:
            assignment.record_actual_times(
                total_minutes=self.container.duracion_ruta or 0
            )
    
    def _complete_final_assignment(self, assignment: Assignment) -> None:
        """Completa asignación para estado FINALIZADO."""
        unloading_minutes = self.container.duracion_descarga
        route_recorded = self.container.duracion_ruta
        
        if assignment.estado != 'COMPLETADA':
            if assignment.fecha_inicio:
                total_minutes = int(
                    (self.now - assignment.fecha_inicio).total_seconds() / 60
                )
            else:
                total_minutes = (
                    self.container.duracion_total 
                    or self.container.duracion_ruta 
                    or 0
                )
            
            assignment.record_actual_times(
                total_minutes=total_minutes,
                route_minutes=route_recorded,
                unloading_minutes=unloading_minutes,
            )
    
    def _create_movement_record(self) -> None:
        """Crea registro de movimiento."""
        movement_code = MovementCode.generate_code('transfer')
        movement_code.created_by = self.user
        movement_code.save(update_fields=['created_by'])
        
        ContainerMovement.objects.create(
            container=self.container,
            movement_type='TRANSFER',
            movement_code=movement_code,
            from_location=self.container.current_location,
            to_location=self.container.current_location,
            movement_date=self.now,
            notes=f'Estado cambiado de {self.old_status} a {self.new_status}',
            created_by=self.user
        )
    
    def _handle_demurrage_alerts(self) -> None:
        """Maneja alertas de demurrage según el nuevo estado."""
        if self.new_status in {
            'ARRIBADO', 'DESCARGADO_CD', 
            'DISPONIBLE_DEVOLUCION', 'EN_RUTA_DEVOLUCION'
        }:
            create_demurrage_alert_if_needed(
                self.container, 
                resolved_by=self.user
            )
        elif self.new_status == 'FINALIZADO':
            resolve_demurrage_alerts(
                self.container, 
                resolved_by=self.user
            )


def update_container_status(
    container: Container, 
    new_status: str, 
    user: User
) -> Dict[str, Any]:
    """
    Actualiza el estado de un contenedor con toda la lógica de negocio.
    
    Args:
        container: Contenedor a actualizar
        new_status: Nuevo estado
        user: Usuario que realiza la actualización
    
    Returns:
        Dict con resultado de la operación
    
    Raises:
        ValueError: Si el estado no es válido
    """
    # Validar estado
    valid_statuses = [choice[0] for choice in Container.CONTAINER_STATUS]
    if new_status not in valid_statuses:
        raise ValueError(f"Estado no válido: {new_status}")
    
    # Ejecutar actualización
    updater = ContainerStatusUpdater(container, new_status, user)
    return updater.update_status()
