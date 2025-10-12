from django.db import models
from django.utils import timezone
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD


class Programacion(models.Model):
    """Modelo de programación de entregas"""
    
    # Relaciones
    container = models.OneToOneField(
        Container,
        on_delete=models.CASCADE,
        related_name='programacion',
        verbose_name='Contenedor'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programaciones',
        verbose_name='Conductor'
    )
    cd = models.ForeignKey(
        CD,
        on_delete=models.CASCADE,
        related_name='programaciones',
        verbose_name='Centro de Distribución'
    )
    
    # Información de entrega
    fecha_programada = models.DateTimeField(verbose_name='Fecha Programada', db_index=True)
    cliente = models.CharField(max_length=200, verbose_name='Cliente')
    direccion_entrega = models.TextField(blank=True, verbose_name='Dirección Entrega')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    
    # Datos de ruta
    eta_minutos = models.IntegerField(null=True, blank=True, verbose_name='ETA (minutos)')
    distancia_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Distancia (km)'
    )
    ruta_geojson = models.JSONField(null=True, blank=True, verbose_name='Ruta GeoJSON')
    
    # Alertas
    alerta_48h_enviada = models.BooleanField(default=False, verbose_name='Alerta 48h Enviada')
    requiere_alerta = models.BooleanField(default=False, verbose_name='Requiere Alerta')
    
    # Timestamps
    fecha_asignacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Asignación')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        verbose_name = 'Programación'
        verbose_name_plural = 'Programaciones'
        ordering = ['fecha_programada']
        indexes = [
            models.Index(fields=['fecha_programada']),
            models.Index(fields=['alerta_48h_enviada', 'requiere_alerta']),
            models.Index(fields=['driver']),
        ]
    
    def __str__(self):
        return f"{self.container.numero_contenedor if self.container else 'N/A'} - {self.cliente}"
    
    @property
    def estado(self):
        """Retorna el estado basado en el estado del contenedor"""
        if self.container:
            return self.container.estado
        return 'sin_contenedor'
    
    def asignar_conductor(self, driver, usuario=None):
        """Asigna un conductor a la programación"""
        self.driver = driver
        self.fecha_asignacion = timezone.now()
        self.save()
        
        # Actualizar estado del contenedor si existe
        if self.container:
            self.container.estado = 'asignado'
            self.container.save()
        
        # Incrementar contador de entregas del conductor
        driver.num_entregas_dia += 1
        driver.save(update_fields=['num_entregas_dia'])
        
        # TODO: Crear notificación para el conductor
        # Esto se implementaría cuando el modelo Notification esté disponible
    
    @property
    def horas_hasta_programacion(self):
        """Calcula horas hasta la fecha programada"""
        if not self.fecha_programada:
            return None
        delta = self.fecha_programada - timezone.now()
        return delta.total_seconds() / 3600
    
    def requiere_conductor_urgente(self):
        """Verifica si requiere asignación urgente (< 48h)"""
        if self.driver:
            return False
        horas = self.horas_hasta_programacion
        if horas is None:
            return False
        return horas < 48
    requiere_conductor_urgente.boolean = True
    requiere_conductor_urgente.short_description = 'Urgente'


class TiempoOperacion(models.Model):
    """Modelo para tracking de tiempos de operación (carga/descarga)"""
    
    TIPOS_OPERACION = [
        ('carga_ccti', 'Carga en CCTI'),
        ('descarga_cd', 'Descarga en CD'),
        ('retiro_puerto', 'Retiro en Puerto'),
        ('devolucion_vacio', 'Devolución Vacío'),
    ]
    
    # Relaciones
    cd = models.ForeignKey(CD, on_delete=models.CASCADE, related_name='tiempos_operacion')
    conductor = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Datos de operación
    tipo_operacion = models.CharField(max_length=20, choices=TIPOS_OPERACION)
    tiempo_estimado_min = models.IntegerField(
        help_text='Tiempo estimado inicial (ej: CD.tiempo_promedio_descarga_min)'
    )
    tiempo_real_min = models.IntegerField(
        help_text='Tiempo real medido desde hora_inicio hasta hora_fin'
    )
    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField()
    fecha = models.DateField(auto_now_add=True, db_index=True)
    anomalia = models.BooleanField(
        default=False,
        help_text='Marca tiempos anómalos (>3x estimado) para excluir del aprendizaje'
    )
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Tiempo de Operación'
        verbose_name_plural = 'Tiempos de Operación'
        ordering = ['-fecha', '-hora_inicio']
        indexes = [
            models.Index(fields=['cd', 'tipo_operacion', '-fecha']),
            models.Index(fields=['conductor', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_operacion_display()} - {self.cd.nombre} ({self.fecha})"


class TiempoViaje(models.Model):
    """Modelo para tracking de tiempos de viaje"""
    
    # Relaciones
    conductor = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    programacion = models.ForeignKey(Programacion, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Coordenadas
    origen_lat = models.DecimalField(max_digits=10, decimal_places=7)
    origen_lon = models.DecimalField(max_digits=10, decimal_places=7)
    destino_lat = models.DecimalField(max_digits=10, decimal_places=7)
    destino_lon = models.DecimalField(max_digits=10, decimal_places=7)
    origen_nombre = models.CharField(max_length=200, blank=True)
    destino_nombre = models.CharField(max_length=200, blank=True)
    
    # Datos de viaje
    tiempo_mapbox_min = models.IntegerField(
        help_text='Tiempo estimado por Mapbox al iniciar viaje'
    )
    tiempo_real_min = models.IntegerField(
        help_text='Tiempo real medido desde salida hasta llegada'
    )
    hora_salida = models.DateTimeField()
    hora_llegada = models.DateTimeField()
    fecha = models.DateField(auto_now_add=True, db_index=True)
    hora_del_dia = models.IntegerField(
        help_text='Hora de salida (0-23) para análisis de tráfico'
    )
    dia_semana = models.IntegerField(
        help_text='Día de la semana (0=Lunes, 6=Domingo)'
    )
    distancia_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text='Distancia en km según Mapbox'
    )
    anomalia = models.BooleanField(
        default=False,
        help_text='Marca viajes anómalos (pausas largas, desvíos) para excluir'
    )
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Tiempo de Viaje'
        verbose_name_plural = 'Tiempos de Viaje'
        ordering = ['-fecha', '-hora_salida']
        indexes = [
            models.Index(fields=['origen_lat', 'origen_lon', 'destino_lat', 'destino_lon']),
            models.Index(fields=['hora_del_dia', 'dia_semana']),
            models.Index(fields=['conductor', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.origen_nombre} → {self.destino_nombre} ({self.fecha})"