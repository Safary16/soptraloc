# 📱 Guía: App Móvil Nativa + Seguimiento Histórico GPS

## 🎯 Descripción General

Esta guía documenta las nuevas funcionalidades implementadas para el portal de conductores:

1. **App Móvil Nativa (PWA)** - Instalación como app nativa en smartphones
2. **Seguimiento Histórico GPS** - Visualización de rutas de conductores en períodos de tiempo

---

## 📱 App Móvil Nativa para Conductores

### ¿Qué es una PWA?

Una Progressive Web App (PWA) es una aplicación web que se puede instalar en dispositivos móviles y funciona como una app nativa, sin necesidad de Google Play Store o App Store.

### Ventajas de la PWA

✅ **Instalación Instantánea** - No requiere tiendas de aplicaciones
✅ **Acceso Rápido** - Icono en pantalla de inicio como app nativa
✅ **GPS en Segundo Plano** - Tracking continuo incluso con pantalla apagada
✅ **Notificaciones Push** - Alertas de nuevas entregas
✅ **Funciona Sin Conexión** - Cache de datos para uso offline
✅ **Actualizaciones Automáticas** - Sin descargas manuales
✅ **Menor Consumo** - Menos batería y datos que apps nativas

### Instalación de la App Móvil

#### Para Conductores - Android/Chrome

1. Abrir el navegador Chrome
2. Ir a: `https://soptraloc.onrender.com/driver/login/`
3. Hacer login con sus credenciales
4. Aparecerá un banner morado: **"Instalar App Móvil"**
5. Presionar el botón **"Instalar Ahora"**
6. Confirmar la instalación
7. ✅ La app aparecerá en el menú de aplicaciones

**Alternativa sin banner:**
- Menú del navegador (⋮) → "Agregar a pantalla de inicio"

#### Para Conductores - iOS/Safari

1. Abrir Safari
2. Ir a: `https://soptraloc.onrender.com/driver/login/`
3. Presionar el botón "Compartir" (cuadrado con flecha)
4. Seleccionar "Agregar a pantalla de inicio"
5. Confirmar el nombre de la app
6. ✅ La app aparecerá en la pantalla de inicio

### Características de la App Móvil

#### 1. Banner de Instalación Inteligente

El banner de instalación:
- Se muestra automáticamente cuando la app es instalable
- Tiene diseño atractivo con gradiente morado
- Incluye lista de beneficios para el conductor
- Botón "Instalar Ahora" - inicia instalación
- Botón "Más tarde" - oculta el banner por 7 días
- Se oculta automáticamente si el usuario rechaza

#### 2. Funcionalidades de la App

Una vez instalada, la app ofrece:

**GPS Automático:**
- Tracking continuo de ubicación
- Actualización cada 30 segundos
- Funciona con app en segundo plano
- Indicador visual de estado GPS

**Gestión de Entregas:**
- Ver contenedores asignados
- Iniciar rutas con un tap
- Marcar entregas como completadas
- Notificar contenedor vacío

**Navegación:**
- Botón directo a Google Maps
- ETA calculado con tráfico en tiempo real
- Direcciones del cliente

**Notificaciones:**
- Nuevas asignaciones de contenedores
- Cambios en el estado de entregas
- Alertas del administrador

---

## 🗺️ Seguimiento Histórico GPS

### ¿Qué es?

Una herramienta de visualización que permite ver el recorrido completo de un conductor en un período de tiempo específico, dibujado como una ruta en el mapa.

### Acceso

**URL:** `https://soptraloc.onrender.com/monitoring/`

Esta funcionalidad está disponible en la página de **Monitoreo en Tiempo Real**.

### Cómo Usar el Seguimiento Histórico

#### Panel de Control

En la barra lateral izquierda, encontrarás el panel **"Seguimiento Histórico"** con:

1. **Selector de Conductor**
   - Dropdown con lista de todos los conductores activos
   - Se actualiza automáticamente cada 15 segundos

2. **Selector de Período**
   - **Últimas 24 horas** - Vista del día actual
   - **Últimos 3 días** - Vista de 3 días
   - **Última semana** - Vista semanal
   - **Último mes** - Vista mensual
   - **Personalizado** - Rango de fechas específico

3. **Rango Personalizado** (cuando se selecciona)
   - Campo "Desde" - fecha y hora de inicio
   - Campo "Hasta" - fecha y hora de fin
   - Formato: YYYY-MM-DD HH:MM

