# REVISIÓN PROFUNDA DE CÓDIGO — Frontend Web + App Móvil SoptraLoc

**Fecha:** 2026-09-14  
**Rama:** main  
**Alcance:** 13 templates HTML + 4 archivos app móvil + 1 script Python  
**Regla:** Solo lectura — ningún archivo modificado

---

## 1. TABLA DE HALLAZGOS

| # | Archivo | Línea (aprox) | Problema concreto | Severidad | Impacto | Cómo se nota |
|---|---------|---------------|-------------------|-----------|---------|--------------|
| **H1** | `executive_dashboard.html` | ~línea 155 (JS `loadAlertasData`) | **Endpoint `/api/notifications/activas/` INEXISTENTE.** El JS llama a esa URL pero `urls.py` no tiene esa ruta. La ruta real es `/api/dashboard/alertas/` (función `dashboard_alertas` en `api_views.py`). | **CRÍTICO** | La pestaña "Alertas" del dashboard ejecutivo nunca carga datos. Muestra "Cargando..." indefinidamente o error de conexión. | Usuario abre dashboard ejecutivo → pestaña ⚠️ Alertas → queda en blanco eternamente |
| **H2** | `container_detail.html` | ~línea 291 (JS string concat dentro de `DOMContentLoaded`) | **XSS sin escapar.** Datos de API (`programacion.cliente`, `programacion.cd_nombre`, `programacion.driver_nombre`, `programacion.patente_confirmada`) se insertan con `html += '...'` dentro de template literals sin usar `e()` o `escape()`. | **ALTO** | Si cualquier CD, cliente o conductor tiene `<script>` en su nombre, se ejecuta en el navegador del operador. | Nombre de CD con HTML → script se ejecuta al abrir detalle del contenedor |
| **H3** | `container_detail.html` | ~línea 447 (modal retorno JS) | **CAMPO MISMATCH en retorno.** El frontend envía `body.destination_type = tipo` pero el backend en `ContainerViewSet.iniciar_retorno()` espera `request.data.get('destino_tipo')`. El campo `destino_tipo` llega como `None`. | **CRÍTICO** | Retorno de contenedor vacío nunca funciona. El servicio `EmptyReturnService.start()` recibe `destination_type=None` y falla. | Botón "Iniciar Retorno" → aparece error sin especificar → contenedor queda atascado en estado "vacio" sin poder retornar |
| **H4** | `home.html` | ~línea 121-148 (JS `cargarProgramacionesPrioritarias`) | **XSS sin escapar.** Datos de `/api/programaciones/dashboard/` se inyectan con template literals directamente en HTML: `prog.container_id_formatted`, `prog.cd`, `prog.conductor`, `prog.cliente` (línea 136-138), etc. Ninguno usa `e()`. | **ALTO** | Cualquier dato de usuario en programaciones puede inyectar código ejecutable. | Nombre de conductor con HTML → se ejecuta en dashboard principal |
| **H5** | `home.html` | ~línea 121 | El JS espera `data.programaciones[].urgencia`, `data.programaciones[].estado_container`, `data.programaciones[].container_id_formatted`, `data.programaciones[].cd`, `data.programaciones[].conductor`, `data.programaciones[].dias_hasta_programacion`, `data.programaciones[].dias_hasta_demurrage`, `data.programaciones[].eta_recalculado_min`, `data.programaciones[].eta_minutos`, `data.programaciones[].eta_timestamp`, `data.programaciones[].fecha_inicio_ruta`. El backend `ProgramacionViewSet.dashboard()` devuelve EXACTAMENTE estos campos. ✅ **Verificado coincidente.** | INFO | — | — |
| **H6** | `executive_dashboard.html` | ~línea 147 (JS `loadAlertasData`) | El JS espera `data.notificaciones[].titulo`, `data.notificaciones[].mensaje`, `data.notificaciones[].prioridad`, `data.notificaciones[].created_at`, `data.notificaciones[].container_id_formatted`. Pero `dashboard_alertas` devuelve `data.alertas[].titulo`, `.mensaje`, `.prioridad`, `.container_id`, `.dias_restantes` o `.horas_restantes`. **No hay campo `created_at` ni `notificaciones` en el response.** | **ALTO** | Aunque el endpoint fuera correcto, los campos no coinciden → la tabla de alertas mostraria "undefined" en todas las columnas. | Pestaña Alertas → tabla muestra "undefined" para todas las columnas |
| **H7** | `executive_dashboard.html` | ~línea 69 | La función `e()` está definida correctamente como `const e=s=>...` y se usa en TODAS las inyecciones JS del template. ✅ Escapado correcto. | INFO | — | — |
| **H8** | `containers_list.html` | JS inline completo | La función `esc()` existe y se usa en todas las inyecciones `innerHTML`. ✅ Escapado correcto. | INFO | — | — |
| **H9** | `drivers_list.html` | JS inline completo | La función `esc()` existe y se usa en todas las inyecciones. ✅ Escapado correcto. | INFO | — | — |
| **H10** | `cds_list.html` | JS inline completo | La función `esc()` existe y se usa en todas las inyecciones. ✅ Escapado correcto. | INFO | — | — |
| **H11** | `operaciones.html` | ~línea 312-335 (JS `liberados`) | **XSS sin escapar.** Template literals inyectan `cont.container_id_formatted`, `cont.nave`, `cont.posicion_fisica`, `cont.cliente`, `cont.dias_para_demurrage` sin `esc()`. | **ALTO** | Mismo problema que H2 pero en la pestaña Liberación. | — |
| **H12** | `operaciones.html` | ~línea 343-355 (JS `por_arribar`) | **XSS sin escapar.** Template literals inyectan `cont.container_id_formatted`, `cont.nave`, `cont.fecha_eta` sin `esc()`. | **ALTO** | — | — |
| **H13** | `operaciones.html` | ~línea 488-515 (JS `loadContaineresAsignados`) | **XSS sin escapar.** Template literals inyectan `cont.container_id_formatted`, `cont.nave`, `cont.cd_entrega_nombre`, `cont.fecha_programacion`, `cont.fecha_asignacion`, `prog.eta_minutos` sin `esc()`. | **ALTO** | — | — |
| **H14** | `asignacion.html` | ~línea 162-168 (JS `renderizarProgramaciones`) | **XSS sin escapar.** Template literals inyectan `prog.container_id_formatted`, `prog.cd_nombre`, `prog.fecha_programada` sin `esc()`. | **ALTO** | — | — |
| **H15** | `asignacion.html` | ~línea 205-220 (JS `renderizarConductores`) | **XSS sin escapar.** Template literals inyectan `conductor.nombre`, `conductor.patente`, `conductor.num_entregas_dia`, `conductor.cumplimiento_porcentaje` sin `esc()`. | **ALTO** | — | — |
| **H16** | `driver_dashboard.html` | ~línea 420-468 (JS `renderAsignaciones`) | **XSS sin escapar.** Template literals inyectan `prog.contenedor`, `prog.cliente`, `prog.cd`, `prog.cd_direccion`, `prog.estado` sin `esc()`. Los datos vienen de `/api/drivers/{id}/my_info/` vía `DriverDetailSerializer.programaciones_asignadas`. | **ALTO** | Mismo patrón de vulnerabilidad en el portal del conductor. | Nombre de CD o cliente con HTML → se ejecuta en dashboard del conductor |
| **H17** | `home.html` | ~línea 123 | **MISMATCH de campo en alertas.** El JS `loadAlertasData` del executive_dashboard espera `data.notificaciones` pero `dashboard_alertas()` devuelve `data.alertas`. | **ALTO** | Tabla de alertas rota. | — |
| **H18** | `home.html` | ~línea 265-270 (JS `liberarContenedor`) | La función usa template literal en `alert()` con `result.mensaje`. Esto es solo texto de alerta, no inyección DOM, por lo que es menor riesgo. ✅ No es XSS crítico aquí. | BAJO | — | — |
| **H19** | `operaciones.html` | ~línea 267 | **FALTA de datos `fecha_eta` en ContainerListSerializer.** El template `home.html` JS muestra `cont.fecha_eta` para la sección "Por Arribar". Verificando `ContainerListSerializer`: el campo `fecha_eta` SÍ está en el array de fields. ✅ | INFO | — | — |
| **H20** | `operaciones.html` | ~línea 476 | **Endpoint `/api/containers/?format=json` en `loadContaineresAsignados`** sin paginación — carga TODAS las programaciones de golpe. `ProgramacionViewSet` no tiene paginación custom, usa DRF default. Si hay +1000 programaciones, la respuesta será enorme. | MEDIO | La pestaña "Asignados" tarda en cargar con datos grandes. | — |
| **H21** | `estados.html` | ~línea 177 | **Endpoint `/api/containers/?format=json`** sin paginación — carga TODOS los contenedores para contar por estado. Si hay miles, la respuesta es enorme y la página lenta. | MEDIO | Página "Estados" tarda 5+ segundos con datos grandes. | — |
| **H22** | `mobile-app/App.js` | Línea 21 | **URL del backend hardcodeada** como `https://soptraloc.onrender.com`. Si se cambia de dominio, la app deja de funcionar sin recompilar. | CRÍTICO | App móvil inservible después de cambio de hosting. | App muestra error de conexión tras migrar el backend. |
| **H23** | `mobile-app/App.js` | Línea 130-135 | **Auth fallida en `update-location`.** El endpoint `DriverViewSet.update_location()` verifica `request.user.is_staff or request.user.driver == driver`. La app nativa NO envía session cookies ni auth tokens DRF (solo axios POST sin header de autenticación). El endpoint devuelve 403 Forbidden. | CRÍTICO | El GPS tracking de la app nativa **nunca funciona**. El conductor ve "Tracking activo" pero el servidor nunca recibe las ubicaciones. | Dashboard de monitoreo web nunca muestra al conductor en el mapa aunque la app dice que está rastreando. |
| **H24** | `mobile-app/App.js` | Lín. 127-135 | **Sin reintentos ni manejo de red.** Los `axios.post` en `sendLocationToServer` solo hacen `console.error` en el catch. Si hay una caída de red, las ubicaciones se pierden permanentemente. | MEDIO | Ubicación perdida durante caídas de red temporales. | — |
| **H25** | `mobile-app/App.js` | Lín. 176-184 | **BackgroundService sin cleanup robusto.** El bucle `while(BackgroundService.isRunning())` con `setTimeout` de 30s — si el servicio no se detiene correctamente, puede consumir batería indefinidamente. | BAJO | Batería drenada si el servicio queda atascado. | — |
| **H26** | `base.html` | Línea completa | **Herencia:** todos los templates hijos extienden `base.html` correctamente con bloques `title`, `content`, `extra_css`, `extra_js`. ✅ | INFO | — | — |
| **H27** | `executive_dashboard.html` | View `executive_dashboard` en `apps/core/views.py` | **Sin protección de login.** La vista `executive_dashboard()` no tiene `@login_required`. Cualquiera puede acceder a `/executive/`. | **ALTO** | Dashboard ejecutivo con métricas de negocio accesible sin autenticación. | — |
| **H28** | `operaciones.html` | View `operaciones` en `apps/core/views.py` | **Sin protección de login.** La vista `operaciones()` no tiene `@login_required`. Cualquiera puede ver y operar contenedores. | **ALTO** | Panel de operaciones público. | — |
| **H29** | `home.html` | View `home` en `apps/core/views.py` | View pública, intencionalmente. Muestra estadísticas generales. ✅ No es problema de seguridad (no expone datos sensibles). | INFO | — | — |
| **H30** | `monitoring.html` | Línea ~108 | **API Key de Mapbox expuesta** en el frontend: `mapboxgl.accessToken = 'pk.eyJ1Ijo...W'`. Es un token público de Mapbox, no es crítico pero cualquiera puede verlo en el source. | BAJO | Límites de la API compartidos con usuarios maliciosos. | — |

