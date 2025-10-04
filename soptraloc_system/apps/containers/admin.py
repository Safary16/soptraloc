from django.contrib import admin
from .models import Container, ContainerMovement, ContainerDocument, ContainerInspection


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = (
        'container_number', 'container_type', 'status', 'position_status', 
        'client', 'vessel', 'eta', 'conductor_asignado', 'is_active'
    )
    list_filter = (
        'container_type', 'status', 'position_status', 'client', 
        'vessel', 'is_active', 'created_at'
    )
    search_fields = ('container_number', 'seal_number', 'customs_document', 'client__name', 'vessel__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('container_number', 'container_type', 'status', 'position_status')
        }),
        ('Información de Importación', {
            'fields': ('sequence_id', 'client', 'port', 'eta', 'vessel', 'cargo_description',
                      'shipping_line', 'agency', 'terminal')
        }),
        ('Liberación y Programación', {
            'fields': ('release_date', 'release_time', 'scheduled_date', 'scheduled_time', 
                      'cd_location', 'demurrage_alert')
        }),
        ('Asignación y Transporte', {
            'fields': ('conductor_asignado', 'current_position', 'position_updated_at')
        }),
        ('Pesos y Especificaciones', {
            'fields': ('cargo_weight', 'total_weight', 'weight_empty', 'max_weight')
        }),
        ('Ubicación Actual', {
            'fields': ('current_location', 'current_vehicle', 'owner_company')
        }),
        ('Información Adicional', {
            'fields': ('seal_number', 'customs_document', 'special_requirements', 
                      'observation_1', 'observation_2', 'additional_service')
        }),
        ('Devolución', {
            'fields': ('deposit_return', 'return_date'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make container_number readonly after creation"""
        if obj:  # Editing existing object
            return self.readonly_fields + ('container_number',)
        return self.readonly_fields


@admin.register(ContainerMovement)
class ContainerMovementAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'movement_type', 'movement_date', 'movement_code', 
        'from_location', 'to_location', 'created_at'
    )
    list_filter = ('movement_type', 'movement_date', 'created_at')
    search_fields = ('container__container_number', 'movement_code__code', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'movement_date'
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('container', 'movement_type', 'movement_code', 'movement_date')
        }),
        ('Ubicaciones', {
            'fields': ('from_location', 'to_location')
        }),
        ('Vehículos', {
            'fields': ('from_vehicle', 'to_vehicle')
        }),
        ('Detalles', {
            'fields': ('weight_at_movement', 'notes')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContainerDocument)
class ContainerDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'document_type', 'document_number', 'document_date', 
        'created_at'
    )
    list_filter = ('document_type', 'document_date', 'created_at')
    search_fields = ('container__container_number', 'document_number', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'document_date'


@admin.register(ContainerInspection)
class ContainerInspectionAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'inspection_type', 'inspection_date', 'inspector_name',
        'overall_condition', 'repair_required', 'created_at'
    )
    list_filter = (
        'inspection_type', 'overall_condition', 'repair_required', 
        'inspection_date', 'created_at'
    )
    search_fields = ('container__container_number', 'inspector_name', 'observations')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'inspection_date'
    
    fieldsets = (
        ('Información de la Inspección', {
            'fields': ('container', 'inspection_type', 'inspection_date', 'inspector_name')
        }),
        ('Condiciones', {
            'fields': ('overall_condition', 'exterior_condition', 'interior_condition')
        }),
        ('Observaciones', {
            'fields': ('observations', 'damage_description')
        }),
        ('Reparaciones', {
            'fields': ('repair_required', 'repair_notes')
        }),
        ('Archivos', {
            'fields': ('photos',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )