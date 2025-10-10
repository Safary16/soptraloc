# 🗺️ Guía Completa: Configurar Mapbox API

**Fecha:** Octubre 7, 2025  
**Sistema:** SOPTRALOC TMS v3.2  
**API:** Mapbox Directions API  

---

## 🎯 ¿Por qué Mapbox?

### Ventajas sobre Google Maps:
- ✅ **$75 de crédito gratis** con GitHub Student Pack
- ✅ **50,000 requests gratis PERMANENTEMENTE cada mes**
- ✅ **API más simple** y fácil de usar
- ✅ **Mapas hermosos** y customizables
- ✅ **Menor costo:** $0.50 por 1,000 requests (vs $5.00 de Google)
- ✅ **Documentación excelente** y ejemplos claros

### Costos Comparados:

| Proveedor | Costo por 1,000 requests | Gratis mensual | Crédito GitHub |
|-----------|-------------------------|----------------|----------------|
| **Mapbox** | $0.50 | 50,000 | $75 |
| Google Maps | $5.00 | 0 | $200 |

**Resultado:** Con Mapbox obtienes 50,000 requests gratis cada mes + 150,000 adicionales con el crédito de $75 = **200,000 requests totales** 🎉

---

## 📋 Paso 1: Activar GitHub Student Pack

### 1.1 Verificar elegibilidad
1. Debes tener una cuenta de GitHub
2. Ser estudiante activo
3. Tener un email universitario (`.edu`, `.cl` de universidad, etc.)

### 1.2 Solicitar el Pack
1. Ve a: **https://education.github.com/pack**
2. Click en **"Get student benefits"**
3. Completa el formulario:
   - Nombre completo
   - Email universitario
   - Nombre de la institución
   - ¿Cómo planeas usar GitHub? → "Desarrollo de proyectos académicos y aprendizaje"
4. Sube una prueba de inscripción:
   - Certificado de matrícula
   - Carnet estudiantil con fecha
   - Email de tu universidad
5. Click en **"Submit"**

### 1.3 Esperar aprobación
- ⏱️ **Tiempo:** 1-7 días hábiles
- 📧 Recibirás un email cuando sea aprobado
- ✅ Acceso inmediato a todos los beneficios

---

## 🗺️ Paso 2: Crear Cuenta en Mapbox

### 2.1 Registrarse
1. Ve a: **https://account.mapbox.com/auth/signup/**
2. Opciones:
   - **Recomendado:** Sign up with GitHub (usa tu cuenta de estudiante)
   - O: Email y contraseña
3. Completa tu perfil

### 2.2 Verificar email
- Revisa tu email y confirma la cuenta
- Si usaste GitHub, no necesitas verificación adicional

---

## 💳 Paso 3: Aplicar Crédito de GitHub Student Pack

### 3.1 Acceder al beneficio
1. Inicia sesión en Mapbox
2. Ve a: **https://account.mapbox.com/billing**
3. En la sección **"Billing"**, busca la opción **"Apply promotional code"**
4. O ve directamente a: **https://www.mapbox.com/github-students**

### 3.2 Conectar con GitHub
1. Click en **"Claim your $75 credit"**
2. Autoriza la conexión Mapbox ↔ GitHub
3. El crédito se aplicará automáticamente

### 3.3 Verificar crédito
1. En **https://account.mapbox.com/billing**
2. Deberías ver:
   ```
   Monthly free tier: 50,000 requests
   Promotional credit: $75.00
   ```

---

## 🔑 Paso 4: Obtener tu API Key

### 4.1 Crear Access Token
1. Ve a: **https://account.mapbox.com/access-tokens/**
2. Verás un token **"Default public token"** (no uses este)
3. Click en **"Create a token"**

### 4.2 Configurar el token
- **Name:** `SOPTRALOC-Production`
- **Scopes:** Marca solo lo necesario:
  - ✅ `directions:read`
  - ✅ `directions:tiles`
- **Token restrictions:** (opcional pero recomendado)
  - **URL restrictions:** Agrega tu dominio:
    ```
    https://tu-app.onrender.com/*
    https://localhost:8000/*  (para desarrollo)
    ```
- Click en **"Create token"**

### 4.3 Copiar el token
⚠️ **IMPORTANTE:** Copia el token AHORA. Solo se muestra una vez.

Ejemplo de token:
```
pk.eyJ1IjoidHVfdXNlcm5hbWUiLCJhIjoiY2x0eDEyMzQ1In0.AbCdEfGhIjKlMnOpQrStUvWxYz
```

---

## ⚙️ Paso 5: Configurar en SOPTRALOC

### 5.1 Desarrollo Local

