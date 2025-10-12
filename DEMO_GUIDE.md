# Demo Guide - Driver Authentication & GPS Tracking System

## Quick Start Demo

### Step 1: Create a Driver User (Admin)

1. Navigate to Django Admin: `http://localhost:8000/admin/`
2. Login with admin credentials
3. Go to **Drivers** section
4. Click **Add Driver** or edit existing driver
5. Fill in driver details:
   - Name: Juan Pérez
   - RUT: 12345678-9
   - Phone: +56912345678
   - Check ✓ Presente
   - Check ✓ Activo
   - Leave **User** field blank (will auto-create)
6. Click **Save**
7. **Important**: Note the success message showing username and password:
   ```
   Usuario creado: juan_pérez / Contraseña: driver123
   (cambiar después del primer login)
   ```

### Step 2: Driver Login

1. Navigate to: `http://localhost:8000/driver/login/`
2. You'll see a beautiful login page with:
   - Truck icon 🚚
   - "Dashboard del Conductor" title
   - Username and password fields
3. Enter credentials:
   - Username: `juan_pérez`
   - Password: `driver123`
4. Click **Iniciar Sesión**
5. You'll be redirected to the driver dashboard

### Step 3: Grant Permissions

When the dashboard loads, you'll see two permission requests:

**GPS Permission:**
```
┌─────────────────────────────────────────────────┐
│ localhost wants to:                             │
│ Know your location                              │
│                                                 │
│ [Block]  [Allow]                                │
└─────────────────────────────────────────────────┘
```
Click **Allow**

**Notification Permission:**
```
┌─────────────────────────────────────────────────┐
│ localhost wants to:                             │
│ Show notifications                              │
│                                                 │
│ [Block]  [Allow]                                │
└─────────────────────────────────────────────────┘
```
Click **Allow**

### Step 4: View Assignments

After granting permissions, you'll see:

**Dashboard Header:**
```
👤 Juan Pérez                    [Activo] [Cerrar Sesión]
Entregas del día: 1/3 • 📍 Ubicación: Activa (±12m)
```

**Assignment Card Example:**
```
╔═══════════════════════════════════════════════════╗
║ 📦 ABCD1234567                                    ║
║                                                   ║
║ Cliente: Coca-Cola Andina SA                      ║
║ Estado: asignado                                  ║
║ Fecha: 12/10/2025 09:00                           ║
║                                                   ║
║ 📍 Presentarse en:                                ║
║ ─────────────────────────────────────────         ║
║ CD Maipú                                          ║
║ 📍 Av. Pajaritos 3000, Maipú, RM                  ║
║ 📞 +56221234567                                   ║
║ 🕐 Horario: 8:00 - 18:00                          ║
║                                                   ║
║ ⏱️ ETA: 25 minutos                                 ║
║ 📏 Distancia: 15.5 km                             ║
║                                                   ║
║ ℹ️ Observaciones:                                  ║
║ Entregar antes de las 15:00. Coordinar con       ║
║ encargado de bodega al llegar.                    ║
║                                                   ║
║ [🗺️ Cómo llegar (Google Maps)]                    ║
╚═══════════════════════════════════════════════════╝
```

### Step 5: GPS Tracking in Action

**What happens automatically:**
1. Dashboard gets current GPS position
2. Sends position to server: `POST /api/drivers/1/track_location/`
3. Updates every 30 seconds in background
4. Header shows accuracy: "📍 Ubicación: Activa (±10m)"

**Behind the scenes:**
```javascript
// Continuous tracking
navigator.geolocation.watchPosition(
    position => {
        // Send to server every 30 seconds
        sendLocationToServer({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy
        });
    },
    { enableHighAccuracy: true }
);
```

### Step 6: Monitor Drivers (Admin/Operations)

1. Navigate to: `http://localhost:8000/monitoring/`
2. You'll see the monitoring dashboard with:

**Left Sidebar:**
```
┌─────────────────────────┐
│ Conductores Activos [2] │
├─────────────────────────┤
│                         │
│ ┌─────────────────────┐ │
│ │ 🟢 Juan Pérez       │ │
│ │ 📦 ABCD1234567      │ │
│ │ 📍 CD Maipú         │ │
│ │ ⏱️ ETA: 25 min      │ │
│ │ 🕐 Hace 2 min       │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ 🟢 María González   │ │
│ │ 📦 EFGH9876543      │ │
│ │ 📍 CD Quilicura     │ │
│ │ ⏱️ ETA: 35 min      │ │
│ │ 🕐 Hace 1 min       │ │
│ └─────────────────────┘ │
│                         │
└─────────────────────────┘
```

