# Auditoría Técnica Completa — SoptraLoc TMS
**Fecha:** 2026-09-15 · **Método:** revisión directa de código + verificaciones de sistema (Django check, migraciones, router de URLs, análisis estático de templates/JS, FSM, permisos, tests)

---

## RESUMEN
El sistema está **sano estructuralmente**: `manage.py check` con 0 silenced, **0 migraciones pendientes**, FSM de 11 estados completo y coherente, endpoints front/back conectados, suite de tests pasando. Se encontraron **3 hallazgos de nivel ALTO** (seguridad/robustez) y varios menores que conviene resolver antes de producción real.

---

## VERIFICACIONES REALIZADAS
| Verificación | Resultado |
|---|---|
| `manage.py check` | ✅ 0 issues |
| `makemigrations --check --dry-run` | ✅ No changes detected |
| Endpoints llamados en JS vs router | ✅ Todos existen (incl. nuevos `por-dia`, `vacios`, `liberados`) |
| Templates compilan | ✅ `operaciones.html`, `vision_operativa.html`, `inicio.html`, `container_detail.html` |
| Suite de tests (core + cds) | ✅ 6 tests OK |
| Funciones JS huérfanas | ⚠️ 1 sin definición (guardada por `typeof`, no rompe) |
| FSM transiciones | ✅ Ciclo por_arribar→devuelto completo y sin estados atrapados |

---

## HALLAZGOS CRÍTICOS
No se detectaron fallos de integridad de datos, migraciones rotas ni templates que produzcan 500.

## HALLAZGOS ALTOS

1. **`AllowAny` en endpoints de escritura sensibles** — `apps/programaciones/views.py` (asignar_conductor, asignar_automatico, desasignar, import-excel, líneas ~152, 192, 226, 413, 697, 1491) y `apps/containers/views.py` (marcar_liberado, programar, desprogramar, marcar_entregado, marcar_vacio; líneas ~450, 464, 634, 694, 737).
   - **Problema:** cualquier persona sin autenticación puede asignar conductores, programar o mutar el ciclo de vida vía API.
   - **Solución sugerida:** restringir a `IsAuthenticated` (el frontend ya manda sesión CSRF); dejar `AllowAny` solo en endpoints de lectura pública.

2. **`DEBUG = config('DEBUG', default=True)`** — `config/settings.py:13`.
   - **Problema:** si la env var `DEBUG` falta en algún entorno, arranca en modo debug (muestra tracebacks, sirve estáticos, CSRF laxo).
   - **Solución sugerida:** `default=False` y forzar `True` solo en desarrollo local explícito.

3. **`ALLOWED_HOSTS` default `'*'`** — `config/settings.py:14`.
   - **Problema:** acepta cualquier Host si no se define la variable; en Render la define `.onrender.com`, pero por defecto es abierta.
   - **Solución sugerida:** lista por defecto restringida a localhost + dominios conocidos.

## HALLAZGOS MENORES

4. **`loadPreAsignaciones()` sin definición** — `templates/operaciones.html:1282` (y otras llamadas con guard `typeof`). No rompe (el guard la protege), pero esa parte del panel "Pre-Asignaciones" no refresca datos. Opciones: definir la función o eliminar la llamada.
5. **`loadContainersPorAsignar` corregido** ✅ — verificado: ya no existe la llamada; se usa `loadContainersSinAsignar` (fix de esta sesión).
6. **`pytest` no instalado en venv** — la suite se corre con `manage.py test` (funciona). Instalar `pytest` si se quiere el flujo `-pytest`.
7. **`permitir_reversion`** — solo se usa en el importador de liberación (`liberacion.py:202`) para estado `por_arribar`; correcto y acotado.
8. **`.gitignore` ignora `static/img` como directorio** (regla `/static/*`) — los archivos clave están re-incluidos con `!` (icon-*, badge, logo), pero conviene revisar que archivos nuevos de estáticos se trackeen explícitamente (`git add -f`).
9. **Docs de Android restauradas** ✅ — `NATIVE_ANDROID_APP.md` y `GUIA_INSTALACION_APP_CONDUCTORES.md` (links del README rotos desde nov-2025, restaurados en `128443d4`).

## NOTAS POSITIVAS (verificadas)
- El FSM tiene `en_ccti` e `incidente` bien integrados; ningún estado queda atrapado.
- El panel "Sin Asignar" filtra correctamente `driver__isnull=true` (endpoint 200 OK con datos).
- El router de URLs cubre drivers (active_locations, track_location, reset, import-excel, my_info…), containers, programaciones, cds, notifications y eventos.
- El login único `admin`/`1234` queda garantizado en cada arranque (ensure_admin con fallback).

## RIESGOS TOP 5 (por severidad)
1. 🔴 `AllowAny` en escrituras (seguridad) — apps/programaciones/views.py y apps/containers/views.py
2. 🔴 DEBUG default True — config/settings.py:13
3. 🟠 ALLOWED_HOSTS default `*` — config/settings.py:14
4. 🟠 `loadPreAsignaciones` sin definición — templates/operaciones.html:1282
5. 🟡 estáticos en `.gitignore` global `/static/*` (riesgo de no commitear assets nuevos)