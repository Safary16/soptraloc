# Excel Upload Fix - Error Desconocido

## Problema Original
Los usuarios reportaban un "error desconocido" al intentar subir archivos Excel a través de la interfaz web en `/importar/`.

## Causa Raíz
Se encontraron dos problemas principales:

### 1. Endpoint de Conductores (Drivers)
- **Problema**: El template HTML intentaba llamar a `/api/drivers/import-excel/` pero el endpoint real era `import_conductores`
- **Resultado**: Error 404 (Not Found) que se mostraba como "error desconocido" en el frontend

### 2. Endpoint de Programaciones Faltante
- **Problema**: El template HTML intentaba llamar a `/api/programaciones/import-excel/` pero este endpoint no existía en el código
- **Resultado**: Error 404 (Not Found) que se mostraba como "error desconocido" en el frontend

### 3. Campos Incorrectos en Importador
- **Problema**: El `ConductorImporter` usaba nombres de campos que no existían en el modelo `Driver` (`vehiculo_patente`, `disponible`)
- **Resultado**: Errores al procesar los archivos Excel

## Solución Implementada

### Cambios en `apps/drivers/views.py`
```python
# Se agregó un nuevo endpoint alias que coincide con el URL del template
@action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='import-excel')
def import_excel(self, request):
    """
    Alias for import_conductores to match the frontend URL pattern
    """
    return self.import_conductores(request)
```

### Cambios en `apps/programaciones/views.py`
```python
# Se creó un nuevo endpoint completo para importar programaciones
@action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='import-excel')
def import_excel(self, request):
    """
    Importa programaciones desde Excel
    Crea programaciones y actualiza contenedores a 'programado'
    """
    # ... implementación completa con manejo de archivos y errores
```

### Cambios en `apps/drivers/importers/__init__.py`
```python
# Se corrigieron los nombres de campos para que coincidan con el modelo Driver
driver, created = Driver.objects.get_or_create(
    nombre=nombre,
    defaults={
        'rut': rut or '',
        'telefono': telefono or '',
        'presente': presente,
        'activo': True,  # En lugar de 'disponible'
        'max_entregas_dia': 8,
    }
)
```

## Endpoints Disponibles Ahora

### Conductores/Drivers
- **URL**: `/api/drivers/import-excel/`
- **Método**: POST
- **Formato**: multipart/form-data con campo `file`
- **Archivo**: Excel (.xlsx, .xls) con columnas:
  - N°
  - Conductor
  - PPU
  - RUT
  - Teléfono
  - ASISTENCIA 06-10

### Programaciones
- **URL**: `/api/programaciones/import-excel/`
- **Método**: POST
- **Formato**: multipart/form-data con campo `file`
- **Archivo**: Excel (.xlsx, .xls) con columnas:
  - CONTENEDOR / Container ID
  - FECHA DE PROGRAMACION / FECHA PROGRAMADA
  - BODEGA / CD
  - CLIENTE (opcional)
  - DIRECCION (opcional)

## Verificación
Los endpoints fueron probados exitosamente:
- ✅ `/api/drivers/import-excel/` - Retorna 200 OK, procesa archivos correctamente
- ✅ `/api/programaciones/import-excel/` - Retorna 200 OK, procesa archivos correctamente

## Para Usuarios
El problema está completamente resuelto. Ahora pueden:
1. Ir a `/importar/` en la aplicación
2. Seleccionar un archivo Excel apropiado
3. Hacer clic en "Importar"
4. El sistema procesará el archivo y mostrará los resultados

Si hay errores en los datos del Excel (contenedores no encontrados, fechas inválidas, etc.), 
el sistema mostrará mensajes de error específicos en lugar de "error desconocido".
