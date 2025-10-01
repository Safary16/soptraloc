# Sistema de Reloj en Tiempo Real y Alertas de Proximidad

## 📋 Descripción General

Sistema integrado que muestra un reloj en tiempo real en todas las páginas y alerta automáticamente cuando un contenedor está a menos de 2 horas de su hora de programación, dándoles máxima prioridad para asignación.

---

## ⏰ Componente de Reloj en Tiempo Real

### Ubicación
El reloj se muestra en el **navbar** de todas las páginas (base.html)

### Características
- **Actualización en tiempo real**: Cada segundo
- **Formato**: HH:MM:SS
- **Fecha**: Día, DD MMM YYYY (ej: "Lun 01 Oct 2025")
- **Icono de reloj**: Bootstrap Icons
- **Visible en todos los views**: Home, Dashboard, Pase Lista, Alertas, Admin

### Código
```javascript
// static/js/realtime-clock.js
- Actualiza cada 1000ms (1 segundo)
- Formato 24 horas con padding de ceros
- Días y meses en español
```

---

## 🚨 Sistema de Alertas de Proximidad

### Concepto
Detecta contenedores programados que están **a menos de 2 horas** de su hora programada y los marca como **urgentes** para asignación prioritaria.

### Niveles de Urgencia

| Nivel | Tiempo Restante | Color Badge | Icono | Acción |
|-------|-----------------|-------------|-------|--------|
| **CRÍTICO** | < 30 minutos | Rojo | ⚠️ | Asignar INMEDIATAMENTE |
| **ALTA** | < 1 hora | Amarillo | ⚠ | Asignar CON URGENCIA |
| **MEDIA** | < 2 horas | Azul | 🕐 | Priorizar asignación |

### Algoritmo de Priorización

```python
# apps/containers/services/proximity_alerts.py

1. Obtener todos los contenedores PROGRAMADOS o LIBERADOS
2. Para cada contenedor:
   - Calcular: scheduled_datetime - now()
   - Si diferencia < 2 horas:
     * Marcar como URGENTE
     * Calcular nivel de urgencia (critical/high/medium)
     * Agregar atributos: _hours_remaining, _minutes_remaining
3. Ordenar por proximidad (más urgente primero)
4. Retornar lista priorizada
```

---

## 📊 API Endpoint

### `/api/v1/containers/urgent/`

**Método**: GET  
**Autenticación**: Requerida (login_required)

**Respuesta**:
```json
{
    "urgent_containers": [
        {
            "id": 123,
            "container_number": "AAAU 123456-1",
            "client": "WALMART CHILE",
            "cd_location": "CD_QUILICURA",
            "scheduled_date": "01/10/2025",
            "scheduled_time": "14:30",
            "status": "PROGRAMADO",
            "hours_remaining": 1.5,
            "minutes_remaining": 30,
            "urgency_level": "high"
        }
    ],
    "total_urgent": 5,
    "critical_count": 1,
    "high_count": 2,
    "medium_count": 2
}
```

**Uso**:
```javascript
// Llamada automática cada 60 segundos desde realtime-clock.js
fetch('/api/v1/containers/urgent/')
    .then(response => response.json())
    .then(data => {
        // Actualizar badge con cantidad urgente
        // Mostrar notificaciones si hay críticos
    });
```

---

## 🎯 Integración en Dashboard

### Ordenamiento Automático

Los contenedores en el dashboard se ordenan con **prioridad urgente primero**:

```python
# apps/core/auth_views.py - dashboard_view()

1. Contenedores urgentes primero (ordered by hours_remaining)
2. Luego contenedores programados (ordered by scheduled_date)
3. Finalmente otros estados
```

### Visualización en Tabla

**Filas destacadas**:
- `table-danger`: Contenedores CRÍTICOS (rojo claro)
- `table-warning`: Contenedores ALTA (amarillo claro)
- `table-info`: Contenedores MEDIA (azul claro)

