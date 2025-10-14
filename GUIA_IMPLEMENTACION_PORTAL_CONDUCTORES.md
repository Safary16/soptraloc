# 🚚 Guía de Implementación: Portal de Conductores

## 📋 Resumen

Este documento explica cómo está implementado el Portal de Conductores y qué pasos seguir para utilizarlo correctamente en producción.

---

## 🎯 Funcionalidades Implementadas

### 1. **Autenticación de Conductores**
- Login con usuario y contraseña
- Sesión persistente
- Token JWT para APIs
- Ruta: `/driver/login/`

### 2. **Dashboard del Conductor**
- Vista de contenedores asignados
- Tracking GPS automático
- Notificaciones en tiempo real
- Ruta: `/driver/dashboard/`

### 3. **Flujo de Trabajo Completo**

#### Estado: ASIGNADO
```
Conductor ve: [ Contenedor asignado ]
Botón visible: "Iniciar Ruta"
Acción: Clic en botón
```

#### Confirmación de Patente
```
Sistema: "🚚 Confirme la PATENTE del vehículo"
Conductor: Ingresa "ABC123"
Sistema: 
  ✓ Valida patente (si tiene asignada)
  ✓ Obtiene GPS automáticamente
  ✓ Registra inicio de ruta
```

#### Estado: EN RUTA
```
Sistema: 
  - GPS se actualiza cada 30 segundos
  - Indicador: "GPS: Activo ±15m"
Botón visible: "Notificar Arribo"
Acción: Al llegar al CD, clic en botón
```

#### Estado: ENTREGADO
```
Sistema: Registra llegada al CD
Botón visible: "Notificar Vacío"
Acción: Después de descargar, clic en botón
```

#### Estado: VACÍO
```
Sistema: Contenedor listo para retorno
Ciclo: Se marca como completado
```

---

## 🛠️ Pasos de Implementación

### Paso 1: Crear Conductores en Admin

1. Acceder a `/admin/drivers/driver/`
2. Crear nuevo conductor con:
   - Nombre y apellido
   - RUT (opcional)
   - Teléfono
   - **Patente del vehículo** (importante para validación)
   - Usuario asociado (crear desde User admin)
   - Marcar como "Activo"

**Ejemplo de creación de conductor:**
```python
# Via Django shell
python manage.py shell

from django.contrib.auth.models import User
from apps.drivers.models import Driver

# Crear usuario
user = User.objects.create_user(
    username='conductor1',
    password='contraseña123',
    first_name='Juan',
    last_name='Pérez'
)

# Crear conductor
driver = Driver.objects.create(
    user=user,
    nombre='Juan',
    apellido='Pérez',
    rut='12345678-9',
    telefono='+56912345678',
    patente='ABC123',
    activo=True
)
```

### Paso 2: Asignar Contenedores a Conductores

#### Opción A: Manual desde Admin
1. Ir a `/admin/programaciones/programacion/`
2. Crear nueva programación:
   - Container: Seleccionar contenedor en estado "programado"
   - Driver: Seleccionar conductor activo
   - Fecha programada: Fecha/hora de la entrega
   - CD destino: Centro de distribución
   - Tipo: "manual" o "automatica"

#### Opción B: Desde Panel de Operaciones
1. Acceder a `/operaciones/`
2. Ir a la pestaña "Pre-Asignación"
3. Seleccionar contenedor programado
4. Seleccionar conductor disponible
5. Clic en "Crear Pre-Asignación"

### Paso 3: Conductor Accede al Portal

1. Conductor navega a `/driver/login/`
2. Ingresa credenciales (username + password)
3. Es redirigido a `/driver/dashboard/`
4. Ve sus contenedores asignados

### Paso 4: Flujo del Conductor

1. **Ver asignaciones**: Dashboard muestra contenedores
2. **Iniciar ruta**: 
   - Clic en "Iniciar Ruta"
   - Confirmar patente
   - GPS se activa automáticamente
3. **Notificar arribo**:
   - Al llegar al CD, clic en "Notificar Arribo"
   - Sistema registra hora y ubicación
4. **Notificar vacío**:
   - Después de descarga, clic en "Notificar Vacío"
   - Contenedor pasa a estado "vacío"

---

## 🔧 Configuración Técnica

### Requisitos Backend

**Archivos modificados:**
- `apps/drivers/models.py` - Campo patente
- `apps/drivers/serializers.py` - Serialización de datos
- `apps/programaciones/models.py` - Tracking de rutas
- `apps/programaciones/views.py` - Endpoints API

