# 🚀 Deploy de Mapbox en Producción - Checklist

**Sistema:** SOPTRALOC TMS v3.2  
**Fecha:** Octubre 7, 2025  
**Cambio:** Google Maps → Mapbox API  
**Estado:** ✅ Código committed y pushed a GitHub  

---

## ✅ Completado en Desarrollo

- [x] ✅ Servicio Mapbox implementado (`apps/routing/mapbox_service.py`)
- [x] ✅ Google Maps eliminado completamente
- [x] ✅ Sistema testeado y funcional
- [x] ✅ Documentación completa creada (3 archivos)
- [x] ✅ Cambios committed a GitHub (commit `aca5566`)
- [x] ✅ Push exitoso a repositorio remoto

**Archivos en repositorio:**
```
✅ CONFIGURAR_MAPBOX_PASO_A_PASO.md (470+ líneas - guía completa)
✅ MIGRACION_MAPBOX_OCT_2025.md (resumen ejecutivo)
✅ ROUTING_ML_QUICKSTART.md (uso del motor de rutas + ML)
✅ soptraloc_system/apps/routing/mapbox_service.py (nuevo)
✅ soptraloc_system/config/settings.py (actualizado)
❌ soptraloc_system/apps/routing/google_maps_service.py (eliminado)
```

---

## 📋 Pasos para Deploy en Producción (Render)

### Paso 1: Obtener Token de Mapbox (15 minutos)

**Seguir la guía:** `CONFIGURAR_MAPBOX_PASO_A_PASO.md`

**Resumen rápido:**

1. **Activar GitHub Student Pack:**
   - https://education.github.com/pack
   - Usar email institucional (.edu)

2. **Crear cuenta Mapbox:**
   - https://account.mapbox.com/auth/signup/
   - Usar mismo email .edu
   - ✅ Se aplica automáticamente $75 de crédito

3. **Crear Access Token:**
   - https://account.mapbox.com/access-tokens/
   - Click en "Create a token"
   - Nombre: `SOPTRALOC Production`
   - **Scopes requeridos:**
     - ✅ `styles:read`
     - ✅ `fonts:read`
     - ✅ `datasets:read`
     - ✅ `vision:read`
     - ✅ **`directions:read`** (CRÍTICO)
   - URL restriction (opcional): `https://soptraloc.onrender.com/*`
   - Click "Create token"
   - **Copiar el token** (empieza con `pk.`)

---

### Paso 2: Configurar en Render (5 minutos)

1. **Ir al Dashboard de Render:**
   - https://dashboard.render.com/
   - Seleccionar tu servicio SOPTRALOC

2. **Agregar Variable de Entorno:**
   - Pestaña: **Environment**
   - Click en: **Add Environment Variable**
   - Key: `MAPBOX_API_KEY`
   - Value: `pk.eyJ1...` (tu token completo)
   - Click **Save Changes**

3. **Eliminar Variable Antigua (opcional):**
   - Buscar: `GOOGLE_MAPS_API_KEY`
   - Click en "Delete" (ya no se usa)

4. **Deploy Automático:**
   - Render detectará el push a GitHub
   - Se desplegará automáticamente
   - O manualmente: Click en "Manual Deploy" → "Deploy latest commit"

---

### Paso 3: Verificar Deploy (5 minutos)

1. **Esperar que termine el deploy:**
   - Ver logs en tiempo real en Render
   - Buscar: `Build succeeded` y `Deploy live`

2. **Abrir Shell de producción:**
   - En Render, pestaña "Shell"
   - O SSH si está configurado

3. **Verificar API Key:**
   ```bash
   echo $MAPBOX_API_KEY
   # Debe mostrar: pk.eyJ1...
   ```

4. **Verificar configuración Django:**
   ```bash
   cd /opt/render/project/src/soptraloc_system
   python manage.py shell
   ```
   
   ```python
   from django.conf import settings
   print("API Key configurada:", bool(settings.MAPBOX_API_KEY))
   print("Primeros 10 caracteres:", settings.MAPBOX_API_KEY[:10] if settings.MAPBOX_API_KEY else "N/A")
   # Debe mostrar:
   # API Key configurada: True
   # Primeros 10 caracteres: pk.eyJ1...
   ```

