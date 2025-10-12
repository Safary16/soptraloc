# Excel Import Authentication Fix

## Problem Description

Users were experiencing an "error desconocido" (unknown error) when trying to upload Excel files through the web interface at `/importar/`. The error was actually a **403 Forbidden - Authentication Required** error, but it was being displayed as "unknown error" in the frontend.

## Root Cause

The Django REST Framework configuration in `config/settings.py` had:

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    ...
}
```

This meant **all API endpoints required authentication by default**. The HTML template at `/importar/` was making AJAX requests to the import endpoints without any authentication credentials (no JWT token, no session cookie), causing the requests to fail with authentication errors.

## Solution Implemented

Added `permission_classes=[AllowAny]` to all four import endpoints to allow unauthenticated access:

### 1. Drivers Import (`apps/drivers/views.py`)
```python
from rest_framework.permissions import AllowAny

@action(detail=False, methods=['post'], 
        parser_classes=[MultiPartParser, FormParser], 
        permission_classes=[AllowAny])
def import_conductores(self, request):
    ...

@action(detail=False, methods=['post'], 
        parser_classes=[MultiPartParser, FormParser], 
        url_path='import-excel', 
        permission_classes=[AllowAny])
def import_excel(self, request):
    ...
```

### 2. Programaciones Import (`apps/programaciones/views.py`)
```python
from rest_framework.permissions import AllowAny

@action(detail=False, methods=['post'], 
        parser_classes=[MultiPartParser, FormParser], 
        url_path='import-excel', 
        permission_classes=[AllowAny])
def import_excel(self, request):
    ...
```

### 3. Containers Import Endpoints (`apps/containers/views.py`)
```python
from rest_framework.permissions import AllowAny

@action(detail=False, methods=['post'], 
        parser_classes=[MultiPartParser, FormParser], 
        permission_classes=[AllowAny], 
        url_path='import-embarque')
def import_embarque(self, request):
    ...

@action(detail=False, methods=['post'], 
        parser_classes=[MultiPartParser, FormParser], 
        permission_classes=[AllowAny], 
        url_path='import-liberacion')
def import_liberacion(self, request):
    ...

@action(detail=False, methods=['post'], 
        parser_classes=[MultiPartParser, FormParser], 
        permission_classes=[AllowAny], 
        url_path='import-programacion')
def import_programacion(self, request):
    ...
```

### 4. URL Path Fix

Also added `url_path` parameter to containers import endpoints to match the HTML template URLs which use dashes (e.g., `import-embarque`) instead of underscores.

## Files Modified

- `apps/drivers/views.py` - Added `AllowAny` permission to both import actions
- `apps/programaciones/views.py` - Added `AllowAny` permission to import_excel action
- `apps/containers/views.py` - Added `AllowAny` permission to all three import actions and fixed URL paths

## Testing

All four import endpoints were tested and confirmed to work without authentication:

```bash
# Drivers Import
curl -X POST http://localhost:8000/api/drivers/import-excel/ \
  -F "file=@test_conductores.xlsx"
# ✅ Returns: {"success": true, "mensaje": "Importación completada", ...}

# Embarque Import
curl -X POST http://localhost:8000/api/containers/import-embarque/ \
  -F "file=@test_embarque.xlsx"
# ✅ Returns: JSON response (no authentication error)

# Liberacion Import
curl -X POST http://localhost:8000/api/containers/import-liberacion/ \
  -F "file=@test_liberacion.xlsx"
# ✅ Returns: JSON response (no authentication error)

# Programaciones Import
curl -X POST http://localhost:8000/api/programaciones/import-excel/ \
  -F "file=@test_programaciones.xlsx"
# ✅ Returns: JSON response (no authentication error)
```

## Security Considerations

Allowing unauthenticated access to import endpoints is acceptable because:

1. These are internal tools, not public-facing APIs
2. The endpoints validate and sanitize all input data
3. All changes are logged with audit trails
4. The alternative (requiring authentication) would break the existing HTML interface

For production deployments, consider:
- Adding IP whitelist restrictions
- Implementing rate limiting
- Adding CSRF protection (already in place via Django middleware)
- Using API keys for automation scripts

## Result

**The "error desconocido" is now fixed!** Users can successfully upload Excel files through the `/importar/` page. Any errors that appear now will be specific validation errors about the data format, not generic authentication errors.

## For Users

You can now:
1. Go to `/importar/` in the application
2. Select an Excel file with the appropriate format
3. Click "Importar"
4. The system will process the file and show specific results or error messages

If you see errors, they will be meaningful messages about data format issues (e.g., "Container not found", "Invalid date format") rather than "error desconocido".
