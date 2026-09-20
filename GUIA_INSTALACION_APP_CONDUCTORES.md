# 📱 Guía de Instalación - SoptraLoc Driver (Para Conductores)

## 🎯 ¿Por qué instalar esta app?

### ✅ Beneficios para ti como conductor:
- **Celular bloqueado mientras conduces** → Cumple ley de tránsito, no multas
- **No necesitas tocar el celular** → Más seguro, concentrado en la ruta
- **GPS siempre activo** → Ubicación precisa sin interrupciones
- **Menos consumo de batería** → Servicio optimizado
- **Legal y seguro** → Ley 18.290 permite GPS sin celular desbloqueado

### ❌ Problema de la versión web anterior:
- Requerías celular desbloqueado todo el tiempo
- Si bloqueabas pantalla → GPS se detenía
- Consumía mucha batería

---

## 📲 Cómo Instalar (Paso a Paso)

### Opción 1: Descarga Directa (Android)

#### 1️⃣ Descargar el APK

Abre este enlace en tu celular:
```
[ENLACE_DE_DESCARGA_APK]
```

**Nota:** El administrador te enviará el enlace correcto.

#### 2️⃣ Permitir Instalación

Cuando descargues, puede aparecer:
> ⚠️ "No se puede instalar - Origen desconocido"

**Solución:**
1. Ve a `Ajustes / Configuración`
2. Busca `Seguridad` o `Aplicaciones`
3. Activa `Orígenes desconocidos` o `Instalar apps desconocidas`
4. Permite instalar desde Chrome/Navegador

#### 3️⃣ Instalar la App

1. Toca el archivo descargado (`soptraloc-driver.apk`)
2. Toca **Instalar**
3. Espera unos segundos
4. Toca **Abrir** cuando termine

#### 4️⃣ Conceder Permisos de Ubicación

**MUY IMPORTANTE:**

Cuando abras la app por primera vez, pedirá permisos:

1. **Ubicación:**
   - ✅ Selecciona **"Permitir todo el tiempo"** o **"Permitir siempre"**
   - ❌ NO selecciones "Solo mientras uso la app"

2. **Notificaciones:**
   - ✅ Permitir notificaciones (para ver que GPS está activo)

#### 5️⃣ Configurar Ahorro de Batería

Para que GPS funcione siempre:

1. Ve a `Ajustes → Batería`
2. Busca `Optimización de batería` o `Ahorro de energía`
3. Busca **SoptraLoc**
4. Selecciona **"No optimizar"** o **"Sin restricciones"**

#### 6️⃣ ¡Listo! Inicia Sesión

1. Abre la app
2. Ingresa tu usuario y contraseña
3. Verás una notificación: **"SoptraLoc GPS Activo"**
4. Ahora puedes bloquear tu celular y conducir tranquilo

---

### Opción 2: Desde Google Play Store (Próximamente)

Si la app se publica en Google Play:

1. Abrir Google Play Store
2. Buscar "SoptraLoc Driver"
3. Tocar **Instalar**
4. Seguir pasos 4-6 de arriba (permisos)

---

## 🔍 Cómo Verificar que Funciona

### ✅ Verificación 1: Notificación Permanente

Cuando la app está activa, verás una notificación:
```
🛰️ SoptraLoc GPS Activo
   Rastreando tu ubicación para entregas
```

**Si NO ves la notificación → GPS NO está funcionando**

### ✅ Verificación 2: Test con Pantalla Bloqueada

1. Abre la app
2. Inicia sesión
3. Bloquea tu celular (botón power)
4. Espera 2 minutos
5. Desbloquea y abre la app nuevamente
6. Si ves actualizaciones de ubicación → **Funciona correctamente** ✅

### ✅ Verificación 3: Pregunta al Administrador

El administrador puede ver tu ubicación en tiempo real en:
```
https://soptraloc-qiss.onrender.com/monitoring/
```

Pídele que confirme que ve tu ubicación actualizándose.

---

## ⚙️ Configuración Recomendada

### 📍 GPS Siempre Activo

```
Ajustes → Ubicación → Modo
→ Seleccionar "Alta precisión"
```

### 🔋 Sin Restricciones de Batería

```
Ajustes → Batería → Optimización de batería
→ SoptraLoc → No optimizar
```

### 🔔 Notificaciones Activas

```
Ajustes → Aplicaciones → SoptraLoc → Notificaciones
→ Permitir todas las notificaciones
```

### 📱 Inicio Automático

```
Ajustes → Aplicaciones → SoptraLoc → Inicio automático
→ Activar
```

---