5. **Probar servicio Mapbox:**
   ```python
   from apps.routing.mapbox_service import mapbox_service
   
   # Test básico
   data = mapbox_service.get_travel_time_with_traffic(
       origin='CCTI',
       destination='CD_PENON'
   )
   
   print("Fuente:", data['source'])
   print("Duración:", data['duration_minutes'], "minutos")
   print("Distancia:", data['distance_km'], "km")
   
   # Debe mostrar:
   # Fuente: mapbox_api (NO 'fallback')
   # Duración: ~35 minutos
   # Distancia: ~24.5 km
   ```

6. **Verificar endpoint REST:**
   ```bash
   curl https://soptraloc.onrender.com/api/v1/routing/route-tracking/locations/ | jq
   
   # Debe retornar JSON con 6 ubicaciones
   ```

---

### Paso 4: Configurar Monitoreo (5 minutos)

1. **Dashboard de Mapbox:**
   - https://account.mapbox.com/statistics/
   - Ver uso en tiempo real
   - Configurar alertas

2. **Configurar Alertas de Uso:**
   - Pestaña "Billing"
   - "Usage alerts"
   - Agregar alerta al 80% del límite gratuito (40,000 requests)
   - Email de notificación

3. **Verificar Créditos:**
   - Pestaña "Billing" → "Credits"
   - Debe mostrar: $75 GitHub Student Pack
   - Válido por 12 meses

---

## 🧪 Testing en Producción

### Test 1: Endpoint de Ubicaciones
```bash
curl https://soptraloc.onrender.com/api/v1/routing/route-tracking/locations/
```

**Respuesta esperada:**
```json
{
  "count": 6,
  "locations": [
    {
      "code": "CCTI",
      "name": "CCTI - Centro de Consolidación y Transferencia Internacional",
      "address": "Camino Los Agricultores, Parcela 41, Maipú",
      "coordinates": {"lat": -33.5167, "lng": -70.8667}
    },
    ...
  ]
}
```

### Test 2: Inicio de Ruta con Tráfico
```bash
curl -X POST https://soptraloc.onrender.com/api/v1/routing/route-tracking/start-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -d '{
    "assignment_id": 123,
    "driver_id": 45,
    "origin": "CCTI",
    "destination": "CD_PENON"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "eta": "2025-10-07T16:50:00",
  "traffic_data": {
    "duration_minutes": 35,
    "distance_km": 24.5,
    "traffic_level": "unknown",
    "source": "mapbox_api"  // ← DEBE decir "mapbox_api", NO "fallback"
  },
  "alert_created": true
}
```

### Test 3: Disponibilidad de Conductores
```bash
curl https://soptraloc.onrender.com/api/v1/routing/route-tracking/available-drivers/?location=CCTI
```

**Respuesta esperada:**
```json
{
  "location": "CCTI",
  "check_time": "2025-10-07T15:30:00",
  "available_drivers": [
    {
      "id": 45,
      "name": "Juan Pérez",
      "rut": "12345678-9",
      "status": "available"
    },
    ...
  ],
  "total_available": 3
}
```

---

## ✅ Checklist de Deploy

### Pre-Deploy:
- [x] ✅ Código tested localmente
- [x] ✅ Commit a GitHub
- [x] ✅ Push exitoso

### Deploy:
- [ ] 🔄 Obtener token de Mapbox
- [ ] 🔄 Configurar `MAPBOX_API_KEY` en Render
- [ ] 🔄 Deploy automático completado
- [ ] 🔄 Logs sin errores

### Post-Deploy:
- [ ] 🔄 Verificar API key en producción
- [ ] 🔄 Probar servicio Mapbox (source='mapbox_api')
- [ ] 🔄 Test endpoint /locations/ (6 ubicaciones)
- [ ] 🔄 Test endpoint /start-route/ (con tráfico real)
- [ ] 🔄 Test endpoint /available-drivers/ (lista correcta)
- [ ] 🔄 Configurar alertas de uso en Mapbox
- [ ] 🔄 Monitorear primeras 24 horas

---

## 🚨 Troubleshooting

### Problema 1: `source: 'fallback'` en respuesta

**Causa:** API key no configurada o inválida

