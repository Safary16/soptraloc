#!/usr/bin/env python3
"""
ALGORITMO DE OPTIMIZACIÓN INTELIGENTE SOPTRALOC
Machine Learning + Optimización para asignación automática de conductores
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import heapq

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone

from apps.drivers.models import Driver, TimeMatrix, Location, Assignment
from apps.containers.models import Container

@dataclass
class OptimizationFactors:
    """Factores para la optimización"""
    service_efficiency: float = 0.0    # Eficiencia del servicio (cumplir horarios)
    resource_utilization: float = 0.0  # Utilización de recursos (conductores)
    travel_optimization: float = 0.0   # Optimización de viajes
    cost_reduction: float = 0.0        # Reducción de costos
    total_score: float = field(init=False)
    
    def __post_init__(self):
        self.total_score = (
            self.service_efficiency * 0.4 +      # 40% - Cumplir servicio es prioridad
            self.resource_utilization * 0.3 +    # 30% - Eficiencia de conductores
            self.travel_optimization * 0.2 +     # 20% - Optimización de rutas
            self.cost_reduction * 0.1           # 10% - Reducción de costos
        )

@dataclass
class AssignmentOption:
    """Opción de asignación"""
    container_id: str
    driver_id: int
    service_type: str  # 'DIRECT', 'RELAY', 'DROP_HOOK', 'TRUCK_UNLOAD'
    start_time: datetime
    estimated_duration: int  # minutos
    factors: OptimizationFactors
    
    def __lt__(self, other):
        return self.factors.total_score > other.factors.total_score  # Heap max

class IntelligentOptimizer:
    """Optimizador Inteligente SOPTRALOC"""
    
    def __init__(self):
        self.destination_keywords = {
            'QUILICURA': 'CD_QUILICURA',
            'CAMPOS': 'CD_CAMPOS',
            'MADERO': 'CD_MADERO',
            'PENON': 'CD_PENON',
            'CHILLAN': 'CD_CHILLAN',
            'TEMUCO': 'CD_TEMUCO',
            'CCTI': 'CCTI',
            'ZEAL': 'ZEAL',
            'CLEP': 'CLEP',
            'ALMACEN': 'ALMACEN_EXTRA',
            'DEPOSITO': 'DEPOSITO_DEV',
            'DEP/DEV': 'DEPOSITO_DEV',
            'DEP DEV': 'DEPOSITO_DEV',
            'TOTTUS': 'CD_QUILICURA',
        }

        self.service_type_map = {
            'DIRECTO': 'DIRECT',
            'DIRECT': 'DIRECT',
            'INDIRECTO_DEPOSITO': 'DROP_HOOK',
            'INDIRECTO DEPOSITO': 'DROP_HOOK',
            'INDIRECTO_CD': 'RELAY',
            'INDIRECTO CD': 'RELAY',
            'TRANSFERENCIA': 'RELAY',
            'REEFER': 'TRUCK_UNLOAD',
        }

        self.location_code_map: Dict[str, Location] = {}
        self.location_name_map: Dict[str, str] = {}
        self.build_location_index()
        self.load_historical_data()

    def build_location_index(self):
        """Construye índices de ubicaciones para cruzar datos"""
        self.location_code_map = {loc.code.upper(): loc for loc in Location.objects.all()}
        self.location_name_map = {
            self.normalize_text(loc.name): loc.code.upper()
            for loc in Location.objects.all()
        }
        
    def load_historical_data(self):
        """Cargar datos históricos para ML"""
        self.historical_assignments = pd.DataFrame()
        self.time_matrices = {}
        try:
            # Cargar datos de asignaciones de septiembre
            self.historical_assignments = pd.read_csv('9 (1).csv', sep=';', encoding='latin-1')
            print(f"📊 Cargados {len(self.historical_assignments)} registros históricos")
            
            # Cargar matriz de tiempos
            for matrix in TimeMatrix.objects.all():
                key = f"{matrix.from_location.code.upper()}_{matrix.to_location.code.upper()}"
                self.time_matrices[key] = {
                    'travel': matrix.travel_time,
                    'loading': matrix.loading_time,
                    'unloading': matrix.unloading_time,
                    'total': matrix.travel_time + matrix.loading_time + matrix.unloading_time
                }
                
        except Exception as e:
            print(f"⚠️ Error cargando datos históricos: {e}")
            
    def determine_service_type(self, container: Container) -> str:
        """Determinar tipo de servicio óptimo basado en destino y contexto"""
        service_type = self.normalize_text(container.service_type or '')
        if service_type in self.service_type_map:
            return self.service_type_map[service_type]

        destination_text = container.cd_location or ''
        destination_code = self.resolve_destination_code(destination_text)
        origin_code = self.resolve_origin_code(container)

        if destination_code in {'CD_QUILICURA', 'CD_CAMPOS', 'CD_MADERO', 'CD_CHILLAN', 'CD_TEMUCO'}:
            return 'TRUCK_UNLOAD'

        if destination_code == 'CD_PENON':
            return 'DROP_HOOK'

        if origin_code in {'ZEAL', 'CLEP'}:
            scheduled_dt = self.get_container_scheduled_datetime(container)
            if scheduled_dt:
                if scheduled_dt.hour < 10:
                    return 'DIRECT'
                return 'RELAY'
            return 'RELAY'

        return 'DIRECT'
            
    def calculate_service_efficiency(self, container: Container, driver: Driver, 
                                   service_type: str, start_time: datetime) -> float:
        """Calcular eficiencia del servicio (0-1)"""
        
        # Factor 1: Cumplimiento de horario programado
        time_score = 1.0
        scheduled_datetime = self.get_container_scheduled_datetime(container)
        if scheduled_datetime:
            time_diff = abs((start_time - scheduled_datetime).total_seconds() / 3600)
            time_score = max(0, 1 - time_diff / 12)  # Penalizar diferencias > 12h
            
        # Factor 2: Experiencia del conductor con el destino
        experience_score = self.get_driver_destination_experience(driver, container.cd_location)
        
        # Factor 3: Tipo de servicio vs destino
        service_match_score = self.get_service_type_match(container.cd_location, service_type)
        
        return (time_score * 0.5 + experience_score * 0.3 + service_match_score * 0.2)
    
    def get_driver_destination_experience(self, driver: Driver, destination: str) -> float:
        """Obtener experiencia del conductor con el destino (0-1)"""
        if self.historical_assignments.empty:
            return 0.7  # Score neutro
            
        if not destination:
            return 0.6

        destination_prefix = self.normalize_text(destination)[:5]
        if not destination_prefix:
            return 0.6

        # Buscar asignaciones históricas del conductor a este destino
        driver_history = self.historical_assignments[
            self.historical_assignments['Conductor'] == driver.nombre
        ]
        
        if len(driver_history) == 0:
            return 0.5  # Conductor nuevo
            
        # Contar entregas a destinos similares
        similar_destinations = driver_history[
            driver_history['Destino'].fillna('').apply(
                lambda value: destination_prefix in self.normalize_text(str(value))
            )
        ]
        
        experience_ratio = len(similar_destinations) / len(driver_history)
        return min(1.0, experience_ratio * 2)  # Max score 1.0
        
    def get_service_type_match(self, destination: str, service_type: str) -> float:
        """Evaluar qué tan bien coincide el tipo de servicio con el destino"""
        if not destination:
            return 0.6

        destination_upper = self.normalize_text(destination)
        
        if service_type == 'TRUCK_UNLOAD':
            if any(cd in destination_upper for cd in ['QUILICURA', 'CAMPOS', 'MADERO', 'TOTTUS']):
                return 1.0
            return 0.3
            
        elif service_type == 'DROP_HOOK':
            if 'PEÑON' in destination_upper:
                return 1.0
            return 0.2
            
        elif service_type == 'DIRECT':
            return 0.8  # Generalmente buena opción
            
        elif service_type == 'RELAY':
            return 0.6  # Opción intermedia
            
        return 0.5
        
    def calculate_resource_utilization(self, driver: Driver, start_time: datetime, 
                                     duration: int) -> float:
        """Calcular utilización de recursos (0-1)"""
        
        # Factor 1: Disponibilidad del conductor
        if not self.is_driver_available(driver, start_time, duration):
            return 0.0
            
        # Factor 2: Balanceamiento de carga
        daily_assignments = self.get_driver_daily_assignments(driver, start_time.date())
        load_balance_score = max(0, 1 - len(daily_assignments) / 8)  # Max 8 asignaciones/día
        
        # Factor 3: Continuidad (asignaciones consecutivas)
        continuity_score = self.calculate_continuity_score(driver, start_time)
        
        return (load_balance_score * 0.6 + continuity_score * 0.4)
        
    def is_driver_available(self, driver: Driver, start_time: datetime, duration: int) -> bool:
        """Verificar disponibilidad del conductor"""
        end_time = start_time + timedelta(minutes=duration)

        overlapping = Assignment.objects.filter(
            driver=driver,
            estado__in=['PENDIENTE', 'EN_CURSO'],
            fecha_programada__lt=end_time,
            fecha_programada__gte=start_time - timedelta(minutes=duration)
        )

        return not overlapping.exists()
        
    def get_driver_daily_assignments(self, driver: Driver, date) -> List:
        """Obtener asignaciones del conductor para el día"""
        day_start = timezone.make_aware(datetime.combine(date, time.min))
        day_end = timezone.make_aware(datetime.combine(date, time.max))

        return list(
            Assignment.objects.filter(
                driver=driver,
                fecha_programada__range=(day_start, day_end),
                estado__in=['PENDIENTE', 'EN_CURSO', 'COMPLETADA']
            )
        )
        
    def calculate_continuity_score(self, driver: Driver, start_time: datetime) -> float:
        """Calcular score de continuidad para asignaciones consecutivas"""
        recent_assignment = Assignment.objects.filter(
            driver=driver,
            estado__in=['PENDIENTE', 'EN_CURSO', 'COMPLETADA'],
            fecha_programada__lt=start_time
        ).order_by('-fecha_programada').first()

        if not recent_assignment or not recent_assignment.fecha_programada:
            return 0.7

        diff_hours = abs((start_time - recent_assignment.fecha_programada).total_seconds() / 3600)

        if diff_hours <= 2:
            return 1.0
        if diff_hours <= 4:
            return 0.8
        if diff_hours <= 8:
            return 0.6
        return 0.5
        
    def calculate_travel_optimization(self, container: Container, service_type: str) -> float:
        """Calcular optimización de viajes (0-1)"""
        
        origin_code = self.resolve_origin_code(container)
        destination_code = self.resolve_destination_code(container.cd_location)
        
        if not origin_code or not destination_code:
            return 0.5
        
        # Obtener tiempo de la matriz
        matrix_key = f"{origin_code}_{destination_code}"

        if matrix_key not in self.time_matrices:
            return 0.5  # Score neutro si no hay datos
            
        travel_data = self.time_matrices[matrix_key]
        
        # Factor 1: Eficiencia del tiempo total
        total_time = travel_data['total']
        efficiency_score = max(0, (300 - total_time) / 300)  # Normalizar a 5h max
        
        # Factor 2: Tipo de servicio vs tiempo
        service_efficiency = 1.0
        if service_type == 'TRUCK_UNLOAD' and total_time > 240:  # 4h
            service_efficiency = 0.7  # Penalizar servicios largos
        elif service_type == 'DROP_HOOK' and total_time < 120:  # 2h
            service_efficiency = 1.2  # Premiar servicios cortos eficientes
            
        return min(1.0, efficiency_score * service_efficiency)
        
    def optimize_assignments(self, containers: List[Container]) -> List[AssignmentOption]:
        """Algoritmo principal de optimización"""
        
        print("🧠 EJECUTANDO ALGORITMO DE OPTIMIZACIÓN INTELIGENTE")
        print("=" * 70)
        
        options_heap = []
        drivers = list(Driver.objects.filter(is_active=True, estado='OPERATIVO'))
        
        for container in containers:
            print(f"📦 Optimizando: {container.container_number} → {container.cd_location}")
            
            # Determinar tipo de servicio óptimo
            optimal_service_type = self.determine_service_type(container)
            
            # Evaluar cada conductor
            for driver in drivers:
                # Calcular tiempo de inicio óptimo
                start_time = self.get_container_scheduled_datetime(container)
                if not start_time:
                    start_time = timezone.now()
                
                # Estimar duración según tipo de servicio
                duration = self.estimate_service_duration(container, optimal_service_type)
                
                # Calcular factores de optimización
                factors = OptimizationFactors(
                    service_efficiency=self.calculate_service_efficiency(
                        container, driver, optimal_service_type, start_time
                    ),
                    resource_utilization=self.calculate_resource_utilization(
                        driver, start_time, duration
                    ),
                    travel_optimization=self.calculate_travel_optimization(
                        container, optimal_service_type
                    ),
                    cost_reduction=self.calculate_cost_reduction(
                        container, driver, optimal_service_type
                    )
                )
                
                # Crear opción de asignación
                option = AssignmentOption(
                    container_id=container.container_number,
                    driver_id=driver.id,
                    service_type=optimal_service_type,
                    start_time=start_time,
                    estimated_duration=duration,
                    factors=factors
                )
                
                heapq.heappush(options_heap, option)
                
        # Obtener mejores opciones
        optimized_assignments = []
        assigned_drivers = set()
        assigned_containers = set()
        
        while options_heap and len(optimized_assignments) < len(containers):
            option = heapq.heappop(options_heap)
            
            # Evitar asignaciones duplicadas
            if (option.driver_id not in assigned_drivers and 
                option.container_id not in assigned_containers):
                
                optimized_assignments.append(option)
                assigned_drivers.add(option.driver_id)
                assigned_containers.add(option.container_id)
                
        return optimized_assignments
        
    def estimate_service_duration(self, container: Container, service_type: str) -> int:
        """Estimar duración del servicio en minutos"""
        
        origin_code = self.resolve_origin_code(container) or 'CCTI'
        destination_code = self.resolve_destination_code(container.cd_location) or 'CD_QUILICURA'
        
        # Buscar en matriz de tiempos
        matrix_key = f"{origin_code}_{destination_code}"
        
        if matrix_key in self.time_matrices:
            base_duration = self.time_matrices[matrix_key]['total']
        else:
            base_duration = 180  # 3h por defecto
            
        # Ajustar según tipo de servicio
        if service_type == 'TRUCK_UNLOAD':
            return base_duration + 60  # +1h para descarga sobre camión
        elif service_type == 'DROP_HOOK':
            return max(90, base_duration - 30)  # -30min por drop & hook
        elif service_type == 'RELAY':
            return base_duration + 30  # +30min por transferencia
            
        return base_duration
        
    def calculate_cost_reduction(self, container: Container, driver: Driver, 
                               service_type: str) -> float:
        """Calcular reducción de costos (0-1)"""
        
        # Factor 1: Eficiencia de combustible (rutas cortas = score alto)
        distance_score = 0.7  # Score neutro
        
        # Factor 2: Utilización de chasis (Drop & Hook es más eficiente)
        chassis_efficiency = 1.0 if service_type == 'DROP_HOOK' else 0.8
        
        # Factor 3: Tiempo de conductor (menos tiempo = menos costo)
        duration = self.estimate_service_duration(container, service_type)
        time_efficiency = max(0, (480 - duration) / 480)  # Normalizar a 8h
        
        return (distance_score * 0.4 + chassis_efficiency * 0.3 + time_efficiency * 0.3)

    # ==== Métodos utilitarios ====
    def normalize_text(self, value: Optional[str]) -> str:
        if not value:
            return ''
        normalized = unicodedata.normalize('NFKD', value)
        normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
        return normalized.upper().strip()

    def resolve_destination_code(self, destination: Optional[str]) -> Optional[str]:
        if not destination:
            return None

        normalized = self.normalize_text(destination)

        if normalized in self.location_code_map:
            return normalized

        if normalized in self.location_name_map:
            return self.location_name_map[normalized]

        for keyword, code in self.destination_keywords.items():
            if keyword in normalized:
                return code

        return None

    def resolve_origin_code(self, container: Container) -> Optional[str]:
        # Priorizar ubicación actual (campo enumerado)
        origin_candidate = container.current_position
        origin_code = self.resolve_destination_code(origin_candidate)

        if origin_code:
            return origin_code

        # Intentar con ubicación física actual (modelo Location del core)
        if container.current_location:
            origin_code = self.resolve_destination_code(container.current_location.name)
            if origin_code:
                return origin_code

        # Intentar con terminal asociada
        if container.terminal:
            origin_code = self.resolve_destination_code(container.terminal.name)
            if origin_code:
                return origin_code

        return None

    def get_container_scheduled_datetime(self, container: Container) -> Optional[datetime]:
        if not container.scheduled_date:
            return None

        scheduled_time = container.scheduled_time or time(hour=8, minute=0)
        naive_datetime = datetime.combine(container.scheduled_date, scheduled_time)

        if timezone.is_naive(naive_datetime):
            return timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        return naive_datetime

def main():
    """Función principal de demostración"""
    
    optimizer = IntelligentOptimizer()
    
    # Obtener contenedores pendientes (simulado)
    containers = list(Container.objects.filter(status='PROGRAMADO')[:5])
    
    if not containers:
        print("⚠️ No hay contenedores para optimizar")
        return
        
    # Ejecutar optimización
    optimized_assignments = optimizer.optimize_assignments(containers)
    
    print("\n🎯 RESULTADOS DE OPTIMIZACIÓN:")
    print("=" * 70)
    
    for i, assignment in enumerate(optimized_assignments, 1):
        driver = Driver.objects.get(id=assignment.driver_id)
        factors = assignment.factors
        
        print(f"\n{i}. 📦 {assignment.container_id}")
        print(f"   👤 Conductor: {driver.nombre}")
        print(f"   🚛 Tipo Servicio: {assignment.service_type}")
        print(f"   ⏱️  Duración Estimada: {assignment.estimated_duration} min")
        print(f"   📊 Score Total: {factors.total_score:.3f}")
        print(f"      • Eficiencia Servicio: {factors.service_efficiency:.3f}")
        print(f"      • Utilización Recursos: {factors.resource_utilization:.3f}")
        print(f"      • Optimización Viajes: {factors.travel_optimization:.3f}")
        print(f"      • Reducción Costos: {factors.cost_reduction:.3f}")

if __name__ == "__main__":
    main()