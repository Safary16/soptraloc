from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class Location(models.Model):
    """Modelo para gestionar ubicaciones del sistema - TMS Central Location Model"""
    import uuid
    
    id = models.CharField(max_length=32, primary_key=True, default='')  # UUID sin guiones desde core_location
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    address = models.TextField(blank=True, verbose_name="Dirección")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Latitud")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name="Longitud")
    city = models.CharField(max_length=100, blank=True, default='', verbose_name="Ciudad")
    region = models.CharField(max_length=100, blank=True, default='', verbose_name="Región")
    country = models.CharField(max_length=100, default='Chile', verbose_name="País")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # NOTA: Container FK apunta a 'core_location', usamos esa tabla
        db_table = 'core_location'
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['name']
    
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
    
    def get_total_time(self, use_learned: bool = True) -> int:
        """Tiempo total estimado incluyendo viaje, carga y descarga."""
        travel_component = self.travel_time
        if use_learned and self.avg_travel_time is not None:
            travel_component = int(round(self.avg_travel_time))

        total = travel_component + self.loading_time + self.unloading_time
        return max(int(round(total)), 15)
    
    def update_historical_data(self, actual_total_minutes: int, route_minutes: int | None = None, unloading_minutes: int | None = None):
        """Actualiza la matriz de tiempos con datos reales recibidos."""
        if actual_total_minutes is None:
            return

        actual_total_minutes = max(int(actual_total_minutes), 0)

        inferred_route = route_minutes
        if inferred_route is None:
            inferred_route = max(actual_total_minutes - (self.loading_time + self.unloading_time), 0)

        smoothing = 0.6

        if self.avg_travel_time is None:
            self.avg_travel_time = inferred_route
        else:
            self.avg_travel_time = (self.avg_travel_time * smoothing) + (inferred_route * (1 - smoothing))

        # Ajustar límites observados
        if self.min_travel_time is None or inferred_route < self.min_travel_time:
            self.min_travel_time = inferred_route

        if self.max_travel_time is None or inferred_route > self.max_travel_time:
            self.max_travel_time = inferred_route

        # Actualizar tiempos manuales si el dato aprendido es más representativo
        if inferred_route > 0:
            self.travel_time = max(int(round(self.avg_travel_time)), 1)

        if unloading_minutes is not None:
            self.unloading_time = max(unloading_minutes, self.unloading_time)

        self.total_trips += 1
        self.save(update_fields=[
            'avg_travel_time',
            'min_travel_time',
            'max_travel_time',
            'travel_time',
            'unloading_time',
            'total_trips',
            'updated_at'
        ])

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

    TIPO_ASIGNACION_CHOICES = [
        ('ENTREGA', 'Entrega a cliente'),
        ('DEVOLUCION', 'Devolución a depósito/CCTI'),
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
    ruta_minutos_real = models.IntegerField(null=True, blank=True, help_text="Tiempo real de ruta")
    descarga_minutos_real = models.IntegerField(null=True, blank=True, help_text="Tiempo real de descarga")
    
    # Estado y ubicaciones
    estado = models.CharField(max_length=20, choices=ESTADO_ASIGNACION_CHOICES, default='PENDIENTE')
    tipo_asignacion = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_CHOICES,
        default='ENTREGA',
        verbose_name='Tipo de asignación'
    )
    origen = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='assignments_from')
    destino = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='assignments_to')
    
    # Campos legacy para compatibilidad
    origen_legacy = models.CharField(max_length=100, blank=True)
    destino_legacy = models.CharField(max_length=100, blank=True)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # 🆕 Información de tráfico (Mapbox)
    traffic_level_at_assignment = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Tráfico Bajo'),
            ('medium', 'Tráfico Medio'),
            ('high', 'Tráfico Alto'),
            ('very_high', 'Tráfico Muy Alto'),
            ('unknown', 'Desconocido'),
        ],
        default='unknown',
        help_text='Nivel de tráfico al momento de crear la asignación (desde Mapbox)'
    )
    
    mapbox_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Datos completos de Mapbox API (rutas alternativas, warnings, etc.)'
    )
    
    class Meta:
        db_table = 'assignments'
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'
        ordering = ['-fecha_asignacion']
    
    def __str__(self):
        return f"{self.container.container_number} -> {self.driver.nombre} ({self.get_estado_display()})"
    
    def get_traffic_emoji(self):
        """Retorna emoji según nivel de tráfico."""
        return {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'very_high': '🔴',
            'unknown': '⚪',
        }.get(self.traffic_level_at_assignment, '⚪')
    
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
    
    def calculate_estimated_time(self, refresh: bool = True, predicted_minutes: int | None = None):
        """Calcula o reutiliza el tiempo estimado de duración."""
        DEFAULT_MINUTES = 120

        if not refresh:
            return self.tiempo_estimado or DEFAULT_MINUTES

        if predicted_minutes is not None and predicted_minutes > 0:
            minutes = predicted_minutes
        else:
            scheduled = self.fecha_programada or timezone.now()
            minutes = None
            if self.origen and self.destino:
                try:
                    from .services.duration_predictor import DriverDurationPredictor
                except ImportError:
                    DriverDurationPredictor = None

                if DriverDurationPredictor is not None:
                    predictor = DriverDurationPredictor()
                    prediction = predictor.predict(
                        origin=self.origen,
                        destination=self.destino,
                        assignment_type=self.tipo_asignacion or 'ENTREGA',
                        scheduled_datetime=scheduled,
                    )
                    minutes = prediction.minutes if prediction else None

                if minutes is None:
                    try:
                        time_matrix = TimeMatrix.objects.get(
                            from_location=self.origen,
                            to_location=self.destino
                        )
                        minutes = time_matrix.get_total_time()
                    except TimeMatrix.DoesNotExist:
                        minutes = None

        self.tiempo_estimado = int(minutes) if minutes else DEFAULT_MINUTES
        return self.tiempo_estimado

    def record_actual_times(self, *, total_minutes: int, route_minutes: int | None = None, unloading_minutes: int | None = None):
        """Guarda los tiempos reales y alimenta la matriz de tiempos."""
        now = timezone.now()
        self.tiempo_real = max(int(total_minutes), 0)
        self.ruta_minutos_real = route_minutes if route_minutes is None else max(int(route_minutes), 0)
        self.descarga_minutos_real = unloading_minutes if unloading_minutes is None else max(int(unloading_minutes), 0)
        self.fecha_completada = now
        self.estado = 'COMPLETADA'
        self.save(update_fields=['tiempo_real', 'ruta_minutos_real', 'descarga_minutos_real', 'fecha_completada', 'estado'])

        if self.origen and self.destino:
            try:
                time_matrix = TimeMatrix.objects.get(from_location=self.origen, to_location=self.destino)
            except TimeMatrix.DoesNotExist:
                return

            time_matrix.update_historical_data(
                actual_total_minutes=self.tiempo_real,
                route_minutes=self.ruta_minutos_real,
                unloading_minutes=self.descarga_minutos_real,
            )


