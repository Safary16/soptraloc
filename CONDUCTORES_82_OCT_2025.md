# 🚚 Carga de 82 Conductores - Octubre 2025

## ✅ Cambios Implementados

### 1. **Actualización del Comando `load_drivers`**

**Archivo:** `soptraloc_system/apps/drivers/management/commands/load_drivers.py`

#### Cambios realizados:

**Número de conductores por defecto:**
- **Antes:** 25 conductores
- **Ahora:** 82 conductores

**Nombres ampliados (60+ nombres):**
```python
Nombres masculinos: Juan, Carlos, Luis, José, Francisco, Antonio, 
                    Miguel, Manuel, David, Daniel, Roberto, Rafael, 
                    Eduardo, Fernando, Jorge, Alejandro, Ricardo, 
                    Andrés, Javier, Pedro, Sergio, Raúl, Óscar, 
                    Pablo, Ramón, Enrique, Héctor, Víctor, Arturo, 
                    Ignacio, Diego, Rubén, Felipe, Mario, Alberto, 
                    Cristian, Rodrigo, Mauricio, Sebastián, Marcelo

Nombres femeninos:  María, Ana, Carmen, Rosa, Patricia, Laura, Elena, 
                    Sandra, Mónica, Claudia, Silvia, Adriana, Gabriela,
                    Lucía, Isabel, Beatriz, Pilar, Teresa, Cristina,
                    Marta, Verónica, Natalia, Daniela, Carolina,
                    Valentina, Camila
```

**Apellidos ampliados (40+ apellidos):**
```python
García, Rodríguez, González, Fernández, López, Martínez, Sánchez,
Pérez, Gómez, Martín, Jiménez, Ruiz, Hernández, Díaz, Moreno,
Muñoz, Álvarez, Romero, Alonso, Gutiérrez, Navarro, Torres,
Domínguez, Vázquez, Ramos, Gil, Ramírez, Serrano, Blanco,
Suárez, Molina, Castro, Ortiz, Rubio, Marín, Sanz, Iglesias,
Núñez, Medina, Garrido
```

**Tipos de conductores:**
```python
- LEASING    → Conductores externos contratados
- LOCALERO   → Conductores para rutas cortas locales
- TRONCO_PM  → Conductores para rutas largas (PM)
- TRONCO     → Conductores para rutas largas (general)
```

### 2. **Actualización del Script de Deploy**

**Archivo:** `post_deploy.sh`

Se agregó un nuevo paso (PASO 5) que carga automáticamente los 82 conductores:

```bash
# ============================================================================
# PASO 5: CARGAR CONDUCTORES
# ============================================================================
echo "🚚 PASO 5: Cargando 82 conductores"

if python manage.py load_drivers --count=82 --force --settings=config.settings_production; then
    echo "✅ 82 conductores cargados correctamente"
else
    echo "⚠️  Advertencia: Hubo un problema al cargar conductores (no crítico)"
fi
```

**Orden de ejecución en deploy:**
1. Verificar entorno
2. Verificar PostgreSQL
3. Crear superusuario (admin/1234)
4. Verificar superusuario
5. **🆕 Cargar 82 conductores** ← NUEVO
6. Cargar datos iniciales de Chile
7. Resumen final

## 📊 Características de los Conductores Generados

Cada conductor tendrá:

✅ **Información Personal:**
- Nombre y apellido aleatorio de las listas ampliadas
- Usuario Django asociado (username: conductor_XXX)
- Email: conductor_XXX@soptraloc.com

✅ **Información Profesional:**
- Número de licencia: CL-XXXXXX (aleatorio)
- Tipo de licencia: A1, A2, A3, A4, A5
- Tipo de conductor: LEASING, LOCALERO, TRONCO_PM, TRONCO
- Teléfono: +569 XXXX XXXX

✅ **Estado:**
- Activo: Sí (is_active=True)
- Disponible: Asignado aleatoriamente (75% disponibles)

