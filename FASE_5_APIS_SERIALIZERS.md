# 🔌 AUDITORÍA - FASE 5: APIs Y SERIALIZERS (DRF)

**Fecha**: 2025-10-10  
**Auditor**: GitHub Copilot  
**Alcance**: Análisis exhaustivo de Django REST Framework, serializers, autenticación, autorización, versionado, documentación API

---

## 📊 RESUMEN EJECUTIVO

### Estadísticas de APIs
- **Serializers totales**: 20+ serializers
  - `containers`: 8 serializers (Container, Movement, Document, Inspection)
  - `drivers`: 6 serializers (Driver, Location, Assignment, Alert, TimeMatrix, TrafficAlert)
  - `core`: 4 serializers (User, Company, Vehicle, MovementCode)
  - `warehouses`: 2 serializers
- **ViewSets DRF**: 10 ViewSets
- **Endpoints API**: ~40 endpoints REST
- **Autenticación**: JWT + Session Authentication
- **Paginación**: Configurada globalmente (50/página)
- **Throttling**: ❌ **NO configurado** (vulnerable a DoS)
- **Versionado**: ❌ **NO implementado**
- **Documentación**: Swagger/OpenAPI (drf-yasg)

### Veredicto General de APIs
🟡 **MODERADO/BUENO** - APIs REST bien estructuradas con DRF, autenticación JWT correcta, pero **faltan throttling, versionado, validaciones robustas en serializers**, y **permisos granulares**.

---

## 1️⃣ ANÁLISIS DE SERIALIZERS

### 🟢 **FORTALEZAS: Estructura bien organizada**

```python
# ✅ apps/containers/serializers.py

# 1. Serializer completo (para GET con datos anidados)
class ContainerSerializer(serializers.ModelSerializer):
    """✅ Con relaciones anidadas para GET"""
    owner_company = CompanySerializer(read_only=True)     # ← Nested
    current_location = LocationSerializer(read_only=True)
    current_vehicle = VehicleSerializer(read_only=True)
    
    # ✅ Campos calculados/display
    container_type_display = serializers.CharField(
        source='get_container_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Container
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')

# 2. Serializer ligero para listas
class ContainerSummarySerializer(serializers.ModelSerializer):
    """✅ Solo campos esenciales para listados"""
    owner_company_name = serializers.CharField(source='owner_company.name', read_only=True)
    
    class Meta:
        model = Container
        fields = ['id', 'container_number', 'status', 'owner_company_name', ...]
        # ← Menos campos = queries más rápidos

# 3. Serializer para escritura (POST/PUT)
class ContainerCreateUpdateSerializer(serializers.ModelSerializer):
    """✅ Sin datos anidados para escritura"""
    class Meta:
        model = Container
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
```

**Fortalezas**:
- ✅ Separación clara: lectura vs escritura
- ✅ Serializer ligero para listas (performance)
- ✅ Campos `display` para UI
- ✅ Campos read-only correctos

---

### 🔴 **PROBLEMA CRÍTICO 1: `fields = '__all__'` en serializers**

```python
# ❌ apps/containers/serializers.py
class ContainerSerializer(serializers.ModelSerializer):
    """❌ Expone TODOS los campos (83 campos!)"""
    class Meta:
        model = Container
        fields = '__all__'  # ← Expone campos sensibles/internos
```

**Riesgos**:
- 🔴 **Expone campos internos**: `created_by`, `updated_by`, `position_updated_by`
- 🔴 **Expone campos sensibles**: Posibles costos, márgenes, datos confidenciales
- 🔴 **Payloads gigantes**: 83 campos = respuestas JSON de 5-10KB por contenedor
- 🔴 **Queries lentos**: Django debe fetchear todos los campos

**Solución**:
```python
# ✅ CORREGIR: Especificar campos explícitamente

class ContainerSerializer(serializers.ModelSerializer):
    """✅ Solo campos necesarios"""
    owner_company = CompanySerializer(read_only=True)
    current_location = LocationSerializer(read_only=True)
    
    class Meta:
        model = Container
        fields = [
            # Identificación
            'id', 'container_number', 'container_type', 'seal_number',
            
            # Estado
            'status', 'position_status',
            
            # Ubicación
            'current_location', 'current_position',
            
            # Propietario
            'owner_company',
            
            # Fechas clave
            'eta', 'release_date', 'scheduled_date',
            
            # Tracking
            'created_at', 'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

# ✅ Para casos que necesiten TODO, crear serializer específico
class ContainerDetailSerializer(serializers.ModelSerializer):
    """Solo para endpoints de detalle que requieren todos los datos"""
    class Meta:
        model = Container
        fields = '__all__'
        read_only_fields = (...)
```