**Opción A: Archivo `.env`** (recomendado)
```bash
# En /workspaces/soptraloc/.env
MAPBOX_API_KEY=pk.eyJ1IjoidHVfdXNlcm5hbWUiLCJhIjoiY2x0eDEyMzQ1In0.AbCdEfGhIjKlMnOpQrStUvWxYz
```

**Opción B: Variable de entorno temporal**
```bash
export MAPBOX_API_KEY="tu-token-aqui"
python manage.py runserver
```

### 5.2 Producción en Render

1. Ve a tu aplicación en **Render Dashboard**
2. Click en tu servicio (ej: `soptraloc`)
3. Ve a **"Environment"** en el menú lateral
4. Click en **"Add Environment Variable"**
5. Agrega:
   - **Key:** `MAPBOX_API_KEY`
   - **Value:** Tu token de Mapbox
6. Click en **"Save Changes"**

**Render redesplegará automáticamente** tu aplicación con el nuevo token.

---

## ✅ Paso 6: Verificar Funcionamiento

### 6.1 En desarrollo local

```bash
cd /workspaces/soptraloc/soptraloc_system
python manage.py shell
```

```python
from apps.routing.mapbox_service import mapbox_service

# Probar con códigos de ubicación
data = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON')

print(f"✅ API Key configurada: {mapbox_service.api_key is not None}")
print(f"📊 Fuente: {data['source']}")  # Debe decir "mapbox_api"
print(f"⏱️ Tiempo: {data['duration_in_traffic_minutes']} min")
print(f"📏 Distancia: {data['distance_km']} km")
```

**Resultado esperado:**
```
✅ API Key configurada: True
📊 Fuente: mapbox_api
⏱️ Tiempo: 35 min
📏 Distancia: 24.5 km
```

### 6.2 En producción (Render)

```bash
# Ver logs en Render
curl https://tu-app.onrender.com/api/v1/routing/route-tracking/locations/

# O usar Postman/Insomnia para probar los endpoints
```

---

## 🧪 Paso 7: Probar el Sistema Completo

### 7.1 Probar disponibilidad de conductores

```bash
# En shell de Django
python manage.py shell
```

```python
from apps.routing.driver_availability_service import driver_availability
from apps.drivers.models import Driver

# Ver conductores disponibles
disponibles = driver_availability.get_available_drivers()
print(f"Conductores disponibles: {len(disponibles)}")

# Ver estado de un conductor específico
driver = Driver.objects.first()
status = driver_availability.get_driver_status(driver.id)
print(f"{driver.nombre}: {status['status']}")
print(f"Ubicación: {status['estimated_location']}")
```

### 7.2 Probar inicio de ruta con tráfico real

```python
from apps.routing.route_start_service import RouteStartService
from apps.drivers.models import Driver, Assignment
from apps.containers.models import Container

# Obtener datos
driver = Driver.objects.first()
container = Container.objects.filter(status='ASSIGNED').first()

# Si no hay contenedor asignado, crear una asignación de prueba
if not container:
    from apps.core.models import Company
    company = Company.objects.first()
    
    # Crear contenedor de prueba
    container = Container.objects.create(
        container_number='TEST1234567',
        container_type='20ST',
        status='ASSIGNED',
        owner_company=company
    )

# Crear asignación
assignment = Assignment.objects.create(
    driver=driver,
    container=container,
    estado='PENDIENTE',
    tipo_asignacion='ENTREGA'
)

# Iniciar ruta usando códigos de ubicación
result = RouteStartService.start_route(
    assignment_id=assignment.id,
    driver_id=driver.id,
    origin_name='CCTI',
    destination_name='CD_PENON',
    origin_lat=-33.5167,
    origin_lng=-70.8667,
    dest_lat=-33.6370,
    dest_lng=-70.7050
)

print(f"✅ Ruta iniciada")
print(f"📊 ETA: {result['time']['eta']}")
print(f"⏱️ Duración: {result['time']['duration_with_traffic']} min")
print(f"🚦 Tráfico: {result['traffic']['level']}")
print(f"📍 Distancia: {result['route']['distance_km']} km")
```

---

## 📊 Paso 8: Monitorear Uso

### 8.1 Ver estadísticas en Mapbox

1. Ve a: **https://account.mapbox.com/statistics/**
2. Verás gráficos de:
   - Requests por día
   - Requests por endpoint (Directions API)
   - Crédito usado vs disponible

### 8.2 Configurar alertas

1. En **https://account.mapbox.com/billing**
2. Sección **"Usage alerts"**
3. Configura alertas:
   - **50% del límite gratis:** Email de advertencia
   - **90% del límite gratis:** Email urgente
   - **100% del límite gratis:** Email crítico

---

## 🔧 Troubleshooting

### Problema 1: "⚠️ MAPBOX_API_KEY no configurada"

