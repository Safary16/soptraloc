# 🚀 INICIO RÁPIDO - Sistema de Tráfico en Tiempo Real

## ⚡ 5 Pasos para Activar el Sistema

### 1️⃣ Obtener API Key de Google Maps (5 minutos)

Con tu **GitHub Student Pack** tienes $200 de crédito gratis.

**Pasos:**
1. Ve a: https://console.cloud.google.com/
2. Click en "Crear proyecto" → Nombre: "SoptraLoc"
3. Habilitar APIs:
   - Distance Matrix API ✅
   - Directions API ✅
4. Ir a "Credenciales" → "Crear credenciales" → "API Key"
5. Copiar la API Key generada

**Ejemplo:** `AIzaSyC4hJ7...` (tu key será diferente)

---

### 2️⃣ Configurar en Render (2 minutos)

1. Ve a: https://dashboard.render.com/
2. Selecciona tu servicio "soptraloc"
3. Click en "Environment" (menú izquierdo)
4. Click en "Add Environment Variable"
5. Agregar:
   ```
   Key:   GOOGLE_MAPS_API_KEY
   Value: AIzaSyC4hJ7...  (tu key)
   ```
6. Click "Save Changes"

**Render redeplegará automáticamente** ✅

---

### 3️⃣ Verificar que Funcionó (1 minuto)

Espera a que termine el deploy (~5 minutos) y verifica:

```bash
# Verificar en logs
# Deberías ver algo como:
# ✅ Google Maps API configurada correctamente

# NO deberías ver:
# ⚠️  GOOGLE_MAPS_API_KEY no configurada
```

---

### 4️⃣ Probar la API (2 minutos)

Obtén un token de autenticación:

```bash
curl -X POST https://soptraloc.onrender.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "1234"}'
```

Guarda el `access` token.

Ahora prueba iniciar una ruta:

```bash
curl -X POST https://soptraloc.onrender.com/api/v1/routing/route-tracking/start-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "assignment_id": 1,
    "driver_id": 1,
    "origin": {
        "name": "CCTI Maipú",
        "latitude": -33.5089,
        "longitude": -70.7593
    },
    "destination": {
        "name": "CD El Peñón",
        "latitude": -33.6297,
        "longitude": -70.7045
    }
}'
```

**Respuesta esperada:**
```json
{
    "success": true,
    "assignment_id": 1,
    "driver_name": "...",
    "route": {
        "distance_km": 15.2
    },
    "time": {
        "duration_with_traffic": 35,
        "eta": "2025-10-07T..."
    },
    "traffic": {
        "level": "medium"
    }
}
```

¡Si ves esto, **FUNCIONA**! 🎉

---

### 5️⃣ Ver Alertas en Admin (1 minuto)

1. Ve a: https://soptraloc.onrender.com/admin/
2. Login: `admin` / `1234`
3. Click en "Drivers" → "Alertas de Tráfico"
4. Deberías ver la alerta generada

**Verás algo como:**
```
🟡 TRAFFIC - Juan Pérez (Tráfico Medio)
```

---

## ✅ Checklist de Verificación

- [ ] API Key de Google Maps obtenida
- [ ] Variable configurada en Render
- [ ] Deploy completado sin errores
- [ ] API responde correctamente
- [ ] Alertas se generan en el admin
- [ ] No aparece warning de API key en logs

---

## 🎯 Uso Diario

### Cuando un conductor inicia una ruta:

```python
# Frontend o app móvil hace request:
POST /api/v1/routing/route-tracking/start-route/

# Sistema automáticamente:
✅ Consulta Google Maps
✅ Obtiene tráfico en tiempo real
✅ Calcula ETA preciso
✅ Genera alertas si hay problemas
✅ Sugiere rutas alternativas
✅ Guarda todo en la base de datos
```

### El conductor recibe:
- ⏱️ Tiempo estimado con tráfico actual
- 🚦 Nivel de tráfico (bajo/medio/alto/muy alto)
- ⚠️ Advertencias (accidentes, cierres, obras)
- 💡 Rutas alternativas (si ahorran tiempo)
- 🕐 ETA preciso

---

## 📱 Integración Frontend

### React/Vue/Angular:

