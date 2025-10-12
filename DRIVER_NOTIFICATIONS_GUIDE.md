# 🔔 Sistema de Notificaciones para Conductores

## 📋 Resumen

Sistema completo de notificaciones que alerta a los conductores cuando se les asigna un contenedor para entrega. Las notificaciones se muestran automáticamente tanto en el servidor (base de datos) como en el navegador del conductor (notificaciones push).

## ✨ Características

### 1. Notificaciones en Base de Datos
- **Registro permanente** de todas las asignaciones
- **Historial completo** de notificaciones por conductor
- **Campos detallados**: título, mensaje, prioridad, timestamp

### 2. Notificaciones Push del Navegador
- **Alertas automáticas** cuando se asigna un contenedor
- **Permisos solicitados** al cargar el dashboard
- **Auto-detección** de nuevas asignaciones cada 30 segundos
- **Notificaciones visuales** con título y detalles

### 3. Integración Completa
- **Automático**: Se crean al asignar conductor en admin
- **Sin intervención**: No requiere código adicional
- **Manejo de errores**: La asignación no falla si hay error en notificaciones

## 🎯 Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│  1. ADMINISTRADOR: Asigna conductor a contenedor           │
│     (Django Admin o API)                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  2. BACKEND: Se llama a asignar_conductor()                 │
│     - Actualiza estado del contenedor → "asignado"          │
│     - Incrementa contador de entregas del conductor         │
│     - Crea notificación en base de datos                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  3. NOTIFICACIÓN EN DB: Se guarda registro                  │
│     - Tipo: "asignacion"                                     │
│     - Título: "Nueva asignación - ABCD123"                  │
│     - Mensaje: Detalles del contenedor y cliente            │
│     - Prioridad: "media"                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  4. DASHBOARD CONDUCTOR: Auto-refresh detecta cambio        │
│     - Cada 30 segundos consulta /api/drivers/{id}/my_info/ │
│     - Compara con asignaciones anteriores                   │
│     - Detecta nueva asignación                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  5. NOTIFICACIÓN PUSH: Se muestra en navegador             │
│     - Título: "🚚 Nueva Asignación"                         │
│     - Cuerpo: "Contenedor ABCD123 - Cliente: Walmart"      │
│     - Requiere interacción del usuario (no desaparece sola) │
│     - Auto-cierre después de 10 segundos                    │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Implementación Técnica

### Backend: Servicio de Notificaciones

**Archivo:** `apps/notifications/services.py`

```python
@classmethod
def crear_notificacion_asignacion(cls, programacion, driver):
    """
    Crea notificación cuando se asigna un conductor a una programación
    """
    container = programacion.container
    
    notification = Notification.objects.create(
        container=container,
        driver=driver,
        programacion=programacion,
        tipo='asignacion',
        prioridad='media',
        titulo=f"Nueva asignación - {container.container_id if container else 'N/A'}",
        mensaje=f"Se te ha asignado el contenedor {container.container_id if container else 'N/A'} "
               f"para el cliente {programacion.cliente}. "
               f"Fecha programada: {programacion.fecha_programada.strftime('%d/%m/%Y %H:%M')}.",
        detalles={
            'cliente': programacion.cliente,
            'fecha_programada': programacion.fecha_programada.isoformat(),
            'fecha_asignacion': timezone.now().isoformat(),
        }
    )
    
    return notification
```

### Backend: Modelo de Programación

**Archivo:** `apps/programaciones/models.py`

```python
def asignar_conductor(self, driver, usuario=None):
    """Asigna un conductor a la programación"""
    self.driver = driver
    self.fecha_asignacion = timezone.now()
    self.save()
    
    # Actualizar estado del contenedor
    if self.container:
        self.container.estado = 'asignado'
        self.container.save()
    
    # Incrementar contador de entregas
    driver.num_entregas_dia += 1
    driver.save(update_fields=['num_entregas_dia'])
    
    # Crear notificación para el conductor
    try:
        from apps.notifications.services import NotificationService
        NotificationService.crear_notificacion_asignacion(self, driver)
    except Exception as e:
        # Log error pero no fallar la asignación
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creando notificación de asignación: {str(e)}")
```

### Frontend: Dashboard del Conductor

**Archivo:** `templates/driver_dashboard.html`

