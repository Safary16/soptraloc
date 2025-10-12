from django.db import models
from django.utils import timezone
from datetime import timedelta


class Programacion(models.Model):
    """Programaciones de entrega de contenedores"""
    
    # Relaciones
    container = models.OneToOneField(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='programacion',
        verbose_name='Contenedor'
    )
    driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programaciones',
        verbose_name='Conductor'
    )
    cd = models.ForeignKey(
        'cds.CD',
        on_delete=models.CASCADE,
        related_name='programaciones',
        verbose_name='Centro de Distribución'
    )
    
    # Información de la programación
    fecha_programada = models.DateTimeField('Fecha Programada', db_index=True)
    cliente = models.CharField('Cliente', max_length=200)
    direccion_entrega = models.TextField('Dirección Entrega', blank=True)
    observaciones = models.TextField('Observaciones', blank=True)
    
    # Datos calculados con Mapbox
    eta_minutos = models.IntegerField('ETA (minutos)', null=True, blank=True)
    distancia_km = models.DecimalField('Distancia (km)', max_digits=10, decimal_places=2, null=True, blank=True)
    ruta_geojson = models.JSONField('Ruta GeoJSON', null=True, blank=True)
    
    # Control de alertas
    alerta_48h_enviada = models.BooleanField('Alerta 48h Enviada', default=False)
    requiere_alerta = models.BooleanField('Requiere Alerta', default=False)
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        ordering = ['fecha_programada']
        verbose_name = 'Programación'
        verbose_name_plural = 'Programaciones'
        indexes = [
            models.Index(fields=['fecha_programada']),
            models.Index(fields=['alerta_48h_enviada', 'requiere_alerta']),
            models.Index(fields=['driver']),
        ]
    
    def __str__(self):
        return f"{self.container.container_id} - {self.fecha_programada.strftime('%Y-%m-%d %H:%M')} - {self.cliente}"
    
    @property
    def horas_hasta_programacion(self):
        """Calcula cuántas horas faltan para la fecha programada"""
        if not self.fecha_programada:
            return None
        delta = self.fecha_programada - timezone.now()
        return delta.total_seconds() / 3600
    
    @property
    def requiere_conductor_urgente(self):
        """Verifica si faltan menos de 48h y no tiene conductor"""
        horas = self.horas_hasta_programacion
        return horas is not None and horas <= 48 and not self.driver
    
    def verificar_alerta(self):
        """Verifica si necesita alerta y la marca"""
        if self.requiere_conductor_urgente and not self.alerta_48h_enviada:
            self.requiere_alerta = True
            self.save(update_fields=['requiere_alerta'])
            return True
        return False
    
    def marcar_alerta_enviada(self):
        """Marca la alerta como enviada"""
        self.alerta_48h_enviada = True
        self.requiere_alerta = False
        self.save(update_fields=['alerta_48h_enviada', 'requiere_alerta'])
    
    def asignar_conductor(self, driver, usuario=None):
        """Asigna un conductor a la programación"""
        self.driver = driver
        self.save(update_fields=['driver'])
        
        # Actualizar estado del contenedor
        self.container.cambiar_estado('asignado', usuario)
        
        # Incrementar contador de entregas del conductor
        driver.num_entregas_dia += 1
        driver.save(update_fields=['num_entregas_dia'])
        
        # Registrar evento
        from apps.events.models import Event
        Event.objects.create(
            container=self.container,
            event_type='asignacion_driver',
            detalles={
                'driver_id': driver.id,
                'driver_nombre': driver.nombre,
                'programacion_id': self.id,
            },
            usuario=usuario
        )
        
        # Crear notificación para el conductor
        from apps.notifications.models import Notification
        Notification.objects.create(
            programacion=self,
            tipo='asignacion_conductor',
            mensaje=f"Se te ha asignado el contenedor {self.container.numero} para entregar en {self.cd.nombre}",
            detalles={
                'container': self.container.numero,
                'cd_nombre': self.cd.nombre,
                'cd_direccion': self.cd.direccion,
                'fecha_programada': self.fecha_programada.isoformat(),
                'cliente': self.cliente,
            }
        )


