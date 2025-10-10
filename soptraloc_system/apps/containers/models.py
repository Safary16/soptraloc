from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, Company, Vehicle, MovementCode
from apps.drivers.models import Location


class ShippingLine(BaseModel):
    """Líneas navieras"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    contact_info = models.TextField(blank=True, verbose_name="Información de contacto")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name = "Línea Naviera"
        verbose_name_plural = "Líneas Navieras"
        ordering = ['name']


class Vessel(BaseModel):
    """Naves"""
    name = models.CharField(max_length=100, verbose_name="Nombre de la nave")
    imo_number = models.CharField(max_length=20, blank=True, verbose_name="Número IMO")
    shipping_line = models.ForeignKey(ShippingLine, on_delete=models.CASCADE, verbose_name="Línea naviera")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Nave"
        verbose_name_plural = "Naves"
        ordering = ['name']


class Agency(BaseModel):
    """Agencias"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    contact_info = models.TextField(blank=True, verbose_name="Información de contacto")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Agencia"
        verbose_name_plural = "Agencias"
        ordering = ['name']


class Container(BaseModel):
    """Modelo principal para contenedores - Extendido para importaciones."""
    CONTAINER_TYPES = [
        ('20ft', '20 pies'),
        ('40ft', '40 pies'),
        ('40hc', '40 pies HC'),
        ('40hr', '40 pies HR'),
        ('40hn', '40 pies HN'),
        ('20st', '20 pies ST'),
        ('40h', '40 pies H'),
        ('45ft', '45 pies'),
        ('reefer', 'Refrigerado'),
        ('tank', 'Tanque'),
        ('flat_rack', 'Flat Rack'),
        ('open_top', 'Open Top'),
    ]
    
    CONTAINER_STATUS = [
        ('available', 'Disponible'),
        ('in_transit', 'En Tránsito'),
        ('loading', 'Cargando'),
        ('unloading', 'Descargando'),
        ('maintenance', 'Mantenimiento'),
        ('damaged', 'Dañado'),
        ('out_of_service', 'Fuera de Servicio'),
        # Estados específicos de importación (ciclo completo)
        ('POR_ARRIBAR', 'Por Arribar'),                    # 1. Nave viene con contenedor
        ('EN_SECUENCIA', 'En Secuencia'),                  # Intermedio
        ('DESCARGADO', 'Descargado'),                      # Descargado en puerto
        ('LIBERADO', 'Liberado'),                          # 2. Liberado por aduana
        ('PROGRAMADO', 'Programado'),                      # 3. Programado para CD
        ('ASIGNADO', 'Asignado'),                          # 4. Con conductor asignado
        ('EN_RUTA', 'En Ruta'),                            # 5. En camino a CD
        ('ARRIBADO', 'Arribado'),                          # 6. Arribado a CD
        ('DESCARGADO_CD', 'Descargado en CD'),             # 7. Descargado en CD
        ('DISPONIBLE_DEVOLUCION', 'Disponible Devolución'), # 8. Listo para devolver
        ('EN_RUTA_DEVOLUCION', 'En Ruta Devolución'),     # 9. Devolviendo a puerto/CCTI
        ('FINALIZADO', 'Finalizado'),                      # 10. Ciclo completo
        ('TRG', 'TRG'),
        ('SECUENCIADO', 'Secuenciado'),
    ]
    
    POSITION_STATUS = [
        ('floor', 'En Piso'),
        ('chassis', 'En Chasis'),
        ('warehouse', 'En Almacén'),
    ]

    SERVICE_TYPE_CHOICES = [
        ('DIRECTO', 'Directo'),
        ('INDIRECTO_DEPOSITO', 'Indirecto Depósito'),
        ('REEFER', 'Reefer'),
    ]
    
    # ===== CAMPOS BÁSICOS EXISTENTES =====
    # Identificación
    container_number = models.CharField(max_length=50, unique=True)
    container_type = models.CharField(max_length=20, choices=CONTAINER_TYPES)
    status = models.CharField(max_length=30, choices=CONTAINER_STATUS, default='available')
    position_status = models.CharField(max_length=20, choices=POSITION_STATUS, default='floor')
    
    # Propietario/Cliente
    owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='containers')
    
    # Especificaciones físicas básicas
    weight_empty = models.DecimalField(max_digits=10, decimal_places=2, help_text="Peso vacío en kg", null=True, blank=True)
    weight_loaded = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Peso cargado en kg")
    max_weight = models.DecimalField(max_digits=10, decimal_places=2, help_text="Peso máximo permitido en kg", null=True, blank=True)
    
    # Ubicación actual
    current_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_containers')
    current_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Información adicional básica
    seal_number = models.CharField(max_length=50, blank=True)
    customs_document = models.CharField(max_length=100, blank=True)
    special_requirements = models.TextField(blank=True)
    
    # ===== CAMPOS ESPECÍFICOS PARA IMPORTACIÓN =====
    # Información de importación
    sequence_id = models.IntegerField(null=True, blank=True, verbose_name="ID Secuencia")
    client = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='import_containers', verbose_name="Cliente")
    port = models.CharField(max_length=50, blank=True, verbose_name="Puerto")
    eta = models.DateField(null=True, blank=True, verbose_name="ETA")
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Nave")
    cargo_description = models.TextField(blank=True, verbose_name="Descripción de carga")
    
    # Pesos específicos de importación
    cargo_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Peso carga")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Peso total")
    
    # Terminal y fechas de liberación
    terminal = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True, related_name='terminal_containers', verbose_name="Terminal")
    release_date = models.DateField(blank=True, null=True, verbose_name="Fecha liberación")
    release_time = models.TimeField(blank=True, null=True, verbose_name="Hora liberación")
    
    # Programación
    scheduled_date = models.DateField(blank=True, null=True, verbose_name="Fecha programación")
    scheduled_time = models.TimeField(blank=True, null=True, verbose_name="Hora programación")
    
    # Arribo en CD
    cd_arrival_date = models.DateField(blank=True, null=True, verbose_name="Fecha arribo CD")
    cd_arrival_time = models.TimeField(blank=True, null=True, verbose_name="Hora arribo CD")
    cd_location = models.CharField(max_length=100, blank=True, verbose_name="CD")
    
    # Descarga (GPS)
    discharge_date = models.DateField(blank=True, null=True, verbose_name="Fecha descarga (GPS)")
    discharge_time = models.TimeField(blank=True, null=True, verbose_name="Hora descarga")
    
    # Devolución
    return_date = models.DateField(blank=True, null=True, verbose_name="Fecha devolución")
    has_eir = models.BooleanField(default=False, verbose_name="EIR")
    
    # Agencia y línea naviera
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Agencia")
    shipping_line = models.ForeignKey(ShippingLine, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Cía Naviera/Línea")
    
    # Información comercial
    deposit_return = models.CharField(max_length=100, blank=True, verbose_name="Dep/Dev")
    free_days = models.IntegerField(default=0, verbose_name="Días libres")
    demurrage_date = models.DateField(blank=True, null=True, verbose_name="Demurrage")
    overtime_2h = models.IntegerField(default=0, verbose_name="Sobreestadía región (x ciclo 2 horas)")
    overtime_4h = models.IntegerField(default=0, verbose_name="Sobreestadía (x ciclo de 4 horas)")
    
    # Almacenaje
    storage_location = models.CharField(max_length=50, blank=True, verbose_name="Almc")
    extra_storage_days = models.IntegerField(default=0, verbose_name="Días extras de almacenaje")
    
    # Chasis
    chassis_status = models.IntegerField(default=0, verbose_name="E.CHASIS")
    
    # Campos para gestión de posición actual
    current_position = models.CharField(
        max_length=30,
        choices=[
            ('EN_PISO', 'En Piso'),
            ('EN_CHASIS', 'En Chasis'),
            ('CCTI', 'CCTI'),
            ('ZEAL', 'ZEAL'),
            ('CLEP', 'CLEP'),
            ('EN_RUTA', 'En Ruta'),
            ('CD_QUILICURA', 'CD Quilicura'),
            ('CD_CAMPOS', 'CD Campos'),
            ('CD_MADERO', 'CD Puerto Madero'),
            ('CD_PENON', 'CD El Peñón'),
            ('DEPOSITO_DEVOLUCION', 'Depósito Devolución'),
        ],
        blank=True,
        verbose_name="Posición Actual"
    )
    
    # Historial de posiciones
    position_updated_at = models.DateTimeField(null=True, blank=True)
    position_updated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='container_position_updates'
    )
    
    # Tipo de servicio
    service_type = models.CharField(
        max_length=30, 
        choices=[
            ('DIRECTO', 'Directo'),
            ('INDIRECTO_DEPOSITO', 'Indirecto con Depósito'),
            ('INDIRECTO_CD', 'Indirecto CD'),
            ('TRANSFERENCIA', 'Transferencia'),
        ],
        verbose_name="Tipo de servicio"
    )
    additional_service = models.CharField(max_length=100, blank=True, verbose_name="Servicio adicional")
    
    # Observaciones
    observation_1 = models.TextField(blank=True, verbose_name="OBS 1")
    observation_2 = models.TextField(blank=True, verbose_name="OBS 2")
    
    # Servicio directo
    direct_service = models.CharField(max_length=50, blank=True, default='', verbose_name="Servicio directo")
    
    # Fechas de actualización
    last_update_date = models.DateField(blank=True, null=True, verbose_name="Fecha actualización")
    last_update_time = models.TimeField(blank=True, null=True, verbose_name="Hora actualización")
    
    # Campos calculados
    calculated_days = models.IntegerField(default=0, verbose_name="Días calculados")
    
    # Conductor asignado
    conductor_asignado = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contenedores_asignados',
        verbose_name="Conductor asignado"
    )
    
    # Tiempos de seguimiento operativo
    tiempo_asignacion = models.DateTimeField(null=True, blank=True, verbose_name="Tiempo de asignación")
    tiempo_inicio_ruta = models.DateTimeField(null=True, blank=True, verbose_name="Tiempo inicio ruta")
    tiempo_llegada = models.DateTimeField(null=True, blank=True, verbose_name="Tiempo de llegada")
    tiempo_descarga = models.DateTimeField(null=True, blank=True, verbose_name="Tiempo de descarga")
    tiempo_finalizacion = models.DateTimeField(null=True, blank=True, verbose_name="Tiempo finalización")
    tiempo_inicio_devolucion = models.DateTimeField(null=True, blank=True, verbose_name="Inicio devolución")
    tiempo_arribo_devolucion = models.DateTimeField(null=True, blank=True, verbose_name="Arribo devolución")
    
    # Duración calculada (en minutos)
    duracion_total = models.IntegerField(null=True, blank=True, verbose_name="Duración total (minutos)")
    duracion_ruta = models.IntegerField(null=True, blank=True, verbose_name="Duración ruta (minutos)")
    duracion_descarga = models.IntegerField(null=True, blank=True, verbose_name="Duración descarga (minutos)")
    duracion_devolucion = models.IntegerField(null=True, blank=True, verbose_name="Duración devolución (minutos)")
    
    # Máquina de estados: transiciones permitidas
    ALLOWED_TRANSITIONS = {
        'available': ['loading', 'maintenance', 'POR_ARRIBAR'],
        'in_transit': ['loading', 'unloading'],
        'loading': ['in_transit', 'available'],
        'unloading': ['available', 'warehouse'],
        'maintenance': ['available', 'damaged', 'out_of_service'],
        'damaged': ['maintenance', 'out_of_service'],
        'out_of_service': ['maintenance'],
        # Flujo de importación
    'POR_ARRIBAR': ['EN_SECUENCIA', 'DESCARGADO', 'LIBERADO', 'PROGRAMADO'],
        'EN_SECUENCIA': ['DESCARGADO'],
        'DESCARGADO': ['LIBERADO', 'TRG'],
        'TRG': ['LIBERADO', 'SECUENCIADO'],
        'SECUENCIADO': ['LIBERADO'],
        'LIBERADO': ['PROGRAMADO'],
        'PROGRAMADO': ['ASIGNADO'],
        'ASIGNADO': ['EN_RUTA', 'PROGRAMADO'],  # Puede volver a PROGRAMADO si se cancela
        'EN_RUTA': ['ARRIBADO'],
        'ARRIBADO': ['DESCARGADO_CD'],
        'DESCARGADO_CD': ['DISPONIBLE_DEVOLUCION'],
        'DISPONIBLE_DEVOLUCION': ['EN_RUTA_DEVOLUCION'],
        'EN_RUTA_DEVOLUCION': ['FINALIZADO'],
        'FINALIZADO': [],  # Estado terminal
    }
    
    def can_transition_to(self, current_status, new_status):
        """Verifica si la transición de estado es válida."""
        if not current_status:  # Si es nuevo, cualquier estado inicial es válido
            return True

        if current_status == new_status:
            return True
        
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])
        return new_status in allowed
    
    def validate_status_transition(self, new_status, *, from_status=None):
        """Valida y retorna error si la transición no es permitida."""
        origin_status = from_status if from_status is not None else self.status

        if not self.can_transition_to(origin_status, new_status):
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f"Transición no permitida: {origin_status or 'SIN_ESTADO'} → {new_status}. "
                f"Estados permitidos desde {origin_status or 'SIN_ESTADO'}: {', '.join(self.ALLOWED_TRANSITIONS.get(origin_status, []))}"
            )
    
    def save(self, *args, **kwargs):
        # Validar transición de estado si está cambiando
        if self.pk:  # Solo para objetos existentes
            try:
                old_instance = Container.objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    # Validar transición
                    self.validate_status_transition(self.status, from_status=old_instance.status)
            except Container.DoesNotExist:
                pass  # Objeto nuevo, no validar
        
        # Calcular días si hay fechas disponibles
        if self.release_date and self.cd_arrival_date:
            delta = self.cd_arrival_date - self.release_date
            self.calculated_days = delta.days
            
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Contenedor'
        verbose_name_plural = 'Contenedores'
        ordering = ['sequence_id', 'container_number']
        indexes = [
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['scheduled_date'], name='idx_scheduled'),
            models.Index(fields=['conductor_asignado'], name='idx_driver'),
            models.Index(fields=['container_number'], name='idx_number'),
            models.Index(fields=['status', 'scheduled_date'], name='idx_status_date'),
            models.Index(fields=['conductor_asignado', 'status'], name='idx_driver_status'),
        ]
        
    def __str__(self):
        if self.client:
            return f"{self.container_number} - {self.client.name}"
        return f"{self.container_number} - {self.get_container_type_display()}"
    
    def get_current_position(self):
        """Retorna la posición actual del contenedor."""
        if self.current_vehicle:
            return f"En chasis {self.current_vehicle.plate}"
        elif self.current_location:
            return f"En {self.current_location.name}"
        else:
            return "Ubicación no definida"
    
    # Propiedades específicas para importación
    def is_import_container(self):
        """Verifica si es un contenedor de importación."""
        return self.sequence_id is not None or self.eta is not None
    
    def days_since_release(self):
        """Calcula días desde la liberación."""
        if self.release_date:
            return (timezone.now().date() - self.release_date).days
        return 0
    
    def is_overdue(self):
        """Verifica si está en sobreestadía."""
        if self.demurrage_date:
            return timezone.now().date() > self.demurrage_date
        return False


