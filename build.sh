#!/usr/bin/env bash
# Build script para Render.com - SoptraLoc TMS
set -o errexit

echo "=========================================="
echo "🚀 SOPTRALOC TMS - BUILD"
echo "=========================================="

# 1. Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 3. Colectar archivos estáticos
echo " Colectando archivos estáticos..."
python manage.py collectstatic --no-input

# Render puede conservar el start command histórico (gunicorn directo) aunque
# render.yaml cambie. Ejecutar migraciones también en build mantiene el esquema
# alineado; `migrate` es idempotente si start.sh vuelve a ejecutarlo.
echo "🔄 Aplicando migraciones..."
max_attempts="${DB_BUILD_MAX_ATTEMPTS:-12}"
retry_seconds="${DB_BUILD_RETRY_SECONDS:-5}"
attempt=1
while ! python manage.py migrate --no-input; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "ERROR: no fue posible migrar PostgreSQL tras ${max_attempts} intentos."
    exit 1
  fi
  echo "PostgreSQL no disponible (intento ${attempt}/${max_attempts}); reintentando en ${retry_seconds}s..."
  attempt=$((attempt + 1))
  sleep "$retry_seconds"
done

echo "=========================================="
echo "✅ Build completado exitosamente"
echo "=========================================="
