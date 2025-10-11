from django.db import models
from django.utils import timezone


class Container(models.Model):
    """Modelo principal de contenedores con 11 estados posibles"""
    
    ESTADOS = [
        ('por_arribar', 'Por Arribar'),
        ('liberado', 'Liberado'),
        ('secuenciado', 'Secuenciado'),
        ('programado', 'Programado'),
        ('asignado', 'Asignado'),
        ('en_ruta', 'En Ruta'),
        ('entregado', 'Entregado'),
        ('descargado', 'Descargado'),
        ('en_almacen_ccti', 'En Almacén CCTI'),
        ('vacio_en_ruta', 'Vacío en Ruta'),
        ('vacio_en_ccti', 'Vacío en CCTI'),
    ]
    
    TIPOS = [
        ('20', "20'"),
        ('40', "40'"),
        ('40HC', "40' HC"),
        ('45', "45'"),
    ]
    
    # Identificación
    container_id = models.CharField('ID Contenedor', max_length=50, unique=True, db_index=True)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPOS)
    
    # Información del embarque
    nave = models.CharField('Nave', max_length=100)
    peso = models.DecimalField('Peso (kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    vendor = models.CharField('Vendor', max_length=200, null=True, blank=True)
    sello = models.CharField('Sello', max_length=100, null=True, blank=True)
    puerto = models.CharField('Puerto', max_length=100, default='Valparaíso')
    
    # Estado y ubicación
    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='por_arribar', db_index=True)
    posicion_fisica = models.CharField('Posición Física', max_length=100, null=True, blank=True, help_text='TPS, STI, PCE, ZEAL, CLEP, etc.')
    
    # Información de entrega
    comuna = models.CharField('Comuna Destino', max_length=100, null=True, blank=True)
    secuenciado = models.BooleanField('Secuenciado', default=False, help_text='Marcado para próxima liberación')
    
    # Timestamps de cada transición de estado
    fecha_arribo = models.DateTimeField('Fecha Arribo', null=True, blank=True)
    fecha_liberacion = models.DateTimeField('Fecha Liberación', null=True, blank=True)
    fecha_programacion = models.DateTimeField('Fecha Programación', null=True, blank=True)
    fecha_asignacion = models.DateTimeField('Fecha Asignación', null=True, blank=True)
    fecha_inicio_ruta = models.DateTimeField('Fecha Inicio Ruta', null=True, blank=True)
    fecha_entrega = models.DateTimeField('Fecha Entrega', null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contenedor'
        verbose_name_plural = 'Contenedores'
        indexes = [
            models.Index(fields=['container_id']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_programacion']),
            models.Index(fields=['secuenciado']),
        ]
    
    def __str__(self):
        return f"{self.container_id} - {self.get_estado_display()}"
    
    def cambiar_estado(self, nuevo_estado, usuario=None):
        """Cambia el estado y registra el timestamp correspondiente"""
        estado_anterior = self.estado
        self.estado = nuevo_estado
        
        # Actualizar timestamp según el nuevo estado
        now = timezone.now()
        if nuevo_estado == 'liberado':
            self.fecha_liberacion = now
        elif nuevo_estado == 'programado':
            self.fecha_programacion = now
        elif nuevo_estado == 'asignado':
            self.fecha_asignacion = now
        elif nuevo_estado == 'en_ruta':
            self.fecha_inicio_ruta = now
        elif nuevo_estado in ['entregado', 'descargado']:
            self.fecha_entrega = now
        
        self.save()
        
        # Registrar evento
        from apps.events.models import Event
        Event.objects.create(
            container=self,
            event_type='cambio_estado',
            detalles={
                'estado_anterior': estado_anterior,
                'estado_nuevo': nuevo_estado,
            },
            usuario=usuario
        )
        
        return self
