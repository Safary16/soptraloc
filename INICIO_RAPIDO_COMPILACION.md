# ⚡ Inicio Rápido - Compilar App Nativa en 5 Minutos

## 🎯 Resumen Ultra-Rápido

```bash
# 1. Clonar
git clone https://github.com/Safary16/soptraloc.git
cd soptraloc/mobile-app

# 2. Instalar dependencias
npm install

# 3. Compilar
npm run build:android-debug

# 4. APK listo
ls -lh android/app/build/outputs/apk/debug/app-debug.apk
```

**Tiempo total:** 5-10 minutos

---

## 📋 Prerequisitos (Instalar UNA SOLA VEZ)

### Windows

```powershell
# 1. Instalar Chocolatey (si no lo tienes)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. Instalar Node.js y Java
choco install nodejs-lts -y
choco install openjdk11 -y

# 3. Instalar Android Studio
# Descargar de: https://developer.android.com/studio
# Instalar con configuración por defecto

# 4. Configurar variables de entorno
setx ANDROID_HOME "C:\Users\%USERNAME%\AppData\Local\Android\Sdk"
setx PATH "%PATH%;%ANDROID_HOME%\platform-tools"
```

### macOS

```bash
# 1. Instalar Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Node.js y Java
brew install node@20
brew install openjdk@11

# 3. Instalar Android Studio
brew install --cask android-studio

# 4. Abrir Android Studio una vez para configurar SDK
# Tools → SDK Manager → Install Android SDK 33

# 5. Configurar variables de entorno
echo 'export ANDROID_HOME=$HOME/Library/Android/sdk' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.zshrc
source ~/.zshrc
```

### Linux (Ubuntu/Debian)

```bash
# 1. Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 2. Instalar Java
sudo apt install -y openjdk-11-jdk

# 3. Descargar Android Studio
wget https://redirector.gvt1.com/edgedl/android/studio/ide-zips/2023.1.1.28/android-studio-2023.1.1.28-linux.tar.gz
tar -xzf android-studio-*.tar.gz
sudo mv android-studio /opt/

# 4. Ejecutar Android Studio
/opt/android-studio/bin/studio.sh
# Seguir el wizard de instalación

# 5. Configurar variables de entorno
echo 'export ANDROID_HOME=$HOME/Android/Sdk' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.bashrc
source ~/.bashrc
```

---

## 🚀 Compilación (CADA VEZ que necesites APK)

### Paso 1: Obtener el Código

```bash
# Si es la primera vez
git clone https://github.com/Safary16/soptraloc.git
cd soptraloc

# Si ya lo clonaste antes, actualizar
cd soptraloc
git pull origin main
```

### Paso 2: Instalar Dependencias

```bash
cd mobile-app
npm install
```

**Resultado esperado:**
```
added 954 packages in 2m
```

### Paso 3: Compilar APK

```bash
npm run build:android-debug
```

**Alternativa (si el comando npm no funciona):**
```bash
cd android
./gradlew assembleDebug
```

**En Windows usar:**
```cmd
gradlew.bat assembleDebug
```

### Paso 4: Verificar APK

```bash
# Linux/macOS
ls -lh android/app/build/outputs/apk/debug/app-debug.apk

# Windows
dir android\app\build\outputs\apk\debug\app-debug.apk
```

**Deberías ver:**
```
-rw-r--r-- 1 user user 35M Oct 14 20:00 app-debug.apk
```

---

## 📱 Instalar en Celular

### Método 1: USB (Más Rápido)

```bash
# 1. Conectar celular por USB
# 2. Habilitar "Depuración USB" en el celular:
#    Ajustes → Acerca → Tocar "Número de compilación" 7 veces
#    Ajustes → Opciones de Desarrollador → Depuración USB

# 3. Verificar conexión
adb devices

# 4. Instalar
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

### Método 2: Transferencia de Archivo

```bash
# 1. Copiar APK a una ubicación accesible
cp android/app/build/outputs/apk/debug/app-debug.apk ~/Desktop/SoptraLoc.apk

# 2. Transferir al celular (USB, email, WhatsApp, Drive)

# 3. En el celular:
#    - Abrir el APK
#    - Permitir instalación de origen desconocido
#    - Instalar
```

---

## 🐛 Solución de Problemas Comunes

### Error: "SDK location not found"

```bash
cd mobile-app/android
echo "sdk.dir=$ANDROID_HOME" > local.properties
```

### Error: "JAVA_HOME is not set"

**Linux/macOS:**
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> ~/.bashrc
```

**Windows:**
```powershell
setx JAVA_HOME "C:\Program Files\OpenJDK\jdk-11.0.x"
```

### Error: "Command failed: npm install"

```bash
# Limpiar caché e intentar de nuevo
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Error: "Execution failed for task ':app:mergeDebugResources'"

```bash
# Limpiar build y reintentar
cd android
./gradlew clean
./gradlew assembleDebug
```

### Build muy lento

```bash
# Aumentar memoria de Gradle
echo "org.gradle.jvmargs=-Xmx4096m" >> android/gradle.properties
```

---

## ✅ Checklist Rápido

Antes de compilar, verifica:

- [ ] Node.js 16+ instalado (`node --version`)
- [ ] Java 11+ instalado (`java -version`)
- [ ] Android SDK instalado (`echo $ANDROID_HOME`)
- [ ] Internet funcionando (`ping google.com`)
- [ ] En directorio correcto (`pwd` muestra `.../soptraloc/mobile-app`)

Para compilar:

- [ ] `npm install` exitoso
- [ ] `npm run build:android-debug` sin errores
- [ ] APK existe en `android/app/build/outputs/apk/debug/`
- [ ] APK tamaño ~30-40 MB

Para distribuir:

- [ ] APK probado en al menos 1 dispositivo
- [ ] GPS funciona con pantalla bloqueada
- [ ] Login por patente funciona
- [ ] Ubicación se envía al backend

---

## 📞 ¿Necesitas Más Ayuda?

- **Guía Completa:** [COMO_COMPILAR_APP_NATIVA.md](COMO_COMPILAR_APP_NATIVA.md)
- **Análisis del Problema:** [SOLUCION_PROBLEMA_APP_NATIVA.md](SOLUCION_PROBLEMA_APP_NATIVA.md)
- **Script de Validación:** `./mobile-app/validate-build-ready.sh`
- **Script de Distribución:** `./distribuir-app.sh`

---

## 🎯 Próximos Pasos Después de Compilar

1. **Probar** en 1 dispositivo primero
2. **Verificar** GPS con pantalla bloqueada
3. **Distribuir** a 3-5 conductores piloto
4. **Monitorear** durante 1 semana
5. **Rollout completo** a todos los conductores

---

**¿Listo para Empezar?** 🚀

```bash
git clone https://github.com/Safary16/soptraloc.git && cd soptraloc/mobile-app && npm install && npm run build:android-debug
```

**¡Eso es todo!** En 5 minutos tendrás tu APK listo. 🎉