class TiempoOperacion(models.Model):
    """
    Registra tiempos reales de operaciones para aprendizaje
    
    Aprende patrones como:
    - CDs con tiempos consistentes vs variables
    - Conductores más rápidos/lentos
    - Diferencias entre tipos de operación
    """
    
    TIPO_OPERACION_CHOICES = [
        ('carga_ccti', 'Carga en CCTI'),
        ('descarga_cd', 'Descarga en CD'),
        ('retiro_puerto', 'Retiro en Puerto'),
        ('devolucion_vacio', 'Devolución Vacío'),
    ]
    
    # Relaciones
    cd = models.ForeignKey('cds.CD', on_delete=models.CASCADE, related_name='tiempos_operacion')
    conductor = models.ForeignKey('drivers.Driver', on_delete=models.SET_NULL, null=True, blank=True)
    container = models.ForeignKey('containers.Container', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tipo de operación
    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION_CHOICES)
    
    # Tiempos
    tiempo_estimado_min = models.IntegerField(
        help_text="Tiempo estimado inicial (ej: CD.tiempo_promedio_descarga_min)"
    )
    tiempo_real_min = models.IntegerField(
        help_text="Tiempo real medido desde hora_inicio hasta hora_fin"
    )
    
    # Contexto
    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField()
    fecha = models.DateField(auto_now_add=True, db_index=True)
    
    # Flags
    anomalia = models.BooleanField(
        default=False,
        help_text="Marca tiempos anómalos (>3x estimado) para excluir del aprendizaje"
    )
    
    # Observaciones
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
        return f"{self.cd.nombre} - {self.get_tipo_operacion_display()} - {self.tiempo_real_min}min"
    
    def calcular_desviacion(self):
        """Calcula % de desviación del tiempo real vs estimado"""
        if self.tiempo_estimado_min == 0:
            return 0
        return ((self.tiempo_real_min - self.tiempo_estimado_min) / self.tiempo_estimado_min) * 100
    
    def marcar_como_anomalia_si_corresponde(self):
        """
        Marca automáticamente como anomalía si el tiempo real
        es más de 3 veces el estimado
        """
        if self.tiempo_real_min > (self.tiempo_estimado_min * 3):
            self.anomalia = True
            self.observaciones += f"\n[AUTO] Anomalía detectada: {self.tiempo_real_min}min > 3x{self.tiempo_estimado_min}min"
    
    @classmethod
    def obtener_tiempo_aprendido(cls, cd, tipo_operacion, conductor=None):
        """
        Obtiene tiempo predicho basado en aprendizaje
        
        Estrategia:
        1. Últimas 10 operaciones (60% peso)
        2. Promedio histórico del CD (40% peso)
        3. Si tiene <5 registros, usa tiempo_promedio del CD
        
        Args:
            cd: CD object
            tipo_operacion: str con tipo de operación
            conductor: Driver object (opcional, para personalizar)
        
        Returns:
            int: Tiempo estimado en minutos
        """
        # Filtrar registros válidos (sin anomalías)
        filtros = {
            'cd': cd,
            'tipo_operacion': tipo_operacion,
            'anomalia': False
        }
        
        if conductor:
            filtros['conductor'] = conductor
        
        registros = cls.objects.filter(**filtros).order_by('-fecha', '-hora_inicio')[:10]
        
        if registros.count() < 5:
            # Pocos datos, usar default del CD
            if tipo_operacion == 'descarga_cd':
                return cd.tiempo_promedio_descarga_min or 60
            return 60  # Default genérico
        
        # Calcular promedio reciente (últimas 10)
        tiempos_recientes = [r.tiempo_real_min for r in registros]
        promedio_reciente = sum(tiempos_recientes) / len(tiempos_recientes)
        
        # Calcular promedio histórico (todas las operaciones del CD)
        historico = cls.objects.filter(
            cd=cd,
            tipo_operacion=tipo_operacion,
            anomalia=False
        )
        promedio_historico = historico.aggregate(
            models.Avg('tiempo_real_min')
        )['tiempo_real_min__avg'] or promedio_reciente
        
        # Ponderación: 60% reciente, 40% histórico
        tiempo_aprendido = (promedio_reciente * 0.6) + (promedio_historico * 0.4)
        
        return int(tiempo_aprendido)


