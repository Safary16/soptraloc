#!/usr/bin/env bash
# Fase 3 soptraloc: sembrar catálogo + mundo simulado en prod.
# Ejecutar EN EL CONTENEDOR de Render (Dashboard -> Shell) o con DATABASE_URL en entorno.
#
# Reglas (NO matar nada):
#   - Idempotente: primero limpia SOLO los contenedores SIM- (marcador sintético),
#     después regenera. Correr 2 veces = mismo resultado, sin UNIQUE constraint.
#   - Aborta ante cualquier fallo (set -euo pipefail); no reintenta a ciegas.
#   - Los contenedores reales (sin marcador SIM-) NUNCA se tocan.
set -euo pipefail

echo ">>> PASO 0: limpiar mundo simulado previo (solo SIM-, aditivo al resto)"
python manage.py simular_operaciones --limpiar

echo ">>> PASO 1: init_cds (catálogo ficticio idempotente)"
python manage.py init_cds

echo ">>> PASO 2: simular_operaciones 40/60/42 (contenedores ficticios SIM-)"
python manage.py simular_operaciones --contenedores 40 --dias 60 --seed 42

echo ">>> FASE 3 COMPLETA — validar con: curl -s \$PUBLIC_URL/api/cds/ y /api/containers/?page_size=50"