class ContainerMovement(BaseModel):
    """Registro de movimientos de contenedores."""
    MOVEMENT_TYPES = [
        ('load_chassis', 'Cargar en Chasis'),
        ('unload_chassis', 'Descargar de Chasis'),
        ('transfer_warehouse', 'Transferir a Almacén'),
        ('transfer_location', 'Transferir Ubicación'),
        ('maintenance_in', 'Ingreso a Mantenimiento'),
        ('maintenance_out', 'Salida de Mantenimiento'),
        ('import', 'Importación'),
        ('export', 'Exportación'),
        # Tipos específicos de importación
        ('PICKUP', 'Retiro'),
        ('DELIVERY', 'Entrega'),
        ('STORAGE_IN', 'Ingreso a almacén'),
        ('STORAGE_OUT', 'Salida de almacén'),
        ('CHASSIS_MOUNT', 'Montaje en chasis'),
        ('CHASSIS_DISMOUNT', 'Desmontaje de chasis'),
        ('TRANSFER', 'Transferencia'),
    ]
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='container_movements')
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    movement_code = models.ForeignKey(MovementCode, on_delete=models.CASCADE, related_name='container_movements')
    
    # Ubicaciones origen y destino
    from_location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='container_movements_from'
    )
    to_location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='container_movements_to'
    )
    
    # Vehículos origen y destino
    from_vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='container_movements_from'
    )
    to_vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='container_movements_to'
    )
    
    # Información del movimiento
    movement_date = models.DateTimeField(default=timezone.now)
    scheduled_datetime = models.DateTimeField(null=True, blank=True, verbose_name="Fecha/hora programada")
    actual_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Fecha/hora real")
    notes = models.TextField(blank=True)
    weight_at_movement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_completed = models.BooleanField(default=False, verbose_name="Completado")
    
    class Meta:
        verbose_name = 'Movimiento de Contenedor'
        verbose_name_plural = 'Movimientos de Contenedores'
        ordering = ['-movement_date']
        
    def __str__(self):
        return f"{self.container.container_number} - {self.get_movement_type_display()} - {self.movement_date.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Actualiza la posición del contenedor al guardar el movimiento."""
        super().save(*args, **kwargs)
        
        # Actualizar posición del contenedor
        if self.movement_type in ['load_chassis', 'CHASSIS_MOUNT']:
            self.container.position_status = 'chassis'
            self.container.current_vehicle = self.to_vehicle
            self.container.current_location = None
        elif self.movement_type in ['unload_chassis', 'CHASSIS_DISMOUNT']:
            self.container.position_status = 'floor'
            self.container.current_vehicle = None
            self.container.current_location = self.to_location
        elif self.movement_type in ['transfer_warehouse', 'STORAGE_IN']:
            self.container.position_status = 'warehouse'
            self.container.current_location = self.to_location
            self.container.current_vehicle = None
        elif self.movement_type in ['transfer_location', 'TRANSFER']:
            self.container.current_location = self.to_location
        
        # Marcar como completado si tiene fecha real
        if self.actual_datetime and not self.is_completed:
            self.is_completed = True
            super().save(update_fields=['is_completed'])
        
        self.container.save()


