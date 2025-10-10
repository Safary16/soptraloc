import uuid

from django.contrib.auth.models import User
from django.db import models, IntegrityError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    """Códigos de movimiento predefinidos para movimientos de contenedores."""
    
    MOVEMENT_TYPES = [
        ('transfer', 'Transferencia'),
        ('load', 'Carga'),
        ('unload', 'Descarga'),
        ('return', 'Devolución'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    description = models.TextField(blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Código de Movimiento"
        verbose_name_plural = "Códigos de Movimiento"

    def __str__(self):
        return f"{self.code} - {self.get_movement_type_display()}"

    @staticmethod
    def generate_code(movement_type: str):
        """Genera un código único; evita colisiones en alta concurrencia/tests."""
        prefix = movement_type.upper()
        description = f"Generated code for {movement_type}"
        # Intentar algunas veces por si hay colisión
        for _ in range(5):
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
            suffix = uuid.uuid4().hex[:6].upper()
            code = f"{prefix}_{timestamp}_{suffix}"
            try:
                return MovementCode.objects.create(
                    code=code,
                    movement_type=movement_type,
                    description=description,
                )
            except IntegrityError:
                continue
        # Último intento directo (muy improbable llegar aquí)
        return MovementCode.objects.create(
            code=f"{prefix}_{uuid.uuid4().hex.upper()}",
            movement_type=movement_type,
            description=description,
        )

    def use_code(self):
        """Marca el código como usado registrando timestamp."""
        if not self.used_at:
            self.used_at = timezone.now()


# FASE 6: RBAC - Perfil de usuario con roles
class UserProfile(models.Model):
    """
    Perfil extendido de usuario con información de roles y permisos.
    FASE 6: Sistema de roles y permisos granulares.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('operator', 'Operador'),
        ('viewer', 'Solo Lectura'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name='Rol'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Empresa'
    )
    can_import_data = models.BooleanField(
        default=False,
        verbose_name='Puede importar datos'
    )
    can_assign_drivers = models.BooleanField(
        default=False,
        verbose_name='Puede asignar conductores'
    )
    can_manage_warehouses = models.BooleanField(
        default=False,
        verbose_name='Puede gestionar almacenes'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_user_profile'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        """Verifica si el usuario es administrador."""
        return self.user.is_superuser or self.user.is_staff or self.role == 'admin'
    
    def is_operator(self):
        """Verifica si el usuario es operador."""
        # Operador si tiene rol operator o es admin/staff.
        # Usamos consulta a BD para evitar problemas de caché cuando el rol se actualiza con .update().
        if self.is_admin():
            return True
        try:
            latest_role = type(self).objects.only('role').get(pk=self.pk).role
            return latest_role == 'operator'
        except type(self).DoesNotExist:
            return self.role == 'operator'
    
    def can_modify_data(self):
        """Verifica si el usuario puede modificar datos."""
        # En este sistema, operador y admin pueden modificar datos
        return self.is_operator()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Signal para crear perfil automáticamente cuando se crea un usuario."""
    if created:
        UserProfile.objects.create(user=instance)
    elif hasattr(instance, 'profile'):
        instance.profile.save()


# Monkey-patch User para acceder a role directamente
def get_user_role(self):
    """Helper para acceder al rol del usuario directamente desde User."""
    if hasattr(self, 'profile'):
        return self.profile.role
    return 'viewer'


def get_user_company(self):
    """Helper para acceder a la empresa del usuario."""
    if hasattr(self, 'profile'):
        return self.profile.company
    return None


# Agregar métodos al modelo User
User.add_to_class('get_role', get_user_role)
User.add_to_class('get_company', get_user_company)
User.add_to_class('role', property(get_user_role))


# ============================================================================
# Location - Modelo histórico necesario para migraciones antiguas
# ============================================================================
# Este modelo existe SOLO para que migraciones históricas (containers.0001,
# routing.0001, warehouses.0001) puedan referenciar "core.Location".
# 
# ⚠️ IMPORTANTE: Los campos DEBEN coincidir EXACTAMENTE con drivers.Location
# La tabla 'core_location' es gestionada por drivers.Location (managed=True)
# Este modelo es solo un proxy para migraciones antiguas (managed=False)
#
# Migration path:
# core.0001 → crea location con UUID
# drivers.0002 → convierte UUID → VARCHAR(32) sin guiones
# drivers.0014 → ajusta metadata a CharField
# core.0004 → elimina metadata (DeleteModel) PERO drivers sigue gestionando tabla
class Location(models.Model):
    """
    Modelo histórico de Location para compatibilidad con migraciones antiguas.
    
    ⚠️ NO USAR ESTE MODELO - Importar desde drivers.models:
        from apps.drivers.models import Location
    
    Este modelo es solo un proxy (managed=False) de la tabla real que
    drivers.Location gestiona (managed=True).
    """
    # CRÍTICO: Los campos deben coincidir con drivers.Location
    id = models.CharField(
        max_length=32,
        primary_key=True,
        editable=False,
    )  # VARCHAR(32) sin guiones (UUID.hex)
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)  # Agregado en drivers
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Chile')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NOTA: created_by/updated_by NO existen en drivers.Location
    # No los incluimos aquí para evitar inconsistencias
    
    class Meta:
        db_table = 'core_location'
        managed = False  # NO gestionar - drivers.Location gestiona la tabla real
        app_label = 'core'
        verbose_name = "Ubicación (Histórico)"
        verbose_name_plural = "Ubicaciones (Histórico)"
        
    def __str__(self):
        return self.name
User.add_to_class('company', property(get_user_company))