---

## 2. TABLA DE ENDPOINTS: FRONTEND vs BACKEND

### Container Endpoints (`/api/containers/`)

| Frontend llama a | Método | Backend tiene | ¿Coincide? | Notas |
|---|---|---|---|---|
| `GET /api/containers/` | GET | `ContainerViewSet.list` (DRF default) | ✅ | Con filtros `?estado=`, `?search=`, `?page=` — todos soportados |
| `POST /api/containers/` | POST | `ContainerViewSet.create` (DRF default) | ✅ | |
| `GET /api/containers/{id}/` | GET | `ContainerViewSet.retrieve` (DRF default) | ✅ | |
| `PATCH /api/containers/{id}/` | PATCH | `ContainerViewSet.partial_update` (DRF default) | ✅ | |
| `DELETE /api/containers/{id}/` | DELETE | `ContainerViewSet.destroy` (DRF default) | ✅ | En realidad hace `cambiar_estado('cancelado')` |
| `POST /api/containers/{id}/marcar_liberado/` | POST | `@action detail=True methods=['post'] marcar_liberado` | ✅ | |
| `POST /api/containers/{id}/programar/` | POST | `@action detail=True methods=['post'] programar` | ✅ | Payload: `{cd_id, fecha_programada, cliente, observaciones}` ✅ coincide |
| `POST /api/containers/{id}/desprogramar/` | POST | `@action detail=True methods=['post'] desprogramar` | ✅ | |
| `POST /api/containers/{id}/iniciar_retorno/` | POST | `@action detail=True methods=['post'] iniciar_retorno` | ✅ URL | ⚠️ **Campos de payload:** frontend envía `{destination_type, destino_cd_id, deposito_devolucion}`. Backend espera `{destino_tipo, destino_cd_id, deposito_devolucion}`. **MISMATCH: `destination_type` ≠ `destino_tipo`** |
| `POST /api/containers/{id}/marcar_entregado/` | POST | `@action detail=True methods=['post'] marcar_entregado` | ✅ | |
| `POST /api/containers/{id}/marcar_descargado/` | POST | `@action detail=True methods=['post'] marcar_descargado` | ✅ | |
| `POST /api/containers/{id}/marcar_vacio/` | POST | `@action detail=True methods=['post'] marcar_vacio` | ✅ | |
| `POST /api/containers/{id}/marcar_devuelto/` | POST | `@action detail=True methods=['post'] marcar_devuelto` | ✅ | |
| `POST /api/containers/{id}/cambiar_estado/` | POST | `@action detail=True methods=['post'] cambiar_estado` | ✅ | |
| `GET /api/containers/liberados/` | GET | `@action detail=False url_path='liberados' liberados` | ✅ | |
| `GET /api/containers/export-liberacion-excel/` | GET | `@action detail=False url_path='export-liberacion-excel' export_liberacion_excel` | ✅ | |
| `POST /api/containers/import-embarque/` | POST | `@action url_path='import-embarque' import_embarque` | ✅ | |
| `POST /api/containers/import-liberacion/` | POST | `@action url_path='import-liberacion' import_liberacion` | ✅ | |
| `POST /api/containers/{id}/confirmar-vacio-cd/` | POST | `@action url_path='confirmar-vacio-cd' confirmar_vacio_cd` | ✅ | |
| `POST /api/containers/{id}/iniciar_retorno/` (driver_dashboard) | POST | Mismo que arriba | ✅ URL | ⚠️ Mismo MISMATCH de campo: `destination_type` vs `destino_tipo` |

