import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Modelo base con campos comunes para todas las entidades."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Company(BaseModel):
    """Modelo para empresas/clientes."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    rut = models.CharField(max_length=12, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        
    def __str__(self):
        return f"{self.name} ({self.code})"


class Vehicle(BaseModel):
    """Modelo para vehículos/chasis."""
    VEHICLE_TYPES = [
        ('truck', 'Camión'),
        ('chassis', 'Chasis'),
        ('trailer', 'Remolque'),
    ]
    
    VEHICLE_STATUS = [
        ('available', 'Disponible'),
        ('in_use', 'En Uso'),
        ('maintenance', 'Mantenimiento'),
        ('out_of_service', 'Fuera de Servicio'),
    ]
    
    plate = models.CharField(max_length=10, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=VEHICLE_STATUS, default='available')
    max_capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Capacidad máxima en toneladas")
    
    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        
    def __str__(self):
        return f"{self.plate} - {self.get_vehicle_type_display()}"


class MovementCode(BaseModel):
    """Modelo para códigos únicos de movimiento."""
    code = models.CharField(max_length=50, unique=True)
    movement_type = models.CharField(max_length=50)  # 'load', 'unload', 'transfer'
    description = models.TextField(blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Código de Movimiento'
        verbose_name_plural = 'Códigos de Movimiento'
        
    def __str__(self):
        return f"{self.code} - {self.movement_type}"
    
    def use_code(self):
        """Marca el código como usado."""
        self.used_at = timezone.now()
        self.save()
        
    @classmethod
    def generate_code(cls, movement_type):
        """Genera un nuevo código único para un tipo de movimiento."""
        import random
        import string
        
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        type_prefix = {
            'load': 'LD',
            'unload': 'UL', 
            'transfer': 'TR'
        }.get(movement_type, 'MV')
        
        code = f"{type_prefix}-{timestamp}-{random_suffix}"
        
        return cls.objects.create(
            code=code,
            movement_type=movement_type
        )