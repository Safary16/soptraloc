# SOPTRALOC — CHECKPOINT DE TRASPASO

Actualizado: 2026-07-18 20:54 America/Santiago
Estado: EN CURSO — abrir sesión nueva antes de continuar
Repo: `/home/openclaw/.openclaw/workspace/github-audit/soptraloc`
Rama: `improve/business-logic-consistency`
Modelo obligatorio para trabajo principal: `openai-canada/gpt-5.6-sol`
No usar subagentes por inestabilidad del proveedor.

## Estado remoto/publicado
- `origin/main`: `6417d23` (merge PR #78 del primer bloque).
- Último commit de la rama, ya subido: `02a5939` — `feat: add GPS arrival geofences and resilient Render startup`.
- La rama remota contiene `02a5939`.
- Segundo PR para `02a5939` aún no se confirmó/mergeó en este checkpoint.

## Ya publicado en `02a5939`
- Arribo manual con GPS obligatorio, hora real y origen `manual`.
- Arribo automático por geocerca configurable en CD; sin radio queda inactivo.
- Tracking periódico desde portal de conductor para alimentar ETA/geocerca.
- Idempotencia y restricción: conductor no opera viajes ajenos.
- Migraciones `cds/0003` y `programaciones/0006`.
- Render: `build.sh` ya no conecta DB; `start.sh` migra con retry; `render.yaml` enlaza `soptraloc-db`.
- Eliminada creación automática insegura del admin `admin/1234` desde build.
- Gates de ese bloque: 30/30 tests OK.

## Decisión Render/base nueva
El usuario considera borrar y recrear servicio/base. Recomendación:
- Solo borrar DB si no necesita datos existentes.
- Recrear como Blueprint usando `render.yaml` crea `soptraloc-db` y enlaza `DATABASE_URL` automáticamente.
- Las tablas se crean por migraciones en `start.sh`.
- El error anterior `could not translate host name dpg-...-a` era URL DB obsoleta/no resolvible, no fallo de dependencias.

## Trabajo ML NO comprometido (working tree)
Objetivo del usuario: aprendizaje real y creciente por horarios, rutas y conductores; no vender reglas como IA.

Implementado en working tree:
- `apps/core/services/learning_engine.py` (nuevo):
  - historial válido de `TiempoViaje`, últimos 120 días;
  - exclusión de anomalías;
  - ponderación por recencia, hora circular y día de semana;
  - ajuste por firma de ruta y conductor;
  - mezcla progresiva Mapbox/histórico (cold-start conservador);
  - perfil de conductor con mínimo 3 muestras;
  - comparación de rutas alternativas y ventanas horarias;
  - confianza, muestras, fuente y explicación.
- `apps/core/services/mapbox.py`: firma SHA-256 de geometría y alternativas Mapbox.
- `Programacion.ruta_firma`, `TiempoViaje.ruta_firma`, `Programacion.prediccion_ml`.
- Migraciones nuevas `programaciones/0007` y `0008`.
- Inicio de ruta usa recomendación híbrida, guarda geometría/firma/predicción auditable.
- Cierre de viaje guarda `ruta_firma` en `TiempoViaje`.
- Endpoint `GET /api/programaciones/{id}/recomendacion_ml/?lat=...&lng=...&ventana_horas=3`.
- Analytics de conductores expone `perfil_velocidad_ml`.
- Scoring de asignación incorpora ritmo aprendido solo con muestras suficientes.
- `apps/core/tests.py` nuevo: cold-start, ajuste histórico, perfiles, rutas/horarios, anomalías.

Verificación ML ejecutada:
- tests ML 4/4 OK;
- tests ML + arribo 9/9 OK;
- suite completa antes del último cambio auditable: 34/34 OK;
- `compileall`, Django check y makemigrations check: OK al momento del checkpoint.

## Trabajo credenciales/CRUD INCOMPLETO — no commitear todavía
Problemas detectados:
- Admin global no tiene bootstrap definido tras quitar `admin/1234`.
- Admin de conductores usaba contraseña fija insegura `driver123`.
- Importador de conductores crea `Driver` pero no necesariamente `User`.
- Pantalla Conductores depende de Admin para crear/editar; no es CRUD operativo real.
- No existe pantalla visible de gestión de CD; solo API/Admin.
- Usuario aclaró: NO borrar funciones/menús por impulso; definir correctamente datos maestros y sincronización frontend/backend.

Cambios parciales ya hechos:
- `apps/core/management/commands/ensure_admin.py` nuevo:
  - usa `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD`;
  - exige password >=12;
  - no imprime contraseña.
- `start.sh` llama `python manage.py ensure_admin` tras migrar.
- `apps/drivers/access.py` nuevo:
  - username normalizado;
  - contraseña temporal aleatoria;
  - `asegurar_acceso()` crea/reset User.
- `apps/drivers/admin.py` fue reescrito para usar `asegurar_acceso` y acción regenerar acceso.

IMPORTANTE: esta pieza de credenciales/CRUD NO tiene aún pruebas finales ni integración frontend/importador. No commitear hasta completarla.

## Próximos pasos exactos en sesión nueva
1. Leer este checkpoint y `git status`.
2. Añadir variables al Blueprint:
   - `DJANGO_SUPERUSER_USERNAME=admin`
   - `DJANGO_SUPERUSER_EMAIL` (valor razonable o sync:false)
   - `DJANGO_SUPERUSER_PASSWORD` con `sync: false`, para que Render la solicite como secreto.
3. Integrar `asegurar_acceso` en:
   - creación API/frontend de conductor;
   - importador Excel (devolver accesos temporales solo para nuevos);
   - acción de reset de acceso.
4. Crear CRUD visible de Conductores (modal/form en `drivers_list.html`) sin depender de Admin; editar/desactivar, no eliminar por defecto.
5. Crear pantalla CRUD visible de CD (`/cds/`): nombre, código, dirección, comuna, tipo, lat/lng, tiempos, drop&hook, geocerca, activo.
6. Añadir ruta/vista/template y navegación `Datos maestros` o accesos Conductores + CD. NO borrar otras pantallas todavía.
7. Corregir permisos API: `DriverViewSet.permission_classes=[]` actualmente es demasiado abierto; CRUD solo staff, tracking/my_info propio conductor. Mantener lecturas operativas necesarias.
8. Pruebas de acceso/admin/importador/CRUD.
9. Volver a ejecutar suite completa, check, migrations, compile, static, shell/yaml.
10. Commit y push del bloque ML + credenciales + CRUD solo cuando todo pase.

## Working tree esperado
Modificados:
- `apps/core/api_views.py`
- `apps/core/services/assignment.py`
- `apps/core/services/mapbox.py`
- `apps/drivers/admin.py`
- `apps/programaciones/models.py`
- `apps/programaciones/serializers.py`
- `apps/programaciones/views.py`
- `start.sh`

Nuevos:
- `apps/core/management/commands/ensure_admin.py`
- `apps/core/services/learning_engine.py`
- `apps/core/tests.py`
- `apps/drivers/access.py`
- `apps/programaciones/migrations/0007_programacion_ruta_firma_tiempoviaje_ruta_firma.py`
- `apps/programaciones/migrations/0008_programacion_prediccion_ml.py`

Local solamente, nunca commitear:
- `.testdeps/`

## Config OpenClaw
- principal/main: `openai-canada/gpt-5.6-sol`.
- heartbeat: `google/gemini-3.1-flash-lite`, aislado/light.
- dreaming: `google/gemini-3.1-flash-lite`.
- cron livianos: Gemini Flash Lite con fallbacks ligeros.
