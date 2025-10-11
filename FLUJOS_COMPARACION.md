# 🔄 COMPARACIÓN DE FLUJOS - Actual vs Requerido

## FLUJO 1: EMBARQUE (Excel → Sistema)

### ✅ ACTUAL (Implementado)
```
Excel Embarque
    ↓
[Container ID, Tipo, Nave, Peso, Vendor, Sello, Puerto, Comuna]
    ↓
Container creado con estado='por_arribar'
    ↓
Vista: Contenedor | Tipo | Peso | Nave | Estado
```

### ⚠️ REQUERIDO (Falta ETA)
```
Excel Embarque
    ↓
[Container ID, Tipo, Nave, **ETA**, Peso, Vendor, Sello, Puerto, Comuna]
    ↓
Container creado con estado='por_arribar' + **fecha_eta**
    ↓
Vista: Contenedor | Tipo | Peso | Nave | **ETA** | Estado
```

**ACCIÓN**: Agregar campo `fecha_eta` y actualizar importador

---

## FLUJO 2: LIBERACIÓN (Excel → Actualización)

### ✅ ACTUAL (Implementado parcialmente)
```
Excel Liberación
    ↓
[Container ID, Posición Física, Comuna]
    ↓
Container.estado = 'liberado'
Container.posicion_fisica = mapeo(Posición) 
    - TPS → ZEAL
    - STI/PCE → CLEP
Container.fecha_liberacion = now()
```

### ❌ REQUERIDO (Faltan campos críticos)
```
Excel Liberación
    ↓
[Container ID, Posición Física, **Depósito Devolución**, **Fecha Demurrage**, Peso*]
    ↓
Container.estado = 'liberado'
Container.posicion_fisica = mapeo(Posición)
**Container.deposito_devolucion = [valor]**
**Container.fecha_demurrage = [fecha]**
Container.fecha_liberacion = now()
Container.peso = [actualizado si viene]
```

**ACCIÓN**: Agregar campos `deposito_devolucion` y `fecha_demurrage`

---

## FLUJO 3: EXPORTACIÓN STOCK

### ✅ ACTUAL (Implementado)
```
Sistema
    ↓
Filtrar: estado IN ('liberado', 'por_arribar')
    ↓
Para cada contenedor:
    IF fecha_liberacion > hoy:
        secuenciado = True
    ↓
Excel: [Contenedor, Tipo, Peso, Estado, **Secuenciado**]
```

### ✅ REQUERIDO (Ya funciona)
```
Sin cambios necesarios
```

---

## FLUJO 4: PROGRAMACIÓN (Excel → Sistema)

### ✅ ACTUAL (Implementado)
```
Excel Programación
    ↓
[Container ID, Fecha Programación, CD Destino, ...]
    ↓
Buscar Container por container_id
    ↓
SI encontrado:
    - Crear Programacion(container, fecha, cd)
    - Container.estado = 'programado'
    - SI fecha < hoy + 48h Y conductor=NULL:
        → Alerta creada
```

### ✅ REQUERIDO (Ya funciona)
```
Sin cambios necesarios
```

---

## FLUJO 5-7: ASIGNACIÓN Y EN RUTA

### ✅ ACTUAL (Implementado)
```
Programacion sin conductor + fecha cercana
    ↓
Alerta en /api/programaciones/alertas/
    ↓
Asignación (manual o automática):
    - Algoritmo evalúa conductores presentes
    - Score: disponibilidad 30% + ocupación 25% + cumplimiento 30% + proximidad 15%
    ↓
Programacion.conductor = conductor_seleccionado
Container.estado = 'asignado'
    ↓
Conductor inicia ruta:
    - Container.estado = 'en_ruta'
    - Mapbox calcula ETA
    - Cliente informado de ETA
```

### ✅ REQUERIDO (Ya funciona)
```
Sin cambios necesarios
```

---

## FLUJO 8-11: ENTREGA Y RETORNO (CRÍTICO - INCOMPLETO)

### ⚠️ ACTUAL (Implementado parcialmente)
```
Conductor arriba
    ↓
Cambio manual: Container.estado = 'entregado'
    ↓
[NO HAY LÓGICA DE DESCARGA]
    ↓
[NO HAY LÓGICA DE RETORNO]
```

### ❌ REQUERIDO (Falta implementar)

#### Opción A: CD Requiere Espera (Puerto Madero, Campos Chile, Quilicura)
```
Conductor arriba
    ↓
POST /api/containers/{id}/registrar_arribo/
    - Container.estado = 'entregado'
    - Container.fecha_entrega = now()
    ↓
Cliente descarga contenedor
    ↓
POST /api/containers/{id}/registrar_descarga/
    - Container.estado = 'descargado'
    - Container.hora_descarga = now()
    - Container.cd_entrega = CD
    ↓
**Conductor espera con contenedor vacío en camión**
    ↓
OPCIÓN 1: Retornar a CCTI
    - Container.estado = 'vacio_en_ruta' (destino: CCTI)
    - Llegada a CCTI:
        * Container.estado = 'en_almacen_ccti'
        * CCTI.vacios_actual += 1
    ↓
OPCIÓN 2: Retornar a Depósito Devolución
    - Container.estado = 'vacio_en_ruta' (destino: Container.deposito_devolucion)
    - Llegada:
        * Container.estado = 'vacio_en_ccti'
        * Contenedor sale del sistema
```

