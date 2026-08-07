#!/usr/bin/env bash
# Arranque seguro en Render: espera PostgreSQL, migra y recién entonces sirve tráfico.
set -o errexit
set -o nounset
set -o pipefail

max_attempts="${DB_STARTUP_MAX_ATTEMPTS:-12}"
retry_seconds="${DB_STARTUP_RETRY_SECONDS:-5}"
attempt=1

while ! python manage.py migrate --no-input; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "ERROR: PostgreSQL no estuvo disponible después de ${max_attempts} intentos."
    echo "Verifica que DATABASE_URL use la Internal Database URL vigente de Render."
    exit 1
  fi
  echo "PostgreSQL aún no está disponible (intento ${attempt}/${max_attempts}); reintentando en ${retry_seconds}s..."
  attempt=$((attempt + 1))
  sleep "$retry_seconds"
done

python manage.py ensure_admin

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}"