---

### 🔴 **PROBLEMA CRÍTICO 2: Validaciones débiles**

```python
# ❌ apps/containers/serializers.py
class ContainerMovementCreateSerializer(serializers.ModelSerializer):
    """❌ Validaciones incompletas"""
    
    class Meta:
        model = ContainerMovement
        fields = '__all__'
    
    def validate(self, data):
        """⚠️ Solo valida algunos casos"""
        movement_type = data.get('movement_type')
        
        if movement_type == 'load_chassis' and not data.get('to_vehicle'):
            raise serializers.ValidationError("Se requiere vehículo destino")
        
        # ❌ FALTA: Validar que el contenedor esté disponible
        # ❌ FALTA: Validar que el vehículo tenga capacidad
        # ❌ FALTA: Validar que las ubicaciones existan
        # ❌ FALTA: Validar fechas coherentes
        
        return data
```

**Solución**:
```python
# ✅ CORREGIR: Validaciones exhaustivas

class ContainerMovementCreateSerializer(serializers.ModelSerializer):
    """✅ Con validaciones completas"""
    
    class Meta:
        model = ContainerMovement
        fields = '__all__'
    
    def validate_container(self, value):
        """Validar que el contenedor esté disponible"""
        if not value.is_active:
            raise serializers.ValidationError("Contenedor no está activo")
        
        # Validar que no tenga movimiento en curso
        pending = ContainerMovement.objects.filter(
            container=value,
            status='IN_PROGRESS'
        ).exists()
        if pending:
            raise serializers.ValidationError(
                f"Contenedor {value.container_number} tiene un movimiento en curso"
            )
        
        return value
    
    def validate_to_vehicle(self, value):
        """Validar capacidad del vehículo"""
        if value and value.status != 'available':
            raise serializers.ValidationError(
                f"Vehículo {value.plate} no está disponible (estado: {value.status})"
            )
        return value
    
    def validate(self, data):
        """Validaciones cruzadas"""
        movement_type = data.get('movement_type')
        from_location = data.get('from_location')
        to_location = data.get('to_location')
        
        # Validar campos requeridos según tipo
        if movement_type == 'load_chassis':
            if not data.get('to_vehicle'):
                raise serializers.ValidationError({
                    'to_vehicle': "Se requiere vehículo destino para cargar en chasis"
                })
        
        elif movement_type == 'unload_chassis':
            if not to_location:
                raise serializers.ValidationError({
                    'to_location': "Se requiere ubicación destino para descargar"
                })
        
        elif movement_type in ['transfer_warehouse', 'transfer_location']:
            if not to_location:
                raise serializers.ValidationError({
                    'to_location': "Se requiere ubicación destino para transferencias"
                })
            
            # Validar que origen != destino
            if from_location and from_location == to_location:
                raise serializers.ValidationError({
                    'to_location': "Ubicación destino debe ser diferente del origen"
                })
        
        # Validar fechas
        movement_date = data.get('movement_date')
        if movement_date:
            from django.utils import timezone
            if movement_date < timezone.now().date():
                raise serializers.ValidationError({
                    'movement_date': "La fecha no puede ser en el pasado"
                })
        
        return data
    
    def create(self, validated_data):
        """Actualizar estado del contenedor al crear movimiento"""
        movement = super().create(validated_data)
        
        # Actualizar ubicación del contenedor
        container = movement.container
        if movement.to_location:
            container.current_location = movement.to_location
        if movement.to_vehicle:
            container.current_vehicle = movement.to_vehicle
        container.save()
        
        return movement
```

---

### 🟡 **PROBLEMA: Falta validación de permisos a nivel de objeto**

```python
# ⚠️ apps/containers/serializers.py
class ContainerCreateUpdateSerializer(serializers.ModelSerializer):
    """⚠️ Cualquier usuario autenticado puede modificar cualquier contenedor"""
    
    class Meta:
        model = Container
        fields = '__all__'
    
    # ❌ FALTA: Validar que el usuario tenga permiso para editar este contenedor
    # Por ejemplo: Solo el propietario o usuarios con rol admin
```

