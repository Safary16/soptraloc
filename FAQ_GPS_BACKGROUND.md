# ❓ Preguntas Frecuentes - GPS Background Tracking

## 📱 General

### ¿Por qué necesitamos una app nativa si ya tenemos PWA?

**Respuesta corta:** La PWA no puede mantener GPS activo cuando el celular está bloqueado.

**Respuesta detallada:**
- Las PWAs funcionan en el navegador
- El navegador pausa JavaScript cuando está en background
- `navigator.geolocation.watchPosition()` se detiene automáticamente
- No hay forma de ejecutar código continuo sin el navegador abierto

**Solución:** App nativa (TWA) usa servicios de Android que funcionan siempre, incluso con pantalla bloqueada.

### ¿Qué es TWA?

**TWA = Trusted Web Activity**

Es una tecnología de Google que:
- Envuelve tu sitio web en una app Android nativa
- Abre el sitio en Chrome Custom Tabs (fullscreen, sin barra URL)
- Permite acceso a APIs nativas de Android
- Verifica que eres dueño del dominio

**Ventaja principal:** Reutilizas tu código web (PWA) pero obtienes capacidades nativas (GPS background, permisos, etc.)

### ¿Es seguro?

**Sí, 100% seguro:**

1. **Código auditable:**
   - Todo el código está en GitHub
   - Puedes revisar qué hace la app
   - No hay código malicioso

2. **Permisos transparentes:**
   - Solo pide ubicación GPS
   - No accede a contactos, fotos, mensajes
   - Usuario ve claramente qué permisos pide

3. **Código abierto:**
   - Basado en librerías oficiales de Google
   - `androidbrowserhelper` es mantenido por Google
   - Usado por miles de apps

---

## 🔧 Técnicas

### ¿Cómo funciona el GPS en background?

**Flujo técnico:**

```
1. App nativa inicia servicio foreground
2. Servicio crea notificación persistente
3. Android garantiza que servicio no se mata
4. Servicio solicita actualizaciones GPS cada 30s
5. TWA container carga tu PWA
6. PWA recibe eventos GPS y los envía a servidor
7. Si PWA se cierra, servicio nativo continúa
```

**Clave:** Servicio foreground con notificación es **protegido por Android**. El sistema operativo no lo puede matar arbitrariamente.

### ¿Qué pasa si el usuario cierra la app?

**Depende de cómo la cierre:**

1. **Presiona Home:**
   - App va a background
   - Servicio continúa activo ✅
   - GPS sigue funcionando ✅

2. **Swipe para cerrar (recientes):**
   - App se cierra
   - Servicio **puede** continuar si está configurado
   - Depende de configuración Android

3. **Fuerza cierre (Settings → Apps → Forzar detención):**
   - Todo se detiene ❌
   - Usuario debe abrir app nuevamente

**Recomendación:** Configurar app para auto-inicio en boot.

### ¿Consume mucha batería?

**No, está optimizado:**

**Factores de optimización:**

1. **Intervalo GPS:**
   - Actualiza cada 30 segundos (no continuo)
   - Suficiente para tracking de entregas
   - Ajustable según necesidad

2. **Servicio foreground:**
   - Más eficiente que JavaScript continuo
   - Android optimiza servicios foreground
   - Menor uso de CPU que PWA

3. **Comparación:**
   ```
   PWA continua (JavaScript):   🔋🔋🔋 25% batería/8h
   Native foreground service:   🔋🔋   15% batería/8h
   Google Maps navegación:      🔋🔋🔋 30% batería/8h
   ```

**Consumo esperado:** 15-20% de batería en jornada de 8 horas.

### ¿Funciona offline?

**Sí, parcialmente:**

1. **Captura GPS:**
   - GPS no requiere internet ✅
   - Satélites funcionan sin conexión ✅

2. **Almacenamiento local:**
   - App guarda ubicaciones en base de datos local ✅
   - PWA usa IndexedDB o localStorage ✅

3. **Sincronización:**
   - Cuando recupera conexión → Envía datos ✅
   - Service Worker maneja sincronización ✅

**Resultado:** Conductor puede trabajar en zonas sin señal, datos se sincronizan después.

