from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta


class Location(models.Model):
    """Modelo para gestionar ubicaciones del sistema"""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drivers_location'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class TimeMatrix(models.Model):
    """Matriz de tiempos entre ubicaciones"""
    
    from_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='time_from')
    to_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='time_to')
    
    # Tiempos en minutos
    travel_time = models.IntegerField(help_text="Tiempo de viaje en minutos")
    loading_time = models.IntegerField(default=0, help_text="Tiempo de carga en minutos")
    unloading_time = models.IntegerField(default=0, help_text="Tiempo de descarga en minutos")
    
    # Tiempos históricos para aprendizaje
    avg_travel_time = models.FloatField(null=True, blank=True, help_text="Tiempo promedio histórico")
    min_travel_time = models.IntegerField(null=True, blank=True)
    max_travel_time = models.IntegerField(null=True, blank=True)
    
    # Estadísticas
    total_trips = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drivers_time_matrix'
        unique_together = ['from_location', 'to_location']
    
    def __str__(self):
        return f"{self.from_location} → {self.to_location} ({self.travel_time}min)"
    
    def get_total_time(self):
        """Tiempo total incluyendo viaje, carga y descarga"""
        return self.travel_time + self.loading_time + self.unloading_time
    
    def update_historical_data(self, actual_time):
        """Actualiza los datos históricos con un tiempo real"""
        if self.avg_travel_time is None:
            self.avg_travel_time = actual_time
        else:
            # Media ponderada para dar más peso a datos recientes
            weight = 0.8
            self.avg_travel_time = (self.avg_travel_time * weight) + (actual_time * (1 - weight))
        
        if self.min_travel_time is None or actual_time < self.min_travel_time:
            self.min_travel_time = actual_time
        
        if self.max_travel_time is None or actual_time > self.max_travel_time:
            self.max_travel_time = actual_time
        
        self.total_trips += 1
        self.save()

class Driver(models.Model):
    """Modelo para gestionar conductores"""
    
    TIPO_CONDUCTOR_CHOICES = [
        ('LEASING', 'Leasing'),
        ('LOCALERO', 'Localero'),
        ('TRONCO_PM', 'Tronco PM'),
        ('TRONCO', 'Tronco'),
    ]
    
    ESTADO_CHOICES = [
        ('OPERATIVO', 'Operativo'),
        ('PANNE', 'Panne'),
        ('PERMISO', 'Permiso'),
        ('NO_DISPONIBLE', 'No Disponible'),
        ('AUSENTE', 'Ausente'),
    ]
    
    UBICACION_CHOICES = [
        ('CCTI', 'CCTI - Base Maipú'),
        ('CD_QUILICURA', 'CD Quilicura'),
        ('CD_CAMPOS', 'CD Campos de Chile - Pudahuel'),
        ('CD_MADERO', 'CD Puerto Madero - Pudahuel'),
        ('CD_PENON', 'CD El Peñón - San Bernardo'),
        ('PUERTO_VALPARAISO', 'Puerto Valparaíso'),
        ('PUERTO_SAN_ANTONIO', 'Puerto San Antonio'),
        ('EN_RUTA', 'En Ruta'),
        ('ALMACEN_EXTRAPORTUARIO', 'Almacén Extraportuario'),
    ]
    
    # Información básica
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    
    # Información del vehículo
    ppu = models.CharField(max_length=10, verbose_name="PPU")
    tracto = models.CharField(max_length=10, blank=True)
    
    # Tipo y estado
    tipo_conductor = models.CharField(max_length=20, choices=TIPO_CONDUCTOR_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='OPERATIVO')
    
    # Coordinación
    coordinador = models.CharField(max_length=50, blank=True)
    faena = models.CharField(max_length=50, blank=True)
    
    # Ubicación actual
    ubicacion_actual = models.CharField(max_length=50, choices=UBICACION_CHOICES, default='CCTI')
    tiempo_en_ubicacion = models.DateTimeField(auto_now_add=True)
    
    # Asignación actual
    contenedor_asignado = models.ForeignKey(
        'containers.Container', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='driver_assigned'
    )
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    ingresa_agy = models.BooleanField(default=True, verbose_name="Ingresa AGY")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Campos de seguimiento de asistencia
    hora_ingreso_hoy = models.DateTimeField(null=True, blank=True, verbose_name="Hora de ingreso hoy")
    ultimo_registro_asistencia = models.DateField(null=True, blank=True, verbose_name="Último registro")
    
    class Meta:
        db_table = 'drivers'
        verbose_name = 'Conductor'
        verbose_name_plural = 'Conductores'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.ppu}) - {self.get_tipo_conductor_display()}"
    
    @property
    def esta_disponible(self):
        """Verifica si el conductor está disponible para asignación"""
        return self.estado == 'OPERATIVO' and self.contenedor_asignado is None
    
    @property
    def tiempo_en_ubicacion_texto(self):
        """Tiempo transcurrido en la ubicación actual"""
        from django.utils import timezone
        tiempo = timezone.now() - self.tiempo_en_ubicacion
        
        if tiempo.days > 0:
            return f"{tiempo.days} días"
        elif tiempo.seconds > 3600:
            horas = tiempo.seconds // 3600
            return f"{horas} horas"
        else:
            minutos = tiempo.seconds // 60
            return f"{minutos} minutos"


