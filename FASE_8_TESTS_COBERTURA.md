# 🧪 AUDITORÍA - FASE 8: TESTS Y COBERTURA

**Fecha**: 2025-10-10  
**Auditor**: GitHub Copilot  
**Alcance**: Análisis exhaustivo de testing: tests unitarios, integración, cobertura, tests de seguridad, tests de ML, tests de APIs, fixtures, mocks, CI/CD testing

---

## 📊 RESUMEN EJECUTIVO

### Estadísticas de Tests
- **Archivos de tests**: 6 archivos de test
- **Líneas de código de tests**: ~818 líneas
- **Test cases identificados**: 13 test methods
- **Apps con tests**:
  - ✅ `containers`: 2 archivos (test_assignment_flow.py, test_excel_importers.py)
  - ✅ `drivers`: 1 archivo (test_time_learning.py)
  - ✅ `routing`: 1 archivo (test_routes.py)
  - ✅ `core`: 2 archivos (test_dashboard.py, test_core_api.py)
  - ❌ `warehouses`: Sin tests
- **Coverage estimado**: ~30-40%
- **Tests de ML**: ✅ 3 tests (time prediction, learning)
- **Tests de API**: ✅ 5+ tests (DRF TestCase)
- **Tests de integración**: ✅ 2 tests (flujo completo)
- **Tests de seguridad**: ❌ No existe
- **Mocks/Patches**: ❌ Sin uso de mocks
- **Fixtures**: ❌ Sin fixtures reutilizables

### Veredicto General de Testing
🟡 **MODERADO/BAJO** - Hay tests básicos funcionales para casos de uso críticos (assignment flow, ML learning, imports Excel), **PERO falta cobertura exhaustiva (60-70% de código sin tests), no hay tests de seguridad, faltan tests de edge cases, sin mocks para APIs externas (Mapbox), sin fixtures organizadas**.

---

## 1️⃣ ANÁLISIS DE COBERTURA

### 🟡 **PROBLEMA: Cobertura baja estimada (~30-40%)**

```
Archivos de test: 6
Líneas totales de código: ~16,543 líneas
Líneas de tests: ~818 líneas
Ratio: ~5% (debería ser 30-50%)
```

**Áreas sin tests**:
- 🔴 **ViewSets**: ContainerViewSet, DriverViewSet, etc. (51 views, solo 3-4 testeados)
- 🔴 **Services**: 8 servicios, solo 1-2 testeados parcialmente
- 🔴 **Serializers**: 20+ serializers sin tests de validación
- 🔴 **Models**: 27 modelos, solo tests indirectos
- 🔴 **Tasks**: 7 Celery tasks sin tests
- 🔴 **Middleware**: Sin tests
- 🔴 **Permissions**: Sin tests de autorización
- 🔴 **Management commands**: 10+ commands sin tests

---

### 🟢 **FORTALEZA: Tests funcionales críticos**

```python
# ✅ apps/containers/tests/test_assignment_flow.py

class ContainerAssignmentFlowTests(APITestCase):
    """✅ Tests de integración del flujo completo"""
    
    def test_assign_driver_via_api_sets_status_assigned(self):
        """✅ Asignación de conductor cambia status a ASIGNADO"""
        url = reverse("container-assign-driver", args=[self.container.id])
        response = self.client.post(url, {"driver_id": self.driver.id}, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.container.refresh_from_db()
        self.assertEqual(self.container.status, "ASIGNADO")
    
    def test_mark_arrived_releases_driver_and_completes_assignment(self):
        """✅ Llegada libera conductor y completa asignación"""
        ...
    
    def test_demurrage_alert_triggers_and_resolves_through_return_flow(self):
        """✅ Flujo completo con alerta de demora"""
        ...
```

**Fortalezas**:
- ✅ Tests de integración del flujo principal (assign → start → arrive → complete)
- ✅ Tests con APITestCase (simula requests reales)
- ✅ Verifica cambios de estado en base de datos

---

### 🟢 **FORTALEZA: Tests de ML (time prediction)**

