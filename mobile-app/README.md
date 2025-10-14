# SoptraLoc Driver - Native Android App

## ⚠️ IMPORTANTE: Esta Es la App Nativa Correcta

Este repositorio contiene **DOS** proyectos Android:

| Directorio | Tipo | ¿Funciona con celular bloqueado? |
|------------|------|-----------------------------------|
| `/android` | TWA (Trusted Web Activity) | ❌ **NO** |
| `/mobile-app/android` | **App Nativa React Native** | ✅ **SÍ** |

**Este directorio (`/mobile-app/android`) es la app nativa REAL que DEBE usarse.**

## 🚀 Quick Start

### ⚠️ Nota Importante Sobre Compilación

**No se puede compilar en el entorno sandbox actual** porque los repositorios de Android (dl.google.com, maven.google.com) están bloqueados.

**Para compilar esta app:** Ver guía completa en [../COMO_COMPILAR_APP_NATIVA.md](../COMO_COMPILAR_APP_NATIVA.md)

### Validar que Todo Está Listo

```bash
./validate-build-ready.sh
```

### Prerequisites
- Node.js 16+ ✅ (tenemos v20.19.5)
- Android Studio or Android SDK ✅
- JDK 11+ ✅ (tenemos v17.0.16)
- **Internet access** ❌ (bloqueado en sandbox - requerido para compilar)

### Installation (Requiere Internet)

```bash
# Install dependencies
npm install

# Build debug APK
npm run build:android-debug

# Build release APK (requires keystore)
npm run build:android
```

### Output
- Debug APK: `android/app/build/outputs/apk/debug/app-debug.apk`
- Release APK: `android/app/build/outputs/apk/release/app-release.apk`

## 📱 Features

- ✅ GPS Background Tracking (works with screen locked)
- ✅ License plate authentication
- ✅ Foreground service for continuous location updates
- ✅ Real-time sync with Django backend
- ✅ Low battery consumption

## 🔧 Configuration

Edit `App.js` to change:
- API_BASE_URL: Backend server URL (default: https://soptraloc.onrender.com)
- GPS update interval: Default 30 seconds (line 243)

## 📖 Documentation

See `/NATIVE_APP_GUIDE.md` in the root directory for complete documentation.

## 🆘 Support

### Common Issues

**GPS not working when locked:**
- Go to Settings → Apps → SoptraLoc Driver → Permissions → Location
- Select "Allow all the time"

**Build errors:**
- Ensure ANDROID_HOME is set correctly
- Run `npm install` again
- Clean build: `cd android && ./gradlew clean`

## 📝 License

Proprietary - CCTi