#### Opción B: CD Permite Soltar (El Peñón)
```
Conductor arriba
    ↓
POST /api/containers/{id}/registrar_arribo/
    - Container.estado = 'entregado'
    - Container.fecha_entrega = now()
    ↓
**Conductor suelta contenedor**
    ↓
POST /api/containers/{id}/soltar_contenedor/
    - Container.estado = 'descargado'
    - Container.hora_descarga = now()
    - Container.cd_entrega = CD
    - CD.vacios_actual += 1
    ↓
**Conductor queda libre inmediatamente**
    - Driver.esta_disponible = True
    ↓
OPCIONAL: Conductor recoge vacío de El Peñón
    - Buscar Container en El Peñón con estado='vacio_en_ccti'
    - Asignar a conductor
    - Container.estado = 'vacio_en_ruta' (destino: CCTI o puerto)
```

**ACCIONES REQUERIDAS**:
1. Agregar campo `cd_entrega` (ForeignKey a CD)
2. Agregar campo `hora_descarga`
3. Agregar campos a CD:
   - `requiere_espera_carga` (Boolean)
   - `permite_soltar_contenedor` (Boolean)
   - `tiempo_promedio_descarga_min` (Integer)
4. Crear endpoints:
   - `/api/containers/{id}/registrar_arribo/`
   - `/api/containers/{id}/registrar_descarga/`
   - `/api/containers/{id}/soltar_contenedor/`
5. Actualizar cálculo de ocupación conductor:
   ```python
   tiempo_ocupado = (
       tiempo_viaje_ida +
       tiempo_descarga +
       (tiempo_espera_carga if cd.requiere_espera_carga else 0) +
       (tiempo_viaje_retorno if not cd.permite_soltar_contenedor else 0)
   )
   ```

---

## FLUJO ESPECIAL: TERCERA OPCIÓN - RETIRO DESDE PUERTO

### ❌ ACTUAL (No implementado)
```
Contenedor liberado en TPS/STI/PCE
    ↓
Movimiento automático:
    - TPS → ZEAL
    - STI/PCE → CLEP
```

### ❌ REQUERIDO (Falta opción 3)
```
Contenedor liberado en TPS/STI/PCE
    ↓
OPCIÓN 1: Movimiento Automático (actual)
    - TPS → ZEAL
    - STI/PCE → CLEP
    - Container.tipo_movimiento = 'automatico'
    ↓
**OPCIÓN 2: CCTI va a buscarlo → CCTI**
    - Crear Programacion especial:
        * origen = Container.posicion_fisica (TPS/STI/PCE)
        * destino = CCTI
        * tipo = 'retiro_ccti'
    - Asignar conductor
    - Container.tipo_movimiento = 'retiro_ccti'
    - Conductor recoge y lleva a CCTI
    - Container.posicion_fisica = 'CCTI'
    - Container.estado = 'en_almacen_ccti'
    ↓
**OPCIÓN 3: CCTI va a buscarlo → Cliente Directo**
    - Crear Programacion especial:
        * origen = Container.posicion_fisica (TPS/STI/PCE)
        * destino = CD Cliente
        * tipo = 'retiro_directo'
    - Asignar conductor
    - Container.tipo_movimiento = 'retiro_directo'
    - Conductor recoge del puerto y entrega directo
    - [Continúa con flujo normal de entrega]
```

**ACCIONES REQUERIDAS**:
1. Agregar campo `tipo_movimiento` con choices:
   - `automatico`: Movimiento automático puerto
   - `retiro_ccti`: Retiro a CCTI
   - `retiro_directo`: Retiro directo a cliente
2. Crear endpoint:
   ```
   POST /api/programaciones/crear_retiro/
   {
       "container_id": "...",
       "tipo": "retiro_ccti" | "retiro_directo",
       "destino_cd_id": 1,  // Solo si retiro_directo
       "fecha_programacion": "2025-10-15T10:00:00"
   }
   ```
3. Actualizar importador de liberación:
   - Si viene columna "Tipo Movimiento" o similar
   - Determinar automáticamente según lógica de negocio

---

## RESUMEN DE ACCIONES POR PRIORIDAD

### 🔴 CRÍTICAS (Bloquean operación)
```sql
-- Migración Container
ALTER TABLE containers_container ADD COLUMN fecha_eta TIMESTAMP NULL;
ALTER TABLE containers_container ADD COLUMN deposito_devolucion VARCHAR(200) NULL;
ALTER TABLE containers_container ADD COLUMN fecha_demurrage TIMESTAMP NULL;
ALTER TABLE containers_container ADD COLUMN cd_entrega_id INTEGER NULL;
ALTER TABLE containers_container ADD COLUMN hora_descarga TIMESTAMP NULL;
ALTER TABLE containers_container ADD COLUMN tipo_movimiento VARCHAR(20) DEFAULT 'automatico';

-- Migración CD
ALTER TABLE cds_cd ADD COLUMN requiere_espera_carga BOOLEAN DEFAULT FALSE;
ALTER TABLE cds_cd ADD COLUMN permite_soltar_contenedor BOOLEAN DEFAULT FALSE;
ALTER TABLE cds_cd ADD COLUMN tiempo_promedio_descarga_min INTEGER DEFAULT 60;
```

### 🟡 IMPORTANTES (Mejoran eficiencia)
- Endpoints de arribo/descarga
- Actualizar cálculo ocupación conductor
- Sistema alertas demurrage
- Rutas manuales

### 🟢 DESEABLES (Futuro)
- Machine Learning tiempos
- Dashboard vacíos
- Estética Ubuntu

---

**¿Procedo con las migraciones críticas?** 🚀