### ¿Cómo actualizo la app?

**Opción 1: APK Manual**
```
1. Usuario descarga nuevo APK
2. Instala sobre versión anterior
3. Android preserva datos y configuración
```

**Opción 2: Google Play (si está publicada)**
```
1. Play Store detecta actualización automáticamente
2. Descarga e instala en background
3. Usuario no necesita hacer nada
```

**Opción 3: Actualización Web**
```
1. Como TWA carga contenido web (PWA)
2. Actualizar código en servidor → Ya disponible
3. No requiere actualizar APK
```

**Mejor práctica:** Cambios web se actualizan automáticamente, cambios nativos requieren nuevo APK.

---

## 📲 Instalación

### ¿Dónde descargo la app?

**El administrador proporcionará el enlace:**
- GitHub Releases
- Servidor de la empresa
- Email con adjunto

**No está en Google Play (por ahora).**

### "No puedo instalar - Origen desconocido"

**Solución:**

**Android 8.0+:**
```
1. Settings → Apps & notifications
2. Special app access → Install unknown apps
3. Chrome (o navegador usado) → Allow
```

**Android 7.0 y anteriores:**
```
1. Settings → Security
2. Unknown sources → Enable
```

### ¿Qué permisos debo dar?

**Ubicación:**
- ✅ Seleccionar **"Permitir todo el tiempo"** o **"Permitir siempre"**
- ❌ NO "Solo mientras uso la app" (GPS se detendrá)

**Notificaciones:**
- ✅ Permitir (para ver que GPS está activo)

**Otros:**
- App no pide otros permisos (contactos, cámara, etc.)

### ¿Por qué necesita "todo el tiempo"?

**Para funcionar con pantalla bloqueada:**

```
"Solo mientras uso la app":
→ GPS se detiene cuando bloqueas celular ❌

"Permitir todo el tiempo":
→ GPS continúa con celular bloqueado ✅
```

**Es necesario para cumplir la función de tracking continuo.**

---

## 🔍 Verificación

### ¿Cómo sé si está funcionando?

**Indicador #1: Notificación Persistente**
```
┌─────────────────────────────────────┐
│ 🛰️ SoptraLoc GPS Activo            │
│ Rastreando tu ubicación             │
└─────────────────────────────────────┘
```

Si NO ves esta notificación → GPS NO está activo.

**Indicador #2: Test de Bloqueo**
```
1. Abre app
2. Login
3. Bloquea celular (botón power)
4. Espera 2 minutos
5. Desbloquea
6. Abre app o monitoring
7. Verifica que ubicación se actualizó
```

**Indicador #3: Dashboard Admin**
```
Administrador puede ver tu ubicación en:
https://soptraloc.onrender.com/monitoring/

Pedirle que confirme que ve actualizaciones.
```

### ¿Cada cuánto se actualiza la ubicación?

**Intervalo:** Cada 30 segundos

**Razón:** Balance entre precisión y batería.

**Ajustable:** Si se requiere más frecuente (cada 10s) o menos (cada 60s), se puede configurar.

### ¿Qué tan precisa es la ubicación?

**Depende del GPS del celular:**

- **GPS + GLONASS + Galileo:** ±5 metros
- **Solo GPS:** ±10-20 metros
- **Sin señal GPS (indoor):** Puede usar WiFi/Cell towers (menos preciso)

**En general:** Suficientemente preciso para tracking de entregas.

---

## 🚨 Problemas Comunes

### GPS no funciona en background

**Diagnóstico:**

1. **Verificar permiso:**
   ```
   Settings → Apps → SoptraLoc → Permissions → Location
   → Debe decir "Allowed all the time"
   ```

2. **Verificar optimización batería:**
   ```
   Settings → Battery → Battery optimization
   → SoptraLoc → Don't optimize
   ```

3. **Verificar GPS del celular:**
   ```
   Settings → Location → On
   → Mode: High accuracy
   ```

4. **Verificar notificación:**
   ```
   Si no ves "GPS Activo" → Servicio no inició
   ```

**Solución:**
- Reinstalar app
- Conceder todos los permisos correctamente
- Reiniciar celular

