from django.contrib import admin
from .models import Warehouse, WarehouseZone, WarehouseStock, WarehouseOperation, WarehouseReservation


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'warehouse_type', 'total_capacity', 'current_occupancy',
        'occupancy_percentage', 'manager_company', 'is_active'
    )
    list_filter = ('warehouse_type', 'manager_company', 'has_crane', 'has_security', 'is_active')
    search_fields = ('name', 'code', 'contact_email', 'contact_phone')
    readonly_fields = ('id', 'created_at', 'updated_at', 'current_occupancy', 'occupancy_percentage')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'warehouse_type', 'location', 'manager_company')
        }),
        ('Capacidad', {
            'fields': ('total_capacity', 'current_occupancy', 'occupancy_percentage')
        }),
        ('Especificaciones', {
            'fields': ('area_m2', 'max_height_m', 'has_crane', 'has_power', 'has_security')
        }),
        ('Horarios', {
            'fields': ('operating_hours_start', 'operating_hours_end', 'operates_weekends')
        }),
        ('Contacto', {
            'fields': ('contact_phone', 'contact_email')
        }),
        ('Auditoría', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )


@admin.register(WarehouseZone)
class WarehouseZoneAdmin(admin.ModelAdmin):
    list_display = (
        'warehouse', 'zone_code', 'zone_name', 'capacity', 'current_occupancy',
        'available_capacity', 'is_refrigerated', 'is_active'
    )
    list_filter = ('warehouse', 'is_refrigerated', 'is_covered', 'is_hazardous_allowed', 'is_active')
    search_fields = ('zone_code', 'zone_name', 'warehouse__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'current_occupancy', 'available_capacity')


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'warehouse', 'zone', 'row', 'column', 'stack_position',
        'entry_date', 'expected_exit_date', 'is_blocked'
    )
    list_filter = ('warehouse', 'zone', 'is_blocked', 'entry_date', 'actual_exit_date')
    search_fields = ('container__container_number', 'warehouse__name', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'entry_date'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('warehouse', 'zone', 'container')
        }),
        ('Ubicación', {
            'fields': ('row', 'column', 'stack_position')
        }),
        ('Fechas', {
            'fields': ('entry_date', 'expected_exit_date', 'actual_exit_date')
        }),
        ('Estado', {
            'fields': ('is_blocked', 'blocked_reason')
        }),
        ('Observaciones', {
            'fields': ('special_handling', 'notes')
        })
    )


@admin.register(WarehouseOperation)
class WarehouseOperationAdmin(admin.ModelAdmin):
    list_display = (
        'warehouse', 'operation_type', 'container', 'operation_date',
        'operator_name', 'duration_minutes'
    )
    list_filter = ('warehouse', 'operation_type', 'operation_date')
    search_fields = ('container__container_number', 'operator_name', 'warehouse__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'duration_minutes')
    date_hierarchy = 'operation_date'


@admin.register(WarehouseReservation)
class WarehouseReservationAdmin(admin.ModelAdmin):
    list_display = (
        'reservation_code', 'warehouse', 'client_company', 'container_count',
        'start_date', 'end_date', 'status'
    )
    list_filter = ('warehouse', 'status', 'start_date', 'end_date')
    search_fields = ('reservation_code', 'client_company__name', 'warehouse__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'