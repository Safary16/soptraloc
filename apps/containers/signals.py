"""
Django signals para Container
Maneja automáticamente el inventario de vacíos en CDs
"""
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Container


@receiver(post_save, sender=Container)
def sincronizar_estado_con_programacion(sender, instance, created, **kwargs):
    """
    Signal que mantiene sincronizado el estado del contenedor con su programación.
    
    Casos:
    1. Si el container vuelve a 'programado' desde 'asignado', limpiar el driver de la programación
    2. Si el container vuelve a 'liberado', eliminar la programación (opcional)
    """
    # Solo procesar si no es creación nueva
    if created:
        return
    
    # Evitar loops infinitos
    if hasattr(instance, '_sincronizacion_en_proceso'):
        return
    
    from apps.programaciones.models import Programacion
    
    try:
        programacion = Programacion.objects.get(container=instance)
    except Programacion.DoesNotExist:
        return  # No hay programación, nada que sincronizar
    except Programacion.MultipleObjectsReturned:
        return  # Caso anómalo, no intervenir
    
    # Si el contenedor vuelve a 'programado' pero tiene conductor asignado
    if instance.estado == 'programado' and programacion.driver:
        # Limpiar asignación del conductor
        programacion.driver = None
        programacion.fecha_asignacion = None
        instance._sincronizacion_en_proceso = True
        programacion.save(update_fields=['driver', 'fecha_asignacion'])
        
        # Crear evento de auditoría
        from apps.events.models import Event
        Event.objects.create(
            container=instance,
            event_type='cambio_estado',
            detalles={
                'estado_nuevo': 'programado',
                'accion': 'asignacion_removida',
                'descripcion': 'Asignación de conductor removida al volver a estado programado',
                'automatico': True
            }
        )


@receiver(post_save, sender=Container)
def manejar_vacios_automaticamente(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Container
    
    Lógica:
    1. Si el contenedor cambia a estado 'vacio'
    2. Y tiene un CD de entrega asignado
    3. Y el CD permite soltar contenedor
    4. Entonces incrementar automáticamente el inventario de vacíos del CD
    """
    # Solo procesar si no es creación nueva
    if created:
        return
    
    # Un drop deja carga llena. Solo contabilizar cuando ya está realmente vacío.
    if instance.estado != 'vacio':
        return
    
    # Verificar que tenga CD de entrega
    if not instance.cd_entrega:
        return
    
    # Verificar que el CD permita soltar contenedor (tipo El Peñón)
    if not instance.cd_entrega.permite_soltar_contenedor:
        return
    
    if instance.vacio_contabilizado:
        return
    
    # Intentar recibir el vacío en el CD
    try:
        with transaction.atomic():
            container = Container.objects.select_for_update().get(pk=instance.pk)
            if container.vacio_contabilizado:
                return
            from apps.cds.models import CD
            cd = CD.objects.select_for_update().get(pk=container.cd_entrega_id)
            if not cd.recibir_vacio():
                return
            Container.objects.filter(pk=container.pk).update(vacio_contabilizado=True)
        
        # Crear evento de auditoría
        from apps.events.models import Event
        Event.objects.create(
            container=instance,
            event_type='contenedor_vacio',
            detalles={
                'cd_id': cd.id,
                'cd_nombre': cd.nombre,
                'vacios_actual': cd.vacios_actuales,
                'descripcion': f'Contenedor vacío recibido automáticamente en {cd.nombre}',
                'automatico': True
            }
        )
        
    except Exception as e:
        # CD lleno, registrar en logs
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"No se pudo recibir vacío {instance.container_id} en {instance.cd_entrega.nombre}: {str(e)}"
        )


@receiver(post_save, sender=Container)
def crear_programacion_automatica(sender, instance, created, **kwargs):
    """
    Signal que crea automáticamente una Programacion cuando un contenedor
    cambia a estado 'programado' y no tiene una programación asociada.
    
    Esto resuelve el problema cuando se usa el botón "Programar" manual
    que solo cambia el estado pero no crea la Programacion.
    """
    # Solo procesar si el estado es 'programado'
    if instance.estado != 'programado':
        return
    
    # Evitar loops infinitos
    if hasattr(instance, '_programacion_auto_creada'):
        return
    
    from apps.programaciones.models import Programacion
    from datetime import timedelta
    from django.utils import timezone
    
    # Verificar si ya existe una programación
    try:
        Programacion.objects.get(container=instance)
        return  # Ya existe, no hacer nada
    except Programacion.DoesNotExist:
        pass  # No existe, crear una nueva
    except Programacion.MultipleObjectsReturned:
        return  # Ya hay programaciones, no crear más
    
    # Nunca inventar un destino: una programación sin CD requiere intervención.
    cd = instance.cd_entrega
    if not cd:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"No se creó programación para {instance.container_id}: falta CD de entrega explícito"
        )
        return
    
    # Determinar fecha programada
    fecha_programada = instance.fecha_programacion or timezone.now()
    
    # Si la fecha está en el pasado, programar para el día siguiente
    if fecha_programada < timezone.now():
        fecha_programada = timezone.now() + timedelta(hours=24)
    
    # Crear la programación
    try:
        programacion = Programacion.objects.create(
            container=instance,
            cd=cd,
            fecha_programada=fecha_programada,
            cliente=instance.cliente or 'Cliente sin especificar',
            direccion_entrega=cd.direccion,
            observaciones='Programación creada automáticamente desde operaciones'
        )
        
        # Crear evento de auditoría
        from apps.events.models import Event
        Event.objects.create(
            container=instance,
            event_type='import_programacion',
            detalles={
                'cd_id': cd.id,
                'cd_nombre': cd.nombre,
                'fecha_programada': fecha_programada.isoformat(),
                'descripcion': f'Programación creada automáticamente para {cd.nombre}',
                'automatico': True
            }
        )
        
        # Marcar como procesado
        instance._programacion_auto_creada = True
        
    except Exception as e:
        # Log error pero no fallar
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creando programación automática para {instance.container_id}: {str(e)}")


@receiver(post_save, sender=Container)
def alertar_demurrage_cercano(sender, instance, created, **kwargs):
    """
    Signal que verifica si el demurrage está cerca de vencer
    y actualiza la alerta en la programación relacionada
    """
    # Solo si tiene fecha_demurrage
    if not instance.fecha_demurrage:
        return
    
    from django.utils import timezone
    from datetime import timedelta
    
    ahora = timezone.now()
    dias_hasta_demurrage = (instance.fecha_demurrage - ahora).total_seconds() / 86400
    
    # Si faltan menos de 2 días para demurrage
    if dias_hasta_demurrage < 2 and dias_hasta_demurrage > 0:
        # Buscar programación asociada
        from apps.programaciones.models import Programacion
        
        try:
            programacion = Programacion.objects.get(container=instance)
            
            # Actualizar flag de alerta si no tiene conductor
            if not programacion.driver:
                programacion.requiere_alerta = True
                programacion.save(update_fields=['requiere_alerta'])
                
                # Crear evento de alerta
                from apps.events.models import Event
                Event.objects.create(
                    container=instance,
                    event_type='alerta_48h',
                    detalles={
                        'fecha_demurrage': instance.fecha_demurrage.isoformat(),
                        'dias_restantes': round(dias_hasta_demurrage, 1),
                        'tiene_conductor': False,
                        'descripcion': f'Alerta: Demurrage vence en {round(dias_hasta_demurrage, 1)} días'
                    }
                )
        except Programacion.DoesNotExist:
            pass
        except Programacion.MultipleObjectsReturned:
            pass
