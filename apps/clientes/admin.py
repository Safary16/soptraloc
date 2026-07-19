from django.contrib import admin

from .models import ClienteEmpresa, ClienteUsuario, SolicitudHorario


@admin.register(ClienteEmpresa)
class ClienteEmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'activo', 'capacidad_por_slot', 'hora_inicio_recepcion', 'hora_fin_recepcion')
    search_fields = ('nombre', 'rut')


@admin.register(ClienteUsuario)
class ClienteUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'empresa', 'puede_solicitar')
    list_filter = ('empresa', 'puede_solicitar')
    autocomplete_fields = ('user', 'empresa')


@admin.register(SolicitudHorario)
class SolicitudHorarioAdmin(admin.ModelAdmin):
    list_display = ('container', 'empresa', 'inicio_solicitado', 'modo', 'estado', 'solicitante')
    list_filter = ('estado', 'modo', 'empresa')
    search_fields = ('container__container_id', 'empresa__nombre', 'solicitante__username')
    readonly_fields = ('recomendacion_snapshot', 'created_at', 'updated_at')
