"""
Servicio para gestionar la disponibilidad y ocupación de conductores.
Considera rutas activas y tiempos estimados para saber dónde estará cada conductor.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Q
import logging

from apps.drivers.models import Driver, Assignment
from apps.routing.locations_catalog import get_location, format_route_name

logger = logging.getLogger(__name__)


class DriverAvailabilityService:
    """
    Servicio para calcular disponibilidad de conductores.
    
    Considera:
    - Rutas activas en progreso
    - Tiempo estimado de llegada
    - Ubicación estimada en tiempo X
    - Prevención de asignaciones duplicadas
    """
    
    @staticmethod
    def get_driver_status(driver_id: int, check_time: Optional[datetime] = None) -> Dict:
        """
        Obtiene el estado actual de un conductor.
        
        Args:
            driver_id: ID del conductor
            check_time: Momento a verificar (None = ahora)
        
        Returns:
            Dict con:
            - is_available: bool
            - status: 'available', 'on_route', 'will_be_busy'
            - current_assignment: Assignment o None
            - estimated_location: str con ubicación estimada
            - available_at: datetime cuando estará disponible
            - estimated_arrival: datetime de llegada si está en ruta
        """
        if not check_time:
            check_time = timezone.now()
        
        driver = Driver.objects.get(id=driver_id)
        
        # Buscar asignaciones activas (EN_CURSO)
        active_assignments = Assignment.objects.filter(
            driver=driver,
            estado='EN_CURSO',
            fecha_completada__isnull=True  # No ha completado aún
        ).order_by('-fecha_inicio')
        
        if not active_assignments.exists():
            return {
                'is_available': True,
                'status': 'available',
                'current_assignment': None,
                'estimated_location': 'Base/Disponible',
                'available_at': check_time,
                'estimated_arrival': None,
                'message': f'{driver.nombre} está disponible'
            }
        
        # Conductor tiene ruta activa
        current_assignment = active_assignments.first()
        
        # Calcular ETA: fecha_inicio + tiempo_estimado
        if current_assignment.fecha_inicio and current_assignment.tiempo_estimado:
            eta = current_assignment.fecha_inicio + timedelta(minutes=current_assignment.tiempo_estimado)
        else:
            eta = None
        
        if not eta:
            # No hay ETA calculado, asumir en ruta
            return {
                'is_available': False,
                'status': 'on_route',
                'current_assignment': current_assignment,
                'estimated_location': 'En ruta (sin ETA calculado)',
                'available_at': check_time + timedelta(minutes=30),  # Estimación genérica
                'estimated_arrival': None,
                'message': f'{driver.nombre} está en ruta sin ETA calculado'
            }
        
        # Comparar tiempo de verificación con ETA
        if check_time < eta:
            # Conductor aún estará ocupado en ese momento
            minutes_remaining = int((eta - check_time).total_seconds() / 60)
            
            return {
                'is_available': False,
                'status': 'on_route',
                'current_assignment': current_assignment,
                'estimated_location': f'En ruta (llegará en {minutes_remaining} min)',
                'available_at': eta,
                'estimated_arrival': eta,
                'message': f'{driver.nombre} llegará a destino a las {eta.strftime("%H:%M")}'
            }
        else:
            # Ya debería haber llegado
            return {
                'is_available': True,
                'status': 'available',
                'current_assignment': current_assignment,
                'estimated_location': f'Disponible (llegó a las {eta.strftime("%H:%M")})',
                'available_at': eta,
                'estimated_arrival': eta,
                'message': f'{driver.nombre} debería estar disponible desde las {eta.strftime("%H:%M")}'
            }
    
    @staticmethod
    def get_available_drivers(
        at_time: Optional[datetime] = None,
        for_location: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene lista de conductores disponibles en un momento específico.
        
        Args:
            at_time: Momento a verificar (None = ahora)
            for_location: Código de ubicación para priorizar conductores cercanos (opcional)
        
        Returns:
            Lista de dicts con info de conductores disponibles, ordenados por prioridad
        """
        if not at_time:
            at_time = timezone.now()
        
        all_drivers = Driver.objects.filter(is_active=True)
        available = []
        
        for driver in all_drivers:
            status = DriverAvailabilityService.get_driver_status(driver.id, at_time)
            
            if status['is_available']:
                available.append({
                    'driver': driver,
                    'driver_id': driver.id,
                    'nombre': driver.nombre,
                    'rut': driver.rut,
                    'status': status,
                    'priority': 1  # Se puede calcular prioridad basada en ubicación
                })
        
        # Ordenar por prioridad (se puede mejorar con distancias reales)
        available.sort(key=lambda x: x['priority'])
        
        logger.info(f"📋 {len(available)} conductores disponibles a las {at_time.strftime('%H:%M')}")
        
        return available
    
    @staticmethod
    def can_assign_route(
        driver_id: int,
        start_time: datetime,
        estimated_duration_minutes: int
    ) -> Tuple[bool, str]:
        """
        Verifica si un conductor puede ser asignado a una ruta en un horario específico.
        
        Args:
            driver_id: ID del conductor
            start_time: Hora de inicio de la ruta
            estimated_duration_minutes: Duración estimada de la ruta
        
        Returns:
            Tuple de (puede_asignar: bool, mensaje: str)
        """
        status = DriverAvailabilityService.get_driver_status(driver_id, start_time)
        
        if status['is_available']:
            return True, f"Conductor disponible"
        
        available_at = status['available_at']
        
        if start_time >= available_at:
            return True, f"Conductor estará disponible a las {available_at.strftime('%H:%M')}"
        
        minutes_until_available = int((available_at - start_time).total_seconds() / 60)
        
        return False, f"Conductor no disponible. Estará libre en {minutes_until_available} minutos (a las {available_at.strftime('%H:%M')})"
    
    @staticmethod
    def get_driver_schedule(
        driver_id: int,
        date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Obtiene el horario completo de un conductor para un día.
        
        Args:
            driver_id: ID del conductor
            date: Fecha a consultar (None = hoy)
        
        Returns:
            Lista de asignaciones del día con tiempos calculados
        """
        if not date:
            date = timezone.now()
        
        # Obtener inicio y fin del día
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        driver = Driver.objects.get(id=driver_id)
        
        # Asignaciones del día
        assignments = Assignment.objects.filter(
            driver=driver,
            fecha_asignacion__range=(day_start, day_end)
        ).order_by('fecha_asignacion')
        
        schedule = []
        
        for assignment in assignments:
            # Calcular ETA si tiene fecha_inicio y tiempo_estimado
            estimated_arrival = None
            if assignment.fecha_inicio and assignment.tiempo_estimado:
                estimated_arrival = assignment.fecha_inicio + timedelta(minutes=assignment.tiempo_estimado)
            
            schedule_item = {
                'assignment': assignment,
                'assignment_id': assignment.id,
                'start_time': assignment.fecha_inicio,
                'estimated_arrival': estimated_arrival,
                'actual_arrival': assignment.fecha_completada,
                'duration_minutes': assignment.tiempo_estimado,
                'status': 'completed' if assignment.fecha_completada else (
                    'in_progress' if assignment.fecha_inicio else 'pending'
                )
            }
            schedule.append(schedule_item)
        
        logger.info(f"📅 Horario de {driver.nombre}: {len(schedule)} asignaciones")
        
        return schedule
    
    @staticmethod
    def suggest_next_driver(
        origin_location: str,
        for_time: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Sugiere el mejor conductor para una ruta desde una ubicación específica.
        
        Args:
            origin_location: Código de ubicación de origen
            for_time: Hora estimada de inicio (None = ahora)
        
        Returns:
            Dict con info del conductor sugerido o None si no hay disponibles
        """
        available = DriverAvailabilityService.get_available_drivers(for_time, origin_location)
        
        if not available:
            return None
        
        # Por ahora retornar el primero, se puede mejorar con:
        # - Distancia real del conductor a la ubicación
        # - Historial de rendimiento
        # - Tipo de vehículo
        # - Horas trabajadas
        
        best_driver = available[0]
        
        logger.info(f"💡 Conductor sugerido: {best_driver['nombre']} (ID: {best_driver['driver_id']})")
        
        return best_driver
    
    @staticmethod
    def check_conflicts(
        driver_id: int,
        start_time: datetime,
        estimated_end_time: datetime
    ) -> List[Dict]:
        """
        Verifica si hay conflictos de horario para un conductor.
        
        Args:
            driver_id: ID del conductor
            start_time: Inicio propuesto
            estimated_end_time: Fin estimado
        
        Returns:
            Lista de asignaciones que se traslapan
        """
        driver = Driver.objects.get(id=driver_id)
        
        # Buscar asignaciones que se traslapen (EN_CURSO o PENDIENTE)
        conflicting = Assignment.objects.filter(
            driver=driver,
            estado__in=['EN_CURSO', 'PENDIENTE'],
            fecha_inicio__isnull=False
        )
        
        conflicts = []
        for assignment in conflicting:
            # Calcular fin estimado
            if assignment.fecha_inicio and assignment.tiempo_estimado:
                estimated_end = assignment.fecha_inicio + timedelta(minutes=assignment.tiempo_estimado)
            else:
                continue  # Skip si no tiene datos para calcular overlap
            
            # Verificar traslape
            has_overlap = (
                (assignment.fecha_inicio <= start_time < estimated_end) or
                (assignment.fecha_inicio < estimated_end_time <= estimated_end) or
                (start_time <= assignment.fecha_inicio and estimated_end_time >= estimated_end)
            )
            
            if has_overlap:
                conflicts.append({
                    'assignment': assignment,
                    'assignment_id': assignment.id,
                    'start': assignment.fecha_inicio,
                    'estimated_end': estimated_end,
                    'overlap': True
                })
        
        if conflicts:
            logger.warning(f"⚠️  {len(conflicts)} conflictos de horario encontrados para conductor {driver.nombre}")
        
        return conflicts


# Instancia global del servicio
driver_availability = DriverAvailabilityService()