```python
# ✅ apps/drivers/tests/test_time_learning.py

class AssignmentLearningTestCase(TestCase):
    """✅ Tests del sistema de aprendizaje de tiempos"""
    
    def test_record_actual_times_updates_matrix(self):
        """✅ Grabación de tiempos reales actualiza matriz"""
        assignment.record_actual_times(total_minutes=180, route_minutes=120, unloading_minutes=60)
        
        self.time_matrix.refresh_from_db()
        self.assertEqual(assignment.tiempo_real, 180)
        self.assertAlmostEqual(self.time_matrix.avg_travel_time, 120, delta=1)
    
    def test_predictor_uses_matrix_when_no_history(self):
        """✅ Predictor usa matriz cuando no hay historial"""
        prediction = predictor.predict(origin, destination, ...)
        
        expected = self.time_matrix.get_total_time()
        self.assertEqual(prediction.minutes, expected)
    
    def test_predictor_learns_from_history(self):
        """✅ Predictor aprende del historial de assignments"""
        ...
```

**Fortalezas**:
- ✅ Tests del algoritmo de ML (TimePredictionML)
- ✅ Tests de actualización de TimeMatrix
- ✅ Tests de fallback (matriz vs historial)

---

## 2️⃣ ANÁLISIS DE TESTS FALTANTES

### 🔴 **CRÍTICO: Sin tests de ViewSets principales**

```python
# ❌ FALTA: apps/containers/tests/test_viewsets.py

# Debería existir:
class ContainerViewSetTests(APITestCase):
    def test_list_containers_returns_paginated_results(self):
        """✅ Listado paginado de contenedores"""
        ...
    
    def test_filter_by_status_returns_correct_containers(self):
        """✅ Filtro por status funciona"""
        ...
    
    def test_search_by_container_number_finds_exact_match(self):
        """✅ Búsqueda por número"""
        ...
    
    def test_retrieve_container_includes_nested_relations(self):
        """✅ Detalle incluye relaciones"""
        ...
    
    def test_create_container_requires_authentication(self):
        """✅ Requiere autenticación"""
        ...
    
    def test_create_container_validates_required_fields(self):
        """✅ Valida campos requeridos"""
        ...
    
    def test_update_container_status_triggers_workflow(self):
        """✅ Cambio de status activa workflow"""
        ...
    
    def test_delete_container_soft_deletes(self):
        """✅ Eliminación es soft delete"""
        ...
```

---

### 🔴 **CRÍTICO: Sin tests de serializers**

```python
# ❌ FALTA: apps/containers/tests/test_serializers.py

class ContainerSerializerTests(TestCase):
    def test_serializer_includes_nested_company(self):
        """✅ Incluye owner_company anidado"""
        container = Container.objects.create(...)
        serializer = ContainerSerializer(container)
        
        self.assertIn('owner_company', serializer.data)
        self.assertEqual(serializer.data['owner_company']['name'], 'Company A')
    
    def test_serializer_read_only_fields_cannot_be_updated(self):
        """✅ Campos read_only no se pueden actualizar"""
        data = {'id': uuid.uuid4(), 'created_at': timezone.now()}
        serializer = ContainerSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
    
    def test_container_movement_validates_required_to_location(self):
        """✅ Valida ubicación destino en movimiento"""
        data = {'movement_type': 'transfer_warehouse', 'from_location': loc1}
        serializer = ContainerMovementCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('to_location', serializer.errors)
```

---

### 🔴 **CRÍTICO: Sin tests de seguridad**

```python
# ❌ FALTA: apps/core/tests/test_security.py

class SecurityTests(APITestCase):
    def test_unauthenticated_request_returns_401(self):
        """✅ Request sin autenticación retorna 401"""
        self.client.logout()
        response = self.client.get('/api/v1/containers/')
        
        self.assertEqual(response.status_code, 401)
    
    def test_rate_limiting_blocks_excessive_requests(self):
        """✅ Rate limiting bloquea requests excesivos"""
        for i in range(10):
            response = self.client.post('/api/v1/auth/token/', {...})
        
        self.assertEqual(response.status_code, 429)  # Too Many Requests
    
    def test_csrf_protected_endpoint_requires_token(self):
        """✅ Endpoint protegido requiere CSRF token"""
        ...
    
    def test_user_cannot_access_other_company_data(self):
        """✅ Usuario no puede ver datos de otra empresa"""
        user_a = self.create_user(company=company_a)
        container_b = Container.objects.create(owner_company=company_b)
        
        self.client.force_authenticate(user_a)
        response = self.client.get(f'/api/v1/containers/{container_b.id}/')
        
        self.assertEqual(response.status_code, 404)  # Not found (no 403 para evitar info leak)
```

---

### 🔴 **CRÍTICO: Sin tests de Celery tasks**

