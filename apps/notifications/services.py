"""
Servicio de gestión de notificaciones
Maneja la creación y envío de notificaciones de arribo y ETAs
"""
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from apps.notifications.models import Notification
from apps.core.services.mapbox import MapboxService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio centralizado para gestión de notificaciones
    """
    
    @classmethod
    def crear_notificacion_asignacion(cls, programacion, driver):
        """
        Crea notificación cuando se asigna un conductor a una programación
        
        Args:
            programacion: Programación asignada
            driver: Conductor asignado
        
        Returns:
            Notification: Notificación creada
        """
        container = programacion.container
        
        notification = Notification.objects.create(
            container=container,
            driver=driver,
            programacion=programacion,
            tipo='asignacion',
            prioridad='media',
            titulo=f"Nueva asignación - {container.container_id if container else 'N/A'}",
            mensaje=f"Se te ha asignado el contenedor {container.container_id if container else 'N/A'} "
                   f"para el cliente {programacion.cliente}. "
                   f"Fecha programada: {programacion.fecha_programada.strftime('%d/%m/%Y %H:%M') if programacion.fecha_programada else 'Por confirmar'}.",
            detalles={
                'cliente': programacion.cliente,
                'fecha_programada': programacion.fecha_programada.isoformat() if programacion.fecha_programada else None,
                'fecha_asignacion': timezone.now().isoformat(),
            }
        )
        
        logger.info(f"Notificación de asignación creada para conductor {driver.nombre}: {notification.id}")
        return notification
    
    @classmethod
    def crear_notificacion_inicio_ruta(cls, programacion, driver, eta_minutos=None, distancia_km=None):
        """
        Crea notificación cuando un conductor inicia la ruta
        
        Args:
            programacion: Programación activa
            driver: Conductor asignado
            eta_minutos: ETA calculado (opcional, se calcula si no se proporciona)
            distancia_km: Distancia calculada (opcional)
        
        Returns:
            Notification: Notificación creada
        """
        container = programacion.container
        cd = programacion.cd
        
        # Calcular ETA si no se proporcionó
        if eta_minutos is None and driver.ultima_posicion_lat and driver.ultima_posicion_lng:
            resultado = MapboxService.calcular_ruta(
                float(driver.ultima_posicion_lng),
                float(driver.ultima_posicion_lat),
                float(cd.lng),
                float(cd.lat)
            )
            if resultado.get('success'):
                eta_minutos = int(resultado['duration_minutes'])
                distancia_km = Decimal(str(resultado['distance_km']))
        
        # Calcular timestamp de ETA
        eta_timestamp = None
        if eta_minutos:
            eta_timestamp = timezone.now() + timedelta(minutes=eta_minutos)
        
        # Determinar prioridad basada en ETA
        prioridad = 'media'
        if eta_minutos and eta_minutos < 30:
            prioridad = 'alta'
        elif eta_minutos and eta_minutos < 15:
            prioridad = 'critica'
        
        # Crear notificación
        notification = Notification.objects.create(
            container=container,
            driver=driver,
            programacion=programacion,
            tipo='ruta_iniciada',
            prioridad=prioridad,
            titulo=f"Ruta iniciada - {container.container_id}",
            mensaje=f"Conductor {driver.nombre} ha iniciado ruta hacia {cd.nombre}. "
                   f"ETA: {eta_minutos} minutos" if eta_minutos else f"Conductor {driver.nombre} ha iniciado ruta hacia {cd.nombre}.",
            eta_minutos=eta_minutos,
            eta_timestamp=eta_timestamp,
            distancia_km=distancia_km,
            lat_actual=driver.ultima_posicion_lat,
            lng_actual=driver.ultima_posicion_lng,
            detalles={
                'cd_nombre': cd.nombre,
                'cd_direccion': cd.direccion,
                'fecha_programada': programacion.fecha_programada.isoformat(),
                'cliente': programacion.cliente,
            }
        )
        
        logger.info(f"Notificación de inicio de ruta creada: {notification.id}")
        return notification
    
    @classmethod
    def actualizar_eta(cls, programacion, driver, nueva_posicion_lat, nueva_posicion_lng):
        """
        Actualiza el ETA basado en la posición actual del conductor
        
        Args:
            programacion: Programación activa
            driver: Conductor
            nueva_posicion_lat: Nueva latitud
            nueva_posicion_lng: Nueva longitud
        
        Returns:
            dict: {
                'eta_minutos': int,
                'distancia_km': Decimal,
                'notificacion': Notification (si se creó)
            }
        """
        cd = programacion.cd
        
        # Calcular nuevo ETA con Mapbox
        resultado = MapboxService.calcular_ruta(
            float(nueva_posicion_lng),
            float(nueva_posicion_lat),
            float(cd.lng),
            float(cd.lat)
        )
        
        if not resultado.get('success'):
            logger.warning(f"Error calculando ETA actualizado: {resultado.get('error')}")
            return None
        
        eta_minutos = int(resultado['duration_minutes'])
        distancia_km = Decimal(str(resultado['distance_km']))
        eta_timestamp = timezone.now() + timedelta(minutes=eta_minutos)
        
        # Actualizar ETA en la programación
        programacion.eta_minutos = eta_minutos
        programacion.distancia_km = distancia_km
        programacion.save(update_fields=['eta_minutos', 'distancia_km'])
        
        # Buscar notificación activa de esta programación
        notificacion_activa = Notification.objects.filter(
            programacion=programacion,
            tipo__in=['ruta_iniciada', 'eta_actualizado'],
            estado__in=['pendiente', 'enviada']
        ).first()
        
        # Crear nueva notificación solo si el ETA cambió significativamente (>10 min)
        crear_nueva = False
        if notificacion_activa:
            if notificacion_activa.eta_minutos:
                diferencia = abs(eta_minutos - notificacion_activa.eta_minutos)
                if diferencia > 10:
                    crear_nueva = True
                    # Archivar la anterior
                    notificacion_activa.archivar()
        else:
            crear_nueva = True
        
        notificacion = None
        if crear_nueva:
            prioridad = 'media'
            if eta_minutos < 30:
                prioridad = 'alta'
            elif eta_minutos < 15:
                prioridad = 'critica'
            
            notificacion = Notification.objects.create(
                container=programacion.container,
                driver=driver,
                programacion=programacion,
                tipo='eta_actualizado',
                prioridad=prioridad,
                titulo=f"ETA Actualizado - {programacion.container.container_id}",
                mensaje=f"Nuevo ETA: {eta_minutos} minutos. Distancia restante: {distancia_km} km.",
                eta_minutos=eta_minutos,
                eta_timestamp=eta_timestamp,
                distancia_km=distancia_km,
                lat_actual=Decimal(str(nueva_posicion_lat)),
                lng_actual=Decimal(str(nueva_posicion_lng)),
                detalles={
                    'cd_nombre': cd.nombre,
                    'posicion_actualizada': True
                }
            )
            
            logger.info(f"Notificación de ETA actualizado creada: {notificacion.id}")
        
        return {
            'eta_minutos': eta_minutos,
            'distancia_km': distancia_km,
            'eta_timestamp': eta_timestamp,
            'notificacion': notificacion
        }
    
    @classmethod
    def crear_alerta_arribo_proximo(cls, programacion, minutos_anticipacion=15):
        """
        Crea alerta cuando el conductor está próximo a llegar
        
        Args:
            programacion: Programación activa
            minutos_anticipacion: Minutos antes de la llegada estimada
        
        Returns:
            Notification: Notificación creada o None
        """
        # Verificar si ya existe alerta similar reciente
        existe_alerta = Notification.objects.filter(
            programacion=programacion,
            tipo='arribo_proximo',
            estado__in=['pendiente', 'enviada'],
            created_at__gte=timezone.now() - timedelta(minutes=30)
        ).exists()
        
        if existe_alerta:
            return None
        
        # Verificar ETA
        if not programacion.eta_minutos or programacion.eta_minutos > minutos_anticipacion:
            return None
        
        notification = Notification.objects.create(
            container=programacion.container,
            driver=programacion.driver,
            programacion=programacion,
            tipo='arribo_proximo',
            prioridad='alta',
            titulo=f"Arribo Próximo - {programacion.container.container_id}",
            mensaje=f"Conductor {programacion.driver.nombre} llegará en {programacion.eta_minutos} minutos a {programacion.cd.nombre}.",
            eta_minutos=programacion.eta_minutos,
            eta_timestamp=timezone.now() + timedelta(minutes=programacion.eta_minutos),
            distancia_km=programacion.distancia_km,
            detalles={
                'cd_nombre': programacion.cd.nombre,
                'cd_direccion': programacion.cd.direccion,
            }
        )
        
        logger.info(f"Alerta de arribo próximo creada: {notification.id}")
        return notification
    
    @classmethod
    def crear_notificacion_llegada(cls, programacion):
        """
        Crea notificación cuando el conductor llega al destino
        
        Args:
            programacion: Programación completada
        
        Returns:
            Notification: Notificación creada
        """
        notification = Notification.objects.create(
            container=programacion.container,
            driver=programacion.driver,
            programacion=programacion,
            tipo='llegada',
            prioridad='media',
            titulo=f"Llegada Confirmada - {programacion.container.container_id}",
            mensaje=f"Conductor {programacion.driver.nombre} ha llegado a {programacion.cd.nombre}.",
            detalles={
                'cd_nombre': programacion.cd.nombre,
                'hora_llegada': timezone.now().isoformat(),
                'fecha_programada': programacion.fecha_programada.isoformat(),
            }
        )
        
        # Archivar notificaciones anteriores de esta programación
        Notification.objects.filter(
            programacion=programacion,
            tipo__in=['ruta_iniciada', 'eta_actualizado', 'arribo_proximo'],
            estado__in=['pendiente', 'enviada']
        ).update(estado='archivada')
        
        logger.info(f"Notificación de llegada creada: {notification.id}")
        return notification
    
    @classmethod
    def obtener_notificaciones_activas(cls, limit=20):
        """
        Obtiene notificaciones activas para el dashboard
        
        Returns:
            QuerySet: Notificaciones ordenadas por prioridad y fecha
        """
        return Notification.objects.filter(
            estado__in=['pendiente', 'enviada']
        ).select_related('container', 'driver', 'programacion').order_by(
            '-prioridad', '-created_at'
        )[:limit]
    
    @classmethod
    def limpiar_notificaciones_antiguas(cls, dias=7):
        """
        Archiva notificaciones antiguas
        
        Args:
            dias: Días de antigüedad para archivar
        """
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        actualizadas = Notification.objects.filter(
            created_at__lt=fecha_limite,
            estado__in=['enviada', 'leida']
        ).update(estado='archivada')
        
        logger.info(f"Archivadas {actualizadas} notificaciones antiguas")
        return actualizadas
