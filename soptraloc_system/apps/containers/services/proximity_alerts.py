"""
Sistema de reloj en tiempo real y alertas de proximidad de programación.
"""
from datetime import datetime
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ProximityAlertSystem:
    """Sistema de alertas de proximidad para contenedores programados"""
    
    # Tiempo de alerta: 2 horas antes de la hora programada
    ALERT_THRESHOLD_HOURS = 2
    
    @classmethod
    def get_urgent_containers(cls, containers_qs) -> list:
        """
        Obtiene contenedores con programación urgente (< 2 horas)
        
        Args:
            containers_qs: QuerySet de contenedores
            
        Returns:
            Lista de contenedores urgentes ordenados por proximidad
        """
        now = timezone.now()
        urgent_containers = []
        
        for container in containers_qs:
            scheduled_datetime = cls._get_scheduled_datetime(container)
            if not scheduled_datetime:
                continue
            
            # Calcular diferencia de tiempo
            time_diff = scheduled_datetime - now
            hours_remaining = time_diff.total_seconds() / 3600
            
            # Si está dentro del threshold (< 2 horas) y no ha pasado
            if 0 < hours_remaining <= cls.ALERT_THRESHOLD_HOURS:
                container.dashboard_hours_remaining = hours_remaining
                container.dashboard_minutes_remaining = int((hours_remaining * 60) % 60)
                container.dashboard_is_urgent = True
                container.dashboard_urgency_level = cls._calculate_urgency_level(hours_remaining)
                urgent_containers.append(container)
        
        # Ordenar por proximidad (más urgente primero)
        urgent_containers.sort(key=lambda c: c.dashboard_hours_remaining)
        
        return urgent_containers
    
    @classmethod
    def _get_scheduled_datetime(cls, container) -> datetime:
        """Obtiene el datetime programado del contenedor"""
        if not container.scheduled_date:
            return None
        
        scheduled_time = container.scheduled_time or datetime.strptime("08:00", "%H:%M").time()
        naive_datetime = datetime.combine(container.scheduled_date, scheduled_time)
        
        # Convertir a timezone-aware
        return timezone.make_aware(naive_datetime, timezone.get_current_timezone())
    
    @classmethod
    def _calculate_urgency_level(cls, hours_remaining: float) -> str:
        """
        Calcula el nivel de urgencia basado en horas restantes
        
        Returns:
            'critical' (< 30 min), 'high' (< 1h), 'medium' (< 2h)
        """
        if hours_remaining < 0.5:  # < 30 minutos
            return 'critical'
        elif hours_remaining < 1.0:  # < 1 hora
            return 'high'
        else:  # < 2 horas
            return 'medium'
    
    @classmethod
    def get_alert_badge_class(cls, urgency_level: str) -> str:
        """Retorna la clase CSS del badge según nivel de urgencia"""
        return {
            'critical': 'bg-danger',
            'high': 'bg-warning',
            'medium': 'bg-info'
        }.get(urgency_level, 'bg-secondary')
    
    @classmethod
    def get_alert_icon(cls, urgency_level: str) -> str:
        """Retorna el icono según nivel de urgencia"""
        return {
            'critical': 'bi-exclamation-triangle-fill',
            'high': 'bi-exclamation-circle-fill',
            'medium': 'bi-clock-fill'
        }.get(urgency_level, 'bi-clock')
    
    @classmethod
    def annotate_containers_with_urgency(cls, containers_qs):
        """
        Anota los contenedores con información de urgencia
        
        Agrega atributos:
        - dashboard_hours_remaining
        - dashboard_minutes_remaining
        - dashboard_is_urgent
        - dashboard_urgency_level
        """
        now = timezone.now()
        
        for container in containers_qs:
            scheduled_datetime = cls._get_scheduled_datetime(container)
            
            if scheduled_datetime:
                time_diff = scheduled_datetime - now
                hours_remaining = time_diff.total_seconds() / 3600
                
                if 0 < hours_remaining <= cls.ALERT_THRESHOLD_HOURS:
                    container.dashboard_hours_remaining = hours_remaining
                    container.dashboard_minutes_remaining = int((hours_remaining * 60) % 60)
                    container.dashboard_is_urgent = True
                    container.dashboard_urgency_level = cls._calculate_urgency_level(hours_remaining)
                else:
                    container.dashboard_is_urgent = False
                    container.dashboard_hours_remaining = None
                    container.dashboard_minutes_remaining = None
                    container.dashboard_urgency_level = None
            else:
                container.dashboard_is_urgent = False
                container.dashboard_hours_remaining = None
                container.dashboard_minutes_remaining = None
                container.dashboard_urgency_level = None
        
        return containers_qs
