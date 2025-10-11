from django.db import models
from django.utils import timezone
from decimal import Decimal


class Driver(models.Model):
    """Modelo de conductores con métricas para asignación automática"""
    
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
        """Calcula el porcentaje de ocupación del día"""
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
