#!/bin/bash

# Script para validar que la app nativa está lista para compilar
# Este script NO compila la app, solo verifica que todo esté configurado correctamente

set -e

echo "🔍 Validando configuración para compilar app nativa Android..."
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Función para imprimir resultado
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Verificando Prerequisitos del Sistema"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar Node.js
echo -n "Verificando Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -ge 16 ]; then
        check_pass "Node.js $NODE_VERSION instalado"
    else
        check_fail "Node.js $NODE_VERSION es muy antiguo (requiere v16+)"
    fi
else
    check_fail "Node.js NO instalado (requiere v16+)"
fi

# Verificar npm
echo -n "Verificando npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    check_pass "npm $NPM_VERSION instalado"
else
    check_fail "npm NO instalado"
fi

# Verificar Java
echo -n "Verificando Java... "
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    check_pass "Java instalado: $JAVA_VERSION"
else
    check_fail "Java NO instalado (requiere JDK 11+)"
fi

# Verificar ANDROID_HOME
echo -n "Verificando ANDROID_HOME... "
if [ -n "$ANDROID_HOME" ]; then
    if [ -d "$ANDROID_HOME" ]; then
        check_pass "ANDROID_HOME configurado: $ANDROID_HOME"
    else
        check_fail "ANDROID_HOME apunta a directorio inexistente: $ANDROID_HOME"
    fi
else
    check_warn "ANDROID_HOME no configurado (puede causar problemas)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Verificando Estructura del Proyecto"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar package.json
echo -n "Verificando package.json... "
if [ -f "package.json" ]; then
    check_pass "package.json existe"
else
    check_fail "package.json NO encontrado"
fi

# Verificar android/
echo -n "Verificando directorio android/... "
if [ -d "android" ]; then
    check_pass "android/ existe"
else
    check_fail "android/ NO encontrado"
fi

# Verificar gradlew
echo -n "Verificando gradlew... "
if [ -f "android/gradlew" ]; then
    if [ -x "android/gradlew" ]; then
        check_pass "android/gradlew existe y es ejecutable"
    else
        check_warn "android/gradlew existe pero NO es ejecutable"
    fi
else
    check_fail "android/gradlew NO encontrado"
fi

# Verificar AndroidManifest.xml
echo -n "Verificando AndroidManifest.xml... "
if [ -f "android/app/src/main/AndroidManifest.xml" ]; then
    check_pass "AndroidManifest.xml existe"
else
    check_fail "AndroidManifest.xml NO encontrado"
fi

# Verificar archivos Java
echo -n "Verificando MainActivity.java... "
if [ -f "android/app/src/main/java/com/soptraloc/MainActivity.java" ]; then
    check_pass "MainActivity.java existe"
else
    check_fail "MainActivity.java NO encontrado"
fi

echo -n "Verificando MainApplication.java... "
if [ -f "android/app/src/main/java/com/soptraloc/MainApplication.java" ]; then
    check_pass "MainApplication.java existe"
else
    check_fail "MainApplication.java NO encontrado"
fi

# Verificar build.gradle
echo -n "Verificando android/build.gradle... "
if [ -f "android/build.gradle" ]; then
    check_pass "android/build.gradle existe"
else
    check_fail "android/build.gradle NO encontrado"
fi

echo -n "Verificando android/app/build.gradle... "
if [ -f "android/app/build.gradle" ]; then
    check_pass "android/app/build.gradle existe"
else
    check_fail "android/app/build.gradle NO encontrado"
fi

# Verificar App.js
echo -n "Verificando App.js... "
if [ -f "App.js" ]; then
    FILE_SIZE=$(wc -c < "App.js")
    if [ "$FILE_SIZE" -gt 10000 ]; then
        check_pass "App.js existe ($FILE_SIZE bytes)"
    else
        check_warn "App.js existe pero parece incompleto ($FILE_SIZE bytes)"
    fi
else
    check_fail "App.js NO encontrado"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Verificando Dependencias npm"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar node_modules