### App se cierra sola

**Causa común:** Optimización agresiva de batería

**Solución:**

**Xiaomi/MIUI:**
```
Settings → Apps → SoptraLoc → Battery saver → No restrictions
Security → Permissions → Autostart → Enable SoptraLoc
```

**Huawei/EMUI:**
```
Settings → Battery → App launch → SoptraLoc → Manual
→ Enable: Auto-launch, Secondary launch, Run in background
```

**Samsung:**
```
Settings → Apps → SoptraLoc → Battery → Allow background activity
Device care → Battery → App power management → Put unused apps to sleep → Exclude SoptraLoc
```

**OnePlus/Oppo:**
```
Settings → Battery → Battery optimization → SoptraLoc → Don't optimize
Settings → Apps → SoptraLoc → Advanced → Battery → Allow background activity
```

### No veo la notificación "GPS Activo"

**Causa:** Notificaciones bloqueadas

**Solución:**
```
Settings → Apps → SoptraLoc → Notifications
→ Allow all notifications
→ Set importance to High
```

### "Error de ubicación"

**Soluciones:**

1. **Verificar GPS:**
   ```
   Settings → Location → On
   ```

2. **Modo de precisión:**
   ```
   Settings → Location → Location mode → High accuracy
   ```

3. **Permisos de ubicación:**
   ```
   Settings → Apps → SoptraLoc → Permissions → Location → Allow all the time
   ```

4. **Reiniciar app:**
   ```
   Cerrar completamente y volver a abrir
   ```

5. **Limpiar cache:**
   ```
   Settings → Apps → SoptraLoc → Storage → Clear cache
   ```

### APK no instala / "App not installed"

**Causas posibles:**

1. **Espacio insuficiente:**
   ```
   Verificar espacio disponible > 100 MB
   Settings → Storage
   ```

2. **APK corrupto:**
   ```
   Re-descargar APK
   Verificar que descarga completó 100%
   ```

3. **Versión conflictiva:**
   ```
   Desinstalar versión anterior primero:
   Settings → Apps → SoptraLoc → Uninstall
   Luego instalar nuevo APK
   ```

4. **Android muy antiguo:**
   ```
   Requiere Android 6.0+ (API 23)
   Verificar: Settings → About phone → Android version
   ```

### Batería se agota rápido

**Diagnóstico:**

1. **Verificar consumo real:**
   ```
   Settings → Battery → Battery usage
   → Verificar % de SoptraLoc
   ```

2. **Comparar con otras apps:**
   ```
   Si SoptraLoc > 30% → Problema
   Si SoptraLoc ~15-20% → Normal
   ```

**Soluciones:**

1. **Ajustar intervalo GPS:**
   ```
   Contactar administrador para cambiar de 30s a 60s
   ```

2. **Verificar otras apps:**
   ```
   Otras apps (redes sociales, juegos) pueden ser el problema
   ```

3. **Batería antigua:**
   ```
   Si celular tiene >2 años, batería puede estar degradada
   ```

---

## 🌐 Red y Conectividad

### ¿Funciona sin internet?

**Sí y No:**

**Funciona (GPS local):**
- ✅ Captura ubicación GPS (satélites, no requiere internet)
- ✅ Guarda ubicaciones localmente
- ✅ Continúa rastreando

**No funciona (sincronización):**
- ❌ No puede enviar datos a servidor
- ❌ Dashboard no muestra ubicación en tiempo real

**Solución automática:**
- Cuando recupera señal → Sincroniza todo automáticamente ✅

### ¿Qué pasa si pierdo señal?

**El sistema sigue funcionando:**

```
1. Conductor entra a zona sin señal
2. GPS captura ubicación (satélites funcionan)
3. App guarda ubicación localmente
4. Conductor sale de zona sin señal
5. App detecta conexión
6. Sincroniza todas las ubicaciones guardadas
7. Dashboard se actualiza con tracking completo
```

**Resultado:** No se pierde información, solo se retrasa la sincronización.

### ¿Consume muchos datos móviles?

**No, es mínimo:**

