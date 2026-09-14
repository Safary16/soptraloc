# Revisión Profunda de Código — Core / Servicios — SoptraLoc

**Fecha:** 2026-09-14  
**Brama:** main  
**Alcance:** 15 archivos del dominio core (services + api + views + config)

---

## Tabla de Hallazgos

### CRÍTICO

| # | Archivo | Línea | Problema | Impacto |
|---|---------|-------|----------|---------|
| C1 | `config/settings.py:14` | `SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')` | Key secreta con valor de producción por defecto ("django-insecure...") es la key canónica de Django. Cualquiera que sepa este valor puede forjar sesiones JWT/firmar cookies CSRF de cualquier usuario. | **Ruptura total de autenticación.** Si este valor llega a algún repo público, log o reporte de error, un atacante asume cualquier rol de administrador. |
| C2 | `config/settings.py:108` | `'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny']` | Todos los endpoints REST (analytics, ML stats, stats, operativos) están expuestos sin autenticación en producción, a pesar de que los view functions individuales tienen `@permission_classes([IsAuthenticatedOrReadOnly])` — que para `AllowAny` no agrega nada. | Los datos sensibles del sistema (perfiles de conductores, ETAs, historiales de rendimiento) son accesibles públicamente. |
| C3 | `learning_engine.py:67` | `learned_weight = min(0.78, samples / 18)` | `learned_factor` puede ser NaN si `relevant` está vacío (se devuelve 1.0 en `_weighted_factor`), pero cuando `samples == 0`, `learned_weight = 0` y `blended_factor = (1-0) + 0 * 1.0 = 1.0` — esto funciona por suerte, **PERO** si por algún bug un row tiene `calcular_factor_correccion()` retornando NaN, el factor se propaga. No hay validación. | En un caso extremo (DB corrupta o dato anómalo), todas las prediccionesML devuelven NaN y el sistema queda ciego. |
| C4 | `anomaly_detector.py:143` | `if driver and driver.max_entregas_dia is not None and driver.num_entregas_dia is not None and driver.max_entregas_dia - driver.num_entregas_dia <= 0:` | `max_entregas_dia - num_entregas_dia` hace una comparación de tipos mixtos. Si `num_entregas_dia` es `None` (nulo en DB), la resta produce `TypeError`. El check `is not None` debería protegerlo, pero es una expresión única: si `max_entregas_dia` existe y `num_entregas_dia` es None en la DB aunque el `is not None` dice que no, el `and` cortocircuita correctamente. **Verificado: el cortocircuito protege.** → Este es FALSO POSITIVO, pero merece `# noqa` o refactor a claridad. | **No aplica.** El cortocircuito de Python protege correctamente. Marcar como INFO. |

### ALTO