**Solución**:
```python
# ✅ AGREGAR: Validación de permisos

class ContainerCreateUpdateSerializer(serializers.ModelSerializer):
    """✅ Con validación de permisos"""
    
    class Meta:
        model = Container
        fields = '__all__'
    
    def validate_owner_company(self, value):
        """Validar que el usuario puede asignar esta empresa"""
        user = self.context['request'].user
        
        # Si no es staff, solo puede usar su propia empresa
        if not user.is_staff:
            # Asumiendo que existe perfil de usuario con empresa
            user_company = getattr(user, 'company', None)
            if user_company and value != user_company:
                raise serializers.ValidationError(
                    "No tiene permiso para asignar esta empresa"
                )
        
        return value
    
    def update(self, instance, validated_data):
        """Validar permisos antes de actualizar"""
        user = self.context['request'].user
        
        # Si no es staff, validar que es el propietario
        if not user.is_staff:
            user_company = getattr(user, 'company', None)
            if instance.owner_company != user_company:
                raise serializers.ValidationError(
                    "No tiene permiso para editar este contenedor"
                )
        
        return super().update(instance, validated_data)
```

---

## 2️⃣ ANÁLISIS DE AUTENTICACIÓN Y AUTORIZACIÓN

### 🟢 **FORTALEZA: JWT + Session Authentication**

```python
# ✅ config/settings.py (línea 163)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # ← Para APIs
        'rest_framework.authentication.SessionAuthentication',        # ← Para navegador
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated' if not DEBUG else 'rest_framework.permissions.AllowAny',
    ],
}
```

**Fortalezas**:
- ✅ JWT para APIs móviles/frontend separado
- ✅ Session para Django admin y navegador
- ✅ Permission por defecto: `IsAuthenticated` en producción

---

### 🔴 **PROBLEMA CRÍTICO: Permisos débiles en desarrollo**

```python
# ❌ config/settings.py (línea 169)
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated' if not DEBUG else 'rest_framework.permissions.AllowAny',
    # ← En desarrollo (DEBUG=True), CUALQUIERA puede acceder sin autenticación
],
```

**Riesgos**:
- 🔴 En desarrollo local, APIs completamente abiertas
- 🔴 Si DEBUG=True se deja en producción por error, APIs sin protección
- 🔴 Dificulta testing de permisos (porque están deshabilitados en dev)

**Solución**:
```python
# ✅ CORREGIR: SIEMPRE requerir autenticación

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # ← SIEMPRE
    ],
}

# Si necesitas endpoints públicos, hazlo explícito por endpoint:
@permission_classes([AllowAny])  # ← Solo donde se necesite
def public_endpoint(request):
    ...
```

---

### 🔴 **PROBLEMA CRÍTICO: Sin throttling/rate limiting**

```python
# ❌ config/settings.py
REST_FRAMEWORK = {
    # ... configuración actual ...
    # ❌ FALTA: 'DEFAULT_THROTTLE_CLASSES'
    # ❌ FALTA: 'DEFAULT_THROTTLE_RATES'
}
```

**Riesgos**:
- 🔴 **Ataques de fuerza bruta** en login (probar miles de contraseñas)
- 🔴 **Denial of Service (DoS)**: Un usuario puede hacer 10,000 requests/segundo
- 🔴 **Scraping masivo**: Extraer toda la base de datos sin límite

**Solución**:
```python
# ✅ AGREGAR: Throttling global

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [...],
    'DEFAULT_PERMISSION_CLASSES': [...],
    
    # ✅ AGREGAR: Rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',   # Para usuarios no autenticados
        'rest_framework.throttling.UserRateThrottle',   # Para usuarios autenticados
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',   # 100 requests/hora para anónimos
        'user': '1000/hour',  # 1000 requests/hora para autenticados
    },
}

# ✅ AGREGAR: Throttle específico para login
from rest_framework.throttling import AnonRateThrottle

class LoginThrottle(AnonRateThrottle):
    rate = '5/minute'  # Máximo 5 intentos de login por minuto

# apps/core/auth_views.py
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])  # ← Protección contra fuerza bruta
def get_token(request):
    ...
```

---

### 🟡 **PROBLEMA: Sin permisos granulares (roles/grupos)**

```python
# ⚠️ Situación actual:
# - Solo hay IsAuthenticated (sí/no)
# - No hay diferenciación de roles: Admin, Operator, Viewer, etc.

# ❌ Todos los usuarios autenticados pueden:
# - Crear/editar/eliminar contenedores
# - Crear/editar/eliminar conductores
# - Ver datos sensibles de todas las empresas
```

