# 🗄️ AUDITORÍA - FASE 2: MODELOS Y BASE DE DATOS

**Fecha**: 2025-01-10  
**Auditor**: GitHub Copilot  
**Alcance**: Análisis exhaustivo de los 27 modelos, relaciones, índices, validaciones y diseño de esquema

---

## 📊 RESUMEN EJECUTIVO

### Estadísticas de Modelos
- **Total modelos**: 27 modelos (3 heredan de `BaseModel`, 24 modelos de negocio)
- **Campos totales**: ~450+ campos en todo el sistema
- **ForeignKeys**: 60+ relaciones
- **ManyToMany**: 0 (no se detectaron)
- **Índices compuestos**: 12 índices explícitos
- **Modelos más complejos**:
  - `Container`: 83 campos 🔴 **GOD OBJECT**
  - `Location`: 28 campos
  - `Warehouse`: 27 campos

### Veredicto General de Base de Datos
🟡 **MODERADO/DEFICIENTE** - Diseño funcional con **graves problemas de normalización**, **índices faltantes críticos**, y **modelo Container sobrecargado**.

---

## 1️⃣ ANÁLISIS DETALLADO POR MODELO

### 🔴 **MODELO CRÍTICO: `Container` (83 campos)**

#### Problemas Identificados

**1. Violación MASIVA del Principio de Responsabilidad Única**

```python
class Container(BaseModel):
    # ❌ MEZCLA 8 DOMINIOS DIFERENTES:
    # 1. Identificación física (container_number, type, seal)
    # 2. Información de embarque (vessel, eta, cargo_description)
    # 3. Aduanas y liberación (release_date, customs_document)
    # 4. Programación (scheduled_date, scheduled_time)
    # 5. Ubicación actual (current_location, current_position)
    # 6. Asignación de conductor (conductor_asignado)
    # 7. Tracking de tiempos (tiempo_asignacion, tiempo_inicio_ruta, ...)
    # 8. Información comercial (owner_company, client, demurrage_date)
```

**Impacto**:
- 🔴 Migraciones extremadamente frágiles
- 🔴 Queries con 20+ joins innecesarios
- 🔴 Imposible testear unitariamente
- 🔴 Violación de 1NF, 2NF, 3NF (Formas Normales)

---

**2. Campos redundantes/calculables**

```python
# ❌ REDUNDANCIA:
weight_empty = models.DecimalField(...)        # Peso vacío
weight_loaded = models.DecimalField(...)       # Peso cargado
cargo_weight = models.DecimalField(...)        # ← weight_loaded - weight_empty?
total_weight = models.DecimalField(...)        # ← Duplica weight_loaded?

# ❌ CALCULABLES:
calculated_days = models.IntegerField(...)     # ← Se puede calcular con release_date vs now()
duracion_total = models.IntegerField(...)      # ← Se puede calcular con timestamps
duracion_ruta = models.IntegerField(...)       # ← Idem
```

**Solución**: Usar `@property` o campos calculados en tiempo real.

---

**3. Máquina de estados implementada incorrectamente**

```python
# ❌ PROBLEMA: Lógica de estado en el modelo
ALLOWED_TRANSITIONS = {
    'POR_ARRIBAR': ['EN_SECUENCIA', 'DESCARGADO', 'LIBERADO', 'PROGRAMADO'],
    # ← Permitir saltar 4 estados es un code smell
    ...
}

def can_transition_to(self, current_status, new_status):
    # ❌ Lógica de negocio en el modelo (debería estar en servicio)
    ...
```

**Problemas**:
- ⚠️ Transiciones permiten saltar estados intermedios
- ⚠️ No hay auditoría de cambios de estado
- ⚠️ Falta validación de precondiciones

**Solución recomendada**:
```python
# ✅ Usar biblioteca django-fsm o crear StateService
from django_fsm import FSMField, transition

class Container(BaseModel):
    status = FSMField(default='POR_ARRIBAR', protected=True)
    
    @transition(field=status, source='POR_ARRIBAR', target='LIBERADO')
    def liberar(self, user, release_date):
        """Liberar contenedor para despacho"""
        self.release_date = release_date
        self.liberado_por = user
        self.save()
```

---

**4. Múltiples campos de fechas sin timezone awareness explícito**

