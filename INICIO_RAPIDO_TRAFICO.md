# 🚀 INICIO RÁPIDO - Sistema de Tráfico en Tiempo Real

## ⚡ 5 Pasos para Activar el Sistema

### 1️⃣ Obtener token de Mapbox (5 minutos)

Con tu **GitHub Student Pack** recibes $75 de crédito y 50,000 requests mensuales gratis.

**Pasos:**
1. Ve a: https://account.mapbox.com/auth/signup/
2. Crea la cuenta usando tu email institucional (.edu) para activar el beneficio
3. En el panel, entra a **Access tokens** → "Create a token"
4. Nombre recomendado: `SOPTRALOC Production`
5. Habilita los scopes necesarios (incluye `directions:read`)
6. Opcional: restringe con `https://soptraloc.onrender.com/*`
7. Guarda el token generado (comienza con `pk.`)

**Ejemplo:** `pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg`

---

### 2️⃣ Configurar en Render (2 minutos)

1. Ve a: https://dashboard.render.com/
2. Selecciona tu servicio "soptraloc"
3. Click en "Environment" (menú izquierdo)
4. Click en "Add Environment Variable"
5. Agregar:
  ```
  Key:   MAPBOX_API_KEY
  Value: pk.eyJ1...  (tu token)
  ```
6. Elimina la variable `GOOGLE_MAPS_API_KEY` si existía
7. Click "Save Changes"

**Render redeplegará automáticamente** ✅

---

### 3️⃣ Verificar que Funcionó (1 minuto)

Espera a que termine el deploy (~5 minutos) y verifica:

```bash
# Verificar en logs
# Deberías ver algo como:
# ✅ Mapbox API configurada correctamente

# NO deberías ver:
# ⚠️  MAPBOX_API_KEY no configurada
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

- [ ] Token de Mapbox obtenido
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
✅ Consulta Mapbox Directions API
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

### Error: "MAPBOX_API_KEY no configurada"
**Solución:** Agrega la variable en Render (ver paso 2)

### Error: "API status != OK"
**Solución:** Verifica que el token siga activo y que tenga `directions:read`

### Error: "Quota exceeded"
**Solución:** Revisa el panel de Mapbox; puedes regenerar el token o ampliar el límite

### Error: "Invalid token"
**Solución:** Verifica que copiaste el token completo sin espacios

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

### APIs de Mapbox:
- Directions API: https://docs.mapbox.com/api/navigation/directions/
- Rate limits: https://docs.mapbox.com/api/navigation/directions/#rate-limits

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