```python
# ❌ FALTA: apps/containers/tests/test_tasks.py

from unittest.mock import patch

class CeleryTasksTests(TestCase):
    @patch('apps.containers.tasks.logger')
    def test_check_containers_requiring_assignment_creates_alerts(self, mock_logger):
        """✅ Task crea alertas para contenedores sin asignar"""
        Container.objects.create(
            status='PROGRAMADO',
            scheduled_date=timezone.localdate(),
            conductor_asignado=None
        )
        
        check_containers_requiring_assignment()
        
        self.assertEqual(Alert.objects.filter(tipo='CONTENEDOR_SIN_ASIGNAR').count(), 1)
        mock_logger.info.assert_called()
    
    def test_cleanup_old_alerts_deletes_inactive_alerts(self):
        """✅ Task elimina alertas antiguas"""
        old_alert = Alert.objects.create(
            tipo='TEST',
            is_active=False,
            created_at=timezone.now() - timedelta(days=60)
        )
        
        cleanup_old_alerts()
        
        self.assertFalse(Alert.objects.filter(id=old_alert.id).exists())
```

---

### 🔴 **CRÍTICO: Sin mocks para APIs externas**

```python
# ❌ PROBLEMA: Tests hacen requests reales a Mapbox API

# ❌ MAL:
def test_mapbox_service_returns_route(self):
    service = MapboxService()
    result = service.get_travel_time(origin, destination)
    # ← Hace request REAL a Mapbox (lento, puede fallar, consume API quota)

# ✅ BIEN: Con mock
from unittest.mock import patch, MagicMock

class MapboxServiceTests(TestCase):
    @patch('apps.routing.mapbox_service.requests.get')
    def test_get_travel_time_returns_parsed_response(self, mock_get):
        """✅ Parsea respuesta de Mapbox correctamente"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'routes': [{
                'duration': 1800,  # 30 minutos
                'distance': 15000  # 15 km
            }]
        }
        mock_get.return_value = mock_response
        
        service = MapboxService()
        result = service.get_travel_time(origin, destination)
        
        self.assertEqual(result['duration_minutes'], 30)
        self.assertEqual(result['distance_km'], 15.0)
        mock_get.assert_called_once()
    
    @patch('apps.routing.mapbox_service.requests.get')
    def test_get_travel_time_handles_api_failure(self, mock_get):
        """✅ Maneja fallo de API con fallback"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        service = MapboxService()
        result = service.get_travel_time(origin, destination)
        
        self.assertEqual(result['source'], 'fallback')
        self.assertIn('warnings', result)
```

---

## 3️⃣ ANÁLISIS DE FIXTURES Y SETUP

### 🔴 **PROBLEMA: Sin fixtures reutilizables**

```python
# ⚠️ ACTUAL: setUp duplicado en cada test

class TestA(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test', ...)  # ← Duplicado
        self.location = Location.objects.create(name='CCTI', ...)  # ← Duplicado
        self.driver = Driver.objects.create(nombre='Juan', ...)  # ← Duplicado

class TestB(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test', ...)  # ← Duplicado
        self.location = Location.objects.create(name='CCTI', ...)  # ← Duplicado
        self.driver = Driver.objects.create(nombre='Juan', ...)  # ← Duplicado
```

