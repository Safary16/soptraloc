from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ClienteEmpresa(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    rut = models.CharField(max_length=20, unique=True, null=True, blank=True)
    activo = models.BooleanField(default=True)
    hora_inicio_recepcion = models.TimeField(default='08:00')
    hora_fin_recepcion = models.TimeField(default='18:00')
    duracion_slot_min = models.PositiveIntegerField(default=60)
    capacidad_por_slot = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Empresa cliente'
        verbose_name_plural = 'Empresas cliente'

    def __str__(self):
        return self.nombre


class ClienteUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='perfil_cliente',
    )
    empresa = models.ForeignKey(
        ClienteEmpresa, on_delete=models.PROTECT, related_name='usuarios'
    )
    puede_solicitar = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario cliente'
        verbose_name_plural = 'Usuarios cliente'

    def __str__(self):
        return f'{self.user.username} · {self.empresa.nombre}'


class SolicitudHorario(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('ajustada', 'Ajustada por Operaciones'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ]
    MODOS = [('recomendado', 'Recomendado'), ('manual', 'Manual')]

    empresa = models.ForeignKey(ClienteEmpresa, on_delete=models.PROTECT, related_name='solicitudes')
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='solicitudes_cliente')
    container = models.ForeignKey('containers.Container', on_delete=models.PROTECT, related_name='solicitudes_horario')
    cd = models.ForeignKey('cds.CD', on_delete=models.PROTECT, related_name='solicitudes_horario')
    modo = models.CharField(max_length=12, choices=MODOS)
    inicio_solicitado = models.DateTimeField(db_index=True)
    fin_solicitado = models.DateTimeField()
    recomendacion_snapshot = models.JSONField(default=dict, blank=True)
    observaciones_cliente = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default='pendiente', db_index=True)
    inicio_confirmado = models.DateTimeField(null=True, blank=True)
    fin_confirmado = models.DateTimeField(null=True, blank=True)
    respuesta_operaciones = models.TextField(blank=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='solicitudes_cliente_revisadas',
    )
    revisado_at = models.DateTimeField(null=True, blank=True)
    programacion = models.OneToOneField(
        'programaciones.Programacion', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='solicitud_cliente',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['inicio_solicitado']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['container'], condition=models.Q(estado='pendiente'),
                name='unique_pending_request_per_container',
            ),
        ]

    def clean(self):
        if self.fin_solicitado <= self.inicio_solicitado:
            raise ValidationError('El fin debe ser posterior al inicio.')
        if self.container_id and self.container.cliente_empresa_id != self.empresa_id:
            raise ValidationError('El contenedor no pertenece a la empresa solicitante.')
        if self.cd_id and self.cd.cliente_empresa_id != self.empresa_id:
            raise ValidationError('El centro de distribución no pertenece a la empresa solicitante.')

    def __str__(self):
        return f'{self.container.container_id} · {self.inicio_solicitado:%d-%m %H:%M}'


class SituacionCliente(models.Model):
    CATEGORIAS = [
        ('operativa', 'Situación operativa'),
        ('documental', 'Documentación'),
        ('stock', 'Diferencia de stock'),
        ('horario', 'Horario o recepción'),
        ('otro', 'Otro'),
    ]
    PRIORIDADES = [('normal', 'Normal'), ('alta', 'Alta'), ('urgente', 'Urgente')]
    ESTADOS = [
        ('abierta', 'Abierta'),
        ('en_revision', 'En revisión'),
        ('resuelta', 'Resuelta'),
        ('cerrada', 'Cerrada'),
    ]

    empresa = models.ForeignKey(ClienteEmpresa, on_delete=models.PROTECT, related_name='situaciones')
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='situaciones_cliente')
    container = models.ForeignKey(
        'containers.Container', null=True, blank=True, on_delete=models.PROTECT,
        related_name='situaciones_cliente',
    )
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='operativa')
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='normal')
    asunto = models.CharField(max_length=160)
    mensaje = models.TextField()
    estado = models.CharField(max_length=15, choices=ESTADOS, default='abierta', db_index=True)
    respuesta_operaciones = models.TextField(blank=True)
    revisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='situaciones_cliente_revisadas',
    )
    revisada_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['empresa', 'estado', 'prioridad'])]

    def clean(self):
        if self.container_id and self.container.cliente_empresa_id != self.empresa_id:
            raise ValidationError('El contenedor no pertenece a la empresa informante.')

    def __str__(self):
        return f'{self.empresa.nombre} · {self.asunto}'