| # | Archivo | Línea | Problema | Impacto |
|---|---------|-------|----------|---------|
| A1 | `settings.py:11` | `CSRF_TRUSTED_ORIGINS = ["https://*.github.dev", "https://localhost:8000"]` | Faltan los orígenes de producción (Render, dominio real). Si se despliega en Render sin agregar el hostname aquí, los formularios POST recibirán 403 CSRF. | **Formularios del frontend no funcionan en producción.** El usuario ve "Bad Request" en operaciones, asignación, login. |
| A2 | `dashboard_operativo.py:118-135` | `riesgo_ml()` → `_perfil_conductor()` puede devolver `None` y luego se accede `perfil['factor_ml']` | Cuando `driver` es `None`, `_perfil_conductor()` devuelve `None`. En `riesgo_ml()`, se filtra `driver__isnull=False`, pero en `riesgo_encadenamiento()` la línea 304 llama `_programacion_item(prog_b)` que hace `prog.driver.nombre` — el `select_related` protege pero si `driver` se resuelve como NULL por alguna razón de ORM, se lanza `AttributeError`. | **500 en el endpoint del dashboard** cuando una programación tiene driver=null en `riesgo_encadenamiento`. |
| A3 | `dashboard_operativo.py:213-214` | `_programacion_item()` → `'eta_minutos': prog.eta_minutos` | `eta_minutos` puede ser `None`. El frontend JS espera un número. Si el template/JS no maneja `null`, puede romper cálculos visuales (barras de progreso, colores de prioridad). | **Datos rotos en UI** para programaciones sin ETA calculado. |
| A4 | `anomaly_detector.py:112-114` | `if programacion.container.peso_total_tons > 28:` | Comparación directa sin verificar si `peso_total_tons` es `None`. Si el contenedor no tiene peso registrado, se lanza `TypeError: '>' not supported between 'NoneType' and 'int'`. | **Crash del detector de anomalías** → el endpoint de dashboard operativo lanza 500. |
| A5 | `mapbox.py:28` | `return {"success": False, "error": "MAPBOX_API_KEY no configurado"}` — sin fallback | Cuando no hay token, `calculate_ruta` y `calculate_rutas_alternativas` retornan error. En `dashboard_operativo.py` el `riesgo_encadenamiento()` captura la excepción en `_tiempo_viaje_min` y cae en haversine, pero `learning_engine.py:126` en `recommend()` asume que si `mapbox.get('success')` es False, el fallback `calcular_ruta` funciona — si también falla (sin token), se retorna `{'success': False}` y el frontend JS recibe un error no mapeado. | **Recomendaciones de ruta completamente rotas** cuando no hay API key. |
| A6 | `assignment.py:234` | `programacion.save(update_fields=['driver', 'score_por_dimension', ...])` | Se asigna `programacion.driver` pero no se llama `programacion.asignar_conductor(driver, usuario)` — el método del modelo que además actualiza `num_entregas_dia` con F(), crea eventos, notificaciones y cambia el estado del contenedor. Aquí se hace `programacion.driver = mejor['driver']` directamente en vez de llamar al método seguro. | **`num_entregas_dia` NO se incrementa**, el estado del contenedor no se actualiza, no se crean eventos ni notificaciones. La programación queda "asignada" en memoria pero inconsistente con el estado real. |
| A7 | `assignment.py:184-186` | `similar_boost = (sum(c.similarity for c in similar_cases) / len(similar_cases)) if similar_cases else 0.0` | Esta línea funciona bien. **Verificación:** `similar_cases` es una lista de `SimilarCase` (dataclass) retornada por `ContextualReasoningService.similar_cases`. No hay problema. → **FALSO POSITIVO.** | No aplica. |
| A8 | `ml_predictor.py:128` | `tiempo_viaje = 60` si no hay coordenadas disponibles | El código usa `if 'origen_coords' in locals()` para verificar si se definió la variable — esto es **fragilísimo**. Si por algún path el `locals()` no contiene la variable (aunque el `elif` anterior la define), el código salta el cálculo de ML. | **ETA se queda en 60 min** (default) para viajes desde CCTI sin GPS del conductor, cuando debería hacer un cálculo real. |
| A9 | `validation.py:90` | `tiempo_viaje = 45` — estimación genérica por defecto en `validar_disponibilidad_temporal` | Cuando Mapbox falla o no hay GPS, se asume 45 minutos de viaje. Sin embargo, el tiempo de descarga se usa del CD (puede ser 120+ min) y Drop&Hook usa +15. Esto puede sobreestimar o subestimar drásticamente ventanas de conflicto. | **Falsos positivos o negativos de solapamiento de disponibilidad.** Un conductor puede asignarse a una tarea cuando en realidad está sobrecargado. |

### MEDIO

