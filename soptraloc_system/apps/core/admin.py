from django.contrib import admin
from .models import Company, Driver, Vehicle, Location, MovementCode


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'rut', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'rut', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'rut')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'license_number', 'phone', 'is_available', 'is_active')
    list_filter = ('is_available', 'is_active', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'license_number', 'phone')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Conductor', {
            'fields': ('user', 'license_number', 'license_type')
        }),
        ('Contacto', {
            'fields': ('phone', 'emergency_contact')
        }),
        ('Disponibilidad', {
            'fields': ('is_available', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Nombre Completo'
    
    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'vehicle_type', 'brand', 'model', 'year', 'status', 'is_active')
    list_filter = ('vehicle_type', 'status', 'brand', 'is_active', 'created_at')
    search_fields = ('plate', 'brand', 'model')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Vehículo', {
            'fields': ('plate', 'vehicle_type', 'brand', 'model', 'year')
        }),
        ('Especificaciones', {
            'fields': ('capacity', 'fuel_type', 'vin')
        }),
        ('Estado', {
            'fields': ('status', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'region', 'country', 'is_active')
    list_filter = ('city', 'region', 'country', 'is_active', 'created_at')
    search_fields = ('name', 'city', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Ubicación', {
            'fields': ('name', 'code')
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'region', 'country', 'postal_code')
        }),
        ('Coordenadas', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"


@admin.register(MovementCode)
class MovementCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'movement_type', 'used_at', 'is_active', 'created_at')
    list_filter = ('movement_type', 'used_at', 'is_active', 'created_at')
    search_fields = ('code', 'movement_type')
    readonly_fields = ('id', 'created_at', 'updated_at', 'used_at')
    
    fieldsets = (
        ('Código de Movimiento', {
            'fields': ('code', 'movement_type')
        }),
        ('Uso', {
            'fields': ('used_at', 'used_by')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    class Meta:
        verbose_name = "Código de Movimiento"
        verbose_name_plural = "Códigos de Movimiento"