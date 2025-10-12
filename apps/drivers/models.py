from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal


class Driver(models.Model):
    """Modelo de conductores con métricas para asignación automática"""
    
    # Usuario del sistema (para login)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_profile',
        verbose_name='Usuario'
    )
    
    # Información básica
    nombre = models.CharField('Nombre', max_length=200, db_index=True)
    rut = models.CharField('RUT', max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField('Teléfono', max_length=20, null=True, blank=True)
    
    # Estado
    presente = models.BooleanField('Presente', default=True, help_text='¿Está disponible hoy?')
    activo = models.BooleanField('Activo', default=True)
    
    # Métricas de desempeño
    cumplimiento_porcentaje = models.DecimalField(
        'Cumplimiento (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('100.00'),
        help_text='Porcentaje de entregas a tiempo'
    )
    
    # Control de carga diaria
    num_entregas_dia = models.IntegerField('Entregas del Día', default=0)
    max_entregas_dia = models.IntegerField('Max Entregas/Día', default=3)
    
    # Última posición conocida (para cálculo de proximidad)
    ultima_posicion_lat = models.DecimalField(
        'Latitud', 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    ultima_posicion_lng = models.DecimalField(
        'Longitud', 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    ultima_actualizacion_posicion = models.DateTimeField(
        'Última Actualización Posición', 
        null=True, 
        blank=True
    )
    
    # Estadísticas históricas
    total_entregas = models.IntegerField('Total Entregas', default=0)
    entregas_a_tiempo = models.IntegerField('Entregas a Tiempo', default=0)
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Conductor'
        verbose_name_plural = 'Conductores'
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['presente', 'activo']),
        ]
    
    def __str__(self):
        estado = "✓" if self.presente and self.activo else "✗"
        return f"{estado} {self.nombre} ({self.num_entregas_dia}/{self.max_entregas_dia})"
    
    @property
    def ocupacion_porcentaje(self):
        """
        Calcula el porcentaje de ocupación del día
        
        Versión básica: num_entregas / max_entregas
        
        TODO: Versión avanzada calculará ocupación por tiempo:
        - Tiempo = viaje_mapbox + cd.tiempo_promedio_descarga_min + 
                   (espera_carga si cd.requiere_espera_carga) +
                   (viaje_retorno si not cd.permite_soltar_contenedor)
        - Ocupación = tiempo_acumulado / tiempo_jornada_laboral (8h)
        """
        if self.max_entregas_dia == 0:
            return Decimal('100.00')
        return Decimal((self.num_entregas_dia / self.max_entregas_dia) * 100)
    
    @property
    def esta_disponible(self):
        """Verifica si el conductor está disponible para asignación"""
        return (
            self.activo and 
            self.presente and 
            self.num_entregas_dia < self.max_entregas_dia
        )
    
    def actualizar_posicion(self, lat, lng):
        """Actualiza la última posición conocida del conductor"""
        self.ultima_posicion_lat = Decimal(str(lat))
        self.ultima_posicion_lng = Decimal(str(lng))
        self.ultima_actualizacion_posicion = timezone.now()
        self.save(update_fields=[
            'ultima_posicion_lat', 
            'ultima_posicion_lng', 
            'ultima_actualizacion_posicion'
        ])
    
    def resetear_entregas_dia(self):
        """Resetea el contador de entregas del día (ejecutar diariamente)"""
        self.num_entregas_dia = 0
        self.save(update_fields=['num_entregas_dia'])
    
    def registrar_entrega(self, a_tiempo=True):
        """Registra una entrega y actualiza métricas"""
        self.total_entregas += 1
        if a_tiempo:
            self.entregas_a_tiempo += 1
        
        # Recalcular cumplimiento
        if self.total_entregas > 0:
            self.cumplimiento_porcentaje = Decimal(
                (self.entregas_a_tiempo / self.total_entregas) * 100
            )
        
        self.save(update_fields=[
            'total_entregas', 
            'entregas_a_tiempo', 
            'cumplimiento_porcentaje'
        ])


class DriverLocation(models.Model):
    """Historial de ubicaciones del conductor para tracking GPS"""
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='location_history',
        verbose_name='Conductor'
    )
    lat = models.DecimalField('Latitud', max_digits=9, decimal_places=6)
    lng = models.DecimalField('Longitud', max_digits=9, decimal_places=6)
    accuracy = models.FloatField('Precisión (metros)', null=True, blank=True)
    timestamp = models.DateTimeField('Fecha/Hora', auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Ubicación del Conductor'
        verbose_name_plural = 'Ubicaciones de Conductores'
        indexes = [
            models.Index(fields=['driver', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.driver.nombre} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
