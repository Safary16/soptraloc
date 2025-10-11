#!/usr/bin/env bash#!/usr/bin/env bash#!/usr/bin/env bash

# Build script automático para Render.com - SoptraLoc TMS

# Se ejecuta automáticamente en cada deploy# Script de build automático para Render# Build script optimizado para Render.com - SoptraLoc TMS v3.0



set -o errexit  # Exit en caso de error# Este script se ejecuta automáticamente en cada deploy# Deploy desde CERO



echo "=========================================================================="set -o errexit

echo "🚀 BUILD SOPTRALOC TMS - RENDER.COM"

echo "=========================================================================="set -o errexit  # Exit en caso de error

echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""echo "=========================================================================="



# 1. Actualizar pipecho "🔧 Instalando dependencias..."echo "🚀 BUILD SOPTRALOC TMS v3.0 - RENDER.COM"

echo "📦 Actualizando pip..."

pip install --upgrade pip setuptools wheelpip install -r requirements.txtecho "=========================================================================="



# 2. Instalar dependenciasecho "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"

echo "📦 Instalando dependencias..."

pip install -r requirements.txtecho "📦 Recolectando archivos estáticos..."echo ""



# 3. Verificar instalación de paquetes críticospython manage.py collectstatic --no-input

echo "🔍 Verificando instalación..."

python -c "import django; print(f'✅ Django {django.get_version()}')"# Actualizar pip

python -c "import psycopg2; print('✅ psycopg2 instalado')"

python -c "import rest_framework; print('✅ djangorestframework instalado')"echo "🗄️ Aplicando migraciones de base de datos..."echo "📦 Actualizando pip..."

python -c "import gunicorn; print('✅ gunicorn instalado')"

python manage.py migrate --no-inputpip install --upgrade pip setuptools wheel

# 4. Recolectar archivos estáticos

echo ""

echo "📁 Recolectando archivos estáticos..."

python manage.py collectstatic --no-inputecho "👤 Creando superusuario automáticamente..."# Instalar dependencias de producción



# 5. Aplicar migracionespython manage.py shell << ENDecho "📦 Instalando dependencias de producción..."

echo ""

echo "🗄️ Aplicando migraciones..."from django.contrib.auth import get_user_modelpip install -r requirements.txt

python manage.py migrate --no-input

User = get_user_model()

# 6. Crear superusuario automáticamente

echo ""if not User.objects.filter(username='admin').exists():# Verificar instalación de paquetes críticos

echo "👤 Creando superusuario admin/admin..."

python manage.py shell << END    User.objects.create_superuser('admin', 'admin@soptraloc.cl', 'admin')echo "🔍 Verificando paquetes críticos..."

from django.contrib.auth import get_user_model

User = get_user_model()    print('✅ Superusuario creado: admin/admin')python -c "import django; print(f'✅ Django {django.get_version()}')"

if not User.objects.filter(username='admin').exists():

    User.objects.create_superuser('admin', 'admin@soptraloc.cl', 'admin')else:python -c "import psycopg2; print('✅ psycopg2 instalado')"

    print('✅ Superusuario creado: admin/admin')

else:    print('ℹ️ Superusuario ya existe')python -c "import whitenoise; print('✅ whitenoise instalado')"

    print('ℹ️ Superusuario ya existe')

ENDENDpython -c "import gunicorn; print('✅ gunicorn instalado')"



# 7. Cargar datos de prueba solo si la BD está vacía

echo ""

echo "🔍 Verificando si cargar datos de prueba..."echo "📊 Cargando datos iniciales de prueba..."# Navegar al directorio del proyecto

python manage.py shell << END

from apps.containers.models import Containerpython manage.py shell << ENDcd soptraloc_system

if Container.objects.count() == 0:

    print('📦 Base de datos vacía, cargando datos de prueba...')from apps.cds.models import CD

    import os

    os.system('python manage.py cargar_datos_prueba')from apps.drivers.models import Driver# Crear directorio de logs si no existe

else:

    print('ℹ️ La base de datos ya tiene datos, omitiendo carga de prueba')from apps.containers.models import Containermkdir -p logs

END



echo ""

echo "=========================================================================="# Solo cargar datos si la base está vacíaecho "🗄️ Ejecutando migraciones..."

echo "✅ BUILD COMPLETADO EXITOSAMENTE"

echo "=========================================================================="if CD.objects.count() == 0:

echo "🌐 Admin: https://tu-app.onrender.com/admin/"

echo "📡 API: https://tu-app.onrender.com/api/"    print('🚀 Base de datos vacía, cargando datos de prueba...')# Aplicar migraciones de base de datos

echo "👤 Usuario: admin / Contraseña: admin"

echo "=========================================================================="    import osecho "🔄 Aplicando migraciones de base de datos..."


    os.system('python manage.py cargar_datos_prueba')python manage.py migrate --settings=config.settings_production --noinput

    print('✅ Datos de prueba cargados')

else:# Recopilar archivos estáticos con compresión

    print('ℹ️ Base de datos ya tiene datos, omitiendo carga inicial')echo "📁 Recopilando y comprimiendo archivos estáticos..."

ENDpython manage.py collectstatic --noinput --clear --settings=config.settings_production



echo "✅ Build completado exitosamente!"# Verificar archivos críticos

echo "🔍 Verificando archivos estáticos críticos..."
if [ -f "staticfiles/js/realtime-clock.js" ]; then
    echo "✅ realtime-clock.js encontrado"
else
    echo "⚠️  ADVERTENCIA: realtime-clock.js no encontrado"
fi

echo ""
echo "=========================================================================="
echo "✅ BUILD COMPLETADO EXITOSAMENTE"
echo "=========================================================================="

# Volver al directorio raíz para ejecutar post_deploy
cd ..

# Ejecutar post-deploy
echo ""
echo "=========================================================================="
echo "🚀 EJECUTANDO POST-DEPLOY"
echo "=========================================================================="

if [ -f "post_deploy.sh" ]; then
    bash post_deploy.sh
else
    echo "⚠️  WARNING: post_deploy.sh no encontrado"
fi

echo ""
echo "=========================================================================="
echo "✅ DEPLOY COMPLETO"
echo "=========================================================================="
echo "Sistema: SoptraLoc TMS v3.0"
echo "Features: Reloj ATC + ML Routing + Alertas"
echo "Apps: routing, containers, drivers, warehouses, core"
echo "Deploy: Desde CERO - Optimizado"
echo "=========================================================================="