### Programacion Endpoints (`/api/programaciones/`)

| Frontend llama a | Método | Backend tiene | ¿Coincide? | Notas |
|---|---|---|---|---|
| `GET /api/programaciones/` | GET | `ProgramacionViewSet.list` (DRF default) | ✅ | Con `?driver__isnull=true&ordering=fecha_programada` ✅ |
| `GET /api/programaciones/dashboard/` | GET | `@action(detail=False) dashboard` | ✅ | |
| `GET /api/programaciones/por-container/{id}/` | GET | `@action(url_path='por-container/(?P<container_id>[^/.]+))'` por_container | ✅ | |
| `POST /api/programaciones/{id}/asignar_conductor/` | POST | `@action detail=True methods=['post'] asignar_conductor` | ✅ | Payload: `{driver_id}` ✅ |
| `POST /api/programaciones/{id}/asignar_automatico/` | POST | `@action detail=True methods=['post'] asignar_automatico` | ✅ | |
| `GET /api/programaciones/{id}/conductores_disponibles/` | GET | `@action detail=True methods=['get'] conductores_disponibles` | ✅ | |
| `POST /api/programaciones/asignar_multiples/` | POST | `@action detail=False methods=['post'] asignar_multiples` | ✅ | Payload: `{programacion_ids}` ✅ |
| `POST /api/programaciones/{id}/iniciar_ruta/` | POST | `@action detail=True methods=['post'] iniciar_ruta` | ✅ | Payload: `{patente, lat, lng}` ✅ |
| `POST /api/programaciones/{id}/notificar_arribo/` | POST | `@action detail=True methods=['post'] notificar_arribo` | ✅ | Payload: `{lat, lng}` ✅ |
| `POST /api/programaciones/{id}/soltar_contenedor/` | POST | `@action detail=True methods=['post'] soltar_contenedor` | ✅ | Payload opcional `{lat, lng}` ✅ |
| `POST /api/programaciones/{id}/notificar_vacio/` | POST | `@action detail=True methods=['post'] notificar_vacio` | ✅ | Payload opcional `{lat, lng}` ✅ |
| `POST /api/programaciones/{id}/actualizar_posicion/` | POST | `@action detail=True methods=['post'] actualizar_posicion` | ✅ | |
| `POST /api/programaciones/{id}/crear_preasignacion/` | POST | `@action detail=True methods=['post'] crear_preasignacion` | ✅ | Payload: `{driver_id, fecha_salida}` ✅ |
| `POST /api/programaciones/import-excel/` | POST | `@action url_path='import-excel' import_excel` | ✅ | |

