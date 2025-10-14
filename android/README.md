# 📱 SoptraLoc Driver - Android Native App

## 🎯 Quick Start

Esta carpeta contiene la configuración para compilar una **app nativa Android (APK)** que envuelve la PWA de SoptraLoc usando **Trusted Web Activity (TWA)**.

### ✅ Características
- **GPS continuo** incluso con pantalla bloqueada
- **Permisos nativos** de Android
- **Servicio foreground** mantiene GPS activo
- **Notificación persistente** indica GPS activo
- **APK descargable** - no requiere Google Play

---

## 🚀 Compilar APK (3 Opciones)

### Opción 1: Script Automático (Más Fácil)

```bash
cd android
./build-apk.sh
```

Selecciona:
- `1` para Debug APK (testing)
- `2` para Release APK (producción)

### Opción 2: Android Studio (Recomendado)

1. Abrir Android Studio
2. `File → Open` → Seleccionar carpeta `/android`
3. Esperar sincronización de Gradle
4. `Build → Build Bundle(s) / APK(s) → Build APK(s)`
5. APK en: `app/build/outputs/apk/`

### Opción 3: Línea de Comandos

```bash
cd android

# Debug APK
./gradlew assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk

# Release APK (requiere firma)
./gradlew assembleRelease
# Output: app/build/outputs/apk/release/app-release.apk
```

---

## 📋 Prerequisitos

- **Java JDK 8+** - [Descargar](https://adoptium.net/)
- **Android SDK** - Incluido en Android Studio
- **(Opcional)** Android Studio para desarrollo

---

## 🔐 Firmar APK para Producción

### 1. Generar Keystore

```bash
keytool -genkey -v -keystore soptraloc-release.keystore \
  -alias soptraloc -keyalg RSA -keysize 2048 -validity 10000
```

**¡Guardar contraseña en lugar seguro!**

### 2. Obtener SHA-256

```bash
keytool -list -v -keystore soptraloc-release.keystore -alias soptraloc
```

Copiar el SHA-256 fingerprint.

### 3. Actualizar assetlinks.json

Editar `../static/.well-known/assetlinks.json`:
```json
{
  "sha256_cert_fingerprints": [
    "TU_SHA256_AQUI"
  ]
}
```

### 4. Configurar Firma en Gradle

Editar `app/build.gradle`:
```gradle
android {
    signingConfigs {
        release {
            storeFile file("../soptraloc-release.keystore")
            storePassword "TU_PASSWORD"
            keyAlias "soptraloc"
            keyPassword "TU_PASSWORD"
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            // ...
        }
    }
}
```

### 5. Compilar

```bash
./gradlew assembleRelease
```

---

## 📲 Instalar en Dispositivo

### USB Debugging

```bash
# Verificar dispositivo conectado
adb devices

# Instalar APK
adb install app/build/outputs/apk/debug/app-debug.apk

# Ver logs
adb logcat | grep -i soptraloc
```

### Descarga Directa

1. Subir APK a servidor/GitHub Releases
2. Abrir enlace en celular Android
3. Descargar e instalar
4. Si aparece "Origen desconocido":
   - `Settings → Seguridad → Permitir instalación desde orígenes desconocidos`

---

## 🧪 Testing

### Test 1: GPS en Background
```
1. Instalar APK
2. Login y verificar GPS activo
3. Presionar Home (background)
4. Esperar 1 minuto
5. Verificar en /monitoring/ que ubicación se actualizó
✅ GPS funciona en background
```

### Test 2: Pantalla Bloqueada
```
1. App abierta, GPS activo
2. Bloquear pantalla
3. Esperar 2 minutos
4. Verificar ubicación en /monitoring/
✅ GPS funciona con pantalla bloqueada
```

---

## 🔍 Troubleshooting

### Error: "Android SDK not found"
```bash
# Instalar Android Studio o configurar SDK path:
export ANDROID_HOME=/path/to/android/sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

### Error: "Java version"
```bash
# Verificar Java
java -version

# Debe ser JDK 8 o superior
```

### GPS no funciona
```
Settings → Apps → SoptraLoc → Permissions → Location
→ "Allow all the time"
```

---

## 📚 Documentación Completa

Ver **[NATIVE_ANDROID_APP.md](../NATIVE_ANDROID_APP.md)** para:
- Arquitectura detallada TWA
- Configuración servidor (assetlinks.json)
- Distribución Google Play
- Troubleshooting avanzado

---

## 🎯 Estructura del Proyecto

```
android/
├── build.gradle              # Config proyecto
├── settings.gradle           # Módulos
├── gradle.properties         # Propiedades
├── build-apk.sh             # Script compilación
├── README.md                # Este archivo
└── app/
    ├── build.gradle         # Config app
    ├── proguard-rules.pro   # Optimización
    └── src/main/
        ├── AndroidManifest.xml    # Permisos & config
        └── res/
            └── values/
                ├── strings.xml    # Textos
                ├── styles.xml     # Temas
                └── colors.xml     # Colores
```

---

**¿Necesitas ayuda?** Revisa [NATIVE_ANDROID_APP.md](../NATIVE_ANDROID_APP.md) o contacta al equipo de desarrollo.
