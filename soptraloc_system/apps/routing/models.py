"""
Modelos para gestión de tiempos y rutas
Sistema híbrido: Tiempos manuales + Machine Learning predictivo
"""
from typing import TYPE_CHECKING
from datetime import timedelta

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.core.models import BaseModel, Vehicle

if TYPE_CHECKING:
    from apps.drivers.models import Location, Driver
    from apps.containers.models import Container


class LocationPair(BaseModel):
    """
    Par de ubicaciones con tiempos de trayecto configurables.
    Permite definir manualmente tiempos entre puntos.
    """
    origin = models.ForeignKey(
        'drivers.Location', 
        on_delete=models.CASCADE,
        related_name='routes_from',
        verbose_name="Origen"
    )
    destination = models.ForeignKey(
        'drivers.Location',
        on_delete=models.CASCADE,
        related_name='routes_to',
        verbose_name="Destino"
    )
    
    # Tiempos base (configurables manualmente)
    base_travel_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Tiempo base de viaje en minutos (sin tráfico)"
    )
    
    # Ajustes por horarios
    peak_hour_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(3.0)],
        help_text="Multiplicador para horas pico (ej: 1.5 = +50%)"
    )
    
    # Configuración de horas pico
    peak_hours_start = models.TimeField(
        default="08:00",
        help_text="Inicio hora pico (ej: 08:00)"
    )
    peak_hours_end = models.TimeField(
        default="10:00",
        help_text="Fin hora pico (ej: 10:00)"
    )
    
    # Segunda ventana de hora pico (tarde)
    peak_hours_2_start = models.TimeField(
        default="18:00",
        help_text="Inicio segunda hora pico"
    )
    peak_hours_2_end = models.TimeField(
        default="20:00",
        help_text="Fin segunda hora pico"
    )
    
    # Distancia (opcional, para cálculos)
    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distancia en kilómetros"
    )
    
    # Tipo de ruta
    ROUTE_TYPES = [
        ('URBAN', 'Urbano'),
        ('HIGHWAY', 'Carretera'),
        ('MIXED', 'Mixto'),
        ('PORT_ACCESS', 'Acceso Portuario'),
    ]
    route_type = models.CharField(
        max_length=20,
        choices=ROUTE_TYPES,
        default='MIXED'
    )
    
    # ML: Tiempo predicho (actualizado por el modelo)
    ml_predicted_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo predicho por ML en minutos"
    )
    ml_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Confianza del modelo ML (0-100)"
    )
    ml_last_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última actualización del modelo ML"
    )
    
    # Estadísticas
    total_trips = models.IntegerField(
        default=0,
        help_text="Total de viajes registrados"
    )
    avg_actual_time = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Promedio de tiempo real registrado"
    )
    
    # Notas
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Par de Ubicaciones"
        verbose_name_plural = "Pares de Ubicaciones"
        unique_together = ['origin', 'destination']
        ordering = ['origin__name', 'destination__name']
        indexes = [
            models.Index(fields=['origin', 'destination']),
        ]
    
    def __str__(self):
        return f"{self.origin.name} → {self.destination.name} ({self.base_travel_time} min)"
    
    def get_estimated_time(self, departure_time=None):
        """
        Calcula tiempo estimado considerando hora pico y ML.
        
        Args:
            departure_time: datetime objeto o None (usa ahora)
        
        Returns:
            int: Tiempo estimado en minutos
        """
        if departure_time is None:
            departure_time = timezone.now()
        
        # Si tenemos predicción ML reciente (< 7 días), usarla
        if self.ml_predicted_time and self.ml_last_update:
            days_old = (timezone.now() - self.ml_last_update).days
            if days_old < 7 and self.ml_confidence and self.ml_confidence > 70:
                return self.ml_predicted_time
        
        # Usar tiempo base con ajuste de hora pico
        base_time = self.base_travel_time
        
        # Verificar si es hora pico
        current_time = departure_time.time()
        is_peak = (
            (self.peak_hours_start <= current_time <= self.peak_hours_end) or
            (self.peak_hours_2_start <= current_time <= self.peak_hours_2_end)
        )
        
        if is_peak:
            return int(base_time * float(self.peak_hours_multiplier))
        
        return base_time