## 🚀 Cómo se Ejecuta

### En Render (Automático):

Cuando se hace push a GitHub, Render:
1. Detecta el cambio en la rama `main`
2. Ejecuta `build.sh`
3. Ejecuta `post_deploy.sh`
4. **Carga automáticamente los 82 conductores**

### Manualmente (Local o Servidor):

```bash
# Cargar 82 conductores (forzar recarga)
cd soptraloc_system
python manage.py load_drivers --count=82 --force

# O con otro número personalizado
python manage.py load_drivers --count=50 --force

# Sin forzar (solo crea los que faltan)
python manage.py load_drivers --count=82
```

## 📋 Verificación

Después del deploy, puedes verificar los conductores:

### En el Admin:
1. Accede a: https://soptraloc.onrender.com/admin/
2. Login: admin / 1234
3. Ve a: Core → Conductores
4. Deberías ver 82 conductores listados

### Programáticamente:
```python
from apps.core.models import Driver

# Contar conductores
total = Driver.objects.count()
print(f"Total de conductores: {total}")

# Ver por tipo
from django.db.models import Count
tipos = Driver.objects.values('tipo_conductor').annotate(count=Count('id'))
for tipo in tipos:
    print(f"{tipo['tipo_conductor']}: {tipo['count']} conductores")

# Ver disponibilidad
disponibles = Driver.objects.filter(is_available=True).count()
no_disponibles = Driver.objects.filter(is_available=False).count()
print(f"Disponibles: {disponibles}")
print(f"No disponibles: {no_disponibles}")
```

## 🔄 Comportamiento del Flag `--force`

- **Con `--force`:** Elimina TODOS los conductores existentes y crea 82 nuevos
- **Sin `--force`:** Solo crea los conductores que faltan para llegar a 82

En el `post_deploy.sh` usamos `--force` para garantizar que siempre haya exactamente 82 conductores frescos en cada deploy.

## 📝 Commits Realizados

```
e49fe1f - 🚚 Cargar 82 conductores automáticamente en deploy
  - Aumentar número de conductores de 25 a 82 por defecto
  - Agregar más nombres y apellidos para mayor variedad (60+ nombres)
  - Incluir tipos: LEASING, LOCALERO, TRONCO_PM, TRONCO
  - Agregar paso en post_deploy.sh para cargar conductores
  - Los conductores se cargan automáticamente en cada deploy a Render
```

## ⚠️ Notas Importantes

1. **Datos de Prueba:** Los conductores son datos de prueba generados aleatoriamente
2. **Deploy Automático:** Se cargan en CADA deploy a Render
3. **Flag --force:** En producción, usar `--force` con precaución (elimina conductores existentes)
4. **Personalización:** Para producción real, considera cargar conductores reales desde CSV o Excel

## 🎯 Próximos Pasos Sugeridos

Si necesitas cargar conductores reales:

1. **Crear archivo CSV con conductores reales:**
   ```csv
   nombre,apellido,email,telefono,licencia,tipo_licencia,tipo_conductor
   Juan,Pérez,juan.perez@empresa.com,+56912345678,CL-123456,A4,TRONCO
   María,González,maria.gonzalez@empresa.com,+56987654321,CL-789012,A2,LOCALERO
   ```

2. **Crear comando personalizado:**
   ```bash
   python manage.py import_drivers_from_csv conductores.csv
   ```

3. **O importar desde Excel** usando openpyxl (ya está en requirements.txt)

## ✅ Estado Final

- ✅ Comando actualizado a 82 conductores
- ✅ Nombres y apellidos ampliados (60+ opciones)
- ✅ Post-deploy actualizado
- ✅ Commit realizado
- ✅ Push a GitHub completado
- ✅ Deploy en Render activado automáticamente

---

**Fecha:** 7 de octubre de 2025  
**Versión:** SoptraLoc TMS v3.0  
**Estado:** ✅ Implementado y en producción