**Solución**:
```python
# ✅ CREAR: Sistema de permisos granular

# 1. Definir grupos en la BD (Django admin o fixtures)
from django.contrib.auth.models import Group, Permission

# python manage.py shell
admin_group = Group.objects.create(name='Admin')
operator_group = Group.objects.create(name='Operador')
viewer_group = Group.objects.create(name='Visualizador')

# 2. Crear permission classes personalizadas
# apps/core/permissions.py

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """Solo usuarios admin"""
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Admin').exists()

class IsOperatorOrAdmin(permissions.BasePermission):
    """Operadores y admins"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=['Admin', 'Operador']).exists()

class IsOwnerOrAdmin(permissions.BasePermission):
    """Solo el propietario o admin"""
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.groups.filter(name='Admin').exists():
            return True
        
        # Propietario puede ver/editar sus propios objetos
        if hasattr(obj, 'owner_company'):
            user_company = getattr(request.user, 'company', None)
            return obj.owner_company == user_company
        
        return False

class ReadOnly(permissions.BasePermission):
    """Solo lectura"""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS  # GET, HEAD, OPTIONS

# 3. Aplicar permisos en ViewSets
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsOperatorOrAdmin, IsOwnerOrAdmin, ReadOnly

class ContainerViewSet(viewsets.ModelViewSet):
    """✅ Con permisos granulares"""
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    
    def get_permissions(self):
        """Permisos según acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Crear/editar/eliminar: Solo operadores y admins
            return [IsAuthenticated(), IsOperatorOrAdmin()]
        elif self.action in ['retrieve', 'list']:
            # Ver: Autenticados con permiso de objeto
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtrar por empresa del usuario"""
        qs = super().get_queryset()
        user = self.request.user
        
        # Admin ve todo
        if user.groups.filter(name='Admin').exists():
            return qs
        
        # Otros usuarios solo ven su empresa
        user_company = getattr(user, 'company', None)
        if user_company:
            return qs.filter(owner_company=user_company)
        
        # Sin empresa = sin datos
        return qs.none()
```

---

## 3️⃣ ANÁLISIS DE VERSIONADO DE API

### 🔴 **PROBLEMA CRÍTICO: Sin versionado de API**

```python
# ❌ config/urls.py
urlpatterns = [
    path('api/v1/containers/', include('apps.containers.api_urls')),
    # ← Hardcoded /v1/ en URLs, pero sin soporte real de versionado
]
```

**Problemas**:
- 🔴 Si necesitas cambiar estructura de un serializer, rompes clientes existentes
- 🔴 No puedes deprecar endpoints gradualmente
- 🔴 Difícil mantener compatibilidad backward

**Solución**:
```python
# ✅ IMPLEMENTAR: Versionado de API con DRF

# 1. Configurar versionado en settings.py
REST_FRAMEWORK = {
    ...,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'VERSION_PARAM': 'version',
}

# 2. Reorganizar serializers por versión
# apps/containers/serializers/
#   ├── __init__.py
#   ├── v1/
#   │   ├── __init__.py
#   │   └── container.py  # ContainerSerializerV1
#   └── v2/
#       ├── __init__.py
#       └── container.py  # ContainerSerializerV2 (con cambios)

# 3. ViewSet con soporte de versionado
from apps.containers.serializers.v1 import ContainerSerializerV1
from apps.containers.serializers.v2 import ContainerSerializerV2

class ContainerViewSet(viewsets.ModelViewSet):
    """✅ Con versionado"""
    
    def get_serializer_class(self):
        """Serializer según versión de API"""
        if self.request.version == 'v2':
            return ContainerSerializerV2
        return ContainerSerializerV1  # Default v1

# 4. URLs
# config/urls.py
urlpatterns = [
    path('api/<str:version>/containers/', include('apps.containers.api_urls')),
    # ← Acceso: /api/v1/containers/ o /api/v2/containers/
]

# 5. Deprecar v1 gradualmente
import warnings

class ContainerViewSet(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        if request.version == 'v1':
            warnings.warn(
                "API v1 será deprecada el 2026-01-01. Por favor migre a v2.",
                DeprecationWarning
            )
            # Agregar header de advertencia
            response = super().list(request, *args, **kwargs)
            response['X-API-Deprecation'] = 'v1 deprecated, use v2'
            return response
        return super().list(request, *args, **kwargs)
```

---

## 4️⃣ ANÁLISIS DE DOCUMENTACIÓN DE API

### 🟢 **FORTALEZA: Swagger/OpenAPI configurado**