## ❓ Preguntas Frecuentes

### ¿Es seguro instalar esta app?

✅ **Sí**, la app fue desarrollada específicamente para SoptraLoc.
- No contiene virus ni malware
- Solo accede a tu ubicación GPS (con tu permiso)
- No accede a contactos, fotos, mensajes, etc.

### ¿Por qué pide "Permitir todo el tiempo"?

Para que el GPS funcione **incluso con tu celular bloqueado**.

Si solo permites "Mientras uso la app":
- GPS se detendrá cuando bloquees el celular
- No cumplirá su función

### ¿Consume mucha batería?

**No**, la app está optimizada:
- Usa servicio foreground eficiente
- Actualiza ubicación cada 30 segundos (no constantemente)
- Consumo similar a Google Maps en background

### ¿Funciona sin internet?

**Sí**, parcialmente:
- Captura ubicación GPS (no requiere internet)
- Guarda ubicaciones localmente
- Sincroniza cuando recuperes conexión

### ¿Puedo usar otras apps mientras conduzco?

**Sí**, puedes:
- Bloquear celular
- Usar Waze/Google Maps
- Recibir llamadas
- Escuchar música

La app de SoptraLoc funciona en segundo plano.

### ¿Cómo sé si está funcionando?

Verás una **notificación permanente**:
```
🛰️ SoptraLoc GPS Activo
```

Si no la ves → No está funcionando → Revisar permisos.

---

## 🚨 Problemas Comunes y Soluciones

### Problema 1: "No se puede instalar"

**Causa:** Orígenes desconocidos bloqueado

**Solución:**
```
Ajustes → Seguridad → Orígenes desconocidos → Activar
```

### Problema 2: GPS no funciona en background

**Causa:** Permiso de ubicación incorrecto

**Solución:**
```
Ajustes → Aplicaciones → SoptraLoc → Permisos → Ubicación
→ Seleccionar "Permitir todo el tiempo"
```

### Problema 3: App se cierra sola

**Causa:** Optimización de batería mata la app

**Solución:**
```
Ajustes → Batería → Optimización de batería → SoptraLoc → No optimizar
```

### Problema 4: No veo la notificación GPS

**Causa:** Notificaciones bloqueadas

**Solución:**
```
Ajustes → Aplicaciones → SoptraLoc → Notificaciones → Permitir todas
```

### Problema 5: "Error de ubicación"

**Solución:**
1. Verificar que GPS del celular está activado:
   ```
   Ajustes → Ubicación → Activar
   ```

2. Verificar modo de precisión:
   ```
   Ajustes → Ubicación → Modo → Alta precisión
   ```

3. Reiniciar la app

### Problema 6: No puedo descargar el APK

**Solución:**
1. Verificar espacio en celular (necesitas al menos 50 MB)
2. Usar WiFi en vez de datos móviles
3. Contactar al administrador para otro método de descarga

---

## 🆘 ¿Necesitas Ayuda?

### Contacta al Administrador:
- **Email:** [admin@soptraloc.com]
- **Teléfono:** [+56 X XXXX XXXX]
- **WhatsApp:** [+56 X XXXX XXXX]

### Antes de contactar, ten lista esta información:
- Modelo de tu celular
- Versión de Android (Ajustes → Acerca del teléfono)
- Descripción del problema
- Capturas de pantalla si es posible

---

## 📝 Checklist de Instalación

Marca cada paso a medida que lo completes:

- [ ] Descargar APK desde el enlace proporcionado
- [ ] Permitir instalación desde orígenes desconocidos
- [ ] Instalar la app
- [ ] Abrir la app
- [ ] Conceder permiso de ubicación → **"Permitir todo el tiempo"**
- [ ] Conceder permiso de notificaciones
- [ ] Configurar batería → **"No optimizar"**
- [ ] Iniciar sesión con usuario y contraseña
- [ ] Verificar notificación **"SoptraLoc GPS Activo"**
- [ ] Test: Bloquear celular, esperar 2 min, verificar funcionamiento
- [ ] Confirmar con administrador que ve tu ubicación

---

## 🎉 ¡Felicitaciones!

Si completaste todos los pasos:
- ✅ GPS funcionando 24/7
- ✅ Celular bloqueado mientras conduces
- ✅ Cumple ley de tránsito
- ✅ Más seguro para ti y otros conductores

**¡Ahora puedes conducir tranquilo sabiendo que estás cumpliendo la ley y el sistema rastrea tus entregas automáticamente!**

---

**Versión:** 1.0  
**Última actualización:** Octubre 2024  
**Desarrollado para:** Conductores SoptraLoc