```python
# ⚠️ RIESGO: Campos sin timezone
release_date = models.DateField(...)           # ← ¿UTC? ¿Local?
release_time = models.TimeField(...)           # ← Separado de la fecha
scheduled_date = models.DateField(...)
scheduled_time = models.TimeField(...)         # ← Patrón antinatural
```

**Solución**:
```python
# ✅ MEJOR: Usar DateTimeField con timezone
release_datetime = models.DateTimeField(null=True, blank=True)
scheduled_datetime = models.DateTimeField(null=True, blank=True)
```

---

**5. Campos legacy y duplicados**

```python
# ❌ CONFUSIÓN:
current_location = ForeignKey(Location, ...)    # Ubicación como FK
cd_location = CharField(max_length=100, ...)    # Ubicación como string ←
current_position = CharField(max_length=30, ...) # OTRO campo de ubicación ←

# ❌ DUPLICACIÓN:
status = CharField(...)                         # Estado general
position_status = CharField(...)                # Estado de posición ← ¿Necesario?
```

**Refactorización URGENTE requerida**:
```python
# ✅ SOLUCIÓN: Un solo campo unificado
location = ForeignKey(Location, ...)  # FK única
# Eliminar: cd_location, current_position, position_status
```

---

### 🔴 **REFACTORIZACIÓN CRÍTICA RECOMENDADA: Dividir `Container`**

```python
# ✅ PROPUESTA: Normalizar en 6 modelos cohesivos

# 1. DATOS FÍSICOS DEL CONTENEDOR
class Container(BaseModel):
    """Identificación física del contenedor"""
    container_number = models.CharField(max_length=50, unique=True, db_index=True)
    container_type = models.CharField(max_length=20, choices=CONTAINER_TYPES)
    seal_number = models.CharField(max_length=50, blank=True)
    weight_empty = models.DecimalField(max_digits=10, decimal_places=2)
    max_weight = models.DecimalField(max_digits=10, decimal_places=2)
    owner_company = models.ForeignKey(Company, ...)
    
    class Meta:
        indexes = [
            models.Index(fields=['container_number']),
            models.Index(fields=['owner_company', 'container_type']),
        ]

# 2. INFORMACIÓN DE EMBARQUE
class ContainerShipment(BaseModel):
    """Datos de arribo y embarque"""
    container = models.OneToOneField(Container, on_delete=models.CASCADE)
    vessel = models.ForeignKey(Vessel, ...)
    port = models.ForeignKey(Location, ...)
    eta = models.DateField()
    cargo_description = models.TextField()
    cargo_weight = models.DecimalField(max_digits=10, decimal_places=2)
    terminal = models.ForeignKey(Location, ...)
    
    class Meta:
        indexes = [
            models.Index(fields=['eta', 'port']),
        ]

# 3. ADUANAS Y LIBERACIÓN
class ContainerCustoms(BaseModel):
    """Información aduanera"""
    container = models.OneToOneField(Container, on_delete=models.CASCADE)
    customs_document = models.CharField(max_length=100)
    release_datetime = models.DateTimeField(null=True, blank=True)
    agency = models.ForeignKey(Agency, ...)
    shipping_line = models.ForeignKey(ShippingLine, ...)
    free_days = models.IntegerField(default=0)
    demurrage_datetime = models.DateTimeField(null=True, blank=True)

# 4. PROGRAMACIÓN Y ASIGNACIÓN
class ContainerSchedule(BaseModel):
    """Programación operativa"""
    container = models.OneToOneField(Container, on_delete=models.CASCADE)
    scheduled_datetime = models.DateTimeField()
    assigned_driver = models.ForeignKey('drivers.Driver', ...)
    origin = models.ForeignKey(Location, related_name='schedules_from')
    destination = models.ForeignKey(Location, related_name='schedules_to')
    estimated_duration = models.IntegerField()  # minutos
    
    class Meta:
        indexes = [
            models.Index(fields=['scheduled_datetime', 'assigned_driver']),
            models.Index(fields=['destination']),
        ]

# 5. ESTADO Y TRACKING
class ContainerState(BaseModel):
    """Máquina de estados con auditoría"""
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='states')
    status = models.CharField(max_length=30, choices=CONTAINER_STATUS)
    location = models.ForeignKey(Location, ...)
    timestamp = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, ...)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container', '-timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]
    
    @property
    def current_status(self):
        """Obtiene el estado actual del contenedor"""
        return self.objects.filter(container=self.container).latest('timestamp')

# 6. TRACKING DE TIEMPOS (Ya existe parcialmente en Assignment)
class ContainerTimeline(BaseModel):
    """Tiempos operativos reales"""
    container = models.OneToOneField(Container, on_delete=models.CASCADE)
    tiempo_asignacion = models.DateTimeField(null=True)
    tiempo_inicio_ruta = models.DateTimeField(null=True)
    tiempo_llegada = models.DateTimeField(null=True)
    tiempo_descarga = models.DateTimeField(null=True)
    tiempo_finalizacion = models.DateTimeField(null=True)
    
    @property
    def duracion_total(self):
        """Calcula duración total (no guardar en DB)"""
        if self.tiempo_asignacion and self.tiempo_finalizacion:
            return (self.tiempo_finalizacion - self.tiempo_asignacion).total_seconds() / 60
        return None
```

