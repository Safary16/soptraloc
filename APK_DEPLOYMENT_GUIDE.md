# 🚀 APK Deployment Guide - Task 47

## ✅ Task 47 Completado

El APK de SoptraLoc Driver ahora está disponible para descarga online a través de GitHub Releases.

---

## 📦 ¿Qué se implementó?

### 1. **GitHub Actions Workflow** (Automatización CI/CD)

**Archivo:** `.github/workflows/build-apk.yml`

**Funcionalidad:**
- ✅ Construye el APK automáticamente en cada push a `main`
- ✅ Crea un GitHub Release cuando haces push de un tag (ej: `v1.0.0`)
- ✅ Sube el APK como artefacto descargable
- ✅ Incluye JDK 17 y Android SDK configurados

**Triggers:**
- Push a branch `main`
- Push de tags con formato `v*` (ej: `v1.0.0`, `v1.0.1`)
- Pull requests a `main`
- Manual dispatch (desde GitHub Actions UI)

### 2. **Documentación de Descarga Completa**

**Archivo:** `DOWNLOAD_APK.md`

Incluye:
- 📱 Enlaces directos de descarga
- 📋 Instrucciones paso a paso de instalación
- 🔧 Guía de solución de problemas
- ✨ Características de la app
- 📊 Requisitos del sistema
- 🔒 Información de seguridad y privacidad

### 3. **Página Web de Descarga**

**Archivo:** `static/download.html`

Una página HTML hermosa y responsive que incluye:
- ✅ Botón de descarga directo
- ✅ Lista de características
- ✅ Instrucciones de instalación
- ✅ Diseño mobile-first
- ✅ Detección automática de dispositivo móvil

**URL de acceso:** `https://soptraloc.onrender.com/static/download.html`

### 4. **Script de Creación de Releases**

**Archivo:** `create-release.sh`

Script bash interactivo para crear releases fácilmente:

```bash
./create-release.sh
```

Funcionalidad:
- ✅ Valida autenticación de GitHub CLI
- ✅ Compila APK si no existe
- ✅ Crea release en GitHub con notas formateadas
- ✅ Sube APK al release
- ✅ Proporciona enlaces directos

---

## 🎯 Cómo Usar el Sistema de APK

### Opción A: Usar GitHub Actions (Recomendado)

#### Crear un release automático:

```bash
# 1. Asegurarte de que los cambios están commiteados
git add .
git commit -m "Preparar versión 1.0.0"

# 2. Crear y pushear un tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 3. GitHub Actions automáticamente:
#    - Compilará el APK
#    - Creará el release
#    - Subirá el APK
```

#### Monitorear el build:

1. Ve a: https://github.com/Safary16/soptraloc/actions
2. Verás la ejecución del workflow "Build Android APK"
3. Espera a que termine (≈5-10 minutos)
4. El release aparecerá en: https://github.com/Safary16/soptraloc/releases

### Opción B: Usar el Script Manual

Si tienes GitHub CLI instalado:

```bash
# 1. Instalar GitHub CLI (si no lo tienes)
# macOS:
brew install gh

# Linux:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# 2. Autenticarte
gh auth login

# 3. Ejecutar el script
./create-release.sh
```

### Opción C: Build Local + Upload Manual

```bash
# 1. Compilar APK localmente
cd android
./gradlew assembleDebug

# 2. APK estará en:
# android/app/build/outputs/apk/debug/app-debug.apk

# 3. Crear release manualmente en GitHub:
# https://github.com/Safary16/soptraloc/releases/new

# 4. Subir el APK al release
```

---

## 📲 Compartir APK con Conductores

### Enlaces de Descarga:

**Última versión:**
```
https://github.com/Safary16/soptraloc/releases/latest
```

**Página de descarga bonita:**
```
https://soptraloc.onrender.com/static/download.html
```

**Descarga directa del APK:**
```
https://github.com/Safary16/soptraloc/releases/latest/download/app-debug.apk
```

### Mensaje para Enviar a Conductores:

```
📱 ¡Descarga la App de SoptraLoc Driver!

👉 Abre este enlace en tu celular:
https://soptraloc.onrender.com/static/download.html

✅ GPS continuo
✅ Funciona con pantalla bloqueada
✅ Bajo consumo de batería

Instrucciones completas incluidas.
```

### Código QR:

Puedes generar un código QR del enlace:
- Usa: https://www.qr-code-generator.com/
- URL: `https://github.com/Safary16/soptraloc/releases/latest`
- Imprime y comparte con los conductores

---

## 🔧 Troubleshooting

### Problema: GitHub Actions falla en build

