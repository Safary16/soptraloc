from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """
    Sistema de notificaciones para alertas de arribo y ETAs
    """
    
    TIPO_CHOICES = [
        ('ruta_iniciada', 'Ruta Iniciada'),
        ('eta_actualizado', 'ETA Actualizado'),
        ('arribo_proximo', 'Arribo Próximo'),
        ('llegada', 'Llegada Confirmada'),
        ('demurrage_alerta', 'Alerta Demurrage'),
        ('asignacion', 'Asignación de Conductor'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('leida', 'Leída'),
        ('archivada', 'Archivada'),
    ]
    
    # Relaciones
    container = models.ForeignKey(
        'containers.Container',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Contenedor'
    )
    driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Conductor'
    )
    programacion = models.ForeignKey(
        'programaciones.Programacion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Programación'
    )
    
    # Información de la notificación
    tipo = models.CharField('Tipo', max_length=30, choices=TIPO_CHOICES, db_index=True)
    prioridad = models.CharField('Prioridad', max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField('Estado', max_length=15, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    
    # Contenido
    titulo = models.CharField('Título', max_length=200)
    mensaje = models.TextField('Mensaje')
    
    # Datos ETA (si aplica)
    eta_minutos = models.IntegerField('ETA (minutos)', null=True, blank=True)
    eta_timestamp = models.DateTimeField('ETA Timestamp', null=True, blank=True)
    distancia_km = models.DecimalField('Distancia (km)', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Posición actual (si aplica)
    lat_actual = models.DecimalField('Latitud Actual', max_digits=9, decimal_places=6, null=True, blank=True)
    lng_actual = models.DecimalField('Longitud Actual', max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Datos adicionales
    detalles = models.JSONField('Detalles', default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Creada', auto_now_add=True, db_index=True)
    enviada_at = models.DateTimeField('Enviada', null=True, blank=True)
    leida_at = models.DateTimeField('Leída', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        indexes = [
            models.Index(fields=['tipo', 'estado', '-created_at']),
            models.Index(fields=['prioridad', 'estado']),
            models.Index(fields=['container', '-created_at']),
            models.Index(fields=['driver', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.container.container_id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def marcar_enviada(self):
        """Marca la notificación como enviada"""
        if self.estado == 'pendiente':
            self.estado = 'enviada'
            self.enviada_at = timezone.now()
            self.save(update_fields=['estado', 'enviada_at'])
    
    def marcar_leida(self):
        """Marca la notificación como leída"""
        if self.estado in ['pendiente', 'enviada']:
            self.estado = 'leida'
            self.leida_at = timezone.now()
            self.save(update_fields=['estado', 'leida_at'])
    
    def archivar(self):
        """Archiva la notificación"""
        self.estado = 'archivada'
        self.save(update_fields=['estado'])
    
    @property
    def tiempo_desde_creacion(self):
        """Retorna tiempo transcurrido desde la creación en minutos"""
        if self.created_at:
            delta = timezone.now() - self.created_at
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def es_reciente(self):
        """Verifica si la notificación fue creada en los últimos 30 minutos"""
        return self.tiempo_desde_creacion <= 30


class NotificationPreference(models.Model):
    """
    Preferencias de notificación por usuario o sistema
    """
    
    CANAL_CHOICES = [
        ('sistema', 'Sistema/Dashboard'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    # Usuario (si aplica)
    usuario = models.CharField('Usuario', max_length=200, null=True, blank=True, db_index=True)
    
    # Configuración de canal
    canal = models.CharField('Canal', max_length=20, choices=CANAL_CHOICES)
    activo = models.BooleanField('Activo', default=True)
    
    # Tipos de notificación que recibe
    tipos_notificacion = models.JSONField('Tipos de Notificación', default=list, blank=True)
    
    # Configuración específica
    email_destino = models.EmailField('Email Destino', null=True, blank=True)
    telefono_destino = models.CharField('Teléfono Destino', max_length=20, null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Preferencia de Notificación'
        verbose_name_plural = 'Preferencias de Notificación'
        unique_together = [['usuario', 'canal']]
    
    def __str__(self):
        usuario_str = self.usuario or 'Sistema'
        return f"{usuario_str} - {self.get_canal_display()}"