**Beneficios**:
- ✅ Modelos cohesivos y enfocados
- ✅ Queries más eficientes (menos joins)
- ✅ Migraciones más simples
- ✅ Testing unitario posible
- ✅ Cumple 3NF

---

## 2️⃣ ANÁLISIS DE OTROS MODELOS CLAVE

### 🟡 **MODELO: `Location` (28 campos)**

**Problemas**:

```python
# ⚠️ UBICACIÓN INCORRECTA (debería estar en core/)
class Location(models.Model):
    # apps/drivers/models.py ← ❌ UBICACIÓN EQUIVOCADA
    ...
    
    class Meta:
        db_table = 'core_location'  # ← ¡Referencia a otra app!
        # INCONSISTENCIA: Modelo en drivers/ apunta a tabla core_*
```

**Impacto**:
- 🟡 Violación de arquitectura limpia
- 🟡 Dependencia circular latente
- 🟡 Confusión en imports

**Solución**:
```python
# ✅ MOVER A: apps/core/models.py
# Y actualizar imports en todas las apps
```

---

### 🟢 **MODELO: `TimeMatrix` - BIEN DISEÑADO**

```python
class TimeMatrix(models.Model):
    """Matriz de tiempos entre ubicaciones"""
    from_location = ForeignKey(Location, ...)
    to_location = ForeignKey(Location, ...)
    
    # Tiempos configurables
    travel_time = IntegerField(...)
    loading_time = IntegerField(...)
    unloading_time = IntegerField(...)
    
    # Aprendizaje histórico
    avg_travel_time = FloatField(null=True)
    total_trips = IntegerField(default=0)
    
    class Meta:
        unique_together = ['from_location', 'to_location']  # ✅ CORRECTO
    
    def update_historical_data(self, actual_minutes):
        """✅ Método de negocio bien ubicado"""
        smoothing = 0.6
        self.avg_travel_time = (self.avg_travel_time * smoothing) + (actual_minutes * (1 - smoothing))
        self.total_trips += 1
        self.save()
```

**✅ BUENAS PRÁCTICAS**:
- Constraint `unique_together` correcto
- Lógica de aprendizaje encapsulada
- Campos nullable apropiados

---

### 🟡 **MODELO: `Driver` (26 campos)**

**Problemas menores**:

```python
# ⚠️ REDUNDANCIA:
contenedor_asignado = ForeignKey('containers.Container', ...)  # ← FK
# Pero también existe Assignment.container + Assignment.driver
# ¿Cuál es la fuente de verdad?
```

**Riesgo**: Inconsistencia de datos.

**Solución**:
```python
# ✅ OPCIÓN 1: Eliminar contenedor_asignado
# Usar siempre: Assignment.objects.filter(driver=driver, estado='EN_CURSO')

# ✅ OPCIÓN 2: Hacer contenedor_asignado calculado
@property
def contenedor_asignado(self):
    assignment = self.assignment_set.filter(estado='EN_CURSO').first()
    return assignment.container if assignment else None
```

---

### 🟢 **MODELO: `Assignment` - BIEN DISEÑADO**

