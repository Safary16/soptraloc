# 📖 Guía del Administrador - SoptraLoc TMS

## 🔐 Acceso al Sistema

### Credenciales de Administrador
Se ha creado el superusuario solicitado:

```
Username: admin
Password: 1234
URL: http://localhost:8000/admin/ (desarrollo)
URL: https://soptraloc.onrender.com/admin/ (producción)
```

**⚠️ IMPORTANTE:** En producción, cambia esta contraseña por una segura siguiendo estos pasos:
1. Ingresa al admin
2. Ve a **Authentication and Authorization** → **Users**
3. Selecciona el usuario `admin`
4. Click en **change password form**
5. Ingresa una contraseña segura
6. Guarda los cambios

---

## 👥 Gestión de Conductores

### Crear un Conductor

1. **Accede al Admin Panel:**
   - Ve a: `http://localhost:8000/admin/` o `https://soptraloc.onrender.com/admin/`
   - Login con: `admin` / `1234`

2. **Navega a Conductores:**
   - Click en **"Drivers"** en el menú lateral
   - O ve directamente a: `/admin/drivers/driver/`

3. **Agregar Nuevo Conductor:**
   - Click en el botón **"ADD DRIVER"** (esquina superior derecha)
   
4. **Completar Información Básica:**
   ```
   Nombre: Juan Pérez
   RUT: 12.345.678-9
   Teléfono: +56912345678
   ```

5. **Configurar Disponibilidad:**
   - ✓ **Presente:** Marcar si está disponible hoy
   - ✓ **Activo:** Marcar para que aparezca en el sistema
   
6. **Control de Entregas:**
   ```
   Num entregas día: 0 (se auto-actualiza)
   Max entregas/día: 3 (ajustar según capacidad)
   ```

7. **Campo Usuario (Opcional):**
   - Si dejas el campo **"User"** vacío, el sistema **automáticamente** creará un usuario
   - El username será generado desde el nombre del conductor
   - La contraseña por defecto será: `driver123`

8. **Guardar:**
   - Click en **"SAVE"**
   - El sistema creará automáticamente las credenciales del conductor

### Usuario Auto-Creado

Cuando guardas un conductor sin usuario, el sistema automáticamente:

```python
Username: juan_perez (generado desde el nombre)
Password: driver123 (contraseña por defecto)
```

**El conductor puede usar estas credenciales en:**
- Dashboard móvil: `http://localhost:8000/driver/login/`
- API: `/api/drivers/{id}/track_location/`

### Verificar Usuario Creado

1. Ve a **Authentication and Authorization** → **Users**
2. Busca el username del conductor (ej: `juan_perez`)
3. Ahí puedes:
   - Ver detalles del usuario
   - Cambiar contraseña
   - Modificar permisos
   - Activar/desactivar cuenta

### Editar un Conductor Existente

1. En la lista de conductores, click en el nombre del conductor
2. Edita los campos necesarios
3. Si necesitas cambiar el usuario asociado:
   - Selecciona otro usuario del dropdown **"User"**
   - O déjalo vacío y guarda (creará uno nuevo)

---

## 🗺️ Sistema de Monitoreo GPS

### Vista de Monitoreo en Tiempo Real

El sistema incluye un **mapa real con Mapbox** que muestra las ubicaciones de los conductores en tiempo real.

**Acceder al Monitoreo:**
```
URL: http://localhost:8000/monitoring/
URL: https://soptraloc.onrender.com/monitoring/
```

### Funcionalidades del Mapa

#### 1. **Mapa Interactivo de Mapbox**
- Mapa real centrado en Santiago, Chile
- Controles de zoom y navegación
- Vista de calles actualizada

#### 2. **Ubicación de Conductores en Tiempo Real**
- Iconos de camiones (🚛) muestran posición GPS de cada conductor
- Colores indican estado:
  - 🟢 **Verde:** Activo (última actualización < 30 minutos)
  - 🔴 **Rojo:** Inactivo (sin actualización reciente)

#### 3. **Sidebar con Conductores Activos**
- Lista de todos los conductores con GPS activo
- Información por conductor:
  - Nombre
  - Entregas del día (ej: 2/3)
  - Última actualización (ej: "Hace 5 min")
  - Estado (activo/inactivo)

#### 4. **Actualización Automática**
- El mapa se actualiza automáticamente cada **15 segundos**
- Indicador visual en la esquina superior derecha muestra última actualización

#### 5. **Interacción con el Mapa**
- Click en un conductor del sidebar → Centra el mapa en su ubicación
- Click en un marcador del mapa → Muestra popup con información
- Zoom automático para mostrar todos los conductores activos

### Cómo Funciona el GPS

#### Para Conductores (Smartphone)

1. **Login en Dashboard Móvil:**
   ```
   URL: http://localhost:8000/driver/login/
   Username: juan_perez
   Password: driver123
   ```

2. **Permisos de Ubicación:**
   - El navegador solicitará permisos de GPS
   - El conductor debe aceptar para compartir ubicación

3. **Tracking Automático:**
   - Al iniciar una ruta, el GPS se activa automáticamente
   - El dashboard envía la ubicación al servidor cada cierto tiempo
   - Botón manual de "Actualizar Ubicación" también disponible

4. **Datos GPS Enviados:**
   ```json
   {
     "lat": -33.4569,
     "lng": -70.6483,
     "accuracy": 10.5
   }
   ```

#### Endpoints API para GPS

**Actualizar Ubicación del Conductor:**
```http
POST /api/drivers/{id}/track_location/
Content-Type: application/json

{
  "lat": -33.4569,
  "lng": -70.6483,
  "accuracy": 10.5
}
```