**Solución:**
1. Ve a Actions: https://github.com/Safary16/soptraloc/actions
2. Click en el build fallido
3. Revisa los logs
4. Problemas comunes:
   - Falta dependencia en build.gradle
   - Error en AndroidManifest.xml
   - Problema con keystore (si es release build)

### Problema: No puedo crear un tag

**Error:** `tag already exists`

**Solución:**
```bash
# Ver tags existentes
git tag

# Eliminar tag local
git tag -d v1.0.0

# Eliminar tag remoto
git push origin :refs/tags/v1.0.0

# Crear nuevo tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

### Problema: El APK no se sube al release

**Solución:**
1. Verifica que el archivo se generó:
   ```bash
   ls -la android/app/build/outputs/apk/debug/
   ```
2. Verifica que el workflow llegó al paso de create release
3. Verifica que el token GITHUB_TOKEN tiene permisos

### Problema: Conductores no pueden instalar el APK

**Causa:** Seguridad de Android bloquea orígenes desconocidos

**Solución:** Ver `DOWNLOAD_APK.md` - sección de instalación

---

## 📊 Monitoreo de Descargas

### Ver estadísticas de release:

```bash
# Usando GitHub CLI
gh release view v1.0.0

# O en el navegador:
# https://github.com/Safary16/soptraloc/releases
```

### Ver builds recientes:

https://github.com/Safary16/soptraloc/actions/workflows/build-apk.yml

---

## 🔄 Proceso de Actualización

### Para publicar una nueva versión:

```bash
# 1. Hacer cambios en el código Android
# android/app/src/main/...

# 2. Actualizar versionCode y versionName
# Editar: android/app/build.gradle
# versionCode 2
# versionName "1.0.1"

# 3. Commitear cambios
git add .
git commit -m "Update to version 1.0.1"

# 4. Crear nuevo tag
git tag -a v1.0.1 -m "Release 1.0.1 - [Descripción de cambios]"

# 5. Pushear
git push origin main
git push origin v1.0.1

# 6. GitHub Actions creará automáticamente el release
```

### Notificar a conductores:

Cuando una nueva versión esté disponible:

```
📢 Nueva versión de SoptraLoc Driver disponible!

🆕 Versión 1.0.1
📝 Cambios:
  - [Lista de mejoras]
  - [Lista de correcciones]

📥 Descargar:
https://github.com/Safary16/soptraloc/releases/latest

💡 Solo instala sobre la app existente, tus datos se mantendrán.
```

---

## 🎯 Checklist de Deployment

Antes de hacer un release oficial:

- [ ] Código está testeado y funcional
- [ ] versionCode incrementado en build.gradle
- [ ] versionName actualizado en build.gradle
- [ ] CHANGELOG.md actualizado (opcional)
- [ ] README.md actualizado si hay cambios importantes
- [ ] Tag creado con formato semántico (v1.0.0)
- [ ] GitHub Actions build exitoso
- [ ] APK probado en al menos un dispositivo
- [ ] Instrucciones de instalación actualizadas si es necesario
- [ ] Conductores notificados sobre la actualización

---

## 🔒 Seguridad

### APK Debug vs Release:

**Debug APK (Actual):**
- ✅ Fácil de distribuir
- ✅ No requiere firma especial
- ⚠️ Solo para uso interno/testing
- ⚠️ Tamaño más grande

**Release APK (Futuro):**
- ✅ Optimizado y comprimido
- ✅ Firma de producción
- ✅ Listo para Google Play Store
- ⚠️ Requiere keystore privado

### Para crear Release APK:

Ver: `NATIVE_ANDROID_APP.md` - sección "Firmar el APK"

---

## 📞 Soporte

### Recursos:

- **Documentación completa:** `DOWNLOAD_APK.md`
- **Guía técnica Android:** `NATIVE_ANDROID_APP.md`
- **Build instructions:** `mobile-app/BUILD_INSTRUCTIONS.md`
- **GitHub Issues:** https://github.com/Safary16/soptraloc/issues

### Contacto:

- Desarrollador: Sebastian Honores (Safary16)
- Email: [tu-email@ejemplo.com]
- GitHub: @Safary16

---

## ✨ Resumen

✅ **Task 47 Completada:**
- Sistema automático de build APK ✅
- GitHub Actions CI/CD configurado ✅
- Documentación completa de descarga ✅
- Página web de descarga ✅
- Script de creación de releases ✅
- APK disponible online para descarga ✅

**El APK está ONLINE y disponible en:**
👉 https://github.com/Safary16/soptraloc/releases/latest

---

**Fecha de implementación:** Octubre 2025  
**Versión del sistema:** 1.0.0  
**Mantenido por:** Sebastian Honores (Safary16)
