from django.db import models
from django.utils import timezone


class Container(models.Model):
    """Modelo principal de contenedores con ciclo de vida completo"""
    
    ESTADOS = [
        # Estados iniciales (pre-arribo)
        ('por_arribar', 'Por Arribar'),
        
        # Estados post-arribo (contenedor lleno en puerto)
        ('arribado', 'Arribado'),  # Nave llegó, contenedor en puerto
        ('liberado', 'Liberado'),  # Liberado por aduana/naviera
        ('secuenciado', 'Secuenciado'),  # Marcado para próxima entrega
        ('programado', 'Programado'),  # Asignado a fecha y CD
        ('asignado', 'Asignado'),  # Asignado a conductor
        
        # Estados en tránsito (lleno)
        ('en_ruta', 'En Ruta'),  # Conductor en camino a CD
        ('entregado', 'Entregado'),  # Llegó a CD cliente
        ('descargado', 'Descargado'),  # Cliente terminó de descargar
        
        # Estados vacío (retorno)
        ('vacio', 'Vacío'),  # Descargado, esperando retiro
        ('vacio_en_ruta', 'Vacío en Ruta'),  # Retornando a depósito
        ('devuelto', 'Devuelto'),  # Devuelto a depósito naviera
    ]
    
    TIPOS = [
        ('20', "20'"),
        ('40', "40'"),
        ('40HC', "40' HC"),
        ('45', "45'"),
    ]
    
    TIPOS_MOVIMIENTO = [
        ('automatico', 'Automático (Puerto)'),
        ('retiro_ccti', 'Retiro a CCTI'),
        ('retiro_directo', 'Retiro Directo a Cliente'),
    ]
    
    # Identificación
    container_id = models.CharField('ID Contenedor', max_length=50, unique=True, db_index=True)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPOS)
    
    # Información del embarque
    nave = models.CharField('Nave', max_length=100)
    fecha_eta = models.DateTimeField('ETA (Estimated Time of Arrival)', null=True, blank=True, help_text='Fecha estimada de arribo')
    peso = models.DecimalField('Peso (kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    vendor = models.CharField('Vendor', max_length=200, null=True, blank=True)
    sello = models.CharField('Sello', max_length=100, null=True, blank=True)
    puerto = models.CharField('Puerto', max_length=100, default='Valparaíso')
    
    # Estado y ubicación
    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='por_arribar', db_index=True)
    posicion_fisica = models.CharField('Posición Física', max_length=100, null=True, blank=True, help_text='TPS, STI, PCE, ZEAL, CLEP, etc.')
    tipo_movimiento = models.CharField('Tipo de Movimiento', max_length=20, choices=TIPOS_MOVIMIENTO, default='automatico')
    
    # Información de entrega
    comuna = models.CharField('Comuna Destino', max_length=100, null=True, blank=True)
    secuenciado = models.BooleanField('Secuenciado', default=False, help_text='Marcado para próxima liberación')
    cd_entrega = models.ForeignKey('cds.CD', on_delete=models.SET_NULL, null=True, blank=True, related_name='contenedores_entregados', verbose_name='CD de Entrega')
    
    # Información de liberación y logística
    deposito_devolucion = models.CharField('Depósito Devolución', max_length=200, null=True, blank=True, help_text='Dónde devolver contenedor vacío')
    fecha_demurrage = models.DateTimeField('Fecha Demurrage', null=True, blank=True, db_index=True, help_text='Fecha de vencimiento de demurrage (después se paga)')
    
    # Timestamps de cada transición de estado (ciclo completo)
    fecha_arribo = models.DateTimeField('Fecha Arribo', null=True, blank=True, help_text='Nave llega a puerto')
    fecha_liberacion = models.DateTimeField('Fecha Liberación', null=True, blank=True, help_text='Liberado por aduana/naviera')
    fecha_programacion = models.DateTimeField('Fecha Programación', null=True, blank=True, help_text='Asignado a fecha y CD')
    fecha_asignacion = models.DateTimeField('Fecha Asignación', null=True, blank=True, help_text='Asignado a conductor')
    fecha_inicio_ruta = models.DateTimeField('Fecha Inicio Ruta', null=True, blank=True, help_text='Conductor sale con contenedor')
    fecha_entrega = models.DateTimeField('Fecha Entrega', null=True, blank=True, help_text='Llega a CD cliente')
    fecha_descarga = models.DateTimeField('Fecha Descarga', null=True, blank=True, help_text='Cliente termina de descargar')
    fecha_vacio = models.DateTimeField('Fecha Vacío', null=True, blank=True, help_text='Contenedor vacío listo para retiro')
    fecha_vacio_ruta = models.DateTimeField('Fecha Vacío en Ruta', null=True, blank=True, help_text='Iniciando retorno a depósito')
    fecha_devolucion = models.DateTimeField('Fecha Devolución', null=True, blank=True, help_text='Devuelto a depósito naviera')
    
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
        timestamp_map = {
            'arribado': 'fecha_arribo',
            'liberado': 'fecha_liberacion',
            'programado': 'fecha_programacion',
            'asignado': 'fecha_asignacion',
            'en_ruta': 'fecha_inicio_ruta',
            'entregado': 'fecha_entrega',
            'descargado': 'fecha_descarga',
            'vacio': 'fecha_vacio',
            'vacio_en_ruta': 'fecha_vacio_ruta',
            'devuelto': 'fecha_devolucion',
        }
        
        if nuevo_estado in timestamp_map:
            setattr(self, timestamp_map[nuevo_estado], now)
        
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
