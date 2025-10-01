# 🚀 GUÍA RÁPIDA DE ACCESO - DASHBOARD LOCAL

## ✅ SISTEMA CORRIENDO EN: http://localhost:8000

---

## 🔐 CREDENCIALES DE ACCESO

### Superusuario Admin
- **Usuario:** `admin`
- **URL Login:** http://localhost:8000/accounts/login/
- **Dashboard:** http://localhost:8000/dashboard/
- **Admin Panel:** http://localhost:8000/admin/

---

## 🎯 PASOS PARA VER EL RELOJ FUNCIONANDO

### 1. Abrir navegador
```
Ctrl+Click en: http://localhost:8000/
```

### 2. Verificar el reloj en navbar
Deberías ver en la esquina superior derecha:
```
┌─────────────────┐
│    22:45:32     │ ← Hora en verde fosforescente
│  MIÉ 30 SEP 2025│ ← Fecha en azul claro
└─────────────────┘
```

### 3. Verificar badge urgente
Si hay contenedores urgentes verás:
```
     [3] ← Badge rojo pulsante
```

### 4. Probar el dashboard
```
1. Click en "Dashboard" en navbar
2. Te redirigirá a login si no estás autenticado
3. Ingresar usuario: admin (con tu contraseña)
4. Verás estadísticas y contenedores urgentes
```

---

## 🖥️ ABRIR EN VS CODE SIMPLE BROWSER

Si quieres ver el dashboard dentro de VS Code:

1. Presiona `Ctrl+Shift+P`
2. Escribe: "Simple Browser: Show"
3. Ingresa la URL: `http://localhost:8000`

---

## 📊 URLS DISPONIBLES

### Páginas principales:
- **Home:** http://localhost:8000/
- **Dashboard:** http://localhost:8000/dashboard/
- **Admin Panel:** http://localhost:8000/admin/
- **Pase de Lista:** http://localhost:8000/drivers/attendance/
- **Alertas:** http://localhost:8000/drivers/alerts/

### APIs (requieren autenticación):
- **Contenedores urgentes:** http://localhost:8000/api/v1/containers/urgent/
- **Todos los contenedores:** http://localhost:8000/api/v1/containers/
- **Rutas:** http://localhost:8000/api/v1/routing/routes/
- **Predicción ML:** http://localhost:8000/api/v1/routing/predict-time/

---

## 🔍 VERIFICAR QUE EL RELOJ FUNCIONA

### Método 1: Consola del navegador
```javascript
// Abrir DevTools (F12)
// Ir a Console
// Verificar que no hay errores
// Deberías ver:
"🕐 Iniciando reloj ATC..."
"✅ Reloj ATC iniciado correctamente"
```

### Método 2: Inspeccionar elementos
```
1. Click derecho en el reloj
2. Seleccionar "Inspeccionar"
3. Verificar que existe:
   <div id="atc-clock" class="atc-clock">
     <div id="atc-clock-time">22:45:32</div>
     <div id="atc-clock-date">MIÉ 30 SEP 2025</div>
   </div>
```

### Método 3: Verificar actualizaciones
```
1. Mira el reloj en la pantalla
2. Los segundos deben cambiar cada segundo
3. Formato: HH:MM:SS (ej: 22:45:32 → 22:45:33)
```

---

## 🚨 VERIFICAR SISTEMA DE ALERTAS

### Si hay contenedores urgentes:
1. Verás un badge rojo con número en la esquina del reloj
2. Click en el badge abre un modal
3. Modal muestra lista de contenedores urgentes
4. Cada contenedor muestra:
   - Número de contenedor
   - Cliente
   - Ubicación
   - Fecha programada
   - Tiempo restante
   - Nivel de urgencia (crítico/alto/medio)

### Crear contenedor urgente de prueba:
```bash
# En otra terminal
cd /workspaces/soptraloc/soptraloc_system
python manage.py shell

# En el shell de Django:
from apps.containers.models import Container
from django.utils import timezone
from datetime import timedelta

# Crear contenedor que vence en 1 hora
container = Container.objects.create(
    container_number="TEST999999",
    status="PROGRAMADO",
    scheduled_date=timezone.now().date(),
    scheduled_time=(timezone.now() + timedelta(hours=1)).time(),
)
print(f"Contenedor urgente creado: {container.container_number}")
```

---