class ContainerDocument(BaseModel):
    """Documentos asociados a contenedores."""
    DOCUMENT_TYPES = [
        ('bill_of_lading', 'Conocimiento de Embarque'),
        ('packing_list', 'Lista de Empaque'),
        ('invoice', 'Factura'),
        ('certificate', 'Certificado'),
        ('customs', 'Documento Aduanero'),
        ('inspection', 'Inspección'),
        ('other', 'Otro'),
    ]
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100)
    document_date = models.DateField()
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='container_documents/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Documento de Contenedor'
        verbose_name_plural = 'Documentos de Contenedores'
        
    def __str__(self):
        return f"{self.container.container_number} - {self.get_document_type_display()} - {self.document_number}"


class ContainerInspection(BaseModel):
    """Inspecciones de contenedores."""
    INSPECTION_TYPES = [
        ('entry', 'Ingreso'),
        ('exit', 'Salida'),
        ('maintenance', 'Mantenimiento'),
        ('damage', 'Daños'),
        ('customs', 'Aduanera'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excelente'),
        ('good', 'Bueno'),
        ('fair', 'Regular'),
        ('poor', 'Malo'),
        ('damaged', 'Dañado'),
    ]
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='inspections')
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPES)
    inspection_date = models.DateTimeField(default=timezone.now)
    inspector_name = models.CharField(max_length=200)
    
    # Condiciones
    overall_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    exterior_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    interior_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    
    # Observaciones
    observations = models.TextField(blank=True)
    damage_description = models.TextField(blank=True)
    repair_required = models.BooleanField(default=False)
    repair_notes = models.TextField(blank=True)
    
    # Archivos adjuntos
    photos = models.FileField(upload_to='container_inspections/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Inspección de Contenedor'
        verbose_name_plural = 'Inspecciones de Contenedores'
        ordering = ['-inspection_date']
        
    def __str__(self):
        return f"{self.container.container_number} - {self.get_inspection_type_display()} - {self.inspection_date.strftime('%d/%m/%Y')}"


# ===== NUEVOS MODELOS REFACTORIZADOS =====

class ContainerSpec(BaseModel):
    """
    Especificaciones físicas del contenedor.
    Separado para reducir complejidad de Container model.
    """
    container = models.OneToOneField(
        Container,
        on_delete=models.CASCADE,
        related_name='spec',
        verbose_name="Contenedor"
    )
    
    # Pesos
    weight_empty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Peso vacío en kg"
    )
    weight_loaded = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Peso cargado en kg"
    )
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Peso máximo permitido en kg"
    )
    
    # Información adicional
    seal_number = models.CharField(max_length=50, blank=True, verbose_name="Número de sello")
    special_requirements = models.TextField(blank=True, verbose_name="Requerimientos especiales")
    
    class Meta:
        verbose_name = "Especificación de Contenedor"
        verbose_name_plural = "Especificaciones de Contenedores"
    
    def __str__(self):
        return f"Specs: {self.container.container_number}"