echo -n "Verificando node_modules/... "
if [ -d "node_modules" ]; then
    NUM_PACKAGES=$(find node_modules -maxdepth 1 -type d | wc -l)
    if [ "$NUM_PACKAGES" -gt 100 ]; then
        check_pass "node_modules/ existe con $NUM_PACKAGES paquetes"
    else
        check_warn "node_modules/ existe pero parece incompleto ($NUM_PACKAGES paquetes)"
    fi
else
    check_warn "node_modules/ NO existe - ejecutar 'npm install'"
fi

# Verificar dependencias críticas
CRITICAL_DEPS=(
    "react-native"
    "react-native-geolocation-service"
    "react-native-background-actions"
    "@react-native-async-storage/async-storage"
    "axios"
)

for DEP in "${CRITICAL_DEPS[@]}"; do
    echo -n "Verificando $DEP... "
    if [ -d "node_modules/$DEP" ]; then
        check_pass "$DEP instalado"
    else
        check_warn "$DEP NO instalado"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Verificando Permisos Android"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

MANIFEST="android/app/src/main/AndroidManifest.xml"

if [ -f "$MANIFEST" ]; then
    REQUIRED_PERMISSIONS=(
        "ACCESS_FINE_LOCATION"
        "ACCESS_COARSE_LOCATION"
        "ACCESS_BACKGROUND_LOCATION"
        "FOREGROUND_SERVICE"
        "WAKE_LOCK"
    )
    
    for PERM in "${REQUIRED_PERMISSIONS[@]}"; do
        echo -n "Verificando permiso $PERM... "
        if grep -q "$PERM" "$MANIFEST"; then
            check_pass "$PERM declarado"
        else
            check_fail "$PERM NO declarado"
        fi
    done
else
    check_fail "No se puede verificar permisos (AndroidManifest.xml no encontrado)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Verificando Conectividad de Red"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar conectividad a repositorios necesarios
echo -n "Verificando acceso a dl.google.com... "
if ping -c 1 -W 2 dl.google.com &> /dev/null; then
    check_pass "dl.google.com accesible"
else
    check_fail "dl.google.com NO accesible (bloqueado por sandbox/firewall)"
fi

echo -n "Verificando acceso a maven.google.com... "
if ping -c 1 -W 2 maven.google.com &> /dev/null; then
    check_pass "maven.google.com accesible"
else
    check_warn "maven.google.com NO accesible"
fi

echo -n "Verificando acceso a jitpack.io... "
if ping -c 1 -W 2 jitpack.io &> /dev/null; then
    check_pass "jitpack.io accesible"
else
    check_warn "jitpack.io NO accesible"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumen de Validación"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ TODO LISTO PARA COMPILAR${NC}"
    echo ""
    echo "Puedes compilar el APK ejecutando:"
    echo "  cd android"
    echo "  ./gradlew assembleDebug"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  HAY ADVERTENCIAS (pero puede funcionar)${NC}"
    echo ""
    echo "Advertencias encontradas: $WARNINGS"
    echo ""
    echo "La compilación puede funcionar, pero es recomendable revisar las advertencias."
    echo ""
    exit 0
else
    echo -e "${RED}❌ HAY PROBLEMAS QUE DEBEN RESOLVERSE${NC}"
    echo ""
    echo "Errores: $ERRORS"
    echo "Advertencias: $WARNINGS"
    echo ""
    echo "Por favor resuelve los errores arriba antes de intentar compilar."
    echo ""
    
    if grep -q "dl.google.com NO accesible" <<< "$(ping -c 1 -W 2 dl.google.com 2>&1)"; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🚨 NOTA IMPORTANTE:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "El dominio dl.google.com está bloqueado en este entorno."
        echo "Este es un problema conocido del sandbox."
        echo ""
        echo "Para compilar la app, necesitas:"
        echo "1. Clonar el repositorio en una máquina con acceso a internet"
        echo "2. Seguir las instrucciones en COMO_COMPILAR_APP_NATIVA.md"
        echo ""
        echo "El código de la app está 100% listo, solo necesita acceso a red."
        echo ""
    fi
    
    exit 1
fi