**Obtener Conductores Activos con GPS:**
```http
GET /api/drivers/active_locations/

Respuesta:
[
  {
    "id": 1,
    "nombre": "Juan Pérez",
    "lat": -33.4569,
    "lng": -70.6483,
    "ultima_actualizacion": "2025-10-12T15:30:00Z",
    "num_entregas_dia": 2,
    "max_entregas_dia": 3
  }
]
```

**Ver Historial de Ubicaciones:**
```http
GET /api/drivers/{id}/historial/?dias=7

Obtiene historial de ubicaciones de los últimos 7 días
```

### Configuración de Mapbox

El sistema ya está configurado con una API Key de Mapbox válida:

```javascript
// En templates/monitoring.html
mapboxgl.accessToken = 'pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg';
```

**Para cambiar el centro del mapa:**
```javascript
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [-70.6483, -33.4569], // [lng, lat] - Santiago, Chile
    zoom: 11
});
```

---

## 📊 Información Adicional

### Ver Datos GPS en el Admin

1. **Ver Última Posición:**
   - Ve a **Drivers** → Click en un conductor
   - Expande la sección **"Ubicación GPS"**
   - Verás:
     - Latitud
     - Longitud
     - Última actualización

2. **Ver Historial Completo:**
   - Ve a **Driver Locations** (si está habilitado en admin)
   - O usa el endpoint API: `/api/drivers/{id}/historial/`

### Criterios de "Conductor Activo"

Un conductor aparece en el monitoreo si cumple:
- ✓ Campo `activo = True`
- ✓ Última actualización GPS < 30 minutos
- ✓ Tiene coordenadas GPS (`ultima_posicion_lat` y `ultima_posicion_lng` no nulos)

### Resolución de Problemas

**Conductor no aparece en el mapa:**
1. Verificar que el conductor esté marcado como **Activo** en el admin
2. Verificar que haya enviado ubicación GPS recientemente (< 30 min)
3. Verificar que el conductor tenga permisos de GPS en su smartphone
4. Revisar que esté logueado en el dashboard móvil

**El mapa no carga:**
1. Verificar conexión a internet
2. Verificar que la API Key de Mapbox sea válida
3. Revisar la consola del navegador (F12) para errores

**GPS no se actualiza:**
1. Verificar permisos de ubicación en el navegador
2. Verificar que el conductor tenga el dashboard abierto
3. Verificar conexión de datos del smartphone

---

## 🚀 Flujo Completo

### Flujo de Trabajo Típico:

1. **Admin crea conductor:**
   - Ingresa datos básicos en `/admin/drivers/driver/add/`
   - Guarda → Sistema crea usuario automáticamente

2. **Conductor se loguea:**
   - Va a `/driver/login/`
   - Ingresa credenciales: `juan_perez` / `driver123`
   - Acepta permisos de GPS

3. **Conductor usa dashboard:**
   - Ve sus entregas asignadas
   - GPS se actualiza automáticamente
   - Navega a destinos con Google Maps

4. **Admin monitorea:**
   - Va a `/monitoring/`
   - Ve ubicación en tiempo real de todos los conductores
   - Puede hacer click para ver detalles

---

## 📞 Comandos Útiles

### Crear/Resetear Superusuario
```bash
# Crear o resetear admin con contraseña personalizada
python manage.py reset_admin --username=admin --password=1234

# Crear otro usuario admin
python manage.py reset_admin --username=operador --password=ops2024
```

### Ver Usuarios Existentes
```bash
# Entrar a shell de Django
python manage.py shell

# Listar todos los usuarios
from django.contrib.auth.models import User
for user in User.objects.all():
    print(f"{user.username} - {'Superuser' if user.is_superuser else 'User'}")
```

### Ver Conductores con GPS Activo
```bash
python manage.py shell

from apps.drivers.models import Driver
from django.utils import timezone
from datetime import timedelta

time_threshold = timezone.now() - timedelta(minutes=30)
drivers = Driver.objects.filter(
    activo=True,
    ultima_actualizacion_posicion__gte=time_threshold
)

for driver in drivers:
    print(f"{driver.nombre} - GPS: {driver.ultima_posicion_lat}, {driver.ultima_posicion_lng}")
```

---

## ✅ Resumen de Características

### Sistema de Administración
- ✅ Superusuario creado: `admin` / `1234`
- ✅ Panel de admin de Django completamente funcional
- ✅ Creación automática de usuarios para conductores
- ✅ Gestión completa de conductores desde el admin

### Sistema de Monitoreo GPS
- ✅ Mapa real con Mapbox (Santiago, Chile)
- ✅ Tracking en tiempo real de conductores
- ✅ Actualización automática cada 15 segundos
- ✅ Vista de sidebar con conductores activos
- ✅ Historial de ubicaciones GPS
- ✅ API REST completa para GPS

### Dashboard de Conductores
- ✅ Login con autenticación
- ✅ GPS automático desde smartphone
- ✅ Visualización de entregas asignadas
- ✅ Navegación con Google Maps
- ✅ Botón manual de actualización GPS

---

## 🎯 Todo está Listo

El sistema **ya está completamente funcional**:

1. ✅ **Superusuario creado** con las credenciales solicitadas (`admin` / `1234`)
2. ✅ **Creación de usuarios de conductores** automática desde el admin
3. ✅ **Mapa real con Mapbox** en la vista de monitoreo (`/monitoring/`)
4. ✅ **GPS desde smartphone** funcionando en el dashboard de conductores

**No se requieren cambios adicionales en el código** - todo está implementado y funcionando.

---

Última actualización: 12 de Octubre, 2025
