import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from apps.programaciones.models import Programacion
from apps.core.services.assignment import AssignmentService

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Programacion)
def trigger_automatic_assignment(sender, instance: Programacion, created: bool, **kwargs):
    """
    Dispara la asignación automática de conductor cuando se crea una nueva programación
    y esta no tiene ya un conductor asignado.
    """
    if created and not instance.driver:
        logger.info(
            f"Nueva programación ID {instance.id} creada. "
            "Iniciando proceso de asignación automática de conductor."
        )
        try:
            # Usamos on_commit para asegurar que la transacción principal se ha completado
            # y el objeto Programacion está disponible en la base de datos para el servicio.
            transaction.on_commit(lambda: _run_assignment_service(instance.id))
        except Exception as e:
            logger.error(
                f"Error al encolar la tarea de asignación para la programación ID {instance.id}. "
                f"Excepción: {e}",
                exc_info=True
            )

def _run_assignment_service(programacion_id: int):
    """
    Función auxiliar que ejecuta el servicio de asignación.
    Se encapsula para facilitar el logging y el manejo de errores.
    """
    try:
        programacion = Programacion.objects.get(pk=programacion_id)
        logger.info(f"Ejecutando AssignmentService para la programación ID {programacion.id}.")
        
        # Se pasa un usuario 'system' para trazabilidad
        AssignmentService.asignar_mejor_conductor(programacion, usuario='system_auto_assign')

        # Recargamos desde la BD para obtener el estado más reciente
        programacion.refresh_from_db()

        if programacion.driver:
            logger.info(
                f"Asignación automática exitosa para la programación ID {programacion.id}. "
                f"Conductor asignado: {programacion.driver.nombre}. "
                f"Clasificación: {programacion.clasificacion_sistema}."
            )
        elif programacion.clasificacion_sistema in ['REVISION_OPERADOR', 'INTERVENCION']:
            logger.warning(
                f"La asignación para la programación ID {programacion.id} requiere revisión humana. "
                f"Clasificación: {programacion.clasificacion_sistema}. "
                f"Razón: {programacion.anomalias_detectadas or 'Score bajo'}"
            )
        else:
            logger.error(
                f"El servicio de asignación se ejecutó para la programación ID {programacion.id} "
                "pero no se asignó conductor ni se marcó para revisión. "
                "Clasificación final: {programacion.clasificacion_sistema}."
            )

    except Programacion.DoesNotExist:
        logger.error(f"No se pudo encontrar la programación con ID {programacion_id} para la asignación.")
    except Exception as e:
        logger.error(
            f"Falló la ejecución del servicio de asignación para la programación ID {programacion_id}. "
            f"Excepción: {e}",
            exc_info=True
        )