**Solución:**
1. Verificar en Render que existe `MAPBOX_API_KEY`
2. Verificar que el token empieza con `pk.`
3. Verificar scopes del token (debe tener `directions:read`)
4. Redeploy después de agregar/corregir

### Problema 2: Error 401 Unauthorized

**Causa:** Token inválido o expirado

**Solución:**
1. Ir a https://account.mapbox.com/access-tokens/
2. Verificar que el token está activo
3. Si está revocado, crear uno nuevo
4. Actualizar en Render y redeploy

### Problema 3: Error 429 Too Many Requests

**Causa:** Límite de requests excedido

**Solución:**
1. Verificar uso en https://account.mapbox.com/statistics/
2. Revisar si hay loops infinitos en el código
3. Considerar aumentar caché a 10 minutos (en lugar de 5)
4. Si es necesario, agregar crédito adicional

### Problema 4: Respuestas lentas (>5 segundos)

**Causa:** API de Mapbox lenta o problemas de red

**Solución:**
1. Verificar status de Mapbox: https://status.mapbox.com/
2. Aumentar timeout en `mapbox_service.py` (línea con `timeout=10`)
3. Verificar latencia de Render a Mapbox
4. El fallback se activará automáticamente si hay timeout

---

## 📊 Monitoreo Post-Deploy

### Primeras 24 horas:

**Verificar cada 4 horas:**
1. ✅ Dashboard Render: Sin errores en logs
2. ✅ Dashboard Mapbox: Uso dentro de límites
3. ✅ Django Admin: Alertas de tráfico generándose correctamente
4. ✅ API endpoints: Respuestas correctas (no fallback)

**Métricas esperadas (día 1):**
- Requests a Mapbox: ~100-500 (depende de tráfico)
- Latencia promedio: <2 segundos
- Tasa de error: <1%
- Cache hit rate: ~80%

### Primera semana:

**Monitorear:**
- Uso semanal de Mapbox (no debe exceder 10,000)
- Costos (debe ser $0 con plan gratuito)
- Alertas generadas (debe haber al menos algunas)
- Feedback de conductores (tiempos precisos)

---

## 💰 Costos Estimados

### Mes 1 (con 50,000 gratis + crédito):
- **Requests esperados:** ~5,000-10,000
- **Costo:** $0 (dentro del límite gratuito)
- **Crédito usado:** $0

### Meses 2-12 (con crédito $75):
- **Requests esperados:** ~10,000/mes
- **Requests gratis:** 50,000/mes
- **Costo:** $0 (dentro del límite gratuito)

### Después de 12 meses (sin crédito):
- **Si <50,000 requests/mes:** $0
- **Si 100,000 requests/mes:** ~$25/mes
- **Comparación Google Maps:** ~$500/mes
- **Ahorro:** ~$475/mes = $5,700/año

---

## 📞 Soporte

### Documentación:
- **Guía completa:** `CONFIGURAR_MAPBOX_PASO_A_PASO.md`
- **Migración:** `MIGRACION_MAPBOX_OCT_2025.md`
- **Sistema tráfico:** `CONFIGURAR_MAPBOX_PASO_A_PASO.md`

### Links útiles:
- **Mapbox Dashboard:** https://account.mapbox.com/
- **Mapbox Docs:** https://docs.mapbox.com/api/navigation/directions/
- **Mapbox Status:** https://status.mapbox.com/
- **GitHub Student Pack:** https://education.github.com/pack

### En caso de problemas:
1. Revisar logs en Render
2. Verificar en Mapbox Dashboard
3. Revisar esta guía de troubleshooting
4. Contactar soporte Mapbox (si es problema de API)

---

## ✅ Deploy Exitoso

**Señales de que todo está bien:**
- ✅ Render deploy sin errores
- ✅ `MAPBOX_API_KEY` configurada correctamente
- ✅ Endpoints REST respondiendo
- ✅ `source: 'mapbox_api'` en respuestas (NO 'fallback')
- ✅ 6 ubicaciones en catálogo
- ✅ Alertas de tráfico generándose
- ✅ Dashboard Mapbox mostrando requests

**¡Felicidades! El sistema está listo para producción** 🎉

---

**Última actualización:** Octubre 7, 2025  
**Próxima revisión:** Una semana después del deploy  
**Responsable:** Equipo de desarrollo SOPTRALOC
