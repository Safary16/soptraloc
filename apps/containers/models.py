from django.db import models
from django.utils import timezone


class Container(models.Model):
    """Modelo principal de contenedores con ciclo de vida completo"""
    
    ESTADOS = [
        # Estados iniciales
        ('por_arribar', 'Por Arribar'),  # Nave en tránsito
        
        # Estados en puerto (contenedor lleno)
        ('liberado', 'Liberado'),  # Liberado por aduana/naviera
        ('secuenciado', 'Secuenciado'),  # Marcado para próxima entrega
        ('programado', 'Programado'),  # Asignado a fecha y CD
        ('asignado', 'Asignado'),  # Asignado a conductor
        
        # Estados en tránsito (lleno)
        ('en_ruta', 'En Ruta'),  # Conductor en camino a CD
        ('entregado', 'Entregado'),  # Llegó a CD cliente
        ('descargado', 'Descargado'),  # Cliente terminó de descargar
        
        # Estados vacío (retorno)
        ('vacio', 'Vacío'),  # Descargado, esperando retiro
        ('vacio_en_ruta', 'Vacío en Ruta'),  # Retornando a depósito
        ('devuelto', 'Devuelto'),  # Devuelto a depósito naviera
    ]
    
    TIPOS = [
        ('20', "20'"),
        ('40', "40'"),
        ('40HC', "40' HC"),
        ('45', "45'"),
    ]
    
    TIPO_CARGA = [
        ('dry', 'Dry (Seco)'),
        ('reefer', 'Reefer (Refrigerado)'),
        ('open_top', 'Open Top'),
        ('flat_rack', 'Flat Rack'),
        ('tank', 'Tank'),
    ]
    
    TIPOS_MOVIMIENTO = [
        ('automatico', 'Automático (Puerto)'),
        ('retiro_ccti', 'Retiro a CCTI'),
        ('retiro_directo', 'Retiro Directo a Cliente'),
    ]
    
    # Identificación
    container_id = models.CharField('ID Contenedor', max_length=50, unique=True, db_index=True)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPOS)
    tipo_carga = models.CharField('Tipo de Carga', max_length=20, choices=TIPO_CARGA, default='dry')
    
    # Información del embarque
    nave = models.CharField('Nave', max_length=100)
    viaje = models.CharField('Viaje', max_length=50, null=True, blank=True, help_text='Número de viaje')
    booking = models.CharField('Booking/MBL', max_length=100, null=True, blank=True, help_text='Número de booking o Master Bill of Lading')
    fecha_eta = models.DateTimeField('ETA (Estimated Time of Arrival)', null=True, blank=True, help_text='Fecha estimada de arribo')
    peso_carga = models.DecimalField('Peso Carga (kg)', max_digits=10, decimal_places=2, null=True, blank=True, help_text='Peso de la mercancía')
    tara = models.DecimalField('Tara (kg)', max_digits=10, decimal_places=2, null=True, blank=True, help_text='Peso del contenedor vacío')
    contenido = models.TextField('Contenido', null=True, blank=True, help_text='Descripción de la carga')
    vendor = models.CharField('Vendor', max_length=200, null=True, blank=True)
    sello = models.CharField('Sello', max_length=100, null=True, blank=True)
    puerto = models.CharField('Puerto', max_length=100, default='Valparaíso')
    referencia = models.CharField('Referencia', max_length=100, null=True, blank=True, help_text='Referencia del cliente')
    
    # Estado y ubicación
    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='por_arribar', db_index=True)
    posicion_fisica = models.CharField('Posición Física', max_length=100, null=True, blank=True, help_text='TPS, STI, PCE, ZEAL, CLEP, etc.')
    tipo_movimiento = models.CharField('Tipo de Movimiento', max_length=20, choices=TIPOS_MOVIMIENTO, default='automatico')
    
    # Información de entrega
    cliente = models.CharField('Cliente', max_length=200, null=True, blank=True, help_text='Nombre del cliente final')
    comuna = models.CharField('Comuna Destino', max_length=100, null=True, blank=True)
    secuenciado = models.BooleanField('Secuenciado', default=False, help_text='Marcado para próxima liberación')
    cd_entrega = models.ForeignKey('cds.CD', on_delete=models.SET_NULL, null=True, blank=True, related_name='contenedores_entregados', verbose_name='CD de Entrega')
    
    # Información de liberación y logística
    deposito_devolucion = models.CharField('Depósito Devolución', max_length=200, null=True, blank=True, help_text='Dónde devolver contenedor vacío')
    fecha_demurrage = models.DateTimeField('Fecha Demurrage', null=True, blank=True, db_index=True, help_text='Fecha de vencimiento de demurrage (después se paga)')
    
    # Timestamps de cada transición de estado (ciclo completo)
    fecha_arribo = models.DateTimeField('Fecha Arribo', null=True, blank=True, help_text='Nave llega a puerto')
    fecha_liberacion = models.DateTimeField('Fecha Liberación', null=True, blank=True, help_text='Liberado por aduana/naviera')
    fecha_programacion = models.DateTimeField('Fecha Programación', null=True, blank=True, help_text='Asignado a fecha y CD')
    fecha_asignacion = models.DateTimeField('Fecha Asignación', null=True, blank=True, help_text='Asignado a conductor')
    fecha_inicio_ruta = models.DateTimeField('Fecha Inicio Ruta', null=True, blank=True, help_text='Conductor sale con contenedor')
    fecha_entrega = models.DateTimeField('Fecha Entrega', null=True, blank=True, help_text='Llega a CD cliente')
    fecha_descarga = models.DateTimeField('Fecha Descarga', null=True, blank=True, help_text='Cliente termina de descargar')
    fecha_vacio = models.DateTimeField('Fecha Vacío', null=True, blank=True, help_text='Contenedor vacío listo para retiro')
    fecha_vacio_ruta = models.DateTimeField('Fecha Vacío en Ruta', null=True, blank=True, help_text='Iniciando retorno a depósito')
    fecha_devolucion = models.DateTimeField('Fecha Devolución', null=True, blank=True, help_text='Devuelto a depósito naviera')
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contenedor'
        verbose_name_plural = 'Contenedores'
        indexes = [
            models.Index(fields=['container_id']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_programacion']),
            models.Index(fields=['secuenciado']),
        ]
    
    def __str__(self):
        return f"{self.container_id} - {self.get_estado_display()}"
    
    @staticmethod
    def normalize_container_id(container_id):
        """
        Normaliza el ID del contenedor eliminando espacios y guiones
        Ejemplo: "TEMU 580105-5" o "TEMU5801055" → "TEMU5801055"
        """
        if not container_id:
            return container_id
        # Eliminar espacios y guiones
        return str(container_id).replace(' ', '').replace('-', '').upper().strip()
    
    @property
    def container_id_formatted(self):
        """
        Retorna el container_id en formato estándar ISO 6346: XXXU 123456-7
        4 letras + espacio + 6 dígitos + guión + 1 dígito verificador
        Ejemplo: "TEMU5801055" → "TEMU 580105-5"
        """
        if not self.container_id:
            return self.container_id
        
        # Normalizar (eliminar espacios y guiones)
        normalized = self.normalize_container_id(self.container_id)
        
        # Validar que tenga al menos 11 caracteres (4 letras + 7 dígitos)
        if len(normalized) < 11:
            return self.container_id  # Retornar original si no cumple formato
        
        # Extraer partes: 4 letras + 6 dígitos + 1 dígito verificador
        prefix = normalized[:4]  # Primeras 4 letras
        numbers = normalized[4:10]  # 6 dígitos
        check = normalized[10:11]  # 1 dígito verificador
        
        # Validar que el prefijo sean letras y los números sean dígitos
        if not prefix.isalpha() or not numbers.isdigit() or not check.isdigit():
            return self.container_id  # Retornar original si no cumple formato
        
        # Retornar formateado
        return f"{prefix} {numbers}-{check}"
    
    def get_tara_default(self):
        """Retorna la tara típica según tipo de contenedor y carga"""
        taras = {
            '20': {'dry': 2300, 'reefer': 3050},
            '40': {'dry': 3750, 'reefer': 4480},
            '40HC': {'dry': 3900, 'reefer': 4600},
            '45': {'dry': 4800, 'reefer': 5200},
        }
        tipo_carga = self.tipo_carga or 'dry'
        return taras.get(self.tipo, {}).get(tipo_carga, 3500)
    
    @property
    def peso_total(self):
        """Calcula el peso total: carga + tara"""
        tara = self.tara or self.get_tara_default()
        peso_carga = self.peso_carga or 0
        return float(peso_carga) + float(tara)
    
    @property
    def peso_total_tons(self):
        """Retorna el peso total en toneladas"""
        return self.peso_total / 1000.0
    
    @property
    def dias_para_demurrage(self):
        """Calcula días restantes hasta demurrage"""
        if not self.fecha_demurrage:
            return None
        delta = self.fecha_demurrage - timezone.now()
        return delta.days
    
    @property
    def dias_vencido_demurrage(self):
        """Retorna días vencidos (valor absoluto cuando es negativo)"""
        dias = self.dias_para_demurrage
        if dias is not None and dias < 0:
            return abs(dias)
        return 0
    
    @property
    def urgencia_demurrage(self):
        """Retorna nivel de urgencia basado en días para demurrage"""
        dias = self.dias_para_demurrage
        if dias is None:
            return 'sin_fecha'
        if dias < 0:
            return 'vencido'
        if dias <= 1:
            return 'critico'
        if dias <= 2:
            return 'alto'
        if dias <= 5:
            return 'medio'
        return 'bajo'
    
    def save(self, *args, **kwargs):
        """Override save para calcular tara si no existe"""
        if not self.tara:
            self.tara = self.get_tara_default()
        super().save(*args, **kwargs)
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        'por_arribar': ['liberado', 'secuenciado'],
        'liberado': ['secuenciado', 'programado'],
        'secuenciado': ['programado', 'liberado'],
        'programado': ['asignado', 'liberado'],
        'asignado': ['en_ruta', 'programado'],
        'en_ruta': ['entregado', 'asignado'],
        'entregado': ['descargado', 'en_ruta'],
        'descargado': ['vacio'],
        'vacio': ['vacio_en_ruta'],
        'vacio_en_ruta': ['devuelto', 'vacio'],
        'devuelto': [],  # Terminal state
    }
    
    def validar_transicion_estado(self, nuevo_estado):
        """
        Valida si la transición de estado es válida
        
        Args:
            nuevo_estado: El nuevo estado al que se quiere cambiar
            
        Returns:
            tuple: (es_valido: bool, mensaje_error: str or None)
        """
        if self.estado == nuevo_estado:
            return True, None
        
        if nuevo_estado not in dict(self.ESTADOS):
            return False, f"Estado inválido: {nuevo_estado}"
        
        estados_permitidos = self.VALID_TRANSITIONS.get(self.estado, [])
        if nuevo_estado not in estados_permitidos:
            return False, (
                f"Transición no permitida: {self.get_estado_display()} → "
                f"{dict(self.ESTADOS)[nuevo_estado]}. "
                f"Estados permitidos: {', '.join([dict(self.ESTADOS)[e] for e in estados_permitidos])}"
            )
        
        return True, None
    
    def cambiar_estado(self, nuevo_estado, usuario=None, forzar=False):
        """
        Cambia el estado y registra el timestamp correspondiente
        
        Args:
            nuevo_estado: Nuevo estado del contenedor
            usuario: Usuario que realiza el cambio (opcional)
            forzar: Si True, omite la validación de transiciones (usar con precaución)
            
        Raises:
            ValueError: Si la transición no es válida
        """
        from django.db import transaction
        
        # Validar transición
        if not forzar:
            es_valido, mensaje_error = self.validar_transicion_estado(nuevo_estado)
            if not es_valido:
                raise ValueError(mensaje_error)
        
        estado_anterior = self.estado
        
        # Usar transacción para asegurar atomicidad
        with transaction.atomic():
            self.estado = nuevo_estado
            
            # Actualizar timestamp según el nuevo estado
            now = timezone.now()
            timestamp_map = {
                'liberado': 'fecha_liberacion',
                'programado': 'fecha_programacion',
                'asignado': 'fecha_asignacion',
                'en_ruta': 'fecha_inicio_ruta',
                'entregado': 'fecha_entrega',
                'descargado': 'fecha_descarga',
                'vacio': 'fecha_vacio',
                'vacio_en_ruta': 'fecha_vacio_ruta',
                'devuelto': 'fecha_devolucion',
            }
            
            if nuevo_estado in timestamp_map:
                setattr(self, timestamp_map[nuevo_estado], now)
            
            self.save()
            
            # Registrar evento
            from apps.events.models import Event
            Event.objects.create(
                container=self,
                event_type='cambio_estado',
                detalles={
                    'estado_anterior': estado_anterior,
                    'estado_nuevo': nuevo_estado,
                    'forzado': forzar,
                },
                usuario=usuario
            )
        
        return self