## 🎨 CARACTERÍSTICAS VISUALES DEL RELOJ

### Colores:
- **Fondo:** Gradiente azul (#1e3c72 → #2a5298)
- **Hora:** Verde fosforescente (#00ff00) con glow
- **Fecha:** Azul claro (#a0cfff)
- **Border:** Blanco semi-transparente
- **Sombra:** rgba(0, 0, 0, 0.3)

### Tipografía:
- **Font:** Courier New (monospace)
- **Hora size:** 28px, weight 700
- **Fecha size:** 13px, weight 600
- **Letter spacing:** 2px (hora), 1px (fecha)

### Efectos:
- **Text shadow:** 0 0 10px rgba(0, 255, 0, 0.5)
- **Box shadow:** 0 4px 15px rgba(0, 0, 0, 0.3)
- **Border radius:** 8px
- **Padding:** 8px 16px

---

## 🧪 COMANDOS DE PRUEBA

### Verificar que el servidor está corriendo:
```bash
ps aux | grep "manage.py runserver"
```

### Ver logs en tiempo real:
```bash
tail -f /tmp/django.log
```

### Probar endpoint de urgentes:
```bash
# Sin autenticación (debería dar 401 o redirect)
curl http://localhost:8000/api/v1/containers/urgent/

# Con sesión (desde navegador después de login)
# Ir a: http://localhost:8000/api/v1/containers/urgent/
```

### Reiniciar servidor si es necesario:
```bash
pkill -f "manage.py runserver"
cd /workspaces/soptraloc/soptraloc_system
python manage.py runserver 0.0.0.0:8000
```

---

## 📱 TESTING EN MÓVIL

### Para probar en dispositivo móvil:
1. **Encontrar tu IP local:**
```bash
hostname -I | awk '{print $1}'
```

2. **Configurar ALLOWED_HOSTS:**
```bash
# Editar config/settings.py
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'TU_IP_LOCAL']
```

3. **Reiniciar servidor:**
```bash
python manage.py runserver 0.0.0.0:8000
```

4. **Acceder desde móvil:**
```
http://TU_IP_LOCAL:8000
```

---

## 🎯 CHECKLIST DE VERIFICACIÓN

Marca cada item cuando lo verifiques:

- [ ] Servidor corriendo en http://localhost:8000
- [ ] Página principal carga sin errores (HTTP 200)
- [ ] Reloj visible en navbar superior derecha
- [ ] Hora se actualiza cada segundo
- [ ] Fecha muestra formato correcto (DÍA DD MES YYYY)
- [ ] Colores correctos (verde hora, azul fecha, fondo azul oscuro)
- [ ] Dashboard requiere login (redirect a /accounts/login/)
- [ ] Login con admin funciona
- [ ] Dashboard muestra estadísticas
- [ ] Badge urgente aparece si hay contenedores (o está oculto)
- [ ] Modal de urgentes se abre al hacer click en badge
- [ ] No hay errores en consola del navegador
- [ ] JavaScript realtime-clock.js se carga correctamente
- [ ] API /api/v1/containers/urgent/ responde (requiere auth)

---

## 🎉 PRÓXIMO PASO

**Una vez verificado localmente, el sistema está listo para producción en Render.com**

El deploy se activa automáticamente al hacer push a GitHub main branch.

**Verificar deploy:**
1. Ir a: https://dashboard.render.com
2. Seleccionar el servicio "soptraloc"
3. Ver la pestaña "Logs"
4. Esperar mensaje: "Deploy live for ..."
5. Probar URL de producción

---

## 💡 TIPS

- **DevTools:** Presiona F12 para abrir herramientas de desarrollador
- **Responsive:** Usa DevTools → Device Toolbar (Ctrl+Shift+M) para simular móvil
- **Network:** Tab Network en DevTools muestra todas las peticiones
- **Console:** Tab Console muestra mensajes del reloj y errores JS
- **Reload:** Ctrl+Shift+R para recargar sin caché

---

## 📞 SOPORTE

Si algo no funciona:
1. Revisar logs: `tail -f /tmp/django.log`
2. Verificar consola del navegador (F12)
3. Confirmar que el servidor está corriendo
4. Verificar que collectstatic se ejecutó
5. Limpiar caché del navegador (Ctrl+Shift+Delete)

---

*Guía rápida de acceso - Actualizada: 30/09/2025 22:46 CLT*