**Nuevos endpoints API:**
```python
POST /api/programaciones/{id}/iniciar_ruta/
POST /api/programaciones/{id}/notificar_arribo/
POST /api/programaciones/{id}/notificar_vacio/
```

### Requisitos Frontend

**Archivos:**
- `templates/driver_login.html` - Login
- `templates/driver_dashboard.html` - Dashboard
- Uso de GPS API del navegador
- Actualización automática cada 30s

### Permisos Necesarios

1. **Geolocalización**: El navegador solicita permiso para GPS
2. **Notificaciones** (opcional): Para alertas push
3. **Cookies**: Para mantener sesión

---

## 📱 Funcionalidades GPS

### Activación Automática
- Se activa al hacer "Iniciar Ruta"
- Solicita permiso al navegador
- Actualiza cada 30 segundos

### Precisión
- Alta precisión: enableHighAccuracy: true
- Timeout: 5 segundos
- Edad máxima: 0 (siempre dato fresco)

### Visualización
Indicador en esquina superior derecha:
- 🟢 GPS: Activo ±15m (verde si activo)
- 🔴 GPS: Inactivo (rojo si no hay señal)

---

## 🔒 Seguridad

### Autenticación
- Login con username/password
- Sesión en cookies (httponly)
- CSRF protection habilitado

### Validaciones
- Patente validada contra registro del conductor
- GPS verificado antes de permitir acciones
- Estados validados en backend

---

## 🐛 Troubleshooting

### Problema: "GPS no se activa"
**Solución:**
1. Verificar permisos del navegador
2. Revisar que sea HTTPS (en producción)
3. Comprobar que el dispositivo tenga GPS

### Problema: "No aparecen contenedores asignados"
**Solución:**
1. Verificar que existan programaciones para el conductor
2. Revisar que el conductor esté marcado como "activo"
3. Verificar que el contenedor esté en estado "asignado"

### Problema: "Error al iniciar ruta"
**Solución:**
1. Verificar que la patente esté registrada en el conductor
2. Comprobar permisos GPS
3. Revisar logs del servidor

---

## 📊 Monitoreo y Logs

### Eventos Registrados
- Inicio de ruta (con GPS)
- Arribo a destino (con GPS)
- Notificación de vacío
- Errores de GPS

### Revisar logs:
```bash
# En producción
tail -f /var/log/gunicorn/error.log

# En desarrollo
python manage.py runserver
```

---

## 🚀 Deployment en Producción

### 1. Migrar Base de Datos
```bash
python manage.py migrate drivers
python manage.py migrate programaciones
```

### 2. Recolectar Archivos Estáticos
```bash
python manage.py collectstatic --noinput
```

### 3. Reiniciar Servidor
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 4. Verificar HTTPS
El GPS requiere HTTPS en producción. Asegurar que:
- Certificado SSL válido
- Redirección HTTP → HTTPS activa

---

## 📚 Documentación Adicional

- **Flujo técnico**: Ver `CAMBIOS_IMPORTADOR_Y_PORTAL.md`
- **Testing**: Ver `CHECKLIST_TESTING.md`
- **Guía rápida**: Ver `GUIA_RAPIDA_CAMBIOS.md`
- **GPS detallado**: Ver `DRIVER_GPS_IMPLEMENTATION.md`
- **Notificaciones**: Ver `DRIVER_NOTIFICATIONS_GUIDE.md`

---

## ✅ Checklist de Implementación

- [ ] Crear conductores en admin con patentes
- [ ] Crear usuarios para cada conductor
- [ ] Asignar contenedores a conductores
- [ ] Verificar permisos GPS en navegadores
- [ ] Probar flujo completo (asignado → vacío)
- [ ] Configurar HTTPS en producción
- [ ] Reiniciar servidor después de cambios
- [ ] Capacitar a conductores en el uso

---

## 💡 Mejores Prácticas

1. **Siempre asignar patente** al crear conductor
2. **Verificar GPS** antes de salir a ruta
3. **No cerrar navegador** durante ruta activa
4. **Mantener batería cargada** para GPS continuo
5. **Usar red móvil estable** para sincronización

---

## 🆘 Soporte

Para problemas técnicos:
1. Revisar esta guía
2. Consultar logs del servidor
3. Verificar documentación adicional
4. Contactar a administrador del sistema

---

**Última actualización:** 2025-10-14
**Versión:** 2.0
