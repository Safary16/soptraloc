"""Views para importación inicial y diagnóstico del sistema."""
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import JsonResponse
from django.shortcuts import render

from apps.containers.models import Container

import logging
import os
import tempfile

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_default_import_user():
    """Obtiene (o crea) el usuario que se utilizará como owner en la importación."""
    user = User.objects.filter(is_superuser=True).order_by('id').first()
    if user:
        return user

    # Si no existe, crea un administrador por defecto (coincide con force_create_admin)
    user = User.objects.create_superuser(
        username='admin',
        email='admin@soptraloc.com',
        password='1234'
    )
    logger.info("Se creó un superusuario por defecto para la importación (admin / 1234)")
    return user


def setup_initial_view(request):
    """Vista pública para importar datos desde Excel o CSV."""
    total_containers = Container.objects.count()
    context = {
        'total_containers': total_containers,
        'has_data': total_containers > 0,
    }

    if request.method == 'GET':
        return render(request, 'containers/setup_initial.html', context)
    
    # POST - Procesar archivo
    if request.method == 'POST':
        mode = request.POST.get('mode', 'append')
        truncate_before_import = mode == 'replace'

        if 'file' not in request.FILES:
            logger.warning("Setup inicial: No se subió archivo")
            return JsonResponse({
                'success': False,
                'error': 'No se subió ningún archivo'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        logger.info(f"Setup inicial: Procesando archivo {uploaded_file.name} ({file_extension})")
        
        if file_extension not in ['.csv', '.xlsx', '.xls']:
            logger.warning(f"Setup inicial: Formato inválido {file_extension}")
            return JsonResponse({
                'success': False,
                'error': 'Solo se aceptan archivos CSV o Excel (.xlsx, .xls)'
            }, status=400)
        
        # Validar tamaño de archivo (máx 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            logger.warning(f"Setup inicial: Archivo muy grande ({uploaded_file.size} bytes)")
            return JsonResponse({
                'success': False,
                'error': 'El archivo es demasiado grande (máximo 10MB)'
            }, status=400)
        
        try:
            import_user = _get_default_import_user()
            logger.info("Setup inicial: Usando usuario %s (ID %s) para la importación", import_user.username, import_user.id)

            # Guardar archivo temporal
            logger.info("Setup inicial: Guardando archivo temporal")
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            logger.info(f"Setup inicial: Archivo guardado en {tmp_path}")
            
            # Ejecutar comando de importación
            logger.info(f"Setup inicial: Ejecutando comando de importación")
            before_count = Container.objects.count()

            command_args = [tmp_path, '--user', str(import_user.id)]
            if truncate_before_import:
                command_args.insert(1, '--truncate')

            if file_extension == '.csv':
                call_command('import_containers', *command_args)
            else:
                # Para Excel usar el importador correspondiente
                call_command('import_containers_walmart', *command_args)
            
            logger.info("Setup inicial: Importación completada")
            
            # Eliminar archivo temporal
            os.unlink(tmp_path)
            logger.info("Setup inicial: Archivo temporal eliminado")
            
            # Normalizar estados
            try:
                logger.info("Setup inicial: Normalizando estados")
                call_command('normalize_container_statuses')
                logger.info("Setup inicial: Estados normalizados")
            except Exception as e:
                logger.warning(f"Setup inicial: Error al normalizar estados (no crítico): {e}")
            
            total_imported = Container.objects.count()
            created_delta = max(total_imported - before_count, 0)
            logger.info(f"Setup inicial: ✅ {total_imported} contenedores importados exitosamente")
            
            context.update({
                'total_containers': total_imported,
                'has_data': total_imported > 0,
            })

            return JsonResponse({
                'success': True,
                'message': f'Se importaron {total_imported} contenedores exitosamente',
                'total': total_imported,
                'created_delta': created_delta,
                'mode': mode,
                'redirect': '/admin/'  # Redirigir al admin después
            })
            
        except Exception as e:
            logger.error(f"Setup inicial: ❌ Error al importar: {str(e)}", exc_info=True)
            
            # Limpiar archivo temporal si existe
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                    logger.info("Setup inicial: Archivo temporal eliminado tras error")
                except Exception as cleanup_error:
                    logger.warning(f"Setup inicial: Error al limpiar archivo temporal: {cleanup_error}")
            
            return JsonResponse({
                'success': False,
                'error': f'Error al importar: {str(e)}'
            }, status=500)


def check_system_status(request):
    """API para verificar si el sistema necesita inicialización"""
    needs_setup = not Container.objects.exists()
    
    return JsonResponse({
        'needs_setup': needs_setup,
        'total_containers': Container.objects.count(),
        'has_users': User.objects.exists(),
    })
