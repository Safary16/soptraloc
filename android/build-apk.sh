#!/bin/bash
# Script para compilar APK de SoptraLoc Driver

set -e

echo "🚀 SoptraLoc Driver - Build Script"
echo "=================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "build.gradle" ]; then
    echo -e "${RED}❌ Error: Este script debe ejecutarse desde el directorio /android${NC}"
    exit 1
fi

# Verificar Java
if ! command -v java &> /dev/null; then
    echo -e "${RED}❌ Java no está instalado${NC}"
    echo "Instalar Java JDK 8+: https://adoptium.net/"
    exit 1
fi

echo -e "${GREEN}✓ Java instalado:${NC}"
java -version
echo ""

# Limpiar build anterior
echo "🧹 Limpiando builds anteriores..."
./gradlew clean
echo -e "${GREEN}✓ Limpieza completada${NC}"
echo ""

# Preguntar qué tipo de build
echo "Selecciona el tipo de build:"
echo "1) Debug (para testing, sin firma)"
echo "2) Release (para producción, requiere firma)"
read -p "Opción [1]: " BUILD_TYPE
BUILD_TYPE=${BUILD_TYPE:-1}

if [ "$BUILD_TYPE" = "1" ]; then
    echo ""
    echo "🔨 Compilando APK Debug..."
    ./gradlew assembleDebug
    
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    
    if [ -f "$APK_PATH" ]; then
        echo ""
        echo -e "${GREEN}✅ APK compilado exitosamente!${NC}"
        echo ""
        echo "📦 APK ubicado en:"
        echo "   $APK_PATH"
        echo ""
        echo "📱 Para instalar en dispositivo conectado:"
        echo "   adb install $APK_PATH"
        echo ""
        echo "⚠️  IMPORTANTE: Este es un APK de DEBUG"
        echo "   Solo para testing, no distribuir en producción"
    else
        echo -e "${RED}❌ Error: APK no fue generado${NC}"
        exit 1
    fi
    
elif [ "$BUILD_TYPE" = "2" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Build Release requiere configuración de firma${NC}"
    echo ""
    echo "Asegúrate de haber configurado el keystore en app/build.gradle"
    echo ""
    read -p "¿Continuar? (y/n): " CONFIRM
    
    if [ "$CONFIRM" != "y" ]; then
        echo "Cancelado"
        exit 0
    fi
    
    echo ""
    echo "🔨 Compilando APK Release..."
    ./gradlew assembleRelease
    
    APK_PATH="app/build/outputs/apk/release/app-release.apk"
    
    if [ -f "$APK_PATH" ]; then
        echo ""
        echo -e "${GREEN}✅ APK Release compilado exitosamente!${NC}"
        echo ""
        echo "📦 APK ubicado en:"
        echo "   $APK_PATH"
        echo ""
        echo "📊 Información del APK:"
        APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
        echo "   Tamaño: $APK_SIZE"
        echo ""
        echo "🚀 Siguiente paso:"
        echo "   1. Probar en dispositivo: adb install $APK_PATH"
        echo "   2. Subir a GitHub Releases o servidor"
        echo "   3. Compartir enlace con conductores"
    else
        echo -e "${RED}❌ Error: APK no fue generado${NC}"
        exit 1
    fi
else
    echo -e "${RED}Opción inválida${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo "✨ Build completado"