class Alert(models.Model):
    """Sistema de alertas para gestión de contenedores"""
    
    TIPO_ALERTA_CHOICES = [
        ('CONTENEDOR_SIN_ASIGNAR', 'Contenedor sin asignar'),
        ('DEMURRAGE_PROXIMO', 'Demurrage próximo'),
        ('DEMURRAGE_VENCIDO', 'Demurrage vencido'),
        ('ENTREGA_RETRASADA', 'Entrega retrasada'),
        ('ASIGNACION_PENDIENTE', 'Asignación sin iniciar'),
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


class TrafficAlert(models.Model):
    """
    Alertas de tráfico generadas automáticamente al iniciar rutas.
    Se alimentan de datos en tiempo real obtenidos desde Mapbox Directions API.
    """
    
    TRAFFIC_LEVEL_CHOICES = [
        ('low', 'Tráfico Bajo'),
        ('medium', 'Tráfico Medio'),
        ('high', 'Tráfico Alto'),
        ('very_high', 'Tráfico Muy Alto'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('TRAFFIC', 'Tráfico Denso'),
        ('ACCIDENT', 'Accidente'),
        ('ROAD_CLOSURE', 'Carretera Cerrada'),
        ('CONSTRUCTION', 'Obras en Ruta'),
        ('DELAY', 'Retraso Estimado'),
        ('ALTERNATIVE', 'Ruta Alternativa Disponible'),
    ]
    
    # Relaciones
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='traffic_alerts',
        help_text="Asignación asociada"
    )
    driver = models.ForeignKey(
        Driver, 
        on_delete=models.CASCADE,
        related_name='traffic_alerts',
        help_text="Conductor notificado"
    )
    
    # Información de la ruta
    origin_name = models.CharField(max_length=200, help_text="Origen")
    destination_name = models.CharField(max_length=200, help_text="Destino")
    
    # Datos de tráfico
    traffic_level = models.CharField(
        max_length=20,
        choices=TRAFFIC_LEVEL_CHOICES,
        help_text="Nivel de tráfico"
    )
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPE_CHOICES,
        help_text="Tipo de alerta"
    )
    
    # Tiempos
    estimated_time_minutes = models.IntegerField(
        help_text="Tiempo estimado sin tráfico (minutos)"
    )
    actual_time_minutes = models.IntegerField(
        help_text="Tiempo actual con tráfico (minutos)"
    )
    delay_minutes = models.IntegerField(
        help_text="Retraso adicional por tráfico (minutos)"
    )
    
    # ETA
    departure_time = models.DateTimeField(
        help_text="Hora de salida"
    )
    estimated_arrival = models.DateTimeField(
        help_text="Hora estimada de llegada (ETA)"
    )
    
    # Mensaje
    message = models.TextField(
        help_text="Mensaje de la alerta para el conductor"
    )
    warnings = models.JSONField(
        default=list,
        blank=True,
        help_text="Advertencias específicas (JSON array)"
    )
    
    # Rutas alternativas
    has_alternatives = models.BooleanField(
        default=False,
        help_text="¿Hay rutas alternativas disponibles?"
    )
    alternative_routes = models.JSONField(
        default=list,
        blank=True,
        help_text="Rutas alternativas sugeridas (JSON array)"
    )
    
    # Datos crudos de la API
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos completos devueltos por Mapbox API"
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        help_text="¿Alerta activa?"
    )
    acknowledged = models.BooleanField(
        default=False,
        help_text="¿Conductor confirmó recepción?"
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de confirmación"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drivers_traffic_alert'
        verbose_name = 'Alerta de Tráfico'
        verbose_name_plural = 'Alertas de Tráfico'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['driver', '-created_at']),
            models.Index(fields=['assignment', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.driver.nombre} ({self.get_traffic_level_display()})"
    
    def get_delay_text(self):
        """Retorna texto descriptivo del retraso"""
        if self.delay_minutes <= 5:
            return "Sin retraso significativo"
        elif self.delay_minutes <= 15:
            return f"Retraso leve: +{self.delay_minutes} minutos"
        elif self.delay_minutes <= 30:
            return f"Retraso moderado: +{self.delay_minutes} minutos"
        else:
            return f"Retraso importante: +{self.delay_minutes} minutos"
    
    def get_traffic_emoji(self):
        """Emoji representativo del nivel de tráfico"""
        emojis = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'very_high': '🔴',
        }
        return emojis.get(self.traffic_level, '⚪')