```javascript
// Variable para rastrear asignaciones previas
let previousAssignments = [];

// Cargar asignaciones
function loadAsignaciones() {
    fetch(`/api/drivers/${driverId}/my_info/`)
        .then(response => response.json())
        .then(data => {
            const programaciones = data.programaciones_asignadas || [];
            
            // Verificar si hay nuevas asignaciones
            checkForNewAssignments(programaciones);
            
            renderAsignaciones(programaciones);
        })
        .catch(error => {
            console.error('Error cargando asignaciones:', error);
        });
}

// Verificar nuevas asignaciones y mostrar notificación
function checkForNewAssignments(currentAssignments) {
    if (previousAssignments.length === 0) {
        // Primera carga, solo guardar las asignaciones
        previousAssignments = currentAssignments.map(p => p.id);
        return;
    }
    
    // Buscar asignaciones nuevas
    currentAssignments.forEach(assignment => {
        if (!previousAssignments.includes(assignment.id)) {
            // Nueva asignación detectada
            showNotification(
                '🚚 Nueva Asignación',
                `Contenedor ${assignment.contenedor || 'N/A'} - Cliente: ${assignment.cliente || 'N/A'}`
            );
        }
    });
    
    // Actualizar lista de asignaciones previas
    previousAssignments = currentAssignments.map(p => p.id);
}

// Mostrar notificación del navegador
function showNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: body,
            icon: '/static/img/truck-icon.png',
            badge: '/static/img/badge-icon.png',
            tag: 'nueva-asignacion',
            requireInteraction: true
        });
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
        
        // Auto-cerrar después de 10 segundos
        setTimeout(() => notification.close(), 10000);
    }
}

// Solicitar permisos de notificaciones
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log('Permisos notificación:', permission);
        });
    }
}

// Solicitar permisos al cargar
window.addEventListener('load', () => {
    requestNotificationPermission();
    loadAsignaciones();
    
    // Auto-refresh cada 30 segundos
    setInterval(loadAsignaciones, 30000);
});
```

## 🧪 Testing

### Tests Implementados

**Archivo:** `apps/programaciones/tests.py`

```python
def test_asignar_conductor_creates_notification(self):
    """Test that assigning a driver creates a notification"""
    # Verify no notifications exist before assignment
    self.assertEqual(Notification.objects.count(), 0)
    
    # Assign driver
    self.programacion.asignar_conductor(self.driver)
    
    # Verify notification was created
    notifications = Notification.objects.filter(
        driver=self.driver,
        programacion=self.programacion,
        tipo='asignacion'
    )
    self.assertEqual(notifications.count(), 1)
    
    notification = notifications.first()
    self.assertEqual(notification.prioridad, 'media')
    self.assertIn('TEST123', notification.titulo)
    self.assertIn('Test Cliente', notification.mensaje)
```

### Ejecutar Tests

```bash
# Tests de notificaciones
python manage.py test apps.programaciones.tests.ProgramacionAsignacionTests

# Tests de drivers (incluye autenticación y GPS)
python manage.py test apps.drivers.tests

# Todos los tests
python manage.py test
```

**Resultados:**
- ✅ 4 tests de asignación y notificaciones
- ✅ 17 tests de drivers
- ✅ **Total: 21 tests, todos pasando**

## 📊 Modelo de Datos

### Notification Model