class OperationTime(BaseModel):
    """
    Tiempos de operaciones específicas en ubicaciones.
    Ej: Tiempo para bajar contenedor a piso, enganchar chasis, etc.
    """
    location = models.ForeignKey(
        'drivers.Location',
        on_delete=models.CASCADE,
        related_name='operation_times',
        verbose_name="Ubicación"
    )
    
    OPERATION_TYPES = [
        # Operaciones con chasis
        ('CHASSIS_HOOK', 'Enganchar Chasis'),
        ('CHASSIS_UNHOOK', 'Desenganchar Chasis'),
        
        # Operaciones con contenedor
        ('CONTAINER_LOAD', 'Cargar Contenedor'),
        ('CONTAINER_UNLOAD', 'Descargar Contenedor'),
        ('CONTAINER_TO_FLOOR', 'Bajar a Piso'),
        ('CONTAINER_FROM_FLOOR', 'Levantar de Piso'),
        
        # Operaciones portuarias
        ('PORT_GATE_IN', 'Ingreso a Puerto'),
        ('PORT_GATE_OUT', 'Salida de Puerto'),
        ('PORT_PICKUP', 'Retiro en Puerto'),
        ('PORT_DELIVERY', 'Entrega en Puerto'),
        
        # Operaciones en almacén
        ('WAREHOUSE_CHECKIN', 'Check-in Almacén'),
        ('WAREHOUSE_CHECKOUT', 'Check-out Almacén'),
        ('WAREHOUSE_STORAGE', 'Almacenaje'),
        
        # Operaciones cliente
        ('CLIENT_DELIVERY', 'Entrega Cliente'),
        ('CLIENT_PICKUP', 'Retiro Cliente'),
        
        # Documentación
        ('PAPERWORK', 'Trámites/Documentos'),
        ('INSPECTION', 'Inspección'),
        
        # Otros
        ('WAITING', 'Espera'),
        ('FUELING', 'Carga Combustible'),
    ]
    
    operation_type = models.CharField(
        max_length=30,
        choices=OPERATION_TYPES,
        verbose_name="Tipo de Operación"
    )
    
    # Tiempos
    min_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Tiempo mínimo en minutos"
    )
    avg_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Tiempo promedio en minutos"
    )
    max_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Tiempo máximo en minutos"
    )
    
    # Variables que afectan el tiempo
    depends_on_container_size = models.BooleanField(
        default=False,
        help_text="¿El tiempo varía según tamaño del contenedor?"
    )
    depends_on_cargo_type = models.BooleanField(
        default=False,
        help_text="¿El tiempo varía según tipo de carga?"
    )
    depends_on_time_of_day = models.BooleanField(
        default=False,
        help_text="¿El tiempo varía según hora del día?"
    )
    
    # ML
    ml_predicted_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo predicho por ML"
    )
    ml_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    ml_last_update = models.DateTimeField(null=True, blank=True)
    
    # Estadísticas
    total_operations = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Tiempo de Operación"
        verbose_name_plural = "Tiempos de Operaciones"
        unique_together = ['location', 'operation_type']
        ordering = ['location__name', 'operation_type']
    
    def __str__(self):
        return f"{self.location.name} - {self.get_operation_type_display()} ({self.avg_time} min)"
    
    def get_estimated_time(self, container=None, current_time=None):
        """
        Retorna tiempo estimado considerando variables.
        """
        # Si tenemos ML reciente, usarlo
        if self.ml_predicted_time and self.ml_confidence and self.ml_confidence > 70:
            return self.ml_predicted_time
        
        # Por ahora retornar promedio
        # TODO: Ajustar según container.size, cargo_type, etc.
        return self.avg_time


