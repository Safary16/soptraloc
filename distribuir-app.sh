#!/bin/bash

# Script para distribuir la app nativa una vez compilada
# Ejecutar DESPUÉS de compilar el APK en una máquina con internet

set -e

echo "📦 SoptraLoc - Distribución de App Nativa"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: Este script debe ejecutarse desde el directorio raíz del repositorio${NC}"
    echo "   Ubicación actual: $(pwd)"
    echo "   Ejecutar: cd /ruta/a/soptraloc && ./distribuir-app.sh"
    exit 1
fi

# Ruta del APK compilado
APK_SOURCE="mobile-app/android/app/build/outputs/apk/debug/app-debug.apk"
APK_DEST="static/soptraloc-driver.apk"
HTML_DEST="static/download-app.html"

echo "1️⃣  Verificando APK compilado..."
if [ ! -f "$APK_SOURCE" ]; then
    echo -e "${RED}❌ APK no encontrado en: $APK_SOURCE${NC}"
    echo ""
    echo "Para compilar el APK:"
    echo "  cd mobile-app"
    echo "  npm install"
    echo "  npm run build:android-debug"
    echo ""
    echo "Ver COMO_COMPILAR_APP_NATIVA.md para instrucciones completas."
    exit 1
fi

APK_SIZE=$(du -h "$APK_SOURCE" | cut -f1)
echo -e "${GREEN}✅ APK encontrado ($APK_SIZE)${NC}"
echo ""

echo "2️⃣  Copiando APK a static/..."
mkdir -p static
cp "$APK_SOURCE" "$APK_DEST"
echo -e "${GREEN}✅ APK copiado a: $APK_DEST${NC}"
echo ""

echo "3️⃣  Creando página de descarga..."
cat > "$HTML_DEST" << 'EOF'
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px 30px;
        }
        
        .download-section {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .download-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 50px;
            border-radius: 50px;
            text-decoration: none;
            font-size: 20px;
            font-weight: bold;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(102, 126, 234, 0.5);
        }
        
        .download-btn:active {
            transform: translateY(0);
        }
        
        .info-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .info-box h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .instructions {
            text-align: left;
        }
        
        .instructions ol {
            padding-left: 25px;
            line-height: 1.8;
        }
        
        .instructions li {
            margin: 12px 0;
            color: #333;
        }
        
        .instructions strong {
            color: #667eea;
        }
        
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        .warning-title {
            font-weight: bold;
            color: #856404;
            margin-bottom: 8px;
        }
        
        .features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 30px 0;
        }
        
        .feature {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .feature-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .feature-text {
            font-size: 14px;
            color: #666;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 14px;
        }
        
        @media (max-width: 600px) {
            .header h1 {
                font-size: 24px;
            }
            
            .download-btn {
                font-size: 18px;
                padding: 15px 40px;
            }
            
            .features {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 SoptraLoc Driver</h1>
            <p>App Nativa para Conductores</p>
        </div>
        
        <div class="content">
            <div class="download-section">
                <a href="/static/soptraloc-driver.apk" class="download-btn" download>
                    ⬇️ Descargar APK
                </a>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-text"><strong>Funciona con celular bloqueado</strong></div>
                </div>
                <div class="feature">
                    <div class="feature-icon">📍</div>
                    <div class="feature-text"><strong>GPS continuo</strong></div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🚗</div>
                    <div class="feature-text"><strong>Manos libres</strong></div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔋</div>
                    <div class="feature-text"><strong>Bajo consumo</strong></div>
                </div>
            </div>
            
            <div class="info-box">
                <h3>📋 Instrucciones de Instalación</h3>
                <div class="instructions">
                    <ol>
                        <li>Toca el botón <strong>"Descargar APK"</strong> arriba</li>
                        <li>Espera a que termine la descarga</li>
                        <li>Abre el archivo descargado desde las notificaciones</li>
                        <li>Si aparece <strong>"Origen desconocido"</strong>:
                            <ul style="margin-top: 8px; line-height: 1.6;">
                                <li>Ve a <strong>Ajustes → Seguridad</strong></li>
                                <li>Habilita <strong>"Orígenes desconocidos"</strong> o <strong>"Instalar apps desconocidas"</strong></li>
                                <li>Vuelve atrás e intenta instalar de nuevo</li>
                            </ul>
                        </li>
                        <li>Toca <strong>"Instalar"</strong> y espera</li>
                        <li>Abre la app e ingresa tu <strong>patente</strong></li>
                    </ol>
                </div>
            </div>
            
            <div class="warning">
                <div class="warning-title">⚠️ IMPORTANTE: Permisos de Ubicación</div>
                <div>
                    Cuando la app solicite permisos de ubicación, debes seleccionar:
                    <ul style="margin-top: 8px; line-height: 1.6;">
                        <li><strong>"Permitir siempre"</strong> o <strong>"Permitir todo el tiempo"</strong></li>
                        <li style="color: #dc3545;">NO selecciones "Solo mientras se usa la app"</li>
                    </ul>
                    <div style="margin-top: 10px; font-size: 13px;">
                        Esto permite que el GPS funcione con el celular bloqueado, cumpliendo con la ley de tránsito.
                    </div>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🎯 ¿Qué hace esta app?</h3>
                <ul style="list-style: none; padding-left: 0;">
                    <li style="margin: 10px 0;">✅ Rastrea tu ubicación GPS cada 30 segundos</li>
                    <li style="margin: 10px 0;">✅ Funciona con pantalla bloqueada y app cerrada</li>
                    <li style="margin: 10px 0;">✅ Muestra notificación mientras está activo</li>
                    <li style="margin: 10px 0;">✅ Envía datos al sistema central de SoptraLoc</li>
                    <li style="margin: 10px 0;">✅ Permite conducir legalmente sin tocar el celular</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Versión 1.0.0 | SoptraLoc © 2025</p>
            <p style="margin-top: 5px;">Para soporte técnico, contacta al administrador</p>
        </div>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✅ Página de descarga creada: $HTML_DEST${NC}"
echo ""

echo "4️⃣  Archivos listos para commit..."
echo ""
echo "Archivos a agregar al repositorio:"
echo "  - $APK_DEST ($APK_SIZE)"
echo "  - $HTML_DEST"
echo ""

read -p "¿Deseas hacer commit y push ahora? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "5️⃣  Haciendo commit..."
    git add "$APK_DEST" "$HTML_DEST"
    git commit -m "Add native Android app APK and download page

- APK compilado: app-debug.apk ($APK_SIZE)
- Página de descarga: download-app.html
- Funciona con pantalla bloqueada
- GPS background tracking completo"
    
    echo ""
    echo "6️⃣  Haciendo push..."
    git push origin main
    
    echo ""
    echo -e "${GREEN}✅ ¡Listo! App subida al repositorio${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Esperar deploy en Render (~5 minutos)"
    echo "  2. Compartir URL con conductores:"
    echo "     https://soptraloc.onrender.com/static/download-app.html"
    echo "  3. Proporcionar soporte durante instalación"
    echo ""
else
    echo ""
    echo "Para hacer commit manualmente:"
    echo "  git add $APK_DEST $HTML_DEST"
    echo "  git commit -m \"Add native Android app for distribution\""
    echo "  git push origin main"
    echo ""
fi

echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Distribución preparada exitosamente${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "URL de descarga (después del deploy):"
echo "  https://soptraloc.onrender.com/static/download-app.html"
echo ""