```python
class Assignment(models.Model):
    container = ForeignKey('containers.Container', ...)
    driver = ForeignKey(Driver, ...)
    
    fecha_programada = DateTimeField()
    fecha_inicio = DateTimeField(null=True)
    fecha_completada = DateTimeField(null=True)
    
    # ✅ Tiempos estimados vs reales
    tiempo_estimado = IntegerField(default=120)
    tiempo_real = IntegerField(null=True)
    
    # ✅ Desglose de tiempos
    ruta_minutos_real = IntegerField(null=True)
    descarga_minutos_real = IntegerField(null=True)
    
    # ✅ Ubicaciones con FK + fallback legacy
    origen = ForeignKey(Location, ...)
    destino = ForeignKey(Location, ...)
    origen_legacy = CharField(max_length=100, blank=True)
    destino_legacy = CharField(max_length=100, blank=True)
```

**✅ BUENAS PRÁCTICAS**:
- Separación de tiempos estimados/reales
- Campos legacy para migración gradual
- Estado con choices correctos

---

## 3️⃣ ANÁLISIS DE RELACIONES (ForeignKey/ManyToMany)

### Total de ForeignKeys: **60+**

#### Relaciones con mayor fan-out:

```
Container → tiene 10+ ForeignKeys:
  ├── owner_company (Company)
  ├── client (Company)
  ├── current_location (Location)
  ├── terminal (Location)
  ├── current_vehicle (Vehicle)
  ├── vessel (Vessel)
  ├── agency (Agency)
  ├── shipping_line (ShippingLine)
  ├── conductor_asignado (Driver)
  └── position_updated_by (User)
```

**❌ PROBLEMA**: Modelo con 10+ FKs indica **falta de normalización**.

---

### 🔴 **AUSENCIA DE ManyToMany**

**Observación**: NO se detectó ninguna relación `ManyToManyField`.

**Pregunta**: ¿Hay relaciones N:M que deberían modelarse?

**Candidatos**:
1. `Container` ↔ `Document`: Un contenedor tiene múltiples documentos
   - Actual: `ContainerDocument` con FK → ✅ Correcto (explícito)
   
2. `Driver` ↔ `Location` (ubicaciones favoritas/frecuentes)
   - Actual: No existe → 🤔 ¿Podría ser útil?

3. `Route` ↔ `Container` (rutas compartidas)
   - Actual: `RouteStop` con FK → ✅ Correcto

**Veredicto**: 🟢 No se requieren M2M adicionales.

---

## 4️⃣ ANÁLISIS DE ÍNDICES DE BASE DE DATOS

### Índices Explícitos Detectados

```python
# ✅ Container - 6 índices
indexes = [
    models.Index(fields=['status']),
    models.Index(fields=['scheduled_date']),
    models.Index(fields=['conductor_asignado']),
    models.Index(fields=['container_number']),
    models.Index(fields=['status', 'scheduled_date']),      # Compuesto
    models.Index(fields=['conductor_asignado', 'status']),  # Compuesto
]

# ✅ LocationPair - 1 índice
indexes = [
    models.Index(fields=['origin', 'destination']),
]

# ✅ Route - 3 índices
indexes = [
    models.Index(fields=['origin', 'destination', 'departure_time']),
    models.Index(fields=['day_of_week', 'hour_of_day']),
]

# ✅ TrafficAlert - 3 índices
indexes = [
    models.Index(fields=['driver', '-created_at']),
    models.Index(fields=['assignment', '-created_at']),
    models.Index(fields=['is_active', '-created_at']),
]
```

**Total índices compuestos**: 8  
**Total índices simples**: 4

---

### 🔴 **ÍNDICES FALTANTES CRÍTICOS**

```python
# ❌ FALTA: Container - Búsquedas frecuentes sin índice
# Queries comunes:
# - Container.objects.filter(release_date__lte=today, status='LIBERADO')
# - Container.objects.filter(agency=X, shipping_line=Y)

# ✅ AGREGAR:
class Container:
    class Meta:
        indexes = [
            # ... existentes ...
            models.Index(fields=['release_date', 'status']),       # ← CRÍTICO
            models.Index(fields=['eta']),                          # ← Consultas de arribos
            models.Index(fields=['agency', 'shipping_line']),      # ← Filtros frecuentes
            models.Index(fields=['cd_location', 'scheduled_date']), # ← Dashboard CD
            models.Index(fields=['demurrage_date']),               # ← Alertas
        ]

# ❌ FALTA: Assignment - Búsquedas por estado y fecha
class Assignment:
    class Meta:
        indexes = [
            models.Index(fields=['estado', 'fecha_programada']),   # ← CRÍTICO
            models.Index(fields=['driver', 'estado']),             # ← Dashboard conductor
            models.Index(fields=['container', 'fecha_asignacion']), # ← Historial
        ]

# ❌ FALTA: Location - Búsquedas geoespaciales
class Location:
    class Meta:
        indexes = [
            models.Index(fields=['code']),                         # ← Búsquedas por código
            models.Index(fields=['city', 'region']),               # ← Filtros geográficos
            # Considerar: GiSTIndex para latitude/longitude con PostGIS
        ]

# ❌ FALTA: TimeMatrix - Lookups bidireccionales
class TimeMatrix:
    class Meta:
        indexes = [
            models.Index(fields=['to_location', 'from_location']),  # ← Ruta inversa
            models.Index(fields=['total_trips']),                   # ← Ranking de rutas
        ]
```