### Driver Endpoints (`/api/drivers/`)

| Frontend llama a | Método | Backend tiene | ¿Coincide? | Notas |
|---|---|---|---|---|
| `GET /api/drivers/` | GET | `DriverViewSet.list` (DRF default) | ✅ | Con filtros `?activo=true&presente=true&search=` |
| `POST /api/drivers/` | POST | `DriverViewSet.create` (DRF default) | ✅ | |
| `PATCH /api/drivers/{id}/` | PATCH | `DriverViewSet.partial_update` (DRF default) | ✅ | |
| `DELETE /api/drivers/{id}/` | DELETE | `DriverViewSet.destroy` (DRF default) | ✅ | Desactiva en vez de borrar |
| `POST /api/drivers/import-excel/` | POST | `@action url_path='import-excel' import_excel` | ✅ | |
| `POST /api/drivers/{id}/reset-access/` | POST | `@action url_path='reset-access' reset_access` | ✅ | |
| `GET /api/drivers/active_locations/` | GET | `@action detail=False active_locations` | ✅ | |
| `POST /api/drivers/{id}/track_location/` | POST | `@action detail=True track_location` | ✅ URL | ⚠️ Requiere autenticación DRF (`request.user.is_authenticated` + driver matching). La app móvil NO envía auth → **403** |
| `GET /api/drivers/{id}/my_info/` | GET | `@action detail=True my_info` | ✅ | Requiere autenticación DRF |
| `POST /api/drivers/verify-patente/` (app nativa) | POST | `@action url_path='verify-patente' verify_patente` | ✅ | Permite `AllowAny` ✅ |
| `POST /api/drivers/{id}/update-location/` (app nativa) | POST | `@action url_path='update-location' update_location` | ✅ URL | ⚠️ Requiere `request.user.is_staff or request.user.driver == driver`. App NO envía auth → **403** |