**Badges en contenedor**:
```html
{% if container._is_urgent %}
    <span class="badge bg-danger">
        <i class="bi bi-exclamation-triangle-fill"></i>
        ¡URGENTE!
    </span>
{% endif %}
```

**Tiempo restante**:
```html
{% if container._is_urgent %}
    <span class="badge bg-danger">
        <i class="bi bi-clock-fill"></i> 
        Faltan {{ container._minutes_remaining }} min
    </span>
{% endif %}
```

---

## 🔔 Modal de Alertas Urgentes

### Botón de Alertas en Navbar

Aparece automáticamente cuando hay contenedores urgentes:

```html
<button class="btn btn-outline-light">
    <i class="bi bi-exclamation-triangle-fill"></i>
    <span class="badge bg-danger">5</span> <!-- Cantidad urgente -->
</button>
```

**Animación**: Badge pulsa cuando hay contenedores CRÍTICOS

### Contenido del Modal

- **Título**: "Contenedores Urgentes (< 2 horas)"
- **Lista**: Todos los contenedores urgentes ordenados por proximidad
- **Por cada contenedor**:
  - Número de contenedor
  - Cliente
  - CD destino
  - Fecha/hora programada
  - Tiempo restante
  - Badge de urgencia
  - Botón "Asignar Ahora" (si está PROGRAMADO)

### Actualización Automática

- **Intervalo**: Cada 60 segundos
- **Verificación**: Llamada a `/api/v1/containers/urgent/`
- **Notificación**: Badge pulsa si hay nuevos críticos

---

## 🎨 Estilos CSS

```css
/* Animación de pulso para alertas críticas */
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.2); }
}

.animate-pulse {
    animation: pulse 0.5s ease-in-out 3;
}

/* Formato del reloj */
#realtime-clock {
    font-family: 'Courier New', monospace;
    text-align: right;
}

#clock-time {
    font-size: 1.1rem;
    font-weight: bold;
}
```

---

## 📈 Flujo de Trabajo

### Escenario 1: Contenedor Urgente sin Asignar

1. **12:00** - Contenedor programado para las 14:00
2. **12:05** - Sistema detecta < 2h → marca como URGENTE
3. **12:05** - Aparece en dashboard con fila amarilla/roja
4. **12:05** - Badge en navbar muestra "1" urgente
5. **12:05** - Usuario ve modal con contenedor destacado
6. **12:10** - Usuario asigna conductor
7. **12:10** - Contenedor desaparece de lista urgente

### Escenario 2: Múltiples Contenedores Críticos

1. **13:40** - 3 contenedores programados para 14:00 (< 30 min)
2. **13:40** - Sistema marca todos como CRÍTICOS
3. **13:40** - Badge en navbar pulsa (animación)
4. **13:40** - Filas en dashboard en rojo intenso
5. **13:40** - Modal muestra los 3 con "¡URGENTE!"
6. **13:45** - Se asignan secuencialmente por proximidad

---

## 🔧 Configuración

### Parámetros Ajustables

```python
# apps/containers/services/proximity_alerts.py

# Tiempo de alerta (horas antes de la programación)
ALERT_THRESHOLD_HOURS = 2

# Niveles de urgencia (en horas)
CRITICAL_THRESHOLD = 0.5  # 30 minutos
HIGH_THRESHOLD = 1.0      # 1 hora
MEDIUM_THRESHOLD = 2.0    # 2 horas
```

```javascript
// static/js/realtime-clock.js

// Intervalo de actualización del reloj (ms)
const REFRESH_INTERVAL = 1000;  // 1 segundo

// Intervalo de verificación de alertas (ms)
const ALERT_CHECK_INTERVAL = 60000;  // 1 minuto
```

---

## ✅ Beneficios del Sistema

### 1. **Visibilidad en Tiempo Real**
- Todos los usuarios ven la hora actual consistente
- Sincronización temporal en decisiones operativas