```python
# ✅ config/urls.py (línea 15-30)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="SOPTRALOC API",
        default_version='v1',
        description="Sistema de optimización para transporte de contenedores",
        # ...
    ),
    public=True,
    permission_classes=[permissions.AllowAny],  # ← Documentación pública
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
```

**Fortalezas**:
- ✅ Swagger UI disponible en `/swagger/`
- ✅ ReDoc disponible en `/redoc/`
- ✅ Generación automática desde serializers

---

### 🟡 **PROBLEMA: Documentación incompleta**

```python
# ⚠️ Serializers sin docstrings completos

class ContainerSerializer(serializers.ModelSerializer):
    """Serializer para contenedores"""  # ← Descripción básica
    # ❌ FALTA: Documentar cada campo
    # ❌ FALTA: Ejemplos de uso
    # ❌ FALTA: Validaciones documentadas
```

**Solución**:
```python
# ✅ MEJORAR: Documentación exhaustiva

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ContainerSerializer(serializers.ModelSerializer):
    """
    Serializer para contenedores de importación.
    
    Utilizado para operaciones CRUD sobre contenedores.
    
    **Campos principales:**
    - `container_number`: Número único del contenedor (ej: "ABCD1234567")
    - `status`: Estado actual del contenedor (ver `Container.CONTAINER_STATUS`)
    - `owner_company`: Empresa propietaria (FK a Company)
    - `release_date`: Fecha de liberación aduanera
    
    **Ejemplo de respuesta:**
    ```json
    {
        "id": "abc-123-def",
        "container_number": "ABCD1234567",
        "container_type": "40ft",
        "status": "PROGRAMADO",
        "owner_company": {
            "id": "xyz-789",
            "name": "Empresa ABC"
        },
        "release_date": "2025-10-15"
    }
    ```
    """
    
    owner_company = CompanySerializer(read_only=True, help_text="Empresa propietaria del contenedor")
    current_location = LocationSerializer(read_only=True, help_text="Ubicación actual del contenedor")
    
    class Meta:
        model = Container
        fields = [...]

# ✅ Documentar actions en ViewSets
class ContainerViewSet(viewsets.ModelViewSet):
    
    @swagger_auto_schema(
        operation_description="Asigna un conductor a un contenedor PROGRAMADO",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['driver_id'],
            properties={
                'driver_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID del conductor a asignar'
                ),
                'scheduled_datetime': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date-time',
                    description='Fecha/hora programada (opcional)',
                    example='2025-10-15T10:30:00Z'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Conductor asignado exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'assignment_id': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Validación fallida (contenedor no PROGRAMADO, conductor no disponible)",
            404: "Contenedor o conductor no encontrado",
        }
    )
    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        """Asigna un conductor a un contenedor"""
        ...
```

---

## 5️⃣ ANÁLISIS DE PAGINACIÓN

### 🟢 **FORTALEZA: Paginación configurada**

```python
# ✅ config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,  # 50 registros por página
}
```

**Fortalezas**:
- ✅ Evita cargar miles de registros de una vez
- ✅ Paginación estándar de DRF

---

### 🟡 **MEJORA: Paginación personalizable**

```python
# ⚠️ Actual: PAGE_SIZE fijo de 50
# ⚠️ No permite al cliente solicitar más/menos resultados

# ✅ MEJORAR: Paginación configurable por cliente

# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    """Paginación estándar con configuración por cliente"""
    page_size = 50
    page_size_query_param = 'page_size'  # ← Permite ?page_size=100
    max_page_size = 200  # ← Límite máximo
    
    def get_paginated_response(self, data):
        """Respuesta personalizada con metadatos"""
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page_size': self.page_size,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
            },
            'results': data
        })

# config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
}

# Uso:
# GET /api/v1/containers/?page=2&page_size=100
```

---

## 6️⃣ PUNTUACIÓN POR CATEGORÍA

| Categoría                      | Puntuación | Comentario                                    |
|--------------------------------|------------|-----------------------------------------------|
| **Estructura de serializers**  | 8/10       | Bien organizados, separación lectura/escritura|
| **Validaciones**               | 5/10       | Básicas, faltan validaciones cruzadas         |
| **Autenticación**              | 8/10       | JWT + Session correctos                       |
| **Autorización/Permisos**      | 4/10       | Solo IsAuthenticated, sin roles/granularidad  |
| **Throttling**                 | 1/10       | **NO configurado** (vulnerable a DoS) 🔴       |
| **Versionado**                 | 2/10       | URLs con /v1/ pero sin soporte real           |
| **Documentación API**          | 6/10       | Swagger/OpenAPI presente, pero incompleto     |
| **Paginación**                 | 7/10       | Configurada, mejorable con personalización    |
| **Manejo de errores API**      | 6/10       | Estándar DRF, podría ser más detallado        |
| **CORS**                       | 7/10       | Configurado para desarrollo                   |