```javascript
async function startRoute(assignmentId, driverId, origin, destination) {
  const response = await fetch(
    'https://soptraloc.onrender.com/api/v1/routing/route-tracking/start-route/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        assignment_id: assignmentId,
        driver_id: driverId,
        origin: origin,
        destination: destination
      })
    }
  );
  
  const data = await response.json();
  
  // Mostrar al usuario
  console.log(`ETA: ${data.time.eta}`);
  console.log(`Tráfico: ${data.traffic.level}`);
  console.log(`Retraso: +${data.time.delay} minutos`);
  
  // Mostrar alertas
  data.alerts.forEach(alert => {
    showAlert(alert.emoji + ' ' + alert.message);
  });
  
  return data;
}

// Uso
startRoute(
  123,  // assignment_id
  45,   // driver_id
  { name: 'CCTI Maipú', latitude: -33.5089, longitude: -70.7593 },
  { name: 'CD El Peñón', latitude: -33.6297, longitude: -70.7045 }
);
```

---

## 🗺️ Coordenadas Importantes

```javascript
const LOCATIONS = {
  // Puertos
  PUERTO_VALPARAISO: { lat: -33.0279, lng: -71.6293 },
  PUERTO_SAN_ANTONIO: { lat: -33.5958, lng: -71.6116 },
  
  // Centros de Distribución
  CCTI_MAIPU: { lat: -33.5089, lng: -70.7593 },
  CD_QUILICURA: { lat: -33.3563, lng: -70.7302 },
  CD_PENON: { lat: -33.6297, lng: -70.7045 },
  CD_PUDAHUEL: { lat: -33.3991, lng: -70.7644 }
};
```

Más coordenadas en: `COORDENADAS_CHILE_EJEMPLOS.md`

---

## 🆘 Troubleshooting

### Error: "GOOGLE_MAPS_API_KEY no configurada"
**Solución:** Agrega la variable en Render (ver paso 2)

### Error: "API status != OK"
**Solución:** Verifica que las APIs estén habilitadas en Google Cloud Console

### Error: "Quota exceeded"
**Solución:** Has usado los $200 de crédito. Agrega billing en Google Cloud.

### Error: "Invalid API key"
**Solución:** Verifica que copiaste la key completa sin espacios

---

## 💡 Tips

### Optimizar Costos:
- ✅ El sistema cachea por 5 minutos automáticamente
- ✅ Solo consulta cuando se inicia una ruta
- ✅ No consulta en bucles o timers

### Mejores Prácticas:
- ✅ Iniciar ruta solo cuando el conductor SALE (no antes)
- ✅ Usar coordenadas precisas (8 decimales)
- ✅ Verificar que driver_id corresponde a assignment

### Monitoreo:
```bash
# Ver alertas generadas hoy
GET /api/v1/routing/route-tracking/alerts/active/

# Ver resumen de tráfico
GET /api/v1/routing/route-tracking/traffic-summary/
```

---

## 📊 Métricas de Uso

Con $200 de crédito:
- **40,000 consultas** = 40,000 elementos
- **~8,000 rutas** (5 consultas por ruta)
- **~160 rutas/día** durante 50 días
- **~5 rutas/hora** durante 333 días (24/7)

**Para uso normal (50 rutas/día):** Crédito dura **~160 días** = **~5 meses**

---

## 🎓 Recursos Útiles

### Documentación Completa:
- `SISTEMA_TRAFICO_TIEMPO_REAL_OCT_2025.md` → Guía técnica completa
- `COORDENADAS_CHILE_EJEMPLOS.md` → Ejemplos y coordenadas
- `RESUMEN_SISTEMA_TRAFICO_OCT_2025.md` → Resumen ejecutivo

### APIs de Google:
- Distance Matrix: https://developers.google.com/maps/documentation/distance-matrix
- Directions: https://developers.google.com/maps/documentation/directions

### GitHub Student Pack:
- https://education.github.com/pack

---

## ✅ ¿Todo Listo?

Si completaste los 5 pasos:
- ✅ API Key configurada
- ✅ Render actualizado
- ✅ API funcionando
- ✅ Alertas generándose
- ✅ Admin accesible

**¡Estás listo para usar el sistema! 🚀**

---

**¿Necesitas ayuda?**
Revisa los logs en Render o la documentación completa.

**Fecha:** 7 de octubre de 2025  
**Versión:** SoptraLoc TMS v3.1
