from django.db import models


class Event(models.Model):
    """Registro de eventos del sistema para auditoría y trazabilidad"""
    
    EVENT_TYPES = [
        ('import_embarque', 'Importación Embarque'),
        ('import_liberacion', 'Importación Liberación'),
        ('import_programacion', 'Importación Programación'),
        ('asignacion_driver', 'Asignación de Conductor'),
        ('inicio_ruta', 'Inicio de Ruta'),
        ('arribo_cd', 'Arribo a CD'),
        ('llegada_destino', 'Llegada a Destino'),
        ('contenedor_vacio', 'Contenedor Vacío'),
        ('contenedor_soltado', 'Contenedor Soltado (Drop & Hook)'),
        ('devolucion_vacio', 'Devolución Vacío'),
        ('alerta_48h', 'Alerta 48 Horas'),
        ('cambio_estado', 'Cambio de Estado'),
        ('actualizacion_posicion', 'Actualización de Posición'),
        ('exportacion_stock', 'Exportación de Stock'),
    ]
    
    # Relación con contenedor
    container = models.ForeignKey(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Contenedor'
    )
    
    # Tipo de evento
    event_type = models.CharField('Tipo de Evento', max_length=50, choices=EVENT_TYPES, db_index=True)
    
    # Detalles en JSON
    detalles = models.JSONField('Detalles', default=dict, blank=True)
    
    # Usuario que realizó la acción
    usuario = models.CharField('Usuario', max_length=200, null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField('Fecha', auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['container', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.container.container_id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
