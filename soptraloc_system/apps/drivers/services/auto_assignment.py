"""
Servicio de auto-asignación de conductores.
FASE 3: Refactoring - Extraer lógica de negocio compleja de views.
"""
from typing import List, Dict, Any, Set, Optional
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth.models import User

from apps.containers.models import Container
from apps.drivers.models import Driver


class AutoAssignmentService:
    """Servicio para asignación automática de conductores a contenedores."""
    
    def __init__(self, user: User):
        self.user = user
        self.assigned_count = 0
        self.pending_containers: List[Dict[str, str]] = []
    
    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la asignación automática.
        
        Returns:
            Dict con estadísticas de asignación
        """
        # Obtener contenedores sin asignar
        unassigned = self._get_unassigned_containers()
        
        # Obtener conductores disponibles
        available_drivers = self._get_available_drivers()
        
        # Procesar asignaciones
        self._process_assignments(unassigned, available_drivers)
        
        return self._build_result()
    
    def _get_unassigned_containers(self) -> List[Container]:
        """Obtiene contenedores sin conductor asignado para hoy y mañana."""
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        
        return list(
            Container.objects.select_related(
                'owner_company', 'client', 'current_location'
            ).filter(
                conductor_asignado__isnull=True,
                status__in=['PROGRAMADO', 'EN_PROCESO', 'EN_SECUENCIA', 'SECUENCIADO'],
                scheduled_date__in=[today, tomorrow]
            ).order_by('scheduled_date', 'scheduled_time', 'container_number')
        )
    
    def _get_available_drivers(self) -> List[Driver]:
        """Obtiene conductores disponibles para asignación."""
        today = timezone.localdate()
        
        return list(
            Driver.objects.filter(
                is_active=True,
                estado='OPERATIVO',
                contenedor_asignado__isnull=True,
                ultimo_registro_asistencia=today,
                hora_ingreso_hoy__isnull=False
            ).order_by('tiempo_en_ubicacion')
        )
    
    def _process_assignments(
        self, 
        containers: List[Container], 
        drivers: List[Driver]
    ) -> None:
        """Procesa las asignaciones intentando asignar cada contenedor."""
        from apps.drivers.views import _pick_driver_for_container, _assign_driver_to_container
        
        for container in containers:
            attempted_ids: Set[int] = set()
            assignment_error: Optional[str] = None
            assigned = False
            
            while drivers:
                driver = _pick_driver_for_container(
                    container, 
                    drivers, 
                    attempted_ids
                )
                
                if not driver:
                    break
                
                attempted_ids.add(driver.id)
                
                try:
                    _assign_driver_to_container(
                        container, 
                        driver, 
                        self.user
                    )
                    self.assigned_count += 1
                    assigned = True
                    break
                except ValueError as exc:
                    assignment_error = str(exc)
                    drivers.append(driver)
                    continue
            
            if not assigned:
                self.pending_containers.append({
                    'number': container.container_number,
                    'reason': assignment_error or 'Sin conductores con horario disponible'
                })
    
    def _build_result(self) -> Dict[str, Any]:
        """Construye el resultado con estadísticas."""
        message = f'{self.assigned_count} contenedores asignados automáticamente'
        
        if self.pending_containers:
            detalles = ', '.join(
                f"{item['number']} ({item['reason']})" 
                for item in self.pending_containers[:5]
            )
            message += f". Sin conductor disponible para: {detalles}"
            if len(self.pending_containers) > 5:
                message += '...'
        
        return {
            'success': True,
            'message': message,
            'assigned_count': self.assigned_count,
            'pending_containers': [
                item['number'] for item in self.pending_containers
            ]
        }


def auto_assign_all_drivers(user: User) -> Dict[str, Any]:
    """
    Ejecuta la asignación automática de conductores a contenedores.
    
    Args:
        user: Usuario que ejecuta la asignación
    
    Returns:
        Dict con resultados de la asignación
    """
    service = AutoAssignmentService(user)
    return service.execute()