**Right Map Area:**
```
┌────────────────────────────────────────┐
│  ⓘ Última actualización: 16:30:45     │
│                                        │
│         [Mapbox Map]                   │
│                                        │
│    📍 Juan (Marker)                    │
│     ╲                                  │
│      ╲ (dashed route)                  │
│       ╲                                │
│        📍 CD Maipú (Destination)       │
│                                        │
│                                        │
│    📍 María (Marker)                   │
│     ╲                                  │
│      ╲ (dashed route)                  │
│       ╲                                │
│        📍 CD Quilicura (Destination)   │
│                                        │
│                                        │
│  [🔍] [+] [-] [⛶]  (Map controls)     │
└────────────────────────────────────────┘
```

**Click on a driver:**
- Map zooms to driver location
- Popup appears with details
- Card in sidebar highlights

**Auto-refresh:**
- Updates every 15 seconds
- Shows timestamp in corner
- Smooth marker transitions

### Step 7: Assign a Container (Trigger Notification)

1. In Django Admin, go to **Programaciones**
2. Click on a programación
3. Assign it to driver Juan Pérez
4. **Result**: Notification is created:
   ```
   Tipo: asignacion_conductor
   Mensaje: "Se te ha asignado el contenedor ABCD1234567 
            para entregar en CD Maipú"
   Estado: pendiente
   ```
5. If driver has dashboard open with notification permission:
   - Browser notification appears
   - Shows container and CD info

---

## API Testing Examples

### 1. Get Driver Info (Authenticated)

**Request:**
```bash
curl -X GET http://localhost:8000/api/drivers/1/my_info/ \
  -H "Cookie: sessionid=..." \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "success": true,
  "driver": {
    "id": 1,
    "nombre": "Juan Pérez",
    "username": "juan_pérez",
    "presente": true,
    "activo": true,
    "num_entregas_dia": 1,
    "max_entregas_dia": 3,
    "cumplimiento_porcentaje": "95.50"
  },
  "programaciones": [
    {
      "id": 10,
      "container": {
        "numero": "ABCD1234567",
        "tipo": "20HC",
        "estado": "asignado"
      },
      "cd": {
        "nombre": "CD Maipú",
        "direccion": "Av. Pajaritos 3000, Maipú",
        "lat": -33.5089,
        "lng": -70.7634,
        "telefono": "+56221234567",
        "horario": "8:00 - 18:00"
      },
      "fecha_programada": "2025-10-12T09:00:00Z",
      "cliente": "Coca-Cola Andina SA",
      "direccion_entrega": "Av. Principal 123, Santiago",
      "observaciones": "Entregar antes de las 15:00",
      "eta_minutos": 25,
      "distancia_km": 15.5
    }
  ]
}
```

### 2. Track Location

**Request:**
```bash
curl -X POST http://localhost:8000/api/drivers/1/track_location/ \
  -H "Cookie: sessionid=..." \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -33.4489,
    "lng": -70.6693,
    "accuracy": 10.5
  }'
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Ubicación registrada",
  "location": {
    "id": 123,
    "driver": 1,
    "driver_name": "Juan Pérez",
    "lat": "-33.448900",
    "lng": "-70.669300",
    "accuracy": 10.5,
    "timestamp": "2025-10-12T16:30:45.123Z"
  }
}
```

### 3. Get Active Locations

**Request:**
```bash
curl -X GET http://localhost:8000/api/drivers/active_locations/
```

**Response:**
```json
{
  "success": true,
  "total": 2,
  "drivers": [
    {
      "id": 1,
      "nombre": "Juan Pérez",
      "lat": -33.4489,
      "lng": -70.6693,
      "ultima_actualizacion": "2025-10-12T16:30:45Z",
      "telefono": "+56912345678",
      "container": "ABCD1234567",
      "cd_destino": "CD Maipú",
      "cd_lat": -33.5089,
      "cd_lng": -70.7634,
      "eta_minutos": 25
    },
    {
      "id": 2,
      "nombre": "María González",
      "lat": -33.3789,
      "lng": -70.5693,
      "ultima_actualizacion": "2025-10-12T16:31:00Z",
      "telefono": "+56987654321",
      "container": "EFGH9876543",
      "cd_destino": "CD Quilicura",
      "cd_lat": -33.3589,
      "cd_lng": -70.6834,
      "eta_minutos": 35
    }
  ]
}
```

---

## Database Queries Examples

### Check Drivers with Users

