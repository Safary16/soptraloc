#!/bin/bash
# Script automatizado para compilar y preparar la app nativa SoptraLoc Driver
# Este script se ejecutará una vez que dl.google.com esté desbloqueado

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  SoptraLoc Driver - Build & Deploy Script     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Variables
PROJECT_ROOT="/home/runner/work/soptraloc/soptraloc"
ANDROID_DIR="$PROJECT_ROOT/android"
STATIC_DIR="$PROJECT_ROOT/static"
APK_NAME="soptraloc-driver.apk"

# Paso 1: Verificar requisitos
echo -e "${YELLOW}📋 Verificando requisitos...${NC}"

if ! command -v java &> /dev/null; then
    echo -e "${RED}❌ Java no encontrado${NC}"
    exit 1
fi

if [ ! -d "$ANDROID_HOME" ]; then
    echo -e "${RED}❌ ANDROID_HOME no configurado correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Java instalado${NC}"
echo -e "${GREEN}✓ Android SDK configurado${NC}"
echo ""

# Paso 2: Verificar conectividad a dl.google.com
echo -e "${YELLOW}🌐 Verificando acceso a dl.google.com...${NC}"

if ! curl -s --connect-timeout 5 https://dl.google.com > /dev/null 2>&1; then
    echo -e "${RED}❌ No se puede acceder a dl.google.com${NC}"
    echo -e "${RED}   Este dominio es necesario para compilar el APK${NC}"
    echo -e "${YELLOW}   Por favor, desbloquea el acceso y vuelve a ejecutar este script${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Acceso a dl.google.com confirmado${NC}"
echo ""

# Paso 3: Limpiar builds anteriores
echo -e "${YELLOW}🧹 Limpiando builds anteriores...${NC}"
cd "$ANDROID_DIR"
./gradlew clean > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Limpieza completada${NC}"
echo ""

# Paso 4: Compilar APK Debug
echo -e "${YELLOW}🔨 Compilando APK debug (esto puede tomar 2-5 minutos)...${NC}"
echo ""

if ./gradlew assembleDebug --no-daemon; then
    echo ""
    echo -e "${GREEN}✅ APK compilado exitosamente!${NC}"
else
    echo ""
    echo -e "${RED}❌ Error al compilar APK${NC}"
    echo -e "${YELLOW}Revisa los logs arriba para más detalles${NC}"
    exit 1
fi
echo ""

# Paso 5: Verificar APK generado
APK_PATH="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"

if [ ! -f "$APK_PATH" ]; then
    echo -e "${RED}❌ APK no encontrado en: $APK_PATH${NC}"
    exit 1
fi

APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
echo -e "${GREEN}✓ APK generado: $APK_SIZE${NC}"
echo ""

# Paso 6: Copiar APK a directorio static
echo -e "${YELLOW}📦 Copiando APK a directorio static...${NC}"

mkdir -p "$STATIC_DIR"
cp "$APK_PATH" "$STATIC_DIR/$APK_NAME"

if [ -f "$STATIC_DIR/$APK_NAME" ]; then
    echo -e "${GREEN}✓ APK copiado a: $STATIC_DIR/$APK_NAME${NC}"
else
    echo -e "${RED}❌ Error al copiar APK${NC}"
    exit 1
fi
echo ""

# Paso 7: Crear página de descarga
echo -e "${YELLOW}📄 Creando página de descarga...${NC}"

DOWNLOAD_PAGE="$STATIC_DIR/download-app.html"

