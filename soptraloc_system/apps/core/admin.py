from django.contrib import admin
from .models import Company, Driver, Vehicle, Location, MovementCode


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'rut', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'rut', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'license_number', 'phone', 'is_available', 'is_active')
    list_filter = ('is_available', 'is_active', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'license_number', 'phone')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Nombre Completo'


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'vehicle_type', 'brand', 'model', 'year', 'status', 'is_active')
    list_filter = ('vehicle_type', 'status', 'brand', 'is_active', 'created_at')
    search_fields = ('plate', 'brand', 'model')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'region', 'country', 'is_active')
    list_filter = ('city', 'region', 'country', 'is_active', 'created_at')
    search_fields = ('name', 'city', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(MovementCode)
class MovementCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'movement_type', 'used_at', 'is_active', 'created_at')
    list_filter = ('movement_type', 'used_at', 'is_active', 'created_at')
    search_fields = ('code', 'movement_type')
    readonly_fields = ('id', 'created_at', 'updated_at', 'used_at')