**Causa:** El token no está en las variables de entorno

**Solución:**
```bash
# Verificar en shell
python manage.py shell
>>> from django.conf import settings
>>> print(settings.MAPBOX_API_KEY)
```

Si es `None`:
1. Verifica que el `.env` tenga `MAPBOX_API_KEY=...`
2. O agrega la variable en Render
3. Reinicia el servidor

### Problema 2: "Unauthorized" o "Invalid token"

**Causa:** Token incorrecto o expirado

**Solución:**
1. Ve a https://account.mapbox.com/access-tokens/
2. Verifica que el token esté activo
3. Revisa que tenga los scopes correctos (`directions:read`)
4. Crea un nuevo token si es necesario

### Problema 3: "Fuente: fallback" en lugar de "mapbox_api"

**Causa:** La API no está respondiendo o hay error de conexión

**Solución:**
```python
# En shell de Django
from apps.routing.mapbox_service import mapbox_service
import requests

# Probar conexión directa
url = f"https://api.mapbox.com/directions/v5/mapbox/driving/-70.8667,-33.5167;-70.7050,-33.6370"
params = {'access_token': mapbox_service.api_key}
response = requests.get(url, params=params)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Si hay error:
1. Verifica tu conexión a internet
2. Revisa que el token sea válido
3. Verifica que las coordenadas sean correctas (lng, lat en Mapbox)

### Problema 4: "Rate limit exceeded"

**Causa:** Superaste el límite de requests

**Solución:**
1. Verifica uso en https://account.mapbox.com/statistics/
2. El sistema usa cache de 5 minutos para reducir llamadas
3. Considera optimizar consultas o aumentar tiempo de cache

---

## 💡 Tips y Mejores Prácticas

### 1. Cache Inteligente
El sistema ya tiene cache de 5 minutos. Para rutas frecuentes, considera:
```python
# En settings.py (opcional)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'soptraloc',
        'TIMEOUT': 300,  # 5 minutos
    }
}
```

### 2. Monitoring Proactivo
```python
# Crear script de monitoreo
from apps.routing.mapbox_service import mapbox_service
import logging

logger = logging.getLogger(__name__)

def check_api_health():
    try:
        data = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON')
        if data['source'] == 'mapbox_api':
            logger.info("✅ Mapbox API funcionando correctamente")
            return True
        else:
            logger.warning("⚠️ Usando fallback. Verificar API key.")
            return False
    except Exception as e:
        logger.error(f"❌ Error en Mapbox API: {e}")
        return False
```

### 3. Fallback Automático
El sistema ya tiene fallback con tiempos estáticos. Para mejorar:
```python
# En locations_catalog.py
STATIC_TRAVEL_TIMES = {
    ('CCTI', 'CD_PENON'): 45,
    ('CCTI', 'CD_QUILICURA'): 35,
    # ... agregar más rutas basadas en datos históricos
}
```

---

## 📚 Recursos Adicionales

### Documentación Oficial:
- **Mapbox Directions API:** https://docs.mapbox.com/api/navigation/directions/
- **Mapbox Pricing:** https://www.mapbox.com/pricing
- **Mapbox Support:** https://support.mapbox.com/

### GitHub Student Pack:
- **Página oficial:** https://education.github.com/pack
- **Mapbox en Student Pack:** https://www.mapbox.com/github-students

### Tutoriales:
- **Getting Started:** https://docs.mapbox.com/help/getting-started/
- **API Examples:** https://docs.mapbox.com/api/navigation/directions/#example-request

---

## ✅ Checklist de Configuración

- [ ] Activar GitHub Student Pack
- [ ] Crear cuenta en Mapbox
- [ ] Aplicar crédito de $75
- [ ] Crear Access Token
- [ ] Configurar scopes (directions:read)
- [ ] Copiar token (solo se muestra una vez)
- [ ] Agregar MAPBOX_API_KEY en .env (local)
- [ ] Agregar MAPBOX_API_KEY en Render (producción)
- [ ] Verificar funcionamiento en shell
- [ ] Probar endpoints REST
- [ ] Configurar alertas de uso
- [ ] Monitorear estadísticas

---

## 🎉 ¡Listo!

Una vez completados todos los pasos:

1. ✅ Tienes **50,000 requests gratis/mes permanentemente**
2. ✅ Tienes **$75 de crédito** = 150,000 requests adicionales
3. ✅ Total: **200,000 requests** para empezar
4. ✅ Sistema con **tráfico en tiempo real**
5. ✅ **Fallback automático** si se agota el crédito

**El sistema está listo para producción** 🚀

---

**Fecha de creación:** Octubre 7, 2025  
**Última actualización:** Octubre 7, 2025  
**Versión:** 1.0