class ContainerImportInfo(BaseModel):
    """
    Información específica de contenedores de importación.
    Separado para no contaminar Container con campos de importación.
    """
    container = models.OneToOneField(
        Container,
        on_delete=models.CASCADE,
        related_name='import_info',
        verbose_name="Contenedor"
    )
    
    # Información de importación
    sequence_id = models.IntegerField(null=True, blank=True, verbose_name="ID Secuencia")
    port = models.CharField(max_length=50, blank=True, verbose_name="Puerto")
    eta = models.DateField(null=True, blank=True, verbose_name="ETA (Estimated Time of Arrival)")
    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Nave"
    )
    cargo_description = models.TextField(blank=True, verbose_name="Descripción de carga")
    
    # Pesos específicos de importación
    cargo_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso carga"
    )
    total_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso total"
    )
    
    # Terminal
    terminal = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='import_containers',
        verbose_name="Terminal"
    )
    
    class Meta:
        verbose_name = "Información de Importación"
        verbose_name_plural = "Información de Importaciones"
        indexes = [
            models.Index(fields=['sequence_id'], name='containers_seq_idx'),
            models.Index(fields=['eta'], name='containers_eta_idx'),
        ]
    
    def __str__(self):
        return f"Import Info: {self.container.container_number}"


class ContainerSchedule(BaseModel):
    """
    Programación y tiempos del contenedor.
    Separado para facilitar queries de programación.
    """
    container = models.OneToOneField(
        Container,
        on_delete=models.CASCADE,
        related_name='schedule',
        verbose_name="Contenedor"
    )
    
    # Fechas de liberación
    release_date = models.DateField(null=True, blank=True, verbose_name="Fecha liberación")
    release_time = models.TimeField(null=True, blank=True, verbose_name="Hora liberación")
    
    # Fechas de programación
    scheduled_date = models.DateField(null=True, blank=True, verbose_name="Fecha programación")
    scheduled_time = models.TimeField(null=True, blank=True, verbose_name="Hora programación")
    
    class Meta:
        verbose_name = "Programación de Contenedor"
        verbose_name_plural = "Programaciones de Contenedores"
        indexes = [
            models.Index(fields=['release_date'], name='containers_rel_date_idx'),
            models.Index(fields=['scheduled_date'], name='containers_sch_date_idx'),
        ]
    
    def __str__(self):
        return f"Schedule: {self.container.container_number}"
    
    def get_release_datetime(self):
        """Retorna datetime combinando release_date + release_time"""
        if self.release_date:
            from datetime import datetime, time as dt_time
            time_obj = self.release_time or dt_time(0, 0)
            return datetime.combine(self.release_date, time_obj)
        return None
    
    def get_scheduled_datetime(self):
        """Retorna datetime combinando scheduled_date + scheduled_time"""
        if self.scheduled_date:
            from datetime import datetime, time as dt_time
            time_obj = self.scheduled_time or dt_time(0, 0)
            return datetime.combine(self.scheduled_date, time_obj)
        return None