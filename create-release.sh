#!/bin/bash
# Script para crear un release de GitHub con el APK

set -e

echo "🚀 SoptraLoc - Create GitHub Release"
echo "====================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "README.md" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que gh está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) no está instalado"
    echo ""
    echo "Instalar GitHub CLI:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "  Windows: https://github.com/cli/cli/releases"
    exit 1
fi

# Verificar autenticación
if ! gh auth status &> /dev/null; then
    echo "❌ Error: No estás autenticado en GitHub CLI"
    echo ""
    echo "Para autenticarte:"
    echo "  gh auth login"
    exit 1
fi

echo "✓ GitHub CLI autenticado correctamente"
echo ""

# Solicitar versión
read -p "Versión del release (ej: v1.0.0): " VERSION

if [ -z "$VERSION" ]; then
    echo "❌ Error: Debes especificar una versión"
    exit 1
fi

# Verificar que el APK existe
APK_PATH="android/app/build/outputs/apk/debug/app-debug.apk"

if [ ! -f "$APK_PATH" ]; then
    echo "⚠️  APK no encontrado en $APK_PATH"
    echo ""
    read -p "¿Deseas compilar el APK ahora? (y/n): " BUILD_NOW
    
    if [ "$BUILD_NOW" = "y" ]; then
        echo ""
        echo "🔨 Compilando APK..."
        cd android
        ./gradlew assembleDebug
        cd ..
        
        if [ ! -f "$APK_PATH" ]; then
            echo "❌ Error: No se pudo compilar el APK"
            exit 1
        fi
        echo "✅ APK compilado exitosamente"
    else
        echo "❌ Error: Se necesita el APK para crear el release"
        exit 1
    fi
fi

echo ""
echo "📦 APK encontrado: $APK_PATH"
APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
echo "   Tamaño: $APK_SIZE"
echo ""

# Crear el release
echo "🚀 Creando release en GitHub..."
echo ""

gh release create "$VERSION" \
    "$APK_PATH#SoptraLoc-Driver-${VERSION}.apk" \
    --title "SoptraLoc Driver $VERSION" \
    --notes "## 📱 SoptraLoc Driver APK

### 📥 Descarga e Instalación

1. **Descargar el APK** en tu celular Android
2. Si aparece \"Origen desconocido\":
   - Configuración → Seguridad → Permitir instalación desde orígenes desconocidos
3. **Instalar el APK**
4. **Abrir la app**
5. **Conceder permisos de ubicación** → \"Permitir todo el tiempo\"

### ✨ Características

- ✅ GPS continuo en background
- ✅ Notificación persistente
- ✅ Funciona con pantalla bloqueada
- ✅ Bajo consumo de batería

### 📊 Requisitos

- Android 6.0 (API 23) o superior
- Conexión a internet
- GPS activado

### 🔧 Solución de Problemas

Ver la [guía completa de descarga](https://github.com/Safary16/soptraloc/blob/main/DOWNLOAD_APK.md) para instrucciones detalladas.

### 📝 Notas

- Esta es una versión DEBUG para testing
- Solo para uso interno de conductores SOPTRA
- Para soporte, contactar al administrador

---

**Tamaño del APK:** $APK_SIZE  
**Fecha:** $(date '+%Y-%m-%d')  
**Desarrollador:** Sebastian Honores (Safary16)"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Release creado exitosamente!"
    echo ""
    echo "🔗 URL del release:"
    gh release view "$VERSION" --web
    echo ""
    echo "📲 Enlace directo al APK:"
    echo "   https://github.com/Safary16/soptraloc/releases/download/$VERSION/SoptraLoc-Driver-${VERSION}.apk"
    echo ""
    echo "📋 Comparte este enlace con los conductores:"
    echo "   https://github.com/Safary16/soptraloc/releases/latest"
else
    echo ""
    echo "❌ Error al crear el release"
    exit 1
fi

echo ""
echo "=================================="
echo "✨ Proceso completado"
