from django.db import models


class CD(models.Model):
    """Centros de Distribución (Clientes y CCTIs)"""
    
    TIPOS = [
        ('cliente', 'Cliente'),
        ('ccti', 'CCTI'),
    ]
    
    # Información básica
    nombre = models.CharField('Nombre', max_length=200, unique=True)
    codigo = models.CharField('Código', max_length=50, unique=True, null=True, blank=True)
    direccion = models.TextField('Dirección')
    comuna = models.CharField('Comuna', max_length=100)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPOS, default='cliente')
    
    # Coordenadas para Mapbox
    lat = models.DecimalField('Latitud', max_digits=9, decimal_places=6)
    lng = models.DecimalField('Longitud', max_digits=9, decimal_places=6)
    
    # Gestión de contenedores vacíos (solo para CCTI)
    capacidad_vacios = models.IntegerField('Capacidad Vacíos', default=0)
    vacios_actuales = models.IntegerField('Vacíos Actuales', default=0)
    
    # Configuración logística (para CDs clientes)
    requiere_espera_carga = models.BooleanField(
        'Requiere Espera para Carga', 
        default=False,
        help_text='Si True: conductor espera descarga sobre camión (Puerto Madero, Campos, Quilicura). Si False: drop & hook (El Peñón)'
    )
    permite_soltar_contenedor = models.BooleanField(
        'Permite Drop & Hook', 
        default=False,
        help_text='Si True: conductor puede soltar contenedor y quedar libre inmediatamente (solo El Peñón)'
    )
    tiempo_promedio_descarga_min = models.IntegerField(
        'Tiempo Promedio Descarga (minutos)', 
        default=60,
        help_text='Tiempo estimado que toma descargar el contenedor en este CD'
    )
    
    # Configuración
    activo = models.BooleanField('Activo', default=True)
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Centro de Distribución'
        verbose_name_plural = 'Centros de Distribución'
        indexes = [
            models.Index(fields=['tipo', 'activo']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    @property
    def puede_recibir_vacios(self):
        """Verifica si el CCTI puede recibir más contenedores vacíos"""
        return (
            self.tipo == 'ccti' and 
            self.activo and 
            self.vacios_actuales < self.capacidad_vacios
        )
    
    @property
    def espacios_disponibles(self):
        """Retorna cuántos espacios libres tiene el CCTI"""
        if self.tipo != 'ccti':
            return 0
        return max(0, self.capacidad_vacios - self.vacios_actuales)
    
    def recibir_vacio(self):
        """Incrementa el contador de vacíos"""
        if self.puede_recibir_vacios:
            self.vacios_actuales += 1
            self.save(update_fields=['vacios_actuales'])
            return True
        return False
    
    def retirar_vacio(self):
        """Decrementa el contador de vacíos"""
        if self.vacios_actuales > 0:
            self.vacios_actuales -= 1
            self.save(update_fields=['vacios_actuales'])
            return True
        return False
