# ⚡ Inicio Rápido - SoptraLoc TMS

## 🔐 Paso 1: Acceder al Sistema

### Credenciales de Admin
```
URL Admin: http://localhost:8000/admin/
Username: admin
Password: 1234
```

**En producción (Render):**
```
URL Admin: https://soptraloc.onrender.com/admin/
Username: admin
Password: 1234
```

---

## 👥 Paso 2: Crear un Conductor

1. **Ir a Drivers:**
   - En el admin, click en **"Drivers"**
   - Click en **"ADD DRIVER"**

2. **Llenar datos:**
   ```
   Nombre: Juan Pérez
   RUT: 12.345.678-9
   Teléfono: +56912345678
   
   ✓ Presente
   ✓ Activo
   
   Max entregas/día: 3
   ```

3. **Dejar campo "User" vacío**
   - El sistema creará el usuario automáticamente

4. **Click en "SAVE"**

### ✅ Usuario Creado Automáticamente

El sistema creó:
```
Username: juan_perez
Password: driver123
```

---

## 📱 Paso 3: Conductor Usa el Dashboard

El conductor puede entrar a:
```
URL: http://localhost:8000/driver/login/
Username: juan_perez
Password: driver123
```

**Funcionalidades:**
- ✓ Ver entregas asignadas
- ✓ GPS automático desde smartphone
- ✓ Navegación con Google Maps
- ✓ Actualizar ubicación manualmente

---

## 🗺️ Paso 4: Monitorear en Tiempo Real

### Acceder al Monitoreo
```
URL: http://localhost:8000/monitoring/
```

**Verás:**
- 🗺️ Mapa real de Mapbox (Santiago, Chile)
- 📍 Ubicación de conductores en tiempo real
- 📊 Lista de conductores activos
- ⏱️ Actualización automática cada 15 segundos

### Cómo Funciona el GPS

1. **Conductor se loguea** en `/driver/login/`
2. **Acepta permisos de GPS** en su smartphone
3. **GPS se activa automáticamente** al usar el dashboard
4. **Ubicación se envía al servidor** periódicamente
5. **Aparece en el mapa** en tiempo real

---

## 🔧 Comandos Útiles

### Crear Otro Admin
```bash
python manage.py reset_admin --username=operador --password=ops2024
```

### Ver Conductores Activos
```bash
python manage.py shell

from apps.drivers.models import Driver
Driver.objects.filter(activo=True)
```

### Resetear Contraseña de Admin
```bash
python manage.py reset_admin --username=admin --password=nueva_password
```

---

## 📍 URLs Importantes

| Descripción | URL |
|-------------|-----|
| Admin Panel | `/admin/` |
| Login Conductor | `/driver/login/` |
| Dashboard Conductor | `/driver/dashboard/` |
| Monitoreo GPS | `/monitoring/` |
| API Drivers | `/api/drivers/` |
| GPS Tracking | `/api/drivers/{id}/track_location/` |
| Conductores Activos | `/api/drivers/active_locations/` |

---

## ⚠️ Seguridad en Producción

**IMPORTANTE:** En producción, cambiar la contraseña del admin:

1. Ir a `/admin/`
2. **Authentication and Authorization** → **Users**
3. Click en `admin`
4. **Change password form**
5. Ingresar contraseña segura
6. **SAVE**

---

## ✅ Todo Listo

El sistema está completamente funcional:

- ✅ Admin creado: `admin` / `1234`
- ✅ Crear conductores desde admin
- ✅ Usuarios auto-creados con password `driver123`
- ✅ Mapa real con Mapbox
- ✅ GPS desde smartphones
- ✅ Monitoreo en tiempo real

**¡Puedes empezar a usarlo inmediatamente!**