**Solución**:
```python
# ✅ CREAR: apps/core/tests/factories.py (usando factory_boy)

import factory
from factory.django import DjangoModelFactory
from apps.core.models import Company, User
from apps.drivers.models import Driver, Location
from apps.containers.models import Container

class CompanyFactory(DjangoModelFactory):
    """Factory para Company"""
    class Meta:
        model = Company
    
    name = factory.Sequence(lambda n: f"Company {n}")
    code = factory.Sequence(lambda n: f"COMP{n:03d}")
    rut = "12.345.678-9"
    email = factory.LazyAttribute(lambda obj: f"{obj.code.lower()}@example.com")
    phone = "+56912345678"
    address = "Calle Falsa 123"

class LocationFactory(DjangoModelFactory):
    """Factory para Location"""
    class Meta:
        model = Location
    
    name = factory.Sequence(lambda n: f"Location {n}")
    code = factory.Sequence(lambda n: f"LOC{n:03d}")
    address = "Dirección de prueba"
    city = "Santiago"
    region = "Metropolitana"
    country = "Chile"

class DriverFactory(DjangoModelFactory):
    """Factory para Driver"""
    class Meta:
        model = Driver
    
    nombre = factory.Faker('name', locale='es_CL')
    rut = factory.Sequence(lambda n: f"{10000000 + n}-{n % 10}")
    telefono = factory.Faker('phone_number', locale='es_CL')
    ppu = factory.Sequence(lambda n: f"AA{n:04d}")
    tipo_conductor = "LOCALERO"
    estado = "OPERATIVO"

class ContainerFactory(DjangoModelFactory):
    """Factory para Container"""
    class Meta:
        model = Container
    
    container_number = factory.Sequence(lambda n: f"TEST{n:07d}")
    container_type = "40ft"
    status = "PROGRAMADO"
    owner_company = factory.SubFactory(CompanyFactory)
    service_type = "INDIRECTO_DEPOSITO"

# ✅ USO en tests:
class ContainerTests(TestCase):
    def test_assign_driver(self):
        # ✅ 1 línea vs 10+ líneas de setUp
        container = ContainerFactory(status='PROGRAMADO')
        driver = DriverFactory(estado='OPERATIVO')
        
        container.assign_driver(driver)
        
        self.assertEqual(container.status, 'ASIGNADO')
```

---

## 4️⃣ ANÁLISIS DE TESTS DE EDGE CASES

### 🔴 **PROBLEMA: Faltan tests de casos borde**

```python
# ❌ FALTA: Tests de validación de edge cases

class ContainerValidationTests(TestCase):
    def test_container_number_must_be_uppercase(self):
        """✅ Número de contenedor debe ser mayúsculas"""
        container = Container(container_number='mscu1234567')  # ← minúsculas
        
        with self.assertRaises(ValidationError):
            container.full_clean()
    
    def test_scheduled_date_cannot_be_in_past(self):
        """✅ Fecha programada no puede ser pasada"""
        container = Container(
            scheduled_date=timezone.localdate() - timedelta(days=1)
        )
        
        with self.assertRaises(ValidationError):
            container.full_clean()
    
    def test_cannot_assign_driver_to_finalized_container(self):
        """✅ No se puede asignar conductor a contenedor finalizado"""
        container = Container.objects.create(status='FINALIZADO', ...)
        driver = Driver.objects.create(...)
        
        with self.assertRaises(ValueError):
            container.assign_driver(driver)
    
    def test_container_with_very_long_seal_number(self):
        """✅ Seal number con longitud máxima"""
        seal = 'A' * 255  # MaxLength
        container = Container.objects.create(seal_number=seal, ...)
        
        self.assertEqual(container.seal_number, seal)
```

---

## 5️⃣ ANÁLISIS DE TESTS DE PERFORMANCE

### 🔴 **PROBLEMA: Sin tests de performance**

```python
# ❌ FALTA: apps/containers/tests/test_performance.py

from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

class PerformanceTests(TestCase):
    def test_dashboard_view_uses_select_related(self):
        """✅ Dashboard usa select_related (no N+1)"""
        # Crear 100 contenedores con relaciones
        for i in range(100):
            ContainerFactory(owner_company=CompanyFactory())
        
        with self.assertNumQueries(3):  # ← Máximo 3 queries
            response = self.client.get('/dashboard/')
            self.assertEqual(response.status_code, 200)
    
    def test_container_list_api_with_1000_items(self):
        """✅ API list maneja 1000 items sin timeout"""
        ContainerFactory.create_batch(1000)
        
        import time
        start = time.time()
        response = self.client.get('/api/v1/containers/')
        elapsed = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0)  # ← Máximo 2 segundos
    
    @override_settings(DEBUG=True)
    def test_assignment_creation_queries_count(self):
        """✅ Creación de assignment es eficiente"""
        container = ContainerFactory()
        driver = DriverFactory()
        
        with self.assertNumQueries(5):  # ← Máximo 5 queries
            Assignment.objects.create(container=container, driver=driver, ...)
```

---

## 6️⃣ PUNTUACIÓN POR CATEGORÍA

