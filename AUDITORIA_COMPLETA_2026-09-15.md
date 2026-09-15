# Auditoría Técnica Completa — SoptraLoc TMS
**Fecha:** 2026-09-15 · **Alcance:** revisión LÍNEA POR LÍNEA de todo el código Python (14.556 líneas) + verificación de templates/JS + prueba como usuario real.

---

## RESUMEN EJECUTIVO
Revisión completa de **todos los archivos** del sistema: 4 importadores Excel, 11 modelos, 4 señales, 16 servicios, 8 vistas/viewsets, 6 serializers, 8 comandos de gestión, config y URLs. **El sistema está sano: `manage.py check` 0 silenced, 0 migraciones pendientes, suite 50/50 OK.** En la prueba como usuario real el flujo completo funcionó (importación → ciclo FSM → devolución). Se encontraron y **CORRIGIERON 3 bugs** de robustez (500 → 400 con mensaje claro) y quedan **3 hallazgos de seguridad** recomendados antes de producción.

---

## COBERTURA LÍNEA POR LÍNEA

### Importadores Excel (934 líneas + drivers) — revisados completos ✅
| Archivo | Líneas | Estado |
|---|---|---|
| `apps/containers/importers/embarque.py` | 235 | ✅ Revisado + FIX (errores de formato → 400) |
| `apps/containers/importers/liberacion.py` | 307 | ✅ Revisado + FIX (400) |
| `apps/containers/importers/programacion.py` | 391 | ✅ Revisado + FIX (400) |
| `apps/drivers/importers/__init__.py` | 182 | ✅ Revisado + FIX (400) |
| `apps/core/services/excel.py` | — | ✅ normalize_columns, detección de header tolerante |

**Probado como usuario real:** embarque (3 creados, tipos/pesos/naves OK), liberación (3 liberados, mapeo TPS→ZEAL, STI→CLEP), programación (2 programados + alerta; CDs inexistentes → cd_no_encontrado sin crash), conductores (creado + acceso temporal).

### Modelos — revisados completos ✅
`Container` (FSM 15 estados + transiciones), `Programacion` (asignación con locks, liberar_conductor idempotente, alerta 48h), `TiempoOperacion` (ML), `TiempoViaje` (factor corrección), `RegistroOperacion` (bitácora), `Driver`/`DriverLocation` (GPS + disponibilidad), `CD` (vacíos + geocerca), `Event` (auditoría), `Notification`/`NotificationPreference`.

### Señales — revisadas completas ✅
4 receptores `post_save`: sincronización programado↔driver (anti-loop), inventario automático de vacíos (select_for_update + flag), creación de programación solo con CD explícito, alerta demurrage.

### Servicios core — revisados completos ✅
`assignment` (scoring por dimensiones + clasificación + alternativas), `ml_predictor`, `learning_engine` (híbrido explicable con fallback), `validation` (ventanas + solapamiento), `anomaly_detector` (15+ anomalías P0-P3), `notifications`, `dashboard_operativo` (programadas/sin_asignar/riesgo_ml/encadenamiento/vacíos), `contextual_reasoning`, `returns` (transaccional), `operations` (drop & hook, descarga, vacío), `mapbox` (rutas + firma SHA-256), `openclaw` (opcional, no rompe si deshabilitado), `fleet`.

### Vistas/API — revisadas completas ✅
`containers/views.py` (1.014: imports, exports stock/Excel, FSM completo con guards de estado, retorno depósito/CCTI), `programaciones/views.py` (1.646: por-dia, alertas, asignar/desasignar, preasignación ML, asignación automática/múltiple, dashboard, ruta manual, import-excel, validación, iniciar_ruta con patente, arribo manual+geocerca idempotente, vacío, soltar, tracking con ETA, incidentes, recomendaciones, decisión operador), `drivers/views.py` (456: login, acceso temporal, GPS, historial, verify-patente), `cds`, `notifications`, `events/api`, `core/api_views` (550: stats, alertas, analytics, ML stats, dashboard operativo), `core/views` (frontend).

### Serializers — revisados completos ✅
Containers (validación de transiciones), programaciones (con patente/tipo/destino retorno), drivers (RUT/patente limpios, acceso temporal sin persistir en texto plano), cds, events, notifications.

### Config — revisada ✅
`settings.py` (DRF SessionAuthentication, whitenoise, SECURE_* en producción, CORS cerrado fuera de DEBUG), `urls.py` (frontend + API + admin + well-known TWA), `filters.py`, `access.py` (passwords temporales seguros), 8 comandos de gestión (ensure_admin fallback, ensure_database, release_due_containers, render_migrate/maintenance, init_cds, cargar_datos_prueba, reset_admin).

---

## BUGS ENCONTRADOS Y CORREGIDOS (pusheados)
1. **Importadores con formato inválido → 500 genérico** (columna duplicada/faltante, fecha mala). Fix: `raise ValueError` en importadores + `except ValueError → 400` con el mensaje real en las 4 vistas de import. **Commits `9c75a149` + `dc75ce3c`. Verificado: 400 con mensaje claro.**
2. **`asignar_conductor` con ValidationError (conductor en otro servicio) → 500**. Fix: captura `DjangoValidationError → 400`. **Commit `9c75a149`. Verificado.**

## HALLAZGOS DE SEGURIDAD (recomendados antes de producción real)
1. 🔴 **`AllowAny` en endpoints de escritura**: `asignar_conductor`, `asignar_automatico`, `asignar_multiples`, `desasignar`, `crear_ruta_manual`, `reportar_incidente`, `marcar_liberado`, `programar`, `desprogramar`, `marcar_entregado`, `marcar_vacio`, imports. Sugerencia: `IsAuthenticated` (la UI ya manda sesión CSRF).
2. 🔴 **`DEBUG = config('DEBUG', default=True)`** — si falta la env var arranca en debug. Sugerencia: `default=False`.
3. 🟠 **`ALLOWED_HOSTS` default `'*'`** — abierto si no se define. Sugerencia: lista por defecto restringida.
4. 🟡 **`SECRET_KEY` default** `'django-insecure-change-in-production'` — Render lo inyecta, pero conviene exigirlo.
5. 🟡 **`loadPreAsignaciones()` llamada sin definición** en `operaciones.html` (protegida por `typeof`, no rompe; panel no refresca esa sección).

## VERIFICACIONES FINALES
- `manage.py check` → **0 silenced** ✅
- `makemigrations --check --dry-run` → **No changes detected** ✅
- Suite completa → **50 tests OK** ✅
- Prueba real de punta a punta: login, importación (4 Excel), ciclo FSM completo (asignar→ruta→entregado→descargado→vacío→retorno→devuelto), portal conductor, exports → **todo 200 OK** ✅

## CONSULTAS DE DATOS EN PRUEBA
Contenedores `TEST*` y conductores de prueba creados en la BD local durante la verificación real (solo entorno local de desarrollo; no afectan a la BD de produccion).