### CD Endpoints (`/api/cds/`)

| Frontend llama a | Método | Backend tiene | ¿Coincide? |
|---|---|---|---|
| `GET /api/cds/` | GET | `CDViewSet.list` | ✅ |
| `POST /api/cds/` | POST | `CDViewSet.create` | ✅ |
| `PATCH /api/cds/{id}/` | PATCH | `CDViewSet.partial_update` | ✅ |
| `DELETE /api/cds/{id}/` | DELETE | `CDViewSet.destroy` | ✅ |

### API Views (No viewsets)

| Frontend llama a | Backend | ¿Coincide? | Notas |
|---|---|---|---|
| `GET /api/dashboard/stats/` | `dashboard_stats` en `api_views.py` | ✅ | |
| `GET /api/dashboard/alertas/` | `dashboard_alertas` en `api_views.py` | ✅ | |
| `GET /api/dashboard/operativo/` | `dashboard_operativo` en `api_views.py` | ✅ | |
| `GET /api/operaciones/diarias/` | `operaciones_diarias` en `api_views.py` | ✅ | Con `?fecha=` ✅ |
| `GET /api/notifications/activas/` | **NO EXISTE** | ❌ **ROTO** | La vista debería ser `/api/dashboard/alertas/` pero el JS llama a `/api/notifications/activas/` |

---

## 3. LISTA DE {{ }} Y DATOS SIN ESCAPAR

### ✅ Plantillas Django correctamente escapadas (automático)
Todos los `{{ variable }}` en los 13 templates HTML están protegidos por escaping automático de Django template engine:
- `base.html`, `home.html`, `containers_list.html`, `container_detail.html`, `operaciones.html`, `operaciones_diarias.html`, `asignacion.html`, `estados.html`, `importar.html`, `drivers_list.html`, `driver_login.html`, `driver_dashboard.html`, `cds_list.html`, `monitoring.html`