### 2. **Prevención de Retrasos**
- Alertas tempranas (2 horas antes)
- Asignación anticipada de conductores
- Reducción de multas por demora

### 3. **Priorización Automática**
- No requiere intervención manual
- Los urgentes siempre están arriba
- Fácil identificación visual

### 4. **Mejora en KPIs**
- ⬆️ Tasa de entrega a tiempo
- ⬇️ Contenedores sin asignar
- ⬇️ Tiempo promedio de asignación
- ⬆️ Satisfacción del cliente

### 5. **Trazabilidad**
- Registro de cuándo se detectó urgencia
- Historial de alertas generadas
- Métricas de tiempo de respuesta

---

## 📱 Uso Práctico

### Para Operadores

**Dashboard diario**:
```
09:00 - Ingresar al dashboard
09:01 - Ver reloj muestra "09:01:23"
09:01 - Badge muestra "3 urgentes"
09:02 - Abrir modal de urgentes
09:03 - Ver contenedor CRÍTICO (< 30 min)
09:05 - Asignar conductor disponible
09:10 - Verificar que badge disminuyó a "2"
```

### Para Supervisores

**Monitoreo continuo**:
- Verificar badge de urgentes cada 15 minutos
- Priorizar asignaciones según nivel (crítico > alto > medio)
- Revisar que contenedores urgentes se asignen en < 10 minutos
- Generar reportes de contenedores que llegaron a crítico

---

## 🚀 Próximas Mejoras

### Fase 2 (Sugerencias)

1. **Notificaciones Push**
   - Enviar notificación al navegador cuando hay críticos
   - Requiere: Service Workers + Push API

2. **Sonido de Alerta**
   - Beep cuando badge llega a crítico
   - Configurable por usuario

3. **Integración con WhatsApp**
   - Enviar mensaje automático a supervisor
   - Cuando hay > 3 contenedores críticos

4. **Dashboard de Predicción**
   - Gráfico de contenedores que entrarán en urgente
   - Proyección de carga operativa por hora

5. **Historial de Alertas**
   - Tabla con todas las alertas generadas
   - Análisis de patrones de urgencia
   - Identificación de clientes problemáticos

---

## 📝 Testing

### Test Manual

```bash
# 1. Crear contenedor de prueba programado para dentro de 1 hora
python manage.py shell
>>> from apps.containers.models import Container
>>> from datetime import datetime, timedelta
>>> Container.objects.create(
...     container_number="TEST 123456-1",
...     status="PROGRAMADO",
...     scheduled_date=datetime.now().date(),
...     scheduled_time=(datetime.now() + timedelta(minutes=45)).time()
... )

# 2. Abrir dashboard
# 3. Verificar que aparece en tabla con badge urgente
# 4. Verificar badge en navbar
# 5. Abrir modal y verificar contenedor en lista
```

### Test Automatizado (Futuro)

```python
# tests/test_proximity_alerts.py

def test_urgent_container_detection():
    # Crear contenedor < 2h
    container = create_urgent_container(hours=1)
    
    # Verificar detección
    urgent = ProximityAlertSystem.get_urgent_containers([container])
    assert len(urgent) == 1
    assert urgent[0]._urgency_level == 'high'
```

---

## 🎓 Conclusión

El sistema de **Reloj en Tiempo Real + Alertas de Proximidad** proporciona:

✅ **Visibilidad temporal** en todos los views  
✅ **Detección automática** de contenedores urgentes  
✅ **Priorización inteligente** sin intervención manual  
✅ **Alertas visuales** claras y efectivas  
✅ **Mejora operativa** medible en KPIs  

**Resultado**: Operaciones más eficientes, menos retrasos, clientes más satisfechos.

---

**Fecha**: Octubre 2025  
**Versión**: 1.0  
**Estado**: ✅ Implementado y funcional
