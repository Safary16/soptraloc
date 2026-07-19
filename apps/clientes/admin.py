from django.contrib import admin

from .models import ClienteEmpresa, ClienteUsuario, SituacionCliente, SolicitudHorario


@admin.register(ClienteEmpresa)
class ClienteEmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'activo', 'capacidad_por_slot', 'hora_inicio_recepcion', 'hora_fin_recepcion')
    search_fields = ('nombre', 'rut')


@admin.register(ClienteUsuario)
class ClienteUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'empresa', 'puede_solicitar')
    list_filter = ('empresa', 'puede_solicitar')
    autocomplete_fields = ('user', 'empresa')


@admin.register(SituacionCliente)
class SituacionClienteAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'asunto', 'categoria', 'prioridad', 'estado', 'created_at')
    list_filter = ('empresa', 'categoria', 'prioridad', 'estado')
    search_fields = ('asunto', 'mensaje', 'container__container_id')


@admin.register(SolicitudHorario)
class SolicitudHorarioAdmin(admin.ModelAdmin):
    list_display = ('container', 'empresa', 'inicio_solicitado', 'modo', 'estado', 'solicitante')
    list_filter = ('estado', 'modo', 'empresa')
    search_fields = ('container__container_id', 'empresa__nombre', 'solicitante__username')
    readonly_fields = ('recomendacion_snapshot', 'created_at', 'updated_at')