**Impacto**:
- 🔴 Queries lentas en tablas con +10k registros
- 🔴 Full table scans en filtros de dashboard
- 🔴 N+1 queries sin optimización

---

## 5️⃣ ANÁLISIS DE CONSTRAINTS Y VALIDACIONES

### ✅ **Constraints de Unicidad Correctos**

```python
# ✅ Container
container_number = models.CharField(max_length=50, unique=True)

# ✅ Location
name = models.CharField(max_length=200, unique=True)
code = models.CharField(max_length=20, unique=True)

# ✅ TimeMatrix
class Meta:
    unique_together = ['from_location', 'to_location']

# ✅ LocationPair
class Meta:
    unique_together = ['origin', 'destination']
```

---

### 🔴 **Validaciones FALTANTES**

```python
# ❌ Container - Sin validación de pesos
class Container:
    weight_empty = DecimalField(...)
    max_weight = DecimalField(...)
    cargo_weight = DecimalField(...)
    
    # ✅ AGREGAR:
    def clean(self):
        if self.weight_empty and self.max_weight:
            if self.weight_empty >= self.max_weight:
                raise ValidationError("Peso vacío no puede ser >= peso máximo")
        
        if self.cargo_weight and self.max_weight:
            if self.cargo_weight > self.max_weight:
                raise ValidationError("Carga excede peso máximo")

# ❌ Assignment - Sin validación de fechas lógicas
class Assignment:
    fecha_programada = DateTimeField()
    fecha_inicio = DateTimeField(null=True)
    fecha_completada = DateTimeField(null=True)
    
    # ✅ AGREGAR:
    def clean(self):
        if self.fecha_inicio and self.fecha_programada:
            if self.fecha_inicio < self.fecha_programada:
                raise ValidationError("Inicio no puede ser antes de fecha programada")
        
        if self.fecha_completada and self.fecha_inicio:
            if self.fecha_completada < self.fecha_inicio:
                raise ValidationError("Completada no puede ser antes de inicio")

# ❌ TimeMatrix - Sin validación de tiempos negativos
class TimeMatrix:
    travel_time = IntegerField(...)  # ← Sin validators
    
    # ✅ AGREGAR:
    travel_time = IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1440)]  # 1 min a 24h
    )
```

---

## 6️⃣ ANÁLISIS DE MIGRACIONES

### Estado de Migraciones

```
core:       2 migraciones
containers: 10 migraciones  ← Múltiples cambios de schema
drivers:    16 migraciones  ← ⚠️ ALTO (indica refactorizaciones frecuentes)
routing:    4 migraciones
warehouses: 2 migraciones
```

**Total**: 34 migraciones

---

### 🔴 **PROBLEMA: Exceso de migraciones en `drivers`**

**Análisis**:
```bash
drivers/migrations/
├── 0001_initial.py
├── 0002_...
├── 0003_...
...
├── 0016_...  ← 16 migraciones indica diseño inestable
```

**Causas**:
- ⚠️ Cambios frecuentes en modelos `Driver`, `Assignment`, `Location`
- ⚠️ Añadir/eliminar campos regularmente
- ⚠️ Posibles errores de planificación de schema

**Recomendación**:
```bash
# ✅ Consolidar migraciones (solo en desarrollo, NO en producción):
python manage.py migrate drivers zero  # Rollback
python manage.py migrate
python manage.py makemigrations --merge
python manage.py squashmigrations drivers 0001 0016
```

---

### 🟡 **Detección de Migraciones Conflictivas**

```bash
# Verificar dependencias circulares
python manage.py showmigrations --plan | grep "^\[ \]"
```

