from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Driver(models.Model):
    """Modelo de conductor con autenticación y GPS tracking"""
    
    # Relación con usuario de Django (para autenticación)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver',
        verbose_name='Usuario'
    )
    
    # Información básica
    nombre = models.CharField(max_length=200, verbose_name='Nombre', db_index=True)
    rut = models.CharField(max_length=20, null=True, blank=True, unique=True, verbose_name='RUT')
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name='Teléfono')
    patente = models.CharField(max_length=20, null=True, blank=True, verbose_name='Patente', help_text='Patente del vehículo asignado')
    
    # Disponibilidad
    presente = models.BooleanField(default=True, verbose_name='Presente', help_text='¿Está disponible hoy?')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    
    # Métricas de desempeño
    cumplimiento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name='Cumplimiento (%)',
        help_text='Porcentaje de entregas a tiempo'
    )
    
    # Control de entregas
    num_entregas_dia = models.IntegerField(default=0, verbose_name='Entregas del Día')
    max_entregas_dia = models.IntegerField(default=3, verbose_name='Max Entregas/Día')
    
    # Posición GPS
    ultima_posicion_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Latitud'
    )
    ultima_posicion_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Longitud'
    )
    ultima_actualizacion_posicion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Actualización Posición'
    )
    
    # Estadísticas
    total_entregas = models.IntegerField(default=0, verbose_name='Total Entregas')
    entregas_a_tiempo = models.IntegerField(default=0, verbose_name='Entregas a Tiempo')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        verbose_name = 'Conductor'
        verbose_name_plural = 'Conductores'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['presente', 'activo']),
        ]
    
    def __str__(self):
        return self.nombre
    
    @property
    def esta_disponible(self):
        """Verifica si el conductor está disponible para asignaciones"""
        return self.activo and self.presente and self.num_entregas_dia < self.max_entregas_dia
    
    def actualizar_posicion(self, lat, lng, accuracy=None):
        """Actualiza la posición GPS del conductor"""
        self.ultima_posicion_lat = lat
        self.ultima_posicion_lng = lng
        self.ultima_actualizacion_posicion = timezone.now()
        self.save(update_fields=['ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion'])
        
        # Crear registro de historial
        DriverLocation.objects.create(
            driver=self,
            lat=lat,
            lng=lng,
            accuracy=accuracy
        )
    
    def reset_entregas_diarias(self):
        """Resetea el contador de entregas del día"""
        self.num_entregas_dia = 0
        self.save(update_fields=['num_entregas_dia'])


class DriverLocation(models.Model):
    """Historial de ubicaciones GPS de conductores"""
    
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='ubicaciones',
        verbose_name='Conductor'
    )
    lat = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Latitud')
    lng = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Longitud')
    accuracy = models.FloatField(null=True, blank=True, verbose_name='Precisión (metros)')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha/Hora')
    
    class Meta:
        verbose_name = 'Ubicación de Conductor'
        verbose_name_plural = 'Ubicaciones de Conductores'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['driver', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.driver.nombre} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"