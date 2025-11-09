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
    patente_confirmada = models.CharField(max_length=20, null=True, blank=True, verbose_name='Patente Confirmada', help_text='Patente confirmada al iniciar ruta')
    fecha_inicio_ruta = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Inicio Ruta', help_text='Timestamp cuando el conductor inició la ruta')
    gps_inicio_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='GPS Inicio Latitud')
    gps_inicio_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='GPS Inicio Longitud')
    
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
        return f"{self.container.container_id if self.container else 'N/A'} - {self.cliente}"
    
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
        
        # Crear notificación para el conductor
        try:
            from apps.notifications.services import NotificationService
            NotificationService.crear_notificacion_asignacion(self, driver)
        except Exception as e:
            # Log error pero no fallar la asignación
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creando notificación de asignación: {str(e)}")
    
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
    
    def verificar_alerta(self):
        """
        Verifica si la programación requiere alerta (< 48h sin conductor) y actualiza el campo
        
        Returns:
            bool: True si se debe generar alerta, False en caso contrario
        """
        if self.driver:
            # Si ya tiene conductor, no requiere alerta
            if self.pk:  # Solo guardar si el objeto ya existe en la DB
                self.requiere_alerta = False
                self.save(update_fields=['requiere_alerta'])
            return False
        
        horas = self.horas_hasta_programacion
        if horas is None:
            return False
        
        # Requiere alerta si faltan menos de 48 horas y no tiene conductor
        requiere = horas < 48 and horas > 0
        
        # Actualizar el campo si cambió (solo si el objeto existe en la DB)
        if self.pk and self.requiere_alerta != requiere:
            self.requiere_alerta = requiere
            self.save(update_fields=['requiere_alerta'])
        
        return requiere


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
    
    def calcular_desviacion(self):
        """
        Calcula el porcentaje de desviación entre el tiempo estimado y el real
        
        Returns:
            float: Porcentaje de desviación (positivo = más lento que estimado, negativo = más rápido)
        """
        if self.tiempo_estimado_min == 0:
            return 0
        return ((self.tiempo_real_min - self.tiempo_estimado_min) / self.tiempo_estimado_min) * 100
    
    @classmethod
    def obtener_tiempo_aprendido(cls, cd, tipo_operacion, conductor=None):
        """
        Obtiene tiempo aprendido basado en operaciones históricas
        
        Estrategia:
        - Promedio móvil de las últimas 10 operaciones válidas (no anómalas)
        - Si hay conductor, priorizarlo pero considerar datos generales del CD
        - Fallback al tiempo promedio del CD
        
        Returns:
            int: Tiempo estimado en minutos
        """
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Avg
        
        # Filtro base: CD + tipo_operacion + sin anomalías + últimos 30 días
        fecha_limite = timezone.now() - timedelta(days=30)
        
        filtros = {
            'cd': cd,
            'tipo_operacion': tipo_operacion,
            'anomalia': False,
            'fecha__gte': fecha_limite
        }
        
        # Intentar con conductor específico primero
        if conductor:
            tiempos_conductor = cls.objects.filter(
                **filtros,
                conductor=conductor
            ).order_by('-fecha')[:10]
            
            if tiempos_conductor.count() >= 3:
                # Suficientes datos del conductor
                promedio = tiempos_conductor.aggregate(Avg('tiempo_real_min'))['tiempo_real_min__avg']
                if promedio:
                    return int(promedio)
        
        # Fallback a datos generales del CD
        tiempos_cd = cls.objects.filter(**filtros).order_by('-fecha')[:20]
        
        if tiempos_cd.count() >= 5:
            # Suficientes datos generales
            promedio = tiempos_cd.aggregate(Avg('tiempo_real_min'))['tiempo_real_min__avg']
            if promedio:
                return int(promedio)
        
        # Fallback final al tiempo promedio del CD
        if tipo_operacion == 'descarga_cd' and cd.tiempo_promedio_descarga_min:
            return cd.tiempo_promedio_descarga_min
        
        # Default genérico
        return 60


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
    
    def calcular_factor_correccion(self):
        """
        Calcula el factor de corrección entre el tiempo de Mapbox y el tiempo real
        
        Returns:
            float: Factor de corrección (>1 = más lento que Mapbox, <1 = más rápido)
        """
        if self.tiempo_mapbox_min == 0:
            return 1.0
        return self.tiempo_real_min / self.tiempo_mapbox_min
    
    @classmethod
    def obtener_tiempo_aprendido(cls, origen_coords, destino_coords, tiempo_mapbox, hora_salida, conductor=None):
        """
        Obtiene tiempo aprendido basado en viajes históricos similares
        
        Estrategia:
        - Buscar viajes en radio de 1km de origen y destino
        - Considerar hora del día y día de semana (tráfico)
        - Calcular factor de corrección sobre tiempo Mapbox
        - Priorizar datos del conductor si disponibles
        
        Args:
            origen_coords: tuple (lat, lon)
            destino_coords: tuple (lat, lon)
            tiempo_mapbox: int (tiempo base de Mapbox)
            hora_salida: datetime
            conductor: Driver opcional
        
        Returns:
            int: Tiempo estimado en minutos
        """
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Avg, Q
        from decimal import Decimal
        
        # Radio de búsqueda: ~1km = 0.009 grados
        radio = Decimal('0.009')
        
        # Extraer hora y día de semana
        hora_del_dia = hora_salida.hour
        dia_semana = hora_salida.weekday()
        
        # Filtros base: origen/destino similares + sin anomalías + últimos 60 días
        fecha_limite = timezone.now() - timedelta(days=60)
        
        filtros_base = Q(
            origen_lat__gte=Decimal(str(origen_coords[0])) - radio,
            origen_lat__lte=Decimal(str(origen_coords[0])) + radio,
            origen_lon__gte=Decimal(str(origen_coords[1])) - radio,
            origen_lon__lte=Decimal(str(origen_coords[1])) + radio,
            destino_lat__gte=Decimal(str(destino_coords[0])) - radio,
            destino_lat__lte=Decimal(str(destino_coords[0])) + radio,
            destino_lon__gte=Decimal(str(destino_coords[1])) - radio,
            destino_lon__lte=Decimal(str(destino_coords[1])) + radio,
            anomalia=False,
            fecha__gte=fecha_limite
        )
        
        # Priorizar misma franja horaria (±2 horas)
        hora_min = max(0, hora_del_dia - 2)
        hora_max = min(23, hora_del_dia + 2)
        
        # Intentar con conductor específico primero
        if conductor:
            viajes_conductor = cls.objects.filter(
                filtros_base,
                conductor=conductor,
                hora_del_dia__gte=hora_min,
                hora_del_dia__lte=hora_max
            ).order_by('-fecha')[:5]
            
            if viajes_conductor.count() >= 2:
                # Suficientes datos del conductor
                promedio_real = viajes_conductor.aggregate(Avg('tiempo_real_min'))['tiempo_real_min__avg']
                if promedio_real:
                    return int(promedio_real)
        
        # Fallback a datos generales (misma franja horaria)
        viajes_similares = cls.objects.filter(
            filtros_base,
            hora_del_dia__gte=hora_min,
            hora_del_dia__lte=hora_max
        ).order_by('-fecha')[:10]
        
        if viajes_similares.count() >= 3:
            # Calcular factor de corrección
            promedio_real = viajes_similares.aggregate(Avg('tiempo_real_min'))['tiempo_real_min__avg']
            promedio_mapbox = viajes_similares.aggregate(Avg('tiempo_mapbox_min'))['tiempo_mapbox_min__avg']
            
            if promedio_real and promedio_mapbox and promedio_mapbox > 0:
                factor = promedio_real / promedio_mapbox
                # Aplicar factor al tiempo actual de Mapbox
                tiempo_ajustado = int(tiempo_mapbox * factor)
                return tiempo_ajustado
        
        # Fallback final: usar Mapbox directo
        return tiempo_mapbox