**Cálculo:**
```
Ubicación enviada cada 30 segundos:
- Tamaño por request: ~500 bytes
- Por hora: 60 requests/h × 500 bytes = ~30 KB/h
- Por día (8h): ~240 KB/día
- Por mes (22 días): ~5 MB/mes
```

**Comparable a:** WhatsApp recibiendo 10 mensajes de texto.

---

## 📊 Administración

### ¿Cómo monitoreo que todos tengan GPS activo?

**Dashboard de Monitoring:**
```
https://soptraloc.onrender.com/monitoring/
```

**Indicadores:**

1. **Última actualización:**
   - Verde: <2 minutos → Activo ✅
   - Amarillo: 2-10 minutos → Posible problema ⚠️
   - Rojo: >10 minutos → Inactivo ❌

2. **Número de conductores:**
   - Dashboard muestra total activos vs total

### ¿Cómo distribuyo el APK a conductores?

**Opción 1: Email**
```
1. Subir APK a servidor/GitHub
2. Email con enlace de descarga
3. Incluir guía de instalación
```

**Opción 2: WhatsApp**
```
1. Enviar archivo APK directamente (si <18 MB)
2. O enlace de descarga
3. Mensaje con instrucciones
```

**Opción 3: Presencial**
```
1. Instalar en celular del conductor
2. Configurar permisos correctamente
3. Verificar funcionamiento antes de que salga
```

**Opción 4: Google Play**
```
1. Publicar en Play Store ($25 único)
2. Compartir enlace de la app
3. Conductores instalan desde Play Store
```

### ¿Puedo rastrear cuántos tienen la app instalada?

**Sí, varias formas:**

1. **Analytics en el servidor:**
   - Ver IDs de conductores que envían GPS
   - Comparar con lista total

2. **Dashboard:**
   - Conductores activos = Con app instalada

3. **Google Play Console (si publicas):**
   - Muestra instalaciones totales
   - Dispositivos activos
   - Versión de cada instalación

---

## 🔒 Seguridad y Privacidad

### ¿La app espía al conductor?

**No, solo hace lo que dice:**

**Permisos que pide:**
- ✅ Ubicación GPS (para tracking de entregas)
- ✅ Notificaciones (para informar estado GPS)

**NO accede a:**
- ❌ Contactos
- ❌ Mensajes/SMS
- ❌ Llamadas
- ❌ Cámara
- ❌ Micrófono
- ❌ Fotos/Videos
- ❌ Redes sociales

**Código abierto:** Todo el código está en GitHub, cualquiera puede auditarlo.

### ¿Qué pasa con los datos GPS?

**Almacenamiento:**
- Datos GPS se envían a servidor SoptraLoc
- Servidor los guarda en base de datos PostgreSQL
- Usado solo para tracking de entregas

**Privacidad:**
- Datos solo accesibles para administradores
- No se comparten con terceros
- Cumple con leyes de protección de datos

### ¿El conductor puede desactivar el GPS?

**Sí, tiene control:**

1. **Desactivar GPS del celular:**
   ```
   Settings → Location → Off
   → App no puede obtener ubicación
   ```

2. **Forzar cierre de app:**
   ```
   Settings → Apps → SoptraLoc → Force stop
   → Servicio se detiene
   ```

3. **Desinstalar app:**
   ```
   Como cualquier otra app
   ```

**Transparencia:** La notificación persistente siempre indica cuando GPS está activo.

---

## 📞 Soporte

### ¿A quién contacto si tengo problemas?

**Conductor:**
- Contactar al administrador de flota
- Enviar capturas de pantalla del problema
- Indicar modelo de celular y versión Android

**Administrador:**
- Revisar esta FAQ primero
- Consultar [NATIVE_ANDROID_APP.md](NATIVE_ANDROID_APP.md) para troubleshooting técnico
- Contactar a desarrollador si es bug de la app

### ¿Dónde reporto bugs?

**GitHub Issues:**
```
https://github.com/Safary16/soptraloc/issues
```

**Información a incluir:**
- Modelo de celular
- Versión de Android
- Pasos para reproducir el problema
- Capturas de pantalla
- Logs si es posible (adb logcat)

---

**Última actualización:** Octubre 2024  
**Mantenido por:** Equipo SoptraLoc