4. **Botones de Acción**
   - **Ver Recorrido** - Dibuja la ruta en el mapa
   - **Limpiar** - Elimina la ruta histórica del mapa

#### Paso a Paso

**Ejemplo: Ver el recorrido de ayer**

1. Ir a `/monitoring/`
2. En "Seguimiento Histórico", seleccionar conductor: **"Juan Pérez"**
3. En "Período", seleccionar: **"Últimas 24 horas"**
4. Presionar **"Ver Recorrido"**
5. El mapa mostrará:
   - Línea roja con el recorrido completo
   - 🟢 Bandera verde = punto de inicio
   - 🏁 Bandera a cuadros = punto final
   - Puntos intermedios en la ruta

**Ejemplo: Ver ruta de un día específico**

1. En "Período", seleccionar: **"Personalizado"**
2. En "Desde", ingresar: `2025-10-10 08:00`
3. En "Hasta", ingresar: `2025-10-10 18:00`
4. Presionar **"Ver Recorrido"**
5. El mapa se ajustará automáticamente al área de la ruta

### Visualización en el Mapa

#### Elementos Visuales

**Línea de Ruta:**
- Color: Rojo (#FF6B6B)
- Grosor: 4px
- Opacidad: 80%
- Tipo: Línea continua conectando puntos GPS

**Marcadores:**
- **Inicio** 🟢 - Bandera verde
  - Popup muestra fecha/hora de inicio
- **Final** 🏁 - Bandera a cuadros roja
  - Popup muestra fecha/hora de llegada
- **Puntos Intermedios** 🔴 - Círculos rojos pequeños
  - Popup muestra timestamp de cada punto
  - Se muestran cada 10 puntos para evitar saturación

#### Interacción

**Zoom Automático:**
- Al cargar una ruta, el mapa se ajusta automáticamente
- Muestra la ruta completa con padding de 50px

**Popups:**
- Click en cualquier marcador muestra información
- Hora exacta del punto GPS
- Precisión de la ubicación

**Navegación:**
- Controles de zoom en esquina superior derecha
- Arrastrar mapa para explorar
- Scroll para zoom

### Indicadores de Estado

En la esquina superior derecha, el indicador muestra:

- **"Cargando historial..."** - Mientras se obtienen datos
- **"[Nombre]: X puntos"** - Ruta cargada exitosamente
- **"Sin datos"** - No hay datos GPS para el período
- **"Error"** - Problema al cargar datos

---

## 🔧 API Endpoints

### 1. Historial de un Conductor

**Endpoint:** `GET /api/drivers/{id}/historial/`

**Parámetros:**

```
?dias=7                  # Últimos 7 días (por defecto)
?dias=1                  # Últimas 24 horas
?dias=30                 # Último mes

O bien:

?fecha_desde=2025-10-01T00:00:00Z&fecha_hasta=2025-10-14T23:59:59Z
```

**Respuesta:**

```json
[
  {
    "id": 123,
    "driver": 1,
    "lat": -33.4569,
    "lng": -70.6483,
    "accuracy": 15.5,
    "timestamp": "2025-10-14T15:30:00Z"
  },
  {
    "id": 124,
    "driver": 1,
    "lat": -33.4580,
    "lng": -70.6495,
    "accuracy": 12.3,
    "timestamp": "2025-10-14T15:31:00Z"
  }
]
```

**Límites:**
- Máximo 1000 puntos por solicitud
- Si hay más puntos, se hace muestreo inteligente
- Puntos ordenados cronológicamente

### 2. Historial de Múltiples Conductores

**Endpoint:** `GET /api/drivers/historial-multiple/`

**Parámetros:**

```
?driver_ids=1,2,3        # IDs de conductores (separados por coma)
?dias=1                  # Período de tiempo
?fecha_desde=...         # O rango personalizado
?fecha_hasta=...
```

**Respuesta:**

```json
{
  "1": {
    "driver_name": "Juan Pérez",
    "locations": [
      {
        "id": 123,
        "lat": -33.4569,
        "lng": -70.6483,
        "timestamp": "2025-10-14T15:30:00Z"
      }
    ]
  },
  "2": {
    "driver_name": "María González",
    "locations": [...]
  }
}
```

**Límites:**
- Máximo 500 puntos por conductor
- Ideal para análisis comparativo

---

## 📊 Casos de Uso

### Para Administradores

**1. Verificación de Entregas**
- Ver la ruta real tomada por el conductor
- Confirmar que visitó el cliente
- Validar tiempos de entrega

**2. Auditoría y Cumplimiento**
- Revisar rutas históricas de cualquier día
- Detectar desvíos o paradas no autorizadas
- Documentar incidentes

**3. Optimización de Rutas**
- Analizar rutas tomadas vs rutas óptimas
- Identificar cuellos de botella
- Mejorar planificación futura

**4. Análisis de Desempeño**
- Comparar conductores en misma ruta
- Medir tiempos reales de entrega
- Identificar mejores prácticas

### Para Operaciones

**1. Soporte al Conductor**
- Ayudar a conductor perdido
- Ver dónde ha estado
- Sugerir ruta alternativa

**2. Resolución de Disputas**
- Cliente dice que nunca llegó el conductor
- Mostrar evidencia GPS de la visita
- Resolver reclamos con datos

**3. Seguimiento de Incidentes**
- Revisar qué pasó en caso de accidente
- Ver ubicación exacta del incidente
- Reconstruir eventos

---

## 🔒 Seguridad y Privacidad

### Permisos de GPS

**Conductores:**
- Deben autorizar explícitamente el GPS
- Pueden revocar permisos en cualquier momento
- GPS solo se activa cuando están logueados

**Administradores:**
- Solo ven datos de conductores activos
- Historial limitado según políticas
- No se comparten datos fuera del sistema

### Almacenamiento de Datos

- Ubicaciones guardadas en base de datos encriptada
- Retención según políticas de la empresa
- Backups automáticos diarios
- Cumple con regulaciones de privacidad

---

## 🚀 Mejores Prácticas

### Para Conductores

1. **Mantener app instalada** - Mejor experiencia
2. **Permitir GPS siempre** - Tracking continuo
3. **Mantener batería cargada** - GPS consume batería
4. **Internet estable** - WiFi o 4G para enviar ubicación

### Para Administradores

1. **Revisar historial diariamente** - Detectar problemas temprano
2. **Exportar datos importantes** - Guardar evidencia
3. **Capacitar conductores** - Explicar beneficios del tracking
4. **Usar períodos cortos primero** - 24h para análisis rápido

---

## 📞 Soporte y Troubleshooting

### Problemas Comunes

**App no se instala:**
- Verificar que el navegador sea Chrome (Android) o Safari (iOS)
- Actualizar el navegador a última versión
- Verificar conexión a internet estable

**GPS no se actualiza:**
- Verificar permisos de ubicación en configuración del teléfono
- Reiniciar la app
- Verificar que el servicio de ubicación esté activado

**Historial no carga:**
- Verificar que haya datos GPS en el período
- Probar con período más amplio (1 semana)
- Refrescar la página

**Ruta no se visualiza:**
- Hacer zoom out en el mapa
- Presionar "Limpiar" y volver a cargar
- Verificar consola del navegador (F12)

### Contacto

Para soporte técnico:
- Email: soporte@soptraloc.com
- Teléfono: +56 9 XXXX XXXX
- Admin: `/admin/` → Ver logs del sistema

---

## 📝 Historial de Cambios

### v1.0.0 (2025-10-14)

**Nuevas Funcionalidades:**
- ✅ Banner de instalación de PWA en dashboard
- ✅ Soporte para instalación Android/iOS
- ✅ Panel de seguimiento histórico en monitoreo
- ✅ Selector de períodos de tiempo (24h, 3d, 7d, 30d, custom)
- ✅ Visualización de rutas en mapa Mapbox
- ✅ Marcadores de inicio/fin de ruta
- ✅ API endpoint para historial con fechas personalizadas
- ✅ API endpoint para múltiples conductores
- ✅ Muestreo inteligente para grandes datasets

**Mejoras:**
- 🔄 API `historial` ahora acepta rangos de fechas
- 🔄 Límite de 1000 puntos con muestreo automático
- 🔄 Ordenamiento cronológico de ubicaciones
- 🔄 Auto-zoom al cargar rutas históricas

---

## 🎯 Próximas Funcionalidades

Funcionalidades planeadas para futuras versiones:

- [ ] Exportar ruta a PDF/Excel
- [ ] Comparar múltiples conductores en el mapa
- [ ] Replay animado de la ruta
- [ ] Heatmap de áreas más visitadas
- [ ] Alertas de geofencing
- [ ] Estadísticas de tiempo en tráfico
- [ ] Integración con Waze
- [ ] Compartir ruta por WhatsApp

---

## 📚 Referencias

- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/)
- [Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)
- [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

---

**Última actualización:** 2025-10-14
**Versión:** 1.0.0
**Autor:** SoptraLoc Development Team