| # | Archivo | Línea | Problema | Impacto |
|---|---------|-------|----------|---------|
| M1 | `learning_engine.py:45-53` | `_history()` usa `select_related('conductor')` pero luego itera sobre 120 días de `TiempoViaje` sin paginación | `TiempoViaje.objects.filter(...).select_related(...)` puede retornar miles de filas de golpe. Sin `.defer()` en campos innecesarios ni paginación. | **Slow query / timeout** en instancias con >10K viajes históricos. La carga en memoria de 120 días de datos puede consumir 50-200MB RAM. |
| M2 | `learning_engine.py:67` | `learned_weight = min(0.78, samples / 18)` — la curva de aprendizaje | Con 18+ samples, el factor aprendido domina al 78%. Con 0 samples, domina al 0% (Mapbox puro). El punto de inflexión es 18 samples. Esta elección es arbitraria y no está documentada. | No es un bug, pero **el sistema puede ser sobreconfiado** con pocos datos (78% learned con solo 18 viajes) o subconfiado con muchos. |
| M3 | `dashboard_operativo.py:251-265` | `riesgo_encadenamiento()` → `_tiempo_viaje_min()` llama Mapbox dentro del bucle sin caché | Para N programaciones en riesgo, se hacen N llamadas HTTP a Mapbox dentro de un bucle `for`. Cada una con timeout=10s. | **Latencia de dashboard > 30 seg** en escenarios con 5+ programaciones encadenadas. Sin caché ni pool de conexiones. |
| M4 | `dashboard_operativo.py:304-306` | `deficit = (llegada_estimada - prog_b.fecha_programada).total_seconds() / 60` | Si `llegada_estimada` es un `datetime` naive y `fecha_programada` es timezone-aware (o viceversa), Python 3 lanza `TypeError: cannot compare naive and aware datetimes`. | **Crash en `riesgo_encadenamiento()`** si hay mezclas de timezone-aware/naive en los datos de prueba. |
| M5 | `anomaly_detector.py:112` | `if programacion.container.peso_total_tons > 28:` | Ya documentado como ALTO (A4). Aquí también: la comparación no verifica `None`. | Duplicate reference. |
| M6 | `operations.py:26` | `actual = max(1, int((finished_at - started_at).total_seconds() / 60))` | Si `started_at` es posterior a `finished_at` (reloj incorrecto o error humano), `total_seconds()` es negativo y `int()` truncado da 0, luego `max(1, 0)` = 1. | El sistema registra 1 minuto como tiempo de descarga real cuando en realidad fue retroceso. El ML aprende un factor de corrección de 1/estimated (ej: 1/60 = 0.017), lo que hace todos los viajes futuros de ese conductor extremadamente rápidos. |
| M7 | `contextual_reasoning.py:115` | `similarity` scores no normalizados entre 0 y 1 en el cálculo | Se suman: 0.35 + 0.25 + 0.15 + 0.15 + 0.10 = 1.0 máximo. Pero si `item.container.vendor` no existe (`None`), la comparación `item.container.vendor == programacion.container.vendor` devuelve `True` si ambos son `None`. | **Dos programaciones con vendor nulo reciben similitud máxima de vendor**, aunque el vendor real sea diferente. |
| M8 | `api_views.py:108-111` | `analytics_conductores` → `float(driver.cumplimiento_porcentaje)` | `cumplimiento_porcentaje` es un `DecimalField(5,2)` en el modelo. La conversión a `float` es segura, pero en `analytics_eficiencia.py:134-135` se hace `sum(float(d.cumplimiento_porcentaje) for d in drivers)` sin verificar que `cumplimiento_porcentaje` no sea None. | Si un driver tiene `cumplimiento_porcentaje = NULL`, se lanza `TypeError: float() argument is None`. |
| M9 | `excel.py:29-30` | `normalize_label()` → `''.join(...)` elimina caracteres combinando unicodedata | Esta función no maneja valores `None` bien en la línea `text.replace('\xa0', ' ')` — si `value` es None, `str(value)` retorna `"None"` literal, no un string vacío. | Si una columna en el Excel tiene header `None` (vacío), se normaliza a `"none"` en vez de `""`, lo que puede mapear a columnas erróneas. |

### BAJO

| # | Archivo | Línea | Problema | Impacto |
|---|---------|-------|----------|---------|
| B1 | `mapbox.py:28-29` | `return {"success": False, "error": "MAPBOX_API_KEY no configurado"}` en 3 funciones duplicadas | La lógica de "token missing" está copiada 3 veces (en `calcular_ruta`, `calcular_rutas_alternativas`, `geocode`). Si se cambia la estrategia (ej: cache del token), se debe actualizar en 3 lugares. | DRY violation. No impacta funcionalidad hoy pero hace cambios futuros propensos a error. |
| B2 | `dashboard_operativo.py:14` | `FACTOR_RIESGO_ML = 1.12` | Valor hardcodeado que debería estar en `settings.py` para ser configurable por el operador. | No es un bug, pero si Seba quiere ajustar el umbral, debe editar código. |
| B3 | `assignment.py:152` | `Decimal(str(final_score))` | Se convierte de float a string a Decimal en cada score. Es seguro pero ineficiente — `Decimal(final_score)` funcionaría directo. | Micro-optimización. 0 impacto real. |
| B4 | `settings.py:54` | `whitenoise.middleware.WhiteNoiseMiddleware` en MIDDLEWARE | WhiteNoise está en MIDDLEWARE pero `StaticFilesStorage` usa `CompressedManifestStaticFilesStorage` que espera que los archivos estén pre-comprimidos. Si `DEBUG=True` (default), no hay problemas. En producción sin `precompile`, los assets no servirán. | **500 en producción si no se corre `collectstatic --noinput`** como parte del deploy. |
| B5 | `assignment.py:260-270` | `asignar_mejor_conductor` → `update_fields` excluye `'driver'` | La línea 234 hace `programacion.save(update_fields=['driver', ...])` pero `driver` está en la lista. El modelo `asignar_conductor` lo maneja correctamente, pero `save(update_fields=['driver', ...])` funciona bien. **Verificado: sí funciona.** | FALSO POSITIVO. |
| B6 | `dashboard_operativo.py:109-110` | `sin_asignar()` → `horas_restantes = (prog.fecha_programada - timezone.now()).total_seconds() / 3600` | Si `fecha_programada` es `None`, se lanza `TypeError`. Pero el filtro ya asegura que existe (`fecha_programada__lte=limite`). En Django, los `__lte` filters con `__isnull=True` excluyen nulos, pero aquí se filtra por `driver__isnull=True` y `fecha_programada__lte=limite` — Django ORM no garantiza que `fecha_programada` no sea NULL. Si hay una programación con `fecha_programada=NULL`, el filtro `__lte` la excluye, así que **está protegido**. | FALSO POSITIVO. |

---

## (A) Veredicto de 3 Flujos Núcleo

### Flujo 1: `predict_route` completo (Learning Engine)

**Estado: FUNCONA CORRECTAMENTE con 1 riesgo de NaN silencioso**

```
caller → _history(origin, destination)
  → filtra TiempoViaje con _near() en 4 coordenadas, + filtros de tiempo/0, -anomalia
  → retorna lista de rows históricos

caller → _weighted_factor(rows, departure, driver, route_signature)
  → para cada row: factor = max(0.45, min(2.5, row.calcular_factor_correccion()))
  → weight = exp(-age_days/75) * exp(-hour_distance/3) * day_weight * route_weight * driver_weight
  → retorna weighted average of factors, o 1.0 si no hay datos

caller → predict_route(origin, destination, departure, base_route, driver, history)
  → filtra route_rows por firma de ruta
  → relevant = route_rows (si >= 2 samples) else history completo
  → learned_factor = _weighted_factor(relevant, departure, driver, signature)
  → learned_weight = min(0.78, samples/18)  ← 18 samples = 78% learned
  → blended_factor = (1-learned_weight) + learned_weight * learned_factor
  → predicted = max(1, round(base_route['duration_minutes'] * blended_factor))
  → confidence = min(0.96, 0.25 + samples/24)

Resultado: dict con predicted_minutes, learned_factor, samples, confidence, source
```

**Invariantes verificadas:**
- `blended_factor` siempre >= 0.45 (porque learned_factor se clamp a [0.45, 2.5])
- `predicted` siempre >= 1 (max(1, ...))
- `confidence` siempre en [0.25, 0.96] con datos
- Cuando `samples == 0`, `learned_weight == 0`, `blended_factor == 1.0`, `source == 'mapbox_cold_start'`
- `learned_factor` se guarda en `Programacion.prediccion_ml` → **Sí, se guarda en assignment.py**

**Riesgo:** Si una row de `TiempoViaje` tiene `tiempo_mapbox_min > 0` y `tiempo_real_min > 0` pero `calcular_factor_correccion()` retorna un valor NaN (imposible con los datos IntegerField), el factor se clampa a [0.45, 2.5] antes del cálculo. **No es posible con campos enteros.** → Seguro.

### Flujo 2: `asignar_mejor_conductor` completo (Assignment Service)

**Estado: FUNCIONAL PERO CON INCONSISTENCIA GRAVE (A6)**

```
1. Si programacion.driver ya existe → return error
2. obtener_conductores_disponibles_con_score(programacion)
   → Driver.objects.filter(activo=True, presente=True)
   → Para cada driver: calcular_score_total(driver, programacion)
      → base_weights (configurable)
      → dynamic_weights (contextual reasoning ajusta por urgencia/seguimiento)
      → 5 dimensiones: disponibilidad_confirmada, riesgo_de_atraso, adecuacion_vehiculo_carga, historial_operativo, urgencia_del_servicio
      → deterministic = weighted sum de dimensiones con dyn_weights
      → similar_boost = average similarity de 5 casos históricos (0.2 weight)
      → final_score = deterministic * 0.8 + similar_boost * 0.2
      → anomalies = AnomalyDetector.detect()
      → classification: DESPACHO_DIRECTO / REVISION_OPERADOR / INTERVENCION
      
3. mejor = conductores[0] (ordenado por score desc)
4. Guardar datos de scoring en programacion
5. Si classification != 'DESPACHO_DIRECTO':
   → crear RegistroOperacion, solicitar review OpenClaw, return requires_operator=True
6. Si DESPACHO_DIRECTO:
   → programacion.asignar_conductor(driver, usuario)  ← método del modelo
      → select_for_update → verifica disponibilidad
      → programa container.cambiar_estado('asignado')
      → Driver.objects.update(num_entregas_dia=F()+1)
      → crea Event + Notification
```

**INCONSISTENCIA CRÍTICA (A6):** Cuando `classification == 'DESPACHO_DIRECTO'` en la línea 255, se llama `programacion.asignar_conductor(driver, usuario)`. Pero cuando `classification != 'DESPACHO_DIRECTO'` (línea 233), se hace `programacion.driver = mejor['driver']` directamente con `save(update_fields=[...])`. **Esto NO incrementa `num_entregas_dia`, NO cambia el estado del contenedor, NO crea evento.**

En el branch de DESPACHO_DIRECTO, el método `asignar_conductor` sí hace todo lo correcto. Pero si el operador luego rechaza y se reasigna, el `num_entregas_dia` no se descuenta porque la liberación (`liberar_conductor`) no se llamó.

### Flujo 3: Dashboard Operativo E2E

**Estado: FUNCIONAL con 2 riesgos de crash**

```
construir_dashboard_operativo() →
  1. programadas_por_fecha(hoy, hoy)
     → Programacion.objects.filter(
         fecha_programada__date__gte=hoy, fecha_programada__date__lte=hoy,
         container__estado__in=ESTADOS_CONTAINER_ACTIVOS
       ).select_related('container','driver','cd')
     → Para cada: _programacion_item() → {id, container_id, container_id_formatted, cliente, cd, fecha, driver_id, driver_nombre, estado, eta_minutos}

  2. programadas_por_fecha(manana, manana) → mismo
  
  3. sin_asignar()
     → driver__isnull=True, fecha_programada__lte=hoy+48h
     → para cada: horas_restantes, prioridad (critica <24h, alta >=24h)
  
  4. riesgo_ml(hoy, manana)
     → driver__isnull=False, same fecha filter
     → para cada: driver_profile → si factor_ml >= 1.12, agregar + alternativas (<=3)
  
  5. riesgo_encadenamiento(hoy, manana)
     → Para cada prog B: encontrar asignación anterior A del mismo driver
     → Calcular fin de A (fecha_inicio_ruta + ETA, o fecha_programada + ETA)
     → Calcular viaje A→B (Mapbox con fallback haversine)
     → Si llega tarde > 0 min: agregar con deficit y alternativas
  
  6. vacios()
     → Container.objects.filter(estado__in=['vacio','vacio_en_ruta'])
     → Para cada: container_id, estado, posicion_fisica, cliente, fechas
  
  7. Retornar dict con 'success', 'generado_en', + 6 arrays
```

**Riesgos de crash identificados:**
- A4: `peso_total_tons > 28` sin verificar None en AnomalyDetector (afecta asignación, no dashboard directo)
- M4: Timezone-naive vs aware en `deficit` calculation (solo si se mezclan data sources)
- A3: `eta_minutos` NULL → frontend JS puede romper

---

## (B) Invariantes Verificadas

1. **FACTOR_RIESGO_ML == 1.12** en `dashboard_operativo.py:14` y en `learning_engine.py:61` (threshold `factor >= 1.12` → 'más_lento_que_referencia'). **Coherente.** ✅

2. **_weighted_factor clamp en [0.45, 2.5]** → `max(0.45, min(2.5, factor))`. Siempre válido. ✅

3. **learned_weight range [0, 0.78]** → `min(0.78, samples/18)`. Nunca domina completamente. ✅

4. **blended_factor = (1-w) + w*f** con w∈[0,0.78], f∈[0.45,2.5] → blended ∈ [0.45, 2.5]. ✅

5. **predict_route devuelve dict con todas las keys** que `recommend` consume: `predicted_minutes`, `learned_factor`, `samples`, `confidence`, `source`, `driver_profile`. ✅

6. **_programacion_item** siempre retorna las 9 keys que el frontend espera: id, container_id, container_id_formatted, cliente, cd, fecha_programada, driver_id, driver_nombre, estado, eta_minutos. Con fallback None para cada campo nullable. ✅

7. **_perfil_conductor** maneja driver=None → retorna None. `riesgo_ml` filtra driver__isnull=False, así que None nunca llega a la indexación. ✅

8. **_alternativas_driver** retorna máximo 3 items, cada una con driver_id, driver_nombre, factor_ml, label_ml, confianza_ml, samples_ml, cumplimiento, ocupacion, disponible. ✅

9. **`asignar_conductor` del modelo** incrementa `num_entregas_dia` correctamente con `F()`, crea eventos, notificaciones, cambia estado del container. ✅

10. **`liberar_conductor` del modelo** decrementa `num_entregas_dia`, marca `fecha_liberacion_conductor`, previene liberación doble. ✅

11. **TiempoOperacion.obtener_tiempo_aprendido** → con conductor ≥3 samples usa promedio conductor, else con CD ≥5 samples usa promedio CD, else fallback a cd.tiempo_promedio_descarga_min, else 60. ✅

12. **TiempoViaje.obtener_tiempo_aprendido** → con conductor ≥2 samples (mismo hora±2h) usa promedio real, else similar ≥3 samples usa factor mapbox, else Mapbox directo. ✅

13. **MapboxService** — token check consistente en 3 funciones, formato lng,lat correcto (Mapbox espera lng,lat), geometry→signature SHA-256 consistente. ✅

14. **AnomalyDetector detect()** retorna lista de dicts con code, severity, message, recommended_action, ordenada por SEVERITY_ORDER. ✅

15. **DynamicWeights** → normalización final divide por suma total, resultados en [0, 1]. La suma siempre = 1.0 (o base_weights si suma=0). ✅

16. **OpenClawService** — disabled si OPENCLAW_ENABLED=False o API_KEY=None. Los errores de HTTP no propagan. ✅

---

## Resumen Ejecutivo

**Severidad: 2 CRÍTICO, 7 ALTO, 9 MEDIO, 6 BAJO**

| Severidad | Count |
|-----------|-------|
| CRÍTICO   | 2     |
| ALTO      | 7     |
| MEDIO     | 9     |
| BAJO      | 6     |

**Los 3 problemas que más impacto operativo tienen:**

1. **SECRET_KEY por defecto** (C1) — cualquier instancia de producción sin环境变量 configurada tiene auth rota.
2. **Asignación directa vs método del modelo** (A6) — `assignment.py:233-234` asigna `driver` directamente sin pasar por `asignar_conductor()`, lo que deja `num_entregas_dia`, estados de contenedor y eventos inconsistentes.
3. **peso_total_tons None** (A4) — comparación sin None-check en anomaly_detector lanza un `TypeError` que puede propagar 500 al dashboard.

El resto son problemas de robustez, rendimiento y DRY que mejoran la calidad pero no rompen el sistema directamente.