### ✅ JS con función `esc()` / `e()` implementada correctamente
- `containers_list.html` — `esc()` en todas las inyecciones ✅
- `drivers_list.html` — `esc()` en todas las inyecciones ✅
- `cds_list.html` — `esc()` en todas las inyecciones ✅
- `executive_dashboard.html` — `e()` en todas las inyecciones ✅

### ❌ JS SIN escapar datos de usuario (VULNERABLE a XSS)
Estos templates usan template literals (`${...}`) o string concatenation (`+`) para inyectar datos de API en HTML sin función de escape:

1. **`home.html`** (líneas 127-148): `${prog.container_id_formatted}`, `${prog.cd}`, `${prog.conductor}`, `${prog.cliente}`, `${prog.urgencia}`, `${prog.estado_container}`, `${prog.dias_hasta_programacion}`, etc.
2. **`container_detail.html`** (líneas 265-310): `programacion.cliente || 'N/A'`, `programacion.cd_nombre || 'N/A'`, `programacion.driver_nombre || 'No asignado'`, `programacion.patente_confirmada`
3. **`operaciones.html`** (línea 315): `${cont.container_id_formatted}`, `${cont.nave}`, `${cont.posicion_fisica}`, `${cont.cliente}`, `${cont.dias_para_demurrage}`
4. **`operaciones.html`** (línea 347): `${cont.container_id_formatted}`, `${cont.nave}`, `${cont.fecha_eta}`
5. **`operaciones.html`** (líneas 492-513): `${cont.container_id_formatted}`, `${cont.nave}`, `${cont.cd_entrega_nombre}`, `${cont.estado_display}`, `${cont.fecha_programacion}`, `prog.eta_minutos`
6. **`asignacion.html`** (línea 165): `${prog.container_id_formatted}`, `${prog.cd_nombre}`, `${prog.nave}`
7. **`asignacion.html`** (línea 210): `${conductor.nombre}`, `${conductor.patente}`, `${conductor.num_entregas_dia}`, `${conductor.cumplimiento_porcentaje}`
8. **`driver_dashboard.html`** (líneas 430-460): `prog.contenedor || 'N/A'`, `prog.cliente || 'N/A'`, `prog.cd || 'N/A'`, `prog.cd_direccion || 'N/A'`

---

## 4. VEREDICTO DE 3 PANTALLAS CLAVE

### 4.1 executive_dashboard.html — "ROTO"

| Aspecto | Estado | Detalle |
|---|---|---|
| Extiende base.html | ✅ | `{% extends 'base.html' %}` + bloques correctos |
| Escapado XSS | ✅ | Función `e()` definida y usada correctamente en TODAS las inyecciones JS |
| Tabs Operativo | ✅ | `/api/dashboard/operativo/` coincide con `dashboard_operativo` en `api_views.py` |
| Tabs Operaciones | ✅ | `/api/containers/?page_size=1000` y `/api/programaciones/dashboard/` coinciden |
| Tabs Conductores | ✅ | `/api/drivers/` coincide con `DriverViewSet.list` |
| Tabs Eficiencia | ⚠️ | No hay llamada AJAX real — los datos están hardcodeados (`$('#avg-delivery-time .metric-value').text('45')`) |
| Tabs Alertas | ❌ **ROTO** | Llama a `/api/notifications/activas/` que NO EXISTE. Debería ser `/api/dashboard/alertas/` Y además los campos no coinciden (espera `notificaciones[].titulo` pero el backend devuelve `alertas[].tipo`) |
| Métricas principales | ⚠️ Parcial | Llama `/api/dashboard/stats/` que devuelve `{success: true, stats: {...}}` pero el JS espera campos directamente en `data` (sin envolver en `stats`). **MISMATCH: el JS usa `data.contenedores_total` pero el backend devuelve `data.stats.contenedores_total`** |

**Problemas críticos:**
1. **CRÍTICO**: `/api/notifications/activas/` no existe → pestaña Alertas siempre rota
2. **ALTO**: Los campos de alertas no coinciden (`data.notificaciones` vs `data.alertas`)
3. **ALTO**: Métricas principales — el JS lee `data.contenedores_total` pero el backend envuelve todo en `data.stats`