cat > "$DOWNLOAD_PAGE" << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargar SoptraLoc Driver</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        .download-section {
            text-align: center;
            margin: 30px 0;
        }
        .download-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 40px;
            border-radius: 12px;
            text-decoration: none;
            font-size: 1.2em;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .download-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }
        .info-box h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .info-box ol, .info-box ul {
            padding-left: 25px;
            line-height: 1.8;
            color: #333;
        }
        .info-box li {
            margin: 10px 0;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        .feature-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .feature h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .feature p {
            color: #666;
            font-size: 0.9em;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 0.9em;
        }
        strong {
            color: #667eea;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 SoptraLoc Driver</h1>
            <p>App Nativa para Conductores</p>
        </div>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">🚗</div>
                <h4>GPS Siempre Activo</h4>
                <p>Funciona con pantalla bloqueada</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h4>Bajo Consumo</h4>
                <p>Optimizado para toda la jornada</p>
            </div>
            <div class="feature">
                <div class="feature-icon">✅</div>
                <h4>Legal y Seguro</h4>
                <p>No necesitas tocar el celular</p>
            </div>
        </div>

        <div class="download-section">
            <a href="/static/soptraloc-driver.apk" class="download-btn" download>
                ⬇️ Descargar App
            </a>
            <p style="margin-top: 15px; color: #999;">Versión 1.0.0 | Android 6.0+</p>
        </div>

        <div class="info-box">
            <h3>📋 Cómo Instalar</h3>
            <ol>
                <li>Toca el botón <strong>"Descargar App"</strong> arriba</li>
                <li>Abre <strong>Configuración → Seguridad</strong> en tu celular</li>
                <li>Activa <strong>"Instalar aplicaciones de origen desconocido"</strong></li>
                <li>Abre el archivo descargado</li>
                <li>Toca <strong>"Instalar"</strong> y espera</li>
                <li>Al abrir, acepta permisos de ubicación: <strong>"Permitir siempre"</strong></li>
            </ol>
        </div>

        <div class="info-box">
            <h3>🚀 Cómo Usar</h3>
            <ol>
                <li>Abre <strong>"SoptraLoc Driver"</strong></li>
                <li>Ingresa la <strong>patente de tu vehículo</strong></li>
                <li>Toca <strong>"Iniciar Sesión"</strong></li>
                <li>Toca <strong>"Iniciar Tracking"</strong></li>
                <li>Guarda el celular en la guantera</li>
                <li>¡Listo! El GPS funciona automáticamente 🎉</li>
            </ol>
        </div>

        <div class="info-box">
            <h3>❓ ¿Necesitas Ayuda?</h3>
            <p>Si tienes problemas con la instalación o el uso de la app:</p>
            <ul>
                <li>Contacta a soporte técnico</li>
                <li>Verifica que tu Android sea versión 6.0 o superior</li>
                <li>Asegúrate de tener GPS activado</li>
                <li>Confirma que tienes conexión a internet</li>
            </ul>
        </div>

        <div class="footer">
            <p>SoptraLoc © 2025 | Tracking GPS en Tiempo Real</p>
        </div>
    </div>
</body>
</html>
EOF

if [ -f "$DOWNLOAD_PAGE" ]; then
    echo -e "${GREEN}✓ Página de descarga creada${NC}"
else
    echo -e "${RED}❌ Error al crear página de descarga${NC}"
    exit 1
fi
echo ""

# Paso 8: Resumen final
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           ✅ BUILD COMPLETADO                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📦 APK Compilado:${NC}"
echo -e "   Ubicación: $STATIC_DIR/$APK_NAME"
echo -e "   Tamaño: $APK_SIZE"
echo ""
echo -e "${GREEN}🌐 Página de Descarga:${NC}"
echo -e "   Archivo: $DOWNLOAD_PAGE"
echo -e "   URL (después de deploy): https://soptraloc.onrender.com/static/download-app.html"
echo ""
echo -e "${YELLOW}📝 Próximos Pasos:${NC}"
echo ""
echo -e "1. ${BLUE}Agregar archivos a Git:${NC}"
echo -e "   cd $PROJECT_ROOT"
echo -e "   git add static/$APK_NAME static/download-app.html"
echo -e "   git commit -m 'Add native driver app for download'"
echo -e "   git push origin main"
echo ""
echo -e "2. ${BLUE}Esperar deploy en Render:${NC}"
echo -e "   Render detectará automáticamente el push y redesplegará (~5 min)"
echo ""
echo -e "3. ${BLUE}Verificar que funciona:${NC}"
echo -e "   https://soptraloc.onrender.com/static/download-app.html"
echo ""
echo -e "4. ${BLUE}Compartir con conductores:${NC}"
echo -e "   Envía el enlace por WhatsApp/Email a todos los conductores"
echo ""
echo -e "${GREEN}🎉 ¡Todo listo para distribuir la app a los conductores!${NC}"
echo ""
