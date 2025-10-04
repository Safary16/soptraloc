#!/usr/bin/env bash
# Script de despliegue automatizado para Render.com
# Ejecuta verificaciones locales, aplica migraciones pendientes y empuja cambios.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${ROOT_DIR}/soptraloc_system"
PYTHON_BIN=${PYTHON_BIN:-python}
PIP_BIN=${PIP_BIN:-pip}
DJANGO_SETTINGS=${DJANGO_SETTINGS:-config.settings}

step() {
  echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "➡️  $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

cd "${ROOT_DIR}"

step "Instalando/actualizando dependencias"
${PIP_BIN} install --upgrade pip setuptools wheel
${PIP_BIN} install -r requirements.txt

step "Verificando migraciones pendientes"
cd "${PROJECT_DIR}"
${PYTHON_BIN} manage.py makemigrations --check --dry-run

step "Ejecutando pruebas unitarias principales"
${PYTHON_BIN} manage.py test apps.drivers.tests.test_time_learning apps.containers.tests.test_excel_importers

step "Chequeo de integridad del proyecto"
${PYTHON_BIN} manage.py check --deploy --settings=config.settings_production

step "Aplicando migraciones en entorno local"
${PYTHON_BIN} manage.py migrate --settings=${DJANGO_SETTINGS}

step "Recolección de estáticos (modo local)"
${PYTHON_BIN} manage.py collectstatic --noinput --settings=${DJANGO_SETTINGS}

cd "${ROOT_DIR}"

if git status --short | grep -q "^"; then
  echo "\n⚠️  Existen cambios sin commitear. Aborta el deploy o confirma que estén listos."
  exit 1
fi

DEFAULT_RENDER_REMOTE="render"
RENDER_REMOTE_NAME=${RENDER_REMOTE_NAME:-$DEFAULT_RENDER_REMOTE}

if git remote get-url origin >/dev/null 2>&1; then
  step "Empujando a origin"
  git push origin main
else
  echo "\nℹ️  No se encontró remoto 'origin'. Omite push automático a origin."
fi

if ! git remote get-url "$RENDER_REMOTE_NAME" >/dev/null 2>&1; then
  if [ -n "${RENDER_REMOTE_URL:-}" ]; then
    step "Configurando remoto $RENDER_REMOTE_NAME"
    git remote add "$RENDER_REMOTE_NAME" "$RENDER_REMOTE_URL"
  else
    echo "\nℹ️  No se configuró un remoto llamado '$RENDER_REMOTE_NAME'."
    echo "   Define la variable de entorno RENDER_REMOTE_URL o ejecuta:"
    echo "   git remote add $RENDER_REMOTE_NAME <url-del-repo-render>"
  fi
fi

if git remote get-url "$RENDER_REMOTE_NAME" >/dev/null 2>&1; then
  step "Empujando a Render ($RENDER_REMOTE_NAME)"
  git push "$RENDER_REMOTE_NAME" main
else
  echo "\nℹ️  Push a Render omitido: remoto '$RENDER_REMOTE_NAME' no disponible."
fi

step "Despliegue local completado. Render iniciará el build automáticamente."