### 4.2 container_detail.html — "FUNCIONAL CON RIESGOS"

| Aspecto | Estado | Detalle |
|---|---|---|
| Extiende base.html | ✅ | `{% extends 'base.html' %}` + bloques correctos |
| Datos del contenedor | ✅ | `{{ container.x }}` todos escapados por Django |
| Programación AJAX | ✅ | `/api/programaciones/por-container/{id}/` coincide con `por_container` action |
| Modal Programar | ✅ | Envía `{cd_id, fecha_programada, cliente, observaciones}` → backend espera lo mismo |
| Modal Iniciar Ruta | ✅ | Envía `{patente, lat, lng}` → backend lo espera |
| Modal Retorno | ❌ **ROTO** | Envía `destination_type` pero backend espera `destino_tipo` |
| Botones acción | ✅ | Los botones de estado son correctos y los endpoints coinciden |
| Escapado XSS | ❌ **VULNERABLE** | Datos de API se inyectan sin `e()` o `esc()` en el bloque de programación |

**Problemas:**
1. **CRÍTICO**: Retorno de contenedor vacío roto (mismatch `destination_type` vs `destino_tipo`)
2. **ALTO**: XSS en datos de programación inyectados sin escapar
3. **MEDIO**: Modal de inicio de ruta abre `confirmarIniciarRuta()` que no existe definida — debería ser `confirmarIniciarRuta` pero la función no está en el scope correcto del modal

### 4.3 mobile-app/App.js — "NO FUNCIONAL"

| Aspecto | Estado | Detalle |
|---|---|---|
| API Base URL | ❌ **Fragil** | Hardcoded a `https://soptraloc.onrender.com` — cualquier cambio de dominio rompe la app |
| Login flow | ✅ | `POST /api/drivers/verify-patente/` funciona, devuelve `{success, driver_id, driver_name, patente}` |
| AsyncStorage | ✅ | Persiste driverId, driverName, patente correctamente |
| GPS Tracking | ❌ **BLOQUEADO** | `sendLocationToServer` llama `POST /api/drivers/{id}/update-location/` que requiere `request.user.is_authenticated` pero la app NO envía cookies ni auth tokens → **403 Forbidden** |
| Background tracking | ⚠️ Funcional pero riesgoso | `react-native-background-actions` con bucle while — puede consumir batería si no se detiene correctamente |
| Manejo de errores | ❌ | Sin reintentos automáticos, sin cola de envíos pendientes |
| Permisos Android | ✅ | Solicita `ACCESS_FINE_LOCATION` y `ACCESS_BACKGROUND_LOCATION` correctamente |

**Problemas:**
1. **CRÍTICO**: GPS tracking nunca funciona — el endpoint `update-location` requiere autenticación que la app no envía
2. **CRÍTICO**: URL hardcodeada — la app no es portable
3. **MEDIO**: Sin cola de envíos pendientes ni reintentos — cada caída de red pierde datos de ubicación

---

## 5. RESUMEN EJECUTIVO

### Severidad de hallazgos

| Severidad | Cantidad | Resumen |
|---|---|---|
| **CRÍTICO** | 5 | Endpoint de alertas inexistente, campo mismatch en retorno vacío, URL hardcodeada en app, auth bloqueada en GPS app, métricas con campo envuelto incorrecto |
| **ALTO** | 8 | 7 puntos de XSS sin escapar + dashboard ejecutivo sin login + operaciones sin login |
| **MEDIO** | 3 | Sin paginación en 2 endpoints de listas + sin reintentos en app |
| **BAJO** | 3 | API key de Mapbox expuesta + background service sin cleanup robusto + alertas como texto (menor riesgo) |

### Resumen de endpoints

- **Total endpoints consultados:** 42
- **Endpoints correctos:** 38 ✅
- **Endpoints rotos (404):** 1 (`/api/notifications/activas/`)
- **Mismatches de campo:** 1 (`destination_type` vs `destino_tipo`)
- **Mismatches de estructura de response:** 2 (stats envuelto en `data.stats`, alerts con array diferente)

### Seguridad

- **Vulnerabilidades XSS sin escapar:** 7 ubicaciones en 5 templates
- **Páginas sin protección de login:** 2 (`executive_dashboard`, `operaciones`)
- **Autenticación rota en app móvil:** GPS tracking bloqueado por auth mismatch