class TiempoViaje(models.Model):
    """
    Registra tiempos reales de viaje para aprendizaje
    
    Compara tiempo Mapbox vs tiempo real para:
    - Identificar rutas con tráfico consistente
    - Ajustar estimaciones por hora del día
    - Personalizar por conductor
    """
    
    # Origen y destino
    origen_lat = models.DecimalField(max_digits=10, decimal_places=7)
    origen_lon = models.DecimalField(max_digits=10, decimal_places=7)
    destino_lat = models.DecimalField(max_digits=10, decimal_places=7)
    destino_lon = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Referencias opcionales
    origen_nombre = models.CharField(max_length=200, blank=True)
    destino_nombre = models.CharField(max_length=200, blank=True)
    
    # Relaciones
    conductor = models.ForeignKey('drivers.Driver', on_delete=models.SET_NULL, null=True, blank=True)
    programacion = models.ForeignKey('programaciones.Programacion', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tiempos
    tiempo_mapbox_min = models.IntegerField(
        help_text="Tiempo estimado por Mapbox al iniciar viaje"
    )
    tiempo_real_min = models.IntegerField(
        help_text="Tiempo real medido desde salida hasta llegada"
    )
    
    # Contexto temporal
    hora_salida = models.DateTimeField()
    hora_llegada = models.DateTimeField()
    fecha = models.DateField(auto_now_add=True, db_index=True)
    hora_del_dia = models.IntegerField(
        help_text="Hora de salida (0-23) para análisis de tráfico"
    )
    dia_semana = models.IntegerField(
        help_text="Día de la semana (0=Lunes, 6=Domingo)"
    )
    
    # Distancia
    distancia_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Distancia en km según Mapbox"
    )
    
    # Flags
    anomalia = models.BooleanField(
        default=False,
        help_text="Marca viajes anómalos (pausas largas, desvíos) para excluir"
    )
    
    # Observaciones
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
        return f"{self.origen_nombre} → {self.destino_nombre} - {self.tiempo_real_min}min"
    
    def calcular_factor_correccion(self):
        """
        Calcula factor de corrección = tiempo_real / tiempo_mapbox
        
        Ej: Si mapbox dice 60min pero tomó 90min, factor = 1.5
        """
        if self.tiempo_mapbox_min == 0:
            return 1.0
        return self.tiempo_real_min / self.tiempo_mapbox_min
    
    def marcar_como_anomalia_si_corresponde(self):
        """
        Marca como anomalía si:
        - Tiempo real > 3x Mapbox
        - Velocidad promedio < 10 km/h (indica pausa larga)
        """
        if self.tiempo_real_min > (self.tiempo_mapbox_min * 3):
            self.anomalia = True
            self.observaciones += f"\n[AUTO] Anomalía: Tiempo 3x mayor al estimado"
        
        # Calcular velocidad promedio
        if self.tiempo_real_min > 0:
            velocidad_promedio = (float(self.distancia_km) / self.tiempo_real_min) * 60  # km/h
            if velocidad_promedio < 10:
                self.anomalia = True
                self.observaciones += f"\n[AUTO] Anomalía: Velocidad promedio {velocidad_promedio:.1f} km/h < 10 km/h"
    
    @classmethod
    def obtener_tiempo_aprendido(cls, origen_coords, destino_coords, tiempo_mapbox, hora_salida=None, conductor=None):
        """
        Obtiene tiempo predicho basado en aprendizaje
        
        Estrategia:
        1. Buscar viajes similares (±0.01° lat/lon = ~1km)
        2. Filtrar por hora del día si es relevante
        3. Ponderar: 60% reciente (últimos 10), 40% histórico
        4. Aplicar factor de corrección al tiempo Mapbox
        
        Args:
            origen_coords: tuple (lat, lon)
            destino_coords: tuple (lat, lon)
            tiempo_mapbox: int tiempo en minutos según Mapbox
            hora_salida: datetime opcional para filtrar por hora del día
            conductor: Driver opcional para personalizar
        
        Returns:
            int: Tiempo estimado en minutos
        """
        # Tolerancia de búsqueda (±0.01° ≈ 1km)
        tolerancia = 0.01
        
        filtros = {
            'origen_lat__range': (origen_coords[0] - tolerancia, origen_coords[0] + tolerancia),
            'origen_lon__range': (origen_coords[1] - tolerancia, origen_coords[1] + tolerancia),
            'destino_lat__range': (destino_coords[0] - tolerancia, destino_coords[0] + tolerancia),
            'destino_lon__range': (destino_coords[1] - tolerancia, destino_coords[1] + tolerancia),
            'anomalia': False
        }
        
        # Filtrar por hora del día si se proporciona
        if hora_salida:
            hora = hora_salida.hour
            # Ventana de ±2 horas para capturar patrones de tráfico
            hora_min = (hora - 2) % 24
            hora_max = (hora + 2) % 24
            if hora_min < hora_max:
                filtros['hora_del_dia__range'] = (hora_min, hora_max)
            # Si cruza medianoche, usar OR (manejado con Q objects)
        
        if conductor:
            filtros['conductor'] = conductor
        
        registros = cls.objects.filter(**filtros).order_by('-fecha', '-hora_salida')[:10]
        
        if registros.count() < 3:
            # Muy pocos datos, usar tiempo Mapbox directamente
            return tiempo_mapbox
        
        # Calcular factores de corrección
        factores_recientes = [r.calcular_factor_correccion() for r in registros]
        factor_reciente = sum(factores_recientes) / len(factores_recientes)
        
        # Factor histórico (todos los viajes similares)
        historico = cls.objects.filter(**filtros)
        factores_historicos = [r.calcular_factor_correccion() for r in historico if not r.anomalia]
        
        if not factores_historicos:
            factor_historico = factor_reciente
        else:
            factor_historico = sum(factores_historicos) / len(factores_historicos)
        
        # Ponderación: 60% reciente, 40% histórico
        factor_final = (factor_reciente * 0.6) + (factor_historico * 0.4)
        
        # Aplicar factor al tiempo Mapbox
        tiempo_aprendido = tiempo_mapbox * factor_final
        
        return int(tiempo_aprendido)
    
    def save(self, *args, **kwargs):
        """Override para calcular campos derivados antes de guardar"""
        # Extraer hora y día de la semana
        if self.hora_salida:
            self.hora_del_dia = self.hora_salida.hour
            self.dia_semana = self.hora_salida.weekday()
        
        # Marcar anomalías automáticamente
        self.marcar_como_anomalia_si_corresponde()
        
        super().save(*args, **kwargs)