class Assignment(models.Model):
    """Asignaciones de contenedores a conductores"""
    
    ESTADO_ASIGNACION_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_CURSO', 'En Curso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    container = models.ForeignKey('containers.Container', on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    
    # Fechas y tiempos
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_programada = models.DateTimeField()
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    
    # Tiempo estimado basado en matriz de tiempos
    tiempo_estimado = models.IntegerField(default=120, help_text="Tiempo estimado en minutos")
    tiempo_real = models.IntegerField(null=True, blank=True, help_text="Tiempo real en minutos")
    
    # Estado y ubicaciones
    estado = models.CharField(max_length=20, choices=ESTADO_ASIGNACION_CHOICES, default='PENDIENTE')
    origen = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='assignments_from')
    destino = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='assignments_to')
    
    # Campos legacy para compatibilidad
    origen_legacy = models.CharField(max_length=100, blank=True)
    destino_legacy = models.CharField(max_length=100, blank=True)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'assignments'
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'
        ordering = ['-fecha_asignacion']
    
    def __str__(self):
        return f"{self.container.container_number} -> {self.driver.nombre} ({self.get_estado_display()})"
    
    def is_available_for_new_assignment(self, start_time, duration_minutes):
        """Verifica si el conductor está disponible para una nueva asignación"""
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Buscar asignaciones que se solapen en el tiempo
        overlapping = Assignment.objects.filter(
            driver=self.driver,
            estado__in=['PENDIENTE', 'EN_CURSO'],
            fecha_programada__lt=end_time,
            fecha_programada__gte=start_time - timedelta(minutes=self.tiempo_estimado)
        ).exclude(id=self.id if self.id else None)
        
        return not overlapping.exists()
    
    def calculate_estimated_time(self):
        """Calcula el tiempo estimado basado en la matriz de tiempos"""
        if self.origen and self.destino:
            try:
                time_matrix = TimeMatrix.objects.get(
                    from_location=self.origen,
                    to_location=self.destino
                )
                self.tiempo_estimado = time_matrix.get_total_time()
            except TimeMatrix.DoesNotExist:
                # Usar tiempo por defecto si no existe en la matriz
                self.tiempo_estimado = 120  # 2 horas por defecto
        else:
            self.tiempo_estimado = 120
    
    def complete_assignment(self, actual_minutes):
        """Completa la asignación y actualiza los datos históricos"""
        self.fecha_completada = datetime.now()
        self.tiempo_real = actual_minutes
        self.estado = 'COMPLETADA'
        self.save()
        
        # Actualizar matriz de tiempos con datos reales
        if self.origen and self.destino:
            try:
                time_matrix = TimeMatrix.objects.get(
                    from_location=self.origen,
                    to_location=self.destino
                )
                time_matrix.update_historical_data(actual_minutes)
            except TimeMatrix.DoesNotExist:
                pass


class Alert(models.Model):
    """Sistema de alertas para gestión de contenedores"""
    
    TIPO_ALERTA_CHOICES = [
        ('CONTENEDOR_SIN_ASIGNAR', 'Contenedor sin asignar'),
        ('DEMURRAGE_PROXIMO', 'Demurrage próximo'),
        ('CONDUCTOR_INACTIVO', 'Conductor inactivo'),
        ('RETRASO_PROGRAMACION', 'Retraso en programación'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    
    # Relaciones
    container = models.ForeignKey('containers.Container', null=True, blank=True, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE)
    
    # Estados
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = 'alerts'
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"[{self.get_prioridad_display()}] {self.titulo}"