**Riesgo**: Dependencias entre apps mal ordenadas.

---

## 7️⃣ ANÁLISIS DE PERFORMANCE

### Queries Lentos Potenciales (Sin select_related/prefetch_related)

```python
# ❌ ANTIPATRÓN: N+1 Queries

# Ejemplo 1: Dashboard de contenedores
containers = Container.objects.filter(status='PROGRAMADO')
for container in containers:
    print(container.vessel.name)             # ← Query por iteración
    print(container.conductor_asignado.nombre) # ← Query por iteración
    print(container.current_location.name)    # ← Query por iteración
# Total: 1 + (N * 3) queries

# ✅ SOLUCIÓN:
containers = Container.objects.filter(status='PROGRAMADO').select_related(
    'vessel',
    'conductor_asignado',
    'current_location',
    'owner_company',
    'terminal'
)
# Total: 1 query con JOINs
```

---

```python
# ❌ ANTIPATRÓN: Query sin filtros eficientes

# Ejemplo 2: Búsqueda de contenedores atrasados
today = timezone.now().date()
containers = Container.objects.all()  # ← Full table scan
atrasados = [c for c in containers if c.release_date and c.release_date < today and c.status == 'LIBERADO']

# ✅ SOLUCIÓN:
atrasados = Container.objects.filter(
    release_date__lt=today,
    status='LIBERADO'
).select_related('conductor_asignado')
```

---

### 🔴 **FALTA: Paginación en Listas Grandes**

```python
# ❌ PROBLEMA: Cargar todos los registros
# apps/containers/views.py
def lista_contenedores(request):
    containers = Container.objects.all()  # ← Si hay 50k registros...
    return render(request, 'lista.html', {'containers': containers})

# ✅ SOLUCIÓN 1: Paginación Django
from django.core.paginator import Paginator

def lista_contenedores(request):
    containers = Container.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(containers, 50)  # 50 por página
    page = request.GET.get('page')
    containers_page = paginator.get_page(page)
    return render(request, 'lista.html', {'containers': containers_page})

# ✅ SOLUCIÓN 2: API con DRF Pagination
from rest_framework.pagination import PageNumberPagination

class ContainerPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 1000

class ContainerViewSet(viewsets.ModelViewSet):
    pagination_class = ContainerPagination
```

---

## 8️⃣ ANÁLISIS DE TIPOS DE DATOS

### 🟢 **Uso Correcto de Tipos**

```python
# ✅ UUIDs para IDs (evita enumeración)
class BaseModel:
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

# ✅ DecimalField para dinero/pesos
weight = models.DecimalField(max_digits=10, decimal_places=2)

# ✅ Choices para estados finitos
status = models.CharField(max_length=30, choices=STATUS_CHOICES)
```

---

### 🟡 **Mejoras Posibles**

```python
# ⚠️ MEJORABLE: CharField para emails
email = models.CharField(max_length=200)  # ← Sin validación

# ✅ MEJOR:
email = models.EmailField(max_length=200)  # ← Valida formato

# ⚠️ MEJORABLE: CharField para URLs
contact_info = models.CharField(max_length=500)  # ← Puede contener URL

# ✅ MEJOR:
contact_email = models.EmailField(blank=True)
contact_phone = models.CharField(max_length=20, blank=True)
contact_url = models.URLField(blank=True)

# ⚠️ MEJORABLE: Teléfonos sin formato estandarizado
telefono = models.CharField(max_length=15)

# ✅ MEJOR: Usar django-phonenumber-field
from phonenumber_field.modelfields import PhoneNumberField
telefono = PhoneNumberField(region='CL')  # ← Valida formato chileno
```

---

## 9️⃣ PUNTUACIÓN POR CATEGORÍA

| Categoría                      | Puntuación | Comentario                                    |
|--------------------------------|------------|-----------------------------------------------|
| **Normalización**              | 3/10       | Container viola 1NF/2NF/3NF                   |
| **Índices**                    | 5/10       | Existen, pero faltan críticos                 |
| **Relaciones**                 | 7/10       | FKs correctos, sin M2M innecesarios           |
| **Validaciones**               | 4/10       | Faltan validaciones de negocio                |
| **Constraints**                | 7/10       | Unique correctos, faltan CHECK constraints    |
| **Migraciones**                | 5/10       | Funcionales, pero exceso en `drivers`         |
| **Performance**                | 4/10       | Sin paginación, N+1 queries latentes          |
| **Tipos de datos**             | 8/10       | Correctos, pequeñas mejoras posibles          |

