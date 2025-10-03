"""
Vista pública para importar datos iniciales al sistema
NO REQUIERE AUTENTICACIÓN - Solo para setup inicial
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.contrib.auth.models import User
from apps.containers.models import Container
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


def setup_initial_view(request):
    """
    Vista pública para importar datos iniciales
    GET: Muestra formulario
    POST: Procesa el archivo Excel/CSV
    """
    # Si ya hay contenedores, redirigir al dashboard
    if Container.objects.exists():
        return render(request, 'containers/setup_complete.html', {
            'total_containers': Container.objects.count(),
            'message': 'El sistema ya tiene contenedores cargados.'
        })
    
    if request.method == 'GET':
        return render(request, 'containers/setup_initial.html')
    
    # POST - Procesar archivo
    if request.method == 'POST':
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
            # Guardar archivo temporal
            logger.info("Setup inicial: Guardando archivo temporal")
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            logger.info(f"Setup inicial: Archivo guardado en {tmp_path}")
            
            # Ejecutar comando de importación
            logger.info(f"Setup inicial: Ejecutando comando de importación")
            if file_extension == '.csv':
                call_command('import_containers', tmp_path, '--truncate', '--user', '1')
            else:
                # Para Excel usar el importador correspondiente
                call_command('import_containers_walmart', tmp_path, '--truncate', '--user', '1')
            
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
            logger.info(f"Setup inicial: ✅ {total_imported} contenedores importados exitosamente")
            
            return JsonResponse({
                'success': True,
                'message': f'Se importaron {total_imported} contenedores exitosamente',
                'total': total_imported,
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
