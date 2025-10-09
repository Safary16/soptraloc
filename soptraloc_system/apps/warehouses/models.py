from django.db import models
from apps.core.models import BaseModel, Company
from apps.drivers.models import Location
from apps.containers.models import Container


class Warehouse(BaseModel):
    """Modelo para almacenes."""
    WAREHOUSE_TYPES = [
        ('container_yard', 'Patio de Contenedores'),
        ('covered', 'Cubierto'),
        ('open_air', 'Aire Libre'),
        ('refrigerated', 'Refrigerado'),
        ('hazardous', 'Materiales Peligrosos'),
        ('customs', 'Zona Aduanera'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    warehouse_type = models.CharField(max_length=30, choices=WAREHOUSE_TYPES)
    location = models.OneToOneField(Location, on_delete=models.CASCADE)
    manager_company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='managed_warehouses'
    )
    
    # Capacidad
    total_capacity = models.IntegerField(help_text="Capacidad total en TEU")
    current_occupancy = models.IntegerField(default=0, help_text="Ocupación actual en TEU")
    
    # Especificaciones técnicas
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_height_m = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    has_crane = models.BooleanField(default=False)
    has_power = models.BooleanField(default=True)
    has_security = models.BooleanField(default=True)
    
    # Horarios de operación
    operating_hours_start = models.TimeField()
    operating_hours_end = models.TimeField()
    operates_weekends = models.BooleanField(default=False)
    
    # Contacto
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    
    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def available_capacity(self):
        """Capacidad disponible."""
        return self.total_capacity - self.current_occupancy
    
    @property
    def occupancy_percentage(self):
        """Porcentaje de ocupación."""
        if self.total_capacity == 0:
            return 0
        return (self.current_occupancy / self.total_capacity) * 100
    
    def update_occupancy(self):
        """Actualiza la ocupación actual basada en los contenedores presentes."""
        containers_count = self.stock_items.filter(
            container__position_status='warehouse'
        ).count()
        self.current_occupancy = containers_count
        self.save()


class WarehouseZone(BaseModel):
    """Zonas dentro de un almacén."""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='zones')
    zone_code = models.CharField(max_length=20)
    zone_name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(help_text="Capacidad en TEU")
    current_occupancy = models.IntegerField(default=0)
    
    # Características especiales
    is_refrigerated = models.BooleanField(default=False)
    is_covered = models.BooleanField(default=True)
    is_hazardous_allowed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Zona de Almacén'
        verbose_name_plural = 'Zonas de Almacén'
        unique_together = ['warehouse', 'zone_code']
        
    def __str__(self):
        return f"{self.warehouse.name} - {self.zone_code} ({self.zone_name})"
    
    @property
    def available_capacity(self):
        return self.capacity - self.current_occupancy


class WarehouseStock(BaseModel):
    """Stock de contenedores en almacén."""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    zone = models.ForeignKey(WarehouseZone, on_delete=models.CASCADE, null=True, blank=True)
    container = models.OneToOneField(Container, on_delete=models.CASCADE)
    
    # Ubicación específica
    row = models.CharField(max_length=10, blank=True)
    column = models.CharField(max_length=10, blank=True)
    stack_position = models.IntegerField(default=1, help_text="Posición en la pila (1 = abajo)")
    
    # Fechas
    entry_date = models.DateTimeField()
    expected_exit_date = models.DateTimeField(null=True, blank=True)
    actual_exit_date = models.DateTimeField(null=True, blank=True)
    
    # Estado
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True)
    
    # Observaciones
    special_handling = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Stock de Almacén'
        verbose_name_plural = 'Stock de Almacenes'
        unique_together = ['warehouse', 'container']
        
    def __str__(self):
        location_str = f"{self.row}-{self.column}-{self.stack_position}" if self.row else "Sin ubicación específica"
        return f"{self.container.container_number} en {self.warehouse.name} ({location_str})"
    
    def save(self, *args, **kwargs):
        """Actualiza la ocupación del almacén y zona al guardar."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and not self.actual_exit_date:
            # Incrementar ocupación
            self.warehouse.current_occupancy += 1
            self.warehouse.save()
            
            if self.zone:
                self.zone.current_occupancy += 1
                self.zone.save()
    
    def mark_exit(self):
        """Marca la salida del contenedor del almacén."""
        if not self.actual_exit_date:
            from django.utils import timezone
            self.actual_exit_date = timezone.now()
            self.save()
            
            # Decrementar ocupación
            self.warehouse.current_occupancy -= 1
            self.warehouse.save()
            
            if self.zone:
                self.zone.current_occupancy -= 1
                self.zone.save()


class WarehouseOperation(BaseModel):
    """Operaciones realizadas en el almacén."""
    OPERATION_TYPES = [
        ('entry', 'Ingreso'),
        ('exit', 'Salida'),
        ('relocation', 'Reubicación'),
        ('inspection', 'Inspección'),
        ('maintenance', 'Mantenimiento'),
        ('inventory', 'Inventario'),
    ]
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='operations')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='warehouse_operations')
    
    # Ubicaciones
    from_zone = models.ForeignKey(
        WarehouseZone, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='operations_from'
    )
    to_zone = models.ForeignKey(
        WarehouseZone, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='operations_to'
    )
    
    # Detalles de la operación
    operation_date = models.DateTimeField()
    operator_name = models.CharField(max_length=200)
    equipment_used = models.CharField(max_length=200, blank=True)
    
    # Tiempos
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Observaciones
    notes = models.TextField(blank=True)
    issues_found = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Operación de Almacén'
        verbose_name_plural = 'Operaciones de Almacén'
        ordering = ['-operation_date']
        
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.container.container_number} - {self.operation_date.strftime('%d/%m/%Y')}"
    
    @property
    def duration_minutes(self):
        """Duración de la operación en minutos."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None


class WarehouseReservation(BaseModel):
    """Reservas de espacio en almacén."""
    RESERVATION_STATUS = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('active', 'Activa'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='reservations')
    zone = models.ForeignKey(WarehouseZone, on_delete=models.CASCADE, null=True, blank=True)
    client_company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Detalles de la reserva
    reservation_code = models.CharField(max_length=50, unique=True)
    container_count = models.IntegerField()
    container_types = models.JSONField(default=list, help_text="Tipos de contenedores a reservar")
    
    # Fechas
    reservation_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Estado
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='pending')
    
    # Observaciones
    special_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Reserva de Almacén'
        verbose_name_plural = 'Reservas de Almacén'
        ordering = ['-reservation_date']
        
    def __str__(self):
        return f"Reserva {self.reservation_code} - {self.client_company.name}"