**PROMEDIO**: **5.4/10** 🟡 **NECESITA REFACTORIZACIÓN IMPORTANTE**

---

## 🔟 RECOMENDACIONES PRIORIZADAS

### 🔴 **CRÍTICO (Hacer AHORA)**

1. **Dividir modelo `Container` en 6 modelos cohesivos**
   - Crear `ContainerShipment`, `ContainerCustoms`, `ContainerSchedule`, `ContainerState`, `ContainerTimeline`
   - Migración gradual con campos deprecados

2. **Agregar índices críticos faltantes**
   ```python
   # Container
   models.Index(fields=['release_date', 'status']),
   models.Index(fields=['eta']),
   models.Index(fields=['demurrage_date']),
   
   # Assignment
   models.Index(fields=['estado', 'fecha_programada']),
   models.Index(fields=['driver', 'estado']),
   ```

3. **Mover `Location` a `apps/core/models.py`**
   - Actualizar imports en todas las apps
   - Renombrar `db_table` a `locations` (no `core_location`)

---

### 🟡 **IMPORTANTE (Próximas 2-4 semanas)**

4. **Implementar validaciones de modelo**
   ```python
   # Container.clean()
   # Assignment.clean()
   # TimeMatrix con validators
   ```

5. **Consolidar migraciones de `drivers`**
   ```bash
   python manage.py squashmigrations drivers 0001 0016
   ```

6. **Agregar paginación en todas las vistas de lista**
   ```python
   # Usar Paginator o DRF PageNumberPagination
   ```

7. **Refactorizar campos redundantes**
   ```python
   # Eliminar: current_position, cd_location (usar location FK única)
   # Eliminar: calculated_days, duracion_* (calcular con @property)
   ```

---

### 🟢 **MEJORAS (Backlog)**

8. Implementar máquina de estados con `django-fsm`
9. Agregar auditoría de cambios con `django-auditlog`
10. Considerar PostGIS para Location (búsquedas geoespaciales)
11. Implementar soft delete en vez de `is_active` (preservar historial)

---

## 1️⃣1️⃣ DIAGRAMA ENTIDAD-RELACIÓN SIMPLIFICADO

```
┌─────────────────┐       ┌─────────────────┐
│   Container     │──────┤│   Vessel        │
│  (83 campos)    │       │                 │
└────────┬────────┘       └─────────────────┘
         │
         │ 1:1
         ├────────────────┐
         │                │
┌────────▼────────┐  ┌────▼──────────────┐
│  Assignment     │  │ ContainerState     │
│  (22 campos)    │  │ (historial)        │
└────────┬────────┘  └────────────────────┘
         │
         │ N:1
         │
┌────────▼────────┐       ┌─────────────────┐
│   Driver        │──────┤│   Location      │
│  (26 campos)    │       │  (28 campos)    │
└─────────────────┘       └────────┬────────┘
                                   │
                                   │ N:M (via TimeMatrix)
                                   │
                          ┌────────▼────────┐
                          │   TimeMatrix    │
                          │  (tiempos)      │
                          └─────────────────┘

PROBLEMAS:
❌ Container es God Object (83 campos)
❌ Location en app incorrecta (drivers/ en vez de core/)
❌ Relación Driver ↔ Container duplicada (FK + Assignment)
```

---

## 1️⃣2️⃣ PRÓXIMOS PASOS (FASE 3)

Con el análisis de modelos completo, ahora procederé a:

1. ✅ **FASE 1 COMPLETADA**: Arquitectura y dependencias
2. ✅ **FASE 2 COMPLETADA**: Modelos y base de datos
3. ⏳ **FASE 3**: Lógica de negocio y servicios
4. ⏳ **FASE 4**: Views y controladores
5. ⏳ **FASE 5**: APIs y serializers
6. ⏳ **FASE 6**: Seguridad profunda
7. ⏳ **FASE 7**: Performance y optimización
8. ⏳ **FASE 8**: Tests y cobertura
9. ⏳ **FASE 9**: Documentación
10. ⏳ **FASE 10**: Deployment e integración

---

**FIN DE FASE 2 - MODELOS Y BASE DE DATOS**  
**Próximo paso**: Análisis exhaustivo de la lógica de negocio y servicios.