class ActualTripRecord(BaseModel):
    """
    Registro de viajes reales para entrenar el modelo ML.
    Cada vez que un contenedor completa un trayecto, se guarda aquí.
    """
    container = models.ForeignKey(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='trip_records',
        verbose_name="Contenedor"
    )
    driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Conductor"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Vehículo"
    )
    
    # Ubicaciones
    origin = models.ForeignKey(
        'drivers.Location',
        on_delete=models.CASCADE,
        related_name='trips_from',
        verbose_name="Origen"
    )
    destination = models.ForeignKey(
        'drivers.Location',
        on_delete=models.CASCADE,
        related_name='trips_to',
        verbose_name="Destino"
    )
    
    # Tiempos
    departure_time = models.DateTimeField(verbose_name="Hora de salida")
    arrival_time = models.DateTimeField(verbose_name="Hora de llegada")
    duration_minutes = models.IntegerField(
        verbose_name="Duración en minutos",
        help_text="Calculado automáticamente"
    )
    
    # Variables contextuales (para ML)
    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="0=Lunes, 6=Domingo"
    )
    hour_of_day = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)]
    )
    was_peak_hour = models.BooleanField(default=False)
    
    # Características del contenedor
    container_size = models.CharField(max_length=10, blank=True)
    container_type = models.CharField(max_length=50, blank=True)
    cargo_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Características del conductor
    driver_experience_days = models.IntegerField(null=True, blank=True)
    
    # Condiciones
    WEATHER_CONDITIONS = [
        ('CLEAR', 'Despejado'),
        ('RAIN', 'Lluvia'),
        ('FOG', 'Neblina'),
        ('UNKNOWN', 'Desconocido'),
    ]
    weather = models.CharField(
        max_length=20,
        choices=WEATHER_CONDITIONS,
        default='UNKNOWN'
    )
    
    # Incidentes
    had_delay = models.BooleanField(
        default=False,
        help_text="¿Hubo retraso significativo?"
    )
    delay_reason = models.TextField(blank=True)
    
    # Notas adicionales
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Registro de Viaje Real"
        verbose_name_plural = "Registros de Viajes Reales"
        ordering = ['-departure_time']
        indexes = [
            models.Index(fields=['origin', 'destination', 'departure_time']),
            models.Index(fields=['day_of_week', 'hour_of_day']),
        ]
    
    def __str__(self):
        return f"{self.origin.name} → {self.destination.name} ({self.duration_minutes} min) - {self.departure_time.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Calcula campos automáticos antes de guardar."""
        # Calcular duración
        if self.arrival_time and self.departure_time:
            delta = self.arrival_time - self.departure_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        
        # Extraer información temporal
        if self.departure_time:
            self.day_of_week = self.departure_time.weekday()
            self.hour_of_day = self.departure_time.hour
        
        # Copiar información del contenedor
        if self.container:
            self.container_size = self.container.size or ''
            self.container_type = self.container.container_type or ''
            self.cargo_weight = self.container.cargo_weight
        
        super().save(*args, **kwargs)


