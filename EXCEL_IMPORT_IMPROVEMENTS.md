# Mejoras en la Importación de Excel

## Problema Identificado

Los usuarios reportaban que la importación de Excel mostraba "importación exitosa pero 0 procesados". Esto ocurría por dos razones principales:

1. **Variaciones en nombres de columnas**: Los archivos Excel pueden venir con diferentes nombres de columnas que no eran reconocidos por el sistema
2. **Filas vacías**: Los archivos Excel a menudo contienen filas vacías que eran contadas como errores

## Solución Implementada

### 1. Normalización Inteligente de Columnas

Se expandió significativamente el mapeo de columnas para soportar múltiples variaciones de nombres:

#### Programación (programacion.py)
```python
# Container ID - ahora reconoce:
- contenedor, container, id
- nº contenedor, n° contenedor, numero contenedor  
- container id, container_id

# Fecha Programada - ahora reconoce:
- fecha, fecha programacion, fecha_programacion
- fecha de programacion, fecha programada, fecha_programada

# CD/Bodega - ahora reconoce:
- centro distribucion, centro_distribucion
- destino, bodega, cd
```

#### Embarque (embarque.py)
```python
# Container ID - múltiples variaciones
- contenedor, container, container numbers
- container number, nº contenedor, etc.

# Tipo/Size - ahora reconoce:
- tipo contenedor, container size
- size, tamaño, tipo

# Nave - ahora reconoce:
- buque, naviera, nave confirmado
- nave, m/n, vessel
```

#### Liberación (liberacion.py)
```python
# Posición Física - ahora reconoce:
- posicion, posición, ubicacion, ubicación
- terminal, almacen, almacén
- posicion fisica, posicion_fisica
```

### 2. Filtrado Inteligente de Filas Vacías

Antes:
```python
# Procesaba TODAS las filas, incluyendo vacías
for idx, row in df.iterrows():
    # Si container_id era vacío, lo contaba como error
```

Después:
```python
# 1. Elimina filas completamente vacías
df = df.dropna(how='all')

# 2. Filtra solo filas con container_id válido
df_filtrado = df[
    df['container_id'].notna() & 
    (df['container_id'] != '') &
    (df['container_id'].astype(str).str.upper() != 'NAN')
]

# 3. Solo procesa filas con datos reales
for idx, row in df_filtrado.iterrows():
    # Ahora todas las filas tienen datos válidos
```

### 3. Mensajes de Debug Mejorados

Se agregaron logs informativos para facilitar el diagnóstico:

```python
print(f"DEBUG - Columnas encontradas: {list(df.columns)}")
print(f"DEBUG - Filas a procesar: {len(df_filtrado)} de {len(df)} totales")
```

### 4. Mensajes de Error Mejorados

Antes:
```
ValueError: Columna requerida 'container_id' no encontrada en el Excel
```

Después:
```
ValueError: Columnas requeridas no encontradas: ['container_id']. 
Columnas disponibles: ['nave', 'container numbers', 'peso', ...]
```

Esto ayuda a identificar rápidamente qué columnas faltan y cuáles están disponibles.

## Resultados

### Antes
- ✗ Solo reconocía nombres exactos de columnas
- ✗ Procesaba filas vacías como errores
- ✗ "Importación exitosa pero 0 procesados"
- ✗ Mensajes de error genéricos

### Después  
- ✓ Reconoce múltiples variaciones de nombres
- ✓ Filtra automáticamente filas vacías
- ✓ Solo cuenta y procesa datos reales
- ✓ Mensajes de error específicos y útiles

## Ejemplos de Uso

### Archivo con diferentes nombres de columnas

**Excel 1:**
```
CONTENEDOR | FECHA DE PROGRAMACION | BODEGA
TCKU123    | 2025-10-04           | PEÑÓN
```

**Excel 2:**
```
Container ID | Fecha Programada | CD
TCKU123      | 2025-10-04       | PEÑÓN
```

**Excel 3:**
```
Nº Contenedor | Fecha | Centro Distribución
TCKU123       | 2025-10-04 | PEÑÓN
```

✓ **Todos estos formatos ahora funcionan correctamente**

### Archivo con filas vacías

**Antes:**
```
Filas totales: 50
Procesados: 0
Errores: 50 (todas las filas vacías contadas como error)
```

**Después:**
```
Filas totales: 50
Filas con datos: 10
Procesados: 10
Errores: 0
```

## Archivos Modificados

1. `apps/containers/importers/programacion.py`
   - Expandido mapeo de columnas
   - Filtrado inteligente de filas
   - Mensajes de debug mejorados

2. `apps/containers/importers/embarque.py`
   - Expandido mapeo de columnas
   - Filtrado inteligente de filas
   - Mensajes de debug mejorados

3. `apps/containers/importers/liberacion.py`
   - Expandido mapeo de columnas
   - Filtrado inteligente de filas
   - Mensajes de debug mejorados

## Pruebas Realizadas

Se probaron los importadores con archivos Excel reales:

```bash
# Programación - 9 filas de datos identificadas
✓ Columnas encontradas y mapeadas correctamente
✓ Filas con datos: 9/9

# Liberación - 34 filas de datos identificadas
✓ Columnas encontradas y mapeadas correctamente  
✓ Filas con datos: 34/35 (1 fila vacía filtrada)

# Embarque - 41 filas de datos identificadas
✓ Columnas encontradas y mapeadas correctamente
✓ Filas con datos: 41/41
```

## Recomendaciones

1. **No es necesario cambiar el formato de los Excel** - El sistema ahora reconoce automáticamente diferentes variaciones de nombres
2. **Las filas vacías se ignoran automáticamente** - No es necesario limpiar manualmente los archivos
3. **Si un archivo no funciona**, revisar los logs de debug para ver qué columnas fueron encontradas

## Soporte Adicional

Si aún tienes problemas con la importación:

1. Revisa los logs de debug que muestran las columnas encontradas
2. Compara con la lista de variaciones soportadas en este documento
3. Si necesitas agregar una nueva variación, edita el diccionario `mapeo` en el importador correspondiente

---

**Fecha de implementación:** 2025-10-12
**Estado:** ✅ Completado y probado