| Categoría                        | Puntuación | Comentario                                    |
|----------------------------------|------------|-----------------------------------------------|
| **Cobertura general**            | 3/10       | 🔴 ~30-40% (debería ser 80%+)                 |
| **Tests unitarios**              | 4/10       | 🟡 Algunos tests básicos, faltan muchos       |
| **Tests de integración**         | 7/10       | 🟢 Flujo principal cubierto                   |
| **Tests de API (DRF)**           | 5/10       | 🟡 Solo algunos endpoints testeados           |
| **Tests de ML**                  | 8/10       | 🟢 TimePredictionML bien testeado             |
| **Tests de seguridad**           | 1/10       | 🔴 No existen                                 |
| **Tests de performance**         | 1/10       | 🔴 No existen                                 |
| **Mocks/Fixtures**               | 2/10       | 🔴 Sin mocks, sin fixtures reutilizables      |
| **Edge cases**                   | 2/10       | 🔴 Pocos tests de validación                  |
| **CI/CD testing**                | 1/10       | 🔴 Sin GitHub Actions ni automatización       |

**PROMEDIO**: **3.4/10** 🔴 **NECESITA ATENCIÓN URGENTE**

---

## 📋 RECOMENDACIONES PRIORIZADAS

### 🔴 **CRÍTICO (Hacer HOY - Bloquea calidad)**

1. **Instalar coverage y medir cobertura real**
   ```bash
   pip install coverage
   coverage run --source='apps' manage.py test
   coverage report
   coverage html  # ← Ver reporte visual
   ```
   **Impacto**: Saber exactamente qué código NO está testeado

2. **Crear tests de seguridad básicos**
   ```python
   # apps/core/tests/test_security.py
   - test_unauthenticated_returns_401
   - test_user_cannot_access_other_company
   - test_rate_limiting_works
   ```
   **Impacto**: Detectar vulnerabilidades antes de producción

3. **Agregar mocks para Mapbox API**
   ```python
   @patch('apps.routing.mapbox_service.requests.get')
   def test_mapbox_with_mock(self, mock_get):
       ...
   ```
   **Impacto**: Tests rápidos, sin dependencia externa

---

### 🔴 **CRÍTICO (Hacer ESTA SEMANA)**

4. **Implementar factories con factory_boy**
   ```bash
   pip install factory-boy
   # Crear factories.py en cada app
   ```
   **Impacto**: Tests 5x más rápidos de escribir

5. **Tests de ViewSets principales**
   ```python
   # test_container_viewset.py con 10+ tests
   ```
   **Impacto**: Cubre 50% del código de views

6. **Tests de serializers con validaciones**
   ```python
   # test_serializers.py con 15+ tests
   ```
   **Impacto**: Detecta bugs de validación

7. **Tests de Celery tasks**
   ```python
   # test_tasks.py con mocks
   ```
   **Impacto**: Asegura que background jobs funcionen

---

### 🟡 **IMPORTANTE (Próximas 2 semanas)**

8. **Configurar GitHub Actions para CI/CD**
   ```yaml
   # .github/workflows/tests.yml
   - Ejecutar tests en cada PR
   - Generar coverage report
   - Bloquear merge si coverage < 70%
   ```

9. **Tests de edge cases**
   ```python
   - Validaciones de campos
   - Límites de longitud
   - Fechas inválidas
   - Estados inválidos
   ```

10. **Tests de performance**
    ```python
    - assertNumQueries
    - Timeouts
    - Bulk operations
    ```

11. **Tests de models (métodos custom)**
    ```python
    - Container.get_current_position()
    - Container.calculate_demurrage_days()
    ```

12. **Tests de servicios**
    ```python
    - ExcelImporterService
    - ProximityAlertSystem
    - EmptyInventoryService
    ```

---

### 🟢 **MEJORAS (Backlog)**

13. Implementar mutation testing (pytest-mutpy)
14. Tests de carga (Locust)
15. Tests E2E (Selenium/Playwright)
16. Visual regression testing
17. Contract testing para APIs

---

## 🎯 EJEMPLO DE SUITE DE TESTS COMPLETA