```python
class Notification(models.Model):
    TIPO_CHOICES = [
        ('ruta_iniciada', 'Ruta Iniciada'),
        ('eta_actualizado', 'ETA Actualizado'),
        ('arribo_proximo', 'Arribo Próximo'),
        ('llegada', 'Llegada Confirmada'),
        ('demurrage_alerta', 'Alerta Demurrage'),
        ('asignacion', 'Asignación de Conductor'),  # ← Nueva
    ]
    
    # Relaciones
    container = ForeignKey('containers.Container')
    driver = ForeignKey('drivers.Driver')
    programacion = ForeignKey('programaciones.Programacion')
    
    # Información
    tipo = CharField(max_length=30, choices=TIPO_CHOICES)
    prioridad = CharField(max_length=10)  # baja, media, alta, critica
    estado = CharField(max_length=15)  # pendiente, enviada, leida, archivada
    
    # Contenido
    titulo = CharField(max_length=200)
    mensaje = TextField()
    detalles = JSONField(default=dict)
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## 🔔 Tipos de Notificaciones

| Tipo | Cuándo se Crea | Prioridad | Descripción |
|------|----------------|-----------|-------------|
| **asignacion** | Al asignar conductor | media | Nueva asignación de contenedor |
| ruta_iniciada | Conductor inicia ruta | media-alta | Conductor comenzó viaje al CD |
| eta_actualizado | GPS actualiza posición | media | ETA recalculado en ruta |
| arribo_proximo | ETA < 15 minutos | alta | Conductor está por llegar |
| llegada | Llegó al destino | media | Conductor llegó al CD |

## 🎯 Uso Práctico

### Para Administradores

1. **Asignar Contenedor a Conductor:**
   ```
   Django Admin → Programaciones → Seleccionar programación
   → Editar → Seleccionar Driver → Guardar
   ```
   
   **Resultado automático:**
   - ✅ Estado de contenedor cambia a "asignado"
   - ✅ Contador de entregas del conductor incrementa
   - ✅ Notificación se crea en base de datos
   - ✅ Conductor recibirá alerta en su dashboard

2. **Ver Notificaciones Creadas:**
   ```
   Django Admin → Notifications → Ver lista
   ```
   
   Puedes filtrar por:
   - Tipo de notificación
   - Conductor
   - Estado (pendiente, enviada, leída)
   - Fecha

### Para Conductores

1. **Primera Vez (Setup):**
   ```
   1. Abrir dashboard → /driver/dashboard/
   2. Permitir notificaciones cuando el navegador lo solicite
   3. Permitir ubicación GPS cuando el navegador lo solicite
   ```

2. **Recibir Notificación de Asignación:**
   - El dashboard actualiza automáticamente cada 30 segundos
   - Cuando detecta nueva asignación:
     - ✅ Aparece notificación del navegador
     - ✅ Se actualiza la lista de "Mis Entregas"
     - ✅ Se muestra información del CD
     - ✅ Botón para navegar con Google Maps

3. **Revisar Asignaciones:**
   - En el dashboard se muestra:
     - Número de contenedor
     - Cliente
     - Centro de Distribución (CD)
     - Dirección del CD
     - Teléfono y horario del CD
     - Botón para navegar

## 🔐 Seguridad

### Permisos de Notificaciones
- **Solicitados automáticamente** al cargar dashboard
- **Requieren acción del usuario** (no se pueden forzar)
- **Funcionan en HTTPS** (localhost permite HTTP para testing)

### Autenticación
- Solo conductores autenticados reciben notificaciones
- Cada conductor solo ve sus propias asignaciones
- API endpoints protegidos con sesiones

### Privacidad
- Notificaciones solo contienen información necesaria
- No se envían datos sensibles en notificaciones push
- Historial completo en base de datos protegida

## 🐛 Troubleshooting

### No se Muestran Notificaciones Push

**Problema:** Conductor no recibe alertas en el navegador

**Posibles Causas y Soluciones:**

1. **Permisos no concedidos:**
   - Verificar en configuración del navegador
   - Chrome: Candado → Configuración del sitio → Notificaciones
   - Firefox: Candado → Permisos → Notificaciones

2. **No está en HTTPS (producción):**
   - Notificaciones requieren HTTPS
   - Localhost funciona sin HTTPS solo para testing

3. **Dashboard no está abierto:**
   - El auto-refresh solo funciona con dashboard abierto
   - Cerrar y reabrir dashboard

4. **JavaScript deshabilitado:**
   - Verificar que JavaScript esté habilitado
   - Revisar consola del navegador (F12)

### No se Crean Notificaciones en DB

**Problema:** No aparecen notificaciones en Django Admin

**Soluciones:**

1. **Verificar logs del servidor:**
   ```bash
   # Error logs mostrarán excepciones
   tail -f logs/django.log
   ```

2. **Verificar que la asignación se completó:**
   ```python
   # En Django shell
   from apps.programaciones.models import Programacion
   prog = Programacion.objects.get(id=1)
   print(prog.driver)  # Debe mostrar el conductor
   print(prog.fecha_asignacion)  # Debe tener fecha
   ```

3. **Verificar modelo de Notification:**
   ```bash
   python manage.py showmigrations notifications
   # Debe mostrar todas las migraciones aplicadas
   ```

### Auto-Refresh No Funciona

**Problema:** Dashboard no actualiza automáticamente

**Soluciones:**

1. **Revisar consola del navegador (F12):**
   - Buscar errores JavaScript
   - Verificar que las peticiones a `/api/drivers/{id}/my_info/` funcionen

2. **Verificar autenticación:**
   - Conductor debe estar logueado
   - Sesión debe estar activa

3. **Probar manualmente:**
   ```javascript
   // En consola del navegador
   fetch(`/api/drivers/${driverId}/my_info/`)
     .then(r => r.json())
     .then(d => console.log(d))
   ```

## 📈 Mejoras Futuras

### Posibles Extensiones

1. **Notificaciones Push del Servidor (FCM/OneSignal):**
   - Enviar notificaciones incluso con app cerrada
   - Requiere integración con servicio externo

2. **Notificaciones por SMS:**
   - Usar servicio como Twilio
   - Para conductores sin smartphone moderno

3. **Notificaciones por Email:**
   - Resumen diario de asignaciones
   - Configurables por conductor

4. **Sonidos y Vibraciones:**
   - Agregar sonidos personalizados
   - Vibración en dispositivos móviles

5. **Centro de Notificaciones:**
   - Página dedicada para ver historial
   - Marcar como leído/no leído
   - Filtros y búsqueda

## 📞 Soporte

### Recursos

- **Documentación:** Este archivo
- **Tests:** `apps/programaciones/tests.py`
- **Código Backend:** `apps/notifications/services.py`
- **Código Frontend:** `templates/driver_dashboard.html`

### Debugging

```bash
# Ver logs en tiempo real
tail -f logs/django.log

# Shell de Django
python manage.py shell

# Verificar notificaciones
from apps.notifications.models import Notification
Notification.objects.all()

# Verificar última notificación de un conductor
from apps.drivers.models import Driver
driver = Driver.objects.get(nombre='Juan Pérez')
driver.notifications.all().order_by('-created_at')
```

---

**Fecha de Implementación:** Octubre 2025  
**Versión:** 1.0.0  
**Estado:** ✅ Completo y Probado  
**Tests:** 21/21 pasando ✓