class ActualOperationRecord(BaseModel):
    """
    Registro de operaciones reales para entrenar ML.
    Ej: Cuánto tardó realmente en bajar el contenedor a piso.
    """
    container = models.ForeignKey(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='operation_records'
    )
    location = models.ForeignKey(
        'drivers.Location',
        on_delete=models.CASCADE,
        related_name='operation_records'
    )
    
    operation_type = models.CharField(
        max_length=30,
        choices=OperationTime.OPERATION_TYPES
    )
    
    # Tiempos
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    
    # Contexto
    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    hour_of_day = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)]
    )
    
    # Variables
    container_size = models.CharField(max_length=10, blank=True)
    had_issues = models.BooleanField(default=False)
    issue_description = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Registro de Operación Real"
        verbose_name_plural = "Registros de Operaciones Reales"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.location.name} - {self.operation_type} ({self.duration_minutes} min)"
    
    def save(self, *args, **kwargs):
        """Calcula campos automáticos."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        
        if self.start_time:
            self.day_of_week = self.start_time.weekday()
            self.hour_of_day = self.start_time.hour
        
        if self.container:
            self.container_size = self.container.size or ''
        
        super().save(*args, **kwargs)


class Route(BaseModel):
    """
    Ruta completa con múltiples paradas.
    Una ruta agrupa varios contenedores para un conductor en un día.
    """
    name = models.CharField(
        max_length=200,
        help_text="Nombre descriptivo de la ruta"
    )
    driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name="Conductor"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Vehículo"
    )
    
    route_date = models.DateField(
        verbose_name="Fecha de la ruta"
    )
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('PLANNED', 'Planificada'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Tiempos estimados vs reales
    estimated_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Inicio estimado"
    )
    estimated_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin estimado"
    )
    estimated_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duración estimada en minutos"
    )
    
    actual_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Inicio real"
    )
    actual_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin real"
    )
    actual_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duración real en minutos"
    )
    
    # Estadísticas
    total_distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_containers = models.IntegerField(default=0)
    completed_stops = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Ruta"
        verbose_name_plural = "Rutas"
        ordering = ['-route_date', '-created_at']
        indexes = [
            models.Index(fields=['route_date', 'status']),
            models.Index(fields=['driver', 'route_date']),
        ]
    
    def __str__(self):
        driver_label = "Sin conductor"
        if self.driver:
            driver_label = getattr(self.driver, "display_name", None) or str(self.driver)

        return f"{self.name} - {driver_label} ({self.route_date})"
    
    def calculate_totals(self):
        """Recalcula estadísticas de la ruta."""
        stops = self.stops.all()
        self.total_containers = stops.count()
        self.completed_stops = stops.filter(is_completed=True).count()
        
        if self.actual_end and self.actual_start:
            delta = self.actual_end - self.actual_start
            self.actual_duration = int(delta.total_seconds() / 60)
        
        self.save()


class RouteStop(BaseModel):
    """
    Parada individual en una ruta.
    Cada parada corresponde a un contenedor en una ubicación.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='stops',
        verbose_name="Ruta"
    )
    container = models.ForeignKey(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='route_stops',
        verbose_name="Contenedor"
    )
    
    # Orden en la ruta
    stop_order = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Orden de la parada (1, 2, 3...)"
    )
    
    # Ubicación y acción
    location = models.ForeignKey(
        'drivers.Location',
        on_delete=models.CASCADE,
        verbose_name="Ubicación"
    )
    
    ACTION_TYPES = [
        ('PICKUP', 'Retiro'),
        ('DELIVERY', 'Entrega'),
        ('TRANSFER', 'Transferencia'),
        ('INSPECTION', 'Inspección'),
    ]
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name="Tipo de Acción"
    )
    
    # Tiempos planificados
    planned_arrival = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Llegada planificada"
    )
    planned_departure = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Salida planificada"
    )
    estimated_operation_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo estimado de operación en minutos"
    )
    
    # Tiempos reales
    actual_arrival = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Llegada real"
    )
    actual_departure = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Salida real"
    )
    actual_operation_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo real de operación en minutos"
    )
    
    # Estado
    is_completed = models.BooleanField(
        default=False,
        verbose_name="¿Completada?"
    )
    completion_notes = models.TextField(blank=True)
    
    # Variación vs planificado
    delay_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minutos de retraso (negativo si adelantado)"
    )
    
    class Meta:
        verbose_name = "Parada de Ruta"
        verbose_name_plural = "Paradas de Rutas"
        ordering = ['route', 'stop_order']
        unique_together = ['route', 'stop_order']
        indexes = [
            models.Index(fields=['route', 'stop_order']),
        ]
    
    def __str__(self):
        return f"Parada #{self.stop_order} - {self.location.name} ({self.container.number})"
    
    def calculate_delay(self):
        """Calcula el retraso comparando real vs planificado."""
        if self.actual_arrival and self.planned_arrival:
            delta = self.actual_arrival - self.planned_arrival
            self.delay_minutes = int(delta.total_seconds() / 60)
            self.save()
    
    def mark_completed(self, actual_departure_time=None, notes=''):
        """Marca la parada como completada."""
        self.is_completed = True
        self.actual_departure = actual_departure_time or timezone.now()
        
        if not self.actual_arrival:
            # Si no se registró llegada, asumir que fue hace X minutos
            self.actual_arrival = self.actual_departure - timedelta(
                minutes=self.estimated_operation_time or 15
            )
        
        # Calcular duración real
        if self.actual_departure and self.actual_arrival:
            delta = self.actual_departure - self.actual_arrival
            self.actual_operation_time = int(delta.total_seconds() / 60)
        
        self.completion_notes = notes
        self.calculate_delay()
        
        self.save()