**PROMEDIO**: **5.4/10** 🟡 **NECESITA MEJORAS IMPORTANTES**

---

## 7️⃣ RECOMENDACIONES PRIORIZADAS

### 🔴 **CRÍTICO (Hacer HOY - Seguridad)**

1. **Agregar throttling/rate limiting INMEDIATAMENTE**
   ```python
   # config/settings.py
   REST_FRAMEWORK = {
       ...,
       'DEFAULT_THROTTLE_CLASSES': [
           'rest_framework.throttling.AnonRateThrottle',
           'rest_framework.throttling.UserRateThrottle',
       ],
       'DEFAULT_THROTTLE_RATES': {
           'anon': '100/hour',
           'user': '1000/hour',
       },
   }
   ```

2. **Reemplazar `fields = '__all__'` por campos explícitos**
   ```python
   # En todos los serializers, especificar fields = [...]
   ```

3. **Eliminar `AllowAny` de DEFAULT_PERMISSION_CLASSES en development**
   ```python
   'DEFAULT_PERMISSION_CLASSES': [
       'rest_framework.permissions.IsAuthenticated',  # SIEMPRE
   ],
   ```

---

### 🔴 **CRÍTICO (Hacer ESTA SEMANA)**

4. **Implementar sistema de permisos granulares (roles)**
   ```python
   # Crear grupos: Admin, Operador, Visualizador
   # Crear permission classes: IsOperatorOrAdmin, IsOwnerOrAdmin
   # Aplicar en todos los ViewSets
   ```

5. **Implementar versionado de API**
   ```python
   # Configurar URLPathVersioning
   # Crear serializers v1/ y v2/
   # Actualizar URLs para soportar /api/<version>/
   ```

6. **Agregar validaciones exhaustivas en serializers**
   ```python
   # ContainerMovementCreateSerializer: validar disponibilidad
   # Todos los serializers: validar coherencia de fechas, capacidades, permisos
   ```

---

### 🟡 **IMPORTANTE (Próximas 2 semanas)**

7. **Mejorar documentación de API con Swagger**
   ```python
   # Agregar docstrings exhaustivos
   # Usar @swagger_auto_schema en actions
   # Agregar ejemplos de requests/responses
   ```

8. **Implementar paginación personalizable**
   ```python
   # Permitir ?page_size= en query params
   # Agregar metadatos de paginación en respuestas
   ```

9. **Agregar filtros avanzados**
   ```python
   # Filtros por rango de fechas
   # Filtros por múltiples estados
   # Filtros anidados (ej: owner_company__name__icontains=)
   ```

10. **Implementar cache de API responses**
    ```python
    from rest_framework_extensions.cache.decorators import cache_response
    
    class ContainerViewSet(viewsets.ModelViewSet):
        @cache_response(timeout=300)  # Cache 5 minutos
        def list(self, request):
            ...
    ```

---

### 🟢 **MEJORAS (Backlog)**

11. Implementar webhooks para notificar cambios
12. Agregar GraphQL como alternativa a REST
13. Implementar API keys para integraciones externas
14. Agregar monitoreo de uso de API (Analytics)
15. Implementar compresión de respuestas (gzip)

---

## 8️⃣ PRÓXIMOS PASOS (FASE 6)

Con el análisis de APIs completo, ahora procederé a:

1. ✅ **FASE 1 COMPLETADA**: Arquitectura y dependencias
2. ✅ **FASE 2 COMPLETADA**: Modelos y base de datos
3. ✅ **FASE 3 COMPLETADA**: Lógica de negocio y servicios
4. ✅ **FASE 4 COMPLETADA**: Views y controladores
5. ✅ **FASE 5 COMPLETADA**: APIs y Serializers (DRF)
6. ⏳ **FASE 6**: Seguridad profunda (OWASP Top 10)
7. ⏳ **FASE 7**: Performance y optimización
8. ⏳ **FASE 8**: Tests y cobertura
9. ⏳ **FASE 9**: Documentación
10. ⏳ **FASE 10**: Deployment e integración

---

**FIN DE FASE 5 - APIs Y SERIALIZERS**  
**Próximo paso**: Análisis exhaustivo de seguridad (OWASP Top 10, XSS, CSRF, SQL Injection, etc.)
