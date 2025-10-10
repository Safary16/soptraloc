from django.contrib import admin
from .models import Company, Vehicle, MovementCode, UserProfile


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
            'fields': ('max_capacity',)
        }),
        ('Estado', {
            'fields': ('status', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MovementCode)
class MovementCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'movement_type', 'is_active', 'created_at')
    list_filter = ('movement_type', 'is_active', 'created_at')
    search_fields = ('code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Código', {
            'fields': ('code', 'movement_type', 'description')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'company', 'can_import_data', 'can_assign_drivers')
    list_filter = ('role', 'company', 'can_import_data', 'can_assign_drivers')
    search_fields = ('user__username', 'user__email', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'role', 'company')
        }),
        ('Permisos', {
            'fields': ('can_import_data', 'can_assign_drivers', 'can_manage_warehouses')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )