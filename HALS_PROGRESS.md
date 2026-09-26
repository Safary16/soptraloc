# Misión Nocturna HALs - Tracker

## Critical HALs (resolve primero)
- [ ] HAL-1 iniciar_ruta ETA fallback haversine
- [ ] HAL-2 ProgramacionListSerializer expose eta_recalculado_min
- [ ] HAL-3 _update_registro_operacion_on_completion crea TiempoViaje aunque eta_minutos=None
- [ ] HAL-4 soltar_contenedor 3-tuple unpack + test integración E5
- [ ] HAL-5 Programacion.objects.create(driver=X) signals.py reorder

## Medium HALs
- [ ] HAL-6 aceptar_asignacion 200 OK
- [ ] HAL-7 iniciar_ruta patente null safety
- [ ] HAL-8 Notification 'llegada' fuera de transacción
- [ ] HAL-9 notificar_inicio_descarga acepta 'descargado'? — criterio propio
- [ ] HAL-10 notificar_arribo setear eta_minutos=0 (o flag)

## Minor HALs
- [ ] HAL-11 docstring tipo_problema
- [ ] HAL-12 cliente_portal.html ETA null
- [ ] HAL-13 notificar_inicio_descarga crear Event siempre (ya lo hace; verificar fin_descarga)
- [ ] HAL-14 SSE eta-stream timeout + Last-Event-ID
- [ ] HAL-15 contenedores vacios_actuales documento contrato
- [ ] HAL-16 aceptar_asignacion admite 'programado' — criterio propio
- [ ] HAL-17 _record_discharge fecha_inicio_descarga prioridad
- [ ] HAL-18 driver_discharge_profile confirmado no bug
- [ ] HAL-19 ContextualReasoning import confirmado no bug
- [ ] HAL-20 /gestion/vacios-ccti/ sin login_required

## Tests nuevos
- [ ] E5: drop&hook → soltar → auto-retorno mismo conductor → vacío 5h
- [ ] E3: serializer lista expone eta_recalculado_min
- [ ] HAL-1/HAL-3: iniciar_ruta ETA haversine fallback + TiempoViaje al arribar