```python
# apps/containers/tests/test_container_viewset.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch

from apps.containers.tests.factories import ContainerFactory, CompanyFactory, DriverFactory
from apps.containers.models import Container

class ContainerViewSetTests(APITestCase):
    """Suite completa de tests para ContainerViewSet"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.user = self.create_authenticated_user()
        self.client.force_authenticate(self.user)
        self.company = CompanyFactory()
        self.base_url = '/api/v1/containers/'
    
    # ========== TESTS DE LIST ==========
    
    def test_list_returns_200(self):
        """✅ Listado retorna 200 OK"""
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_returns_paginated_results(self):
        """✅ Listado está paginado"""
        ContainerFactory.create_batch(60)
        response = self.client.get(self.base_url)
        
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 50)  # PAGE_SIZE
    
    def test_list_filters_by_status(self):
        """✅ Filtro por status funciona"""
        ContainerFactory.create_batch(5, status='PROGRAMADO')
        ContainerFactory.create_batch(3, status='FINALIZADO')
        
        response = self.client.get(self.base_url, {'status': 'PROGRAMADO'})
        
        self.assertEqual(response.data['count'], 5)
    
    def test_list_searches_by_container_number(self):
        """✅ Búsqueda por número funciona"""
        container = ContainerFactory(container_number='MSCU1234567')
        ContainerFactory.create_batch(5)
        
        response = self.client.get(self.base_url, {'search': 'MSCU123'})
        
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['container_number'], 'MSCU1234567')
    
    # ========== TESTS DE CREATE ==========
    
    def test_create_container_returns_201(self):
        """✅ Creación exitosa retorna 201"""
        data = {
            'container_number': 'TEST1234567',
            'container_type': '40ft',
            'status': 'POR_ARRIBAR',
            'owner_company': self.company.id,
        }
        
        response = self.client.post(self.base_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Container.objects.count(), 1)
    
    def test_create_validates_required_fields(self):
        """✅ Valida campos requeridos"""
        data = {'container_type': '40ft'}  # Falta container_number
        
        response = self.client.post(self.base_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('container_number', response.data)
    
    def test_create_rejects_duplicate_container_number(self):
        """✅ Rechaza números duplicados"""
        ContainerFactory(container_number='DUP1234567')
        data = {
            'container_number': 'DUP1234567',
            'container_type': '40ft',
            'owner_company': self.company.id,
        }
        
        response = self.client.post(self.base_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========== TESTS DE UPDATE ==========
    
    def test_update_container_status(self):
        """✅ Actualiza status correctamente"""
        container = ContainerFactory(status='PROGRAMADO')
        url = f'{self.base_url}{container.id}/'
        
        response = self.client.patch(url, {'status': 'ASIGNADO'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        container.refresh_from_db()
        self.assertEqual(container.status, 'ASIGNADO')
    
    # ========== TESTS DE PERMISSIONS ==========
    
    def test_unauthenticated_request_returns_401(self):
        """✅ Sin autenticación retorna 401"""
        self.client.logout()
        response = self.client.get(self.base_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== TESTS DE PERFORMANCE ==========
    
    def test_list_uses_select_related(self):
        """✅ List usa select_related (no N+1)"""
        ContainerFactory.create_batch(10, owner_company=self.company)
        
        with self.assertNumQueries(3):  # ← 1 para containers, 1 para count, 1 para auth
            self.client.get(self.base_url)
    
    # ========== TESTS DE CUSTOM ACTIONS ==========
    
    @patch('apps.containers.views.Assignment.objects.create')
    def test_assign_driver_action(self, mock_create):
        """✅ Acción assign_driver crea Assignment"""
        container = ContainerFactory(status='PROGRAMADO')
        driver = DriverFactory()
        url = f'{self.base_url}{container.id}/assign_driver/'
        
        response = self.client.post(url, {'driver_id': driver.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_create.assert_called_once()
```

---

## 🎯 PRÓXIMOS PASOS (FASE 9)

Con el análisis de tests completo, ahora procederé a:

1. ✅ **FASE 1 COMPLETADA**: Arquitectura y dependencias (5.3/10)
2. ✅ **FASE 2 COMPLETADA**: Modelos y base de datos (5.4/10)
3. ✅ **FASE 3 COMPLETADA**: Lógica de negocio y servicios (5.9/10)
4. ✅ **FASE 4 COMPLETADA**: Views y controladores (4.5/10)
5. ✅ **FASE 5 COMPLETADA**: APIs y Serializers (5.4/10)
6. ✅ **FASE 6 COMPLETADA**: Seguridad profunda (6.3/10)
7. ✅ **FASE 7 COMPLETADA**: Performance y optimización (5.7/10)
8. ✅ **FASE 8 COMPLETADA**: Tests y cobertura (3.4/10)
9. ⏳ **FASE 9**: Documentación completa
10. ⏳ **FASE 10**: Deployment e integración

---

**FIN DE FASE 8 - TESTS Y COBERTURA**  
**Próximo paso**: Análisis exhaustivo de documentación (docstrings, type hints, API docs, diagramas, guías)
