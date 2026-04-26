import logging
from django.conf import settings

from apps.drivers.models import Driver
from apps.programaciones.models import Programacion

logger = logging.getLogger(__name__)

class FleetStatusService:
    """
    Servicio para analizar el estado y la capacidad operativa de la flota de conductores.
    """

    @classmethod
    def get_fleet_utilization_rate(cls) -> float:
        """
        Calcula la tasa de utilización de la flota.

        Returns:
            float: Un valor entre 0.0 y 1.0 que representa el porcentaje de la flota
                   disponible que está actualmente ocupada en servicios activos.
                   Retorna 0.0 si no hay conductores disponibles para evitar divisiones por cero.
        """
        try:
            # Conductores disponibles para operar
            available_drivers = Driver.objects.filter(activo=True, presente=True).count()

            if available_drivers == 0:
                logger.warning("No hay conductores disponibles en la flota.")
                return 1.0  # Se considera la flota 100% utilizada si no hay nadie disponible

            # Programaciones que ocupan activamente a un conductor
            active_assignments = Programacion.objects.filter(
                container__estado__in=['asignado', 'en_ruta']
            ).distinct('driver').count()
            
            utilization_rate = active_assignments / available_drivers
            
            return round(utilization_rate, 3)

        except Exception as e:
            logger.error(f"Error al calcular la tasa de utilización de la flota: {e}", exc_info=True)
            return 0.0 # Retornar un valor neutral en caso de error

    @classmethod
    def is_fleet_at_limit(cls) -> bool:
        """
        Determina si la flota está operando cerca de su capacidad máxima.

        El umbral se define en la configuración de Django 'FLEET_CAPACITY_LIMIT_THRESHOLD'.

        Returns:
            bool: True si la tasa de utilización supera el umbral, False en caso contrario.
        """
        threshold = float(getattr(settings, 'FLEET_CAPACITY_LIMIT_THRESHOLD', 0.9))
        utilization_rate = cls.get_fleet_utilization_rate()
        
        is_at_limit = utilization_rate >= threshold
        
        if is_at_limit:
            logger.info(f"La flota está al límite de su capacidad. Tasa de utilización: {utilization_rate:.2%}, Umbral: {threshold:.2%}")
            
        return is_at_limit
