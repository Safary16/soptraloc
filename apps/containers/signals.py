"""
Django signals para Container
Maneja automáticamente el inventario de vacíos en CDs
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Container


@receiver(post_save, sender=Container)
def manejar_vacios_automaticamente(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Container
    
    Lógica:
    1. Si el contenedor cambia a estado 'descargado'
    2. Y tiene un CD de entrega asignado
    3. Y el CD permite soltar contenedor
    4. Entonces incrementar automáticamente el inventario de vacíos del CD
    """
    # Solo procesar si no es creación nueva
    if created:
        return
    
    # Solo procesar si el estado es 'descargado'
    if instance.estado != 'descargado':
        return
    
    # Verificar que tenga CD de entrega
    if not instance.cd_entrega:
        return
    
    # Verificar que el CD permita soltar contenedor (tipo El Peñón)
    if not instance.cd_entrega.permite_soltar_contenedor:
        return
    
    # Verificar que no hayamos procesado esto antes
    # (para evitar incrementar múltiples veces)
    if hasattr(instance, '_vacio_ya_procesado'):
        return
    
    # Intentar recibir el vacío en el CD
    try:
        instance.cd_entrega.recibir_vacio(instance)
        
        # Crear evento de auditoría
        from apps.events.models import Event
        Event.objects.create(
            container=instance,
            tipo_evento='container_vacio_recibido',
            descripcion=f'Contenedor vacío recibido automáticamente en {instance.cd_entrega.nombre}',
            detalles={
                'cd_id': instance.cd_entrega.id,
                'cd_nombre': instance.cd_entrega.nombre,
                'vacios_actual': instance.cd_entrega.vacios_actual,
                'automatico': True
            }
        )
        
        # Marcar como procesado para evitar loops
        instance._vacio_ya_procesado = True
        
    except ValueError as e:
        # CD lleno, registrar en logs
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"No se pudo recibir vacío {instance.container_id} en {instance.cd_entrega.nombre}: {str(e)}"
        )


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
                    tipo_evento='alerta_demurrage',
                    descripcion=f'Alerta: Demurrage vence en {round(dias_hasta_demurrage, 1)} días',
                    detalles={
                        'fecha_demurrage': instance.fecha_demurrage.isoformat(),
                        'dias_restantes': round(dias_hasta_demurrage, 1),
                        'tiene_conductor': False
                    }
                )
        except Programacion.DoesNotExist:
            pass
        except Programacion.MultipleObjectsReturned:
            pass
