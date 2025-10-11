from django.db import models
from django.utils import timezone
from datetime import timedelta


class Programacion(models.Model):
    """Programaciones de entrega de contenedores"""
    
    # Relaciones
    container = models.OneToOneField(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='programacion',
        verbose_name='Contenedor'
    )
    driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programaciones',
        verbose_name='Conductor'
    )
    cd = models.ForeignKey(
        'cds.CD',
        on_delete=models.CASCADE,
        related_name='programaciones',
        verbose_name='Centro de Distribución'
    )
    
    # Información de la programación
    fecha_programada = models.DateTimeField('Fecha Programada', db_index=True)
    cliente = models.CharField('Cliente', max_length=200)
    direccion_entrega = models.TextField('Dirección Entrega', blank=True)
    observaciones = models.TextField('Observaciones', blank=True)
    
    # Datos calculados con Mapbox
    eta_minutos = models.IntegerField('ETA (minutos)', null=True, blank=True)
    distancia_km = models.DecimalField('Distancia (km)', max_digits=10, decimal_places=2, null=True, blank=True)
    ruta_geojson = models.JSONField('Ruta GeoJSON', null=True, blank=True)
    
    # Control de alertas
    alerta_48h_enviada = models.BooleanField('Alerta 48h Enviada', default=False)
    requiere_alerta = models.BooleanField('Requiere Alerta', default=False)
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        ordering = ['fecha_programada']
        verbose_name = 'Programación'
        verbose_name_plural = 'Programaciones'
        indexes = [
            models.Index(fields=['fecha_programada']),
            models.Index(fields=['alerta_48h_enviada', 'requiere_alerta']),
            models.Index(fields=['driver']),
        ]
    
    def __str__(self):
        return f"{self.container.container_id} - {self.fecha_programada.strftime('%Y-%m-%d %H:%M')} - {self.cliente}"
    
    @property
    def horas_hasta_programacion(self):
        """Calcula cuántas horas faltan para la fecha programada"""
        if not self.fecha_programada:
            return None
        delta = self.fecha_programada - timezone.now()
        return delta.total_seconds() / 3600
    
    @property
    def requiere_conductor_urgente(self):
        """Verifica si faltan menos de 48h y no tiene conductor"""
        horas = self.horas_hasta_programacion
        return horas is not None and horas <= 48 and not self.driver
    
    def verificar_alerta(self):
        """Verifica si necesita alerta y la marca"""
        if self.requiere_conductor_urgente and not self.alerta_48h_enviada:
            self.requiere_alerta = True
            self.save(update_fields=['requiere_alerta'])
            return True
        return False
    
    def marcar_alerta_enviada(self):
        """Marca la alerta como enviada"""
        self.alerta_48h_enviada = True
        self.requiere_alerta = False
        self.save(update_fields=['alerta_48h_enviada', 'requiere_alerta'])
    
    def asignar_conductor(self, driver, usuario=None):
        """Asigna un conductor a la programación"""
        self.driver = driver
        self.save(update_fields=['driver'])
        
        # Actualizar estado del contenedor
        self.container.cambiar_estado('asignado', usuario)
        
        # Incrementar contador de entregas del conductor
        driver.num_entregas_dia += 1
        driver.save(update_fields=['num_entregas_dia'])
        
        # Registrar evento
        from apps.events.models import Event
        Event.objects.create(
            container=self.container,
            event_type='asignacion_driver',
            detalles={
                'driver_id': driver.id,
                'driver_nombre': driver.nombre,
                'programacion_id': self.id,
            },
            usuario=usuario
        )