```python
from apps.drivers.models import Driver
from django.contrib.auth.models import User

# Get all drivers with users
drivers_with_users = Driver.objects.exclude(user=None)
for driver in drivers_with_users:
    print(f"{driver.nombre} → {driver.user.username}")

# Output:
# Juan Pérez → juan_pérez
# María González → maría_gonzález
# Pedro Sánchez → pedro_sánchez
```

### Check GPS Tracking History

```python
from apps.drivers.models import DriverLocation

# Get recent locations for a driver
driver = Driver.objects.get(nombre="Juan Pérez")
recent_locations = driver.location_history.all()[:10]

for loc in recent_locations:
    print(f"{loc.timestamp}: ({loc.lat}, {loc.lng}) ±{loc.accuracy}m")

# Output:
# 2025-10-12 16:30:45: (-33.4489, -70.6693) ±10.5m
# 2025-10-12 16:30:15: (-33.4492, -70.6695) ±12.0m
# 2025-10-12 16:29:45: (-33.4495, -70.6698) ±11.5m
```

### Check Notifications

```python
from apps.notifications.models import Notification

# Get pending notifications for a programación
notifications = Notification.objects.filter(
    tipo='asignacion_conductor',
    estado='pendiente'
)

for notif in notifications:
    print(f"{notif.programacion.driver.nombre}: {notif.mensaje}")

# Output:
# Juan Pérez: Se te ha asignado el contenedor ABCD1234567 para entregar en CD Maipú
```

---

## Mobile Testing

### Testing on Mobile Device

1. Connect phone to same network as dev server
2. Find your computer's local IP (e.g., 192.168.1.100)
3. On phone, navigate to: `http://192.168.1.100:8000/driver/login/`
4. Login with driver credentials
5. Grant GPS permission when prompted
6. Grant notification permission when prompted
7. GPS will track automatically using phone's location

**Mobile-Specific Features:**
- Responsive layout adapts to phone screen
- Touch-friendly buttons and cards
- GPS uses phone's high-accuracy sensors
- Works in Chrome, Safari, Firefox mobile
- Can add to home screen (PWA-like)

---

## Production Deployment Notes

### Required Environment Variables

```bash
# .env file
MAPBOX_API_KEY=pk.your_actual_mapbox_token_here
DATABASE_URL=postgresql://user:pass@host/dbname
SECRET_KEY=your_long_random_secret_key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### HTTPS Requirement

In production, GPS and Notifications **require HTTPS**:
- GPS: Works only on HTTPS (except localhost)
- Notifications: Works only on HTTPS (except localhost)
- Use Let's Encrypt for free SSL certificates

### First Deployment Steps

1. Run migrations: `python manage.py migrate`
2. Create superuser: `python manage.py createsuperuser`
3. Create drivers in admin
4. Share credentials with drivers
5. Monitor at `/monitoring/`

---

## Support & Troubleshooting

### GPS Not Working?

**Check:**
1. Browser permissions granted?
2. Using HTTPS in production?
3. Device has GPS enabled?
4. Check browser console for errors

**Fix:**
- Go to browser settings → Site permissions → Location
- Enable for your site
- Refresh page

### Notifications Not Showing?

**Check:**
1. Notification permission granted?
2. Using HTTPS in production?
3. Browser supports notifications?

**Fix:**
- Go to browser settings → Site permissions → Notifications
- Enable for your site
- Refresh page and re-request permission

### Login Issues?

**Check:**
1. Username and password correct?
2. User has driver_profile relationship?
3. Driver is activo=True?

**Fix:**
- Reset password in Django admin
- Verify driver.user is set
- Check error message on login page

---

## Demo Video Script

If creating a demo video, follow this script:

1. **[0:00-0:30]** Show admin creating driver user
2. **[0:30-1:00]** Navigate to login page, show UI
3. **[1:00-1:30]** Login as driver, grant permissions
4. **[1:30-2:30]** Show dashboard with assignments
5. **[2:30-3:00]** Click Google Maps button
6. **[3:00-4:00]** Show monitoring page with live map
7. **[4:00-4:30]** Click driver on map, show details
8. **[4:30-5:00]** Show auto-refresh working

---

## Success Metrics

After implementation, you should see:

- ✅ 6 drivers with user accounts
- ✅ Login page accessible at `/driver/login/`
- ✅ Dashboard protected (requires auth)
- ✅ GPS tracking updating every 30 seconds
- ✅ Monitoring page showing active drivers
- ✅ Notifications created on assignment
- ✅ All 12 tests passing
- ✅ No console errors

Congratulations! The system is fully operational! 🎉
