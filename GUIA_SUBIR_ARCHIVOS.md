📁 GUÍA: CÓMO SUBIR ARCHIVOS AL WORKSPACE
==========================================

🎯 MÉTODO 1: ARRASTRAR Y SOLTAR (RECOMENDADO)
============================================
1. Abre VS Code (ya lo tienes abierto)
2. En el panel izquierdo, ve al "Explorer" (icono de carpetas)
3. Arrastra tu archivo Excel desde tu computadora
4. Suéltalo en la carpeta del proyecto

📍 UBICACIONES RECOMENDADAS:
• /workspaces/soptraloc/ (raíz del proyecto)
• /workspaces/soptraloc/soptraloc_system/ (carpeta Django)

🎯 MÉTODO 2: MENÚ CONTEXTUAL VS CODE
===================================
1. Clic derecho en el Explorer (panel izquierdo)
2. Selecciona "Upload..." o "Subir..."
3. Busca tu archivo Excel
4. Confirma la subida

🎯 MÉTODO 3: COMANDO VS CODE
===========================
1. Presiona Ctrl+Shift+P (Paleta de comandos)
2. Escribe "Upload"
3. Selecciona "File: Upload..."
4. Selecciona tu archivo

🎯 MÉTODO 4: TERMINAL (AVANZADO)
===============================
Si tienes el archivo en otra ubicación del sistema:
```bash
# Copiar desde otra ubicación
cp /ruta/al/archivo.xlsx /workspaces/soptraloc/

# O crear un archivo desde URL (si está en cloud)
wget "URL_DEL_ARCHIVO" -O /workspaces/soptraloc/containers.xlsx
```

📊 FORMATOS SOPORTADOS PARA TU EXCEL:
====================================
✅ .xlsx (Excel 2007+)
✅ .xls (Excel 97-2003)  
✅ .csv (Valores separados por comas)
✅ .tsv (Valores separados por tabs)

🔍 VERIFICAR SUBIDA:
===================
Una vez subido, verifica que el archivo esté en:
• Panel Explorer de VS Code
• Terminal: ls -la /workspaces/soptraloc/

🚀 PROCESAMIENTO AUTOMÁTICO:
============================
Cuando subas tu Excel, el sistema puede:
✅ Detectar automáticamente columnas
✅ Mapear campos a la base de datos
✅ Importar contenedores programados
✅ Generar reportes y dashboard

💡 CONSEJO:
==========
Sube el archivo Excel a la raíz del proyecto:
/workspaces/soptraloc/tu_archivo.xlsx

¡Así será más fácil de procesar!