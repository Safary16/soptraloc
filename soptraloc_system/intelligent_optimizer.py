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
    distance_weight: float = 0.3
    time_weight: float = 0.25
    driver_availability_weight: float = 0.2
    container_priority_weight: float = 0.15
    historical_performance_weight: float = 0.1

@dataclass
class DriverScore:
    """Puntuación de un conductor para una asignación específica"""
    driver_id: str
    driver_name: str
    total_score: float
    factors: Dict[str, float] = field(default_factory=dict)
    estimated_time: int = 0
    confidence: float = 0.0

class IntelligentOptimizer:
    """
    Sistema de optimización inteligente para asignación de conductores
    Utiliza múltiples factores y machine learning para optimización automática
    """
    
    def __init__(self):
        self.factors = OptimizationFactors()
        self.locations_cache = {}
        self.time_matrix_cache = {}
        self.driver_performance_cache = {}
        
    def optimize_assignments(self, containers: List[Container] = None, max_assignments: int = 10) -> Dict:
        """
        Optimiza las asignaciones de conductores para contenedores
        
        Args:
            containers: Lista de contenedores a asignar (si None, usa pendientes)
            max_assignments: Máximo número de asignaciones a generar
            
        Returns:
            Dict con asignaciones optimizadas y métricas
        """
        print("🧠 INICIANDO OPTIMIZACIÓN INTELIGENTE")
        print("=" * 50)
        
        if containers is None:
            containers = self._get_pending_containers()
            
        if not containers:
            return {
                'success': False,
                'message': 'No hay contenedores pendientes para optimizar',
                'assignments': [],
                'metrics': {}
            }
            
        print(f"📦 Contenedores a optimizar: {len(containers)}")
        
        # Obtener conductores disponibles
        available_drivers = self._get_available_drivers()
        print(f"🚗 Conductores disponibles: {len(available_drivers)}")
        
        if not available_drivers:
            return {
                'success': False,
                'message': 'No hay conductores disponibles',
                'assignments': [],
                'metrics': {}
            }
        
        # Preparar datos
        self._prepare_optimization_data()
        
        # Generar asignaciones optimizadas
        optimized_assignments = []
        total_score = 0
        processed = 0
        
        for container in containers[:max_assignments]:
            best_assignment = self._find_best_driver_for_container(container, available_drivers)
            
            if best_assignment:
                optimized_assignments.append(best_assignment)
                total_score += best_assignment.total_score
                processed += 1
                
                # Remover driver de disponibles temporalmente para evitar sobreasignación
                available_drivers = [d for d in available_drivers if d.id != best_assignment.driver_id]
                
                print(f"✅ {container.container_number} → {best_assignment.driver_name} (Score: {best_assignment.total_score:.2f})")
            else:
                print(f"❌ No se pudo asignar: {container.container_number}")
        
        # Calcular métricas
        metrics = self._calculate_optimization_metrics(optimized_assignments, total_score, processed)
        
        print("\n📊 RESULTADOS DE OPTIMIZACIÓN")
        print("=" * 50)
        print(f"Asignaciones generadas: {len(optimized_assignments)}")
        print(f"Score promedio: {metrics.get('average_score', 0):.2f}")
        print(f"Eficiencia estimada: {metrics.get('efficiency_percentage', 0):.1f}%")
        
        return {
            'success': True,
            'assignments': optimized_assignments,
            'metrics': metrics,
            'processed_containers': processed,
            'total_containers': len(containers)
        }
    
    def _get_pending_containers(self) -> List[Container]:
        """Obtiene contenedores pendientes de asignación"""
        return list(Container.objects.filter(
            status__in=['available', 'pending']
        ).order_by('eta', 'sequence_id'))
    
    def _get_available_drivers(self) -> List[Driver]:
        """Obtiene conductores disponibles"""
        return list(Driver.objects.filter(
            estado='OPERATIVO'
        ).exclude(
            id__in=Assignment.objects.filter(
                fecha=datetime.now().date(),
                estado__in=['assigned', 'in_progress']
            ).values_list('conductor_id', flat=True)
        ))
    
    def _prepare_optimization_data(self):
        """Prepara datos para optimización"""
        # Cachear ubicaciones
        locations = Location.objects.all()
        self.locations_cache = {loc.id: loc for loc in locations}
        
        # Cachear matriz de tiempos
        time_matrices = TimeMatrix.objects.all()
        for tm in time_matrices:
            key = f"{tm.from_location_id}_{tm.to_location_id}"
            self.time_matrix_cache[key] = tm
    
    def _find_best_driver_for_container(self, container: Container, drivers: List[Driver]) -> Optional[DriverScore]:
        """
        Encuentra el mejor conductor para un contenedor específico
        """
        if not drivers:
            return None
            
        driver_scores = []
        
        for driver in drivers:
            score = self._calculate_driver_score(driver, container)
            if score:
                driver_scores.append(score)
        
        if not driver_scores:
            return None
            
        # Ordenar por score y retornar el mejor
        driver_scores.sort(key=lambda x: x.total_score, reverse=True)
        return driver_scores[0]
    
    def _calculate_driver_score(self, driver: Driver, container: Container) -> Optional[DriverScore]:
        """
        Calcula la puntuación de un conductor para un contenedor específico
        """
        try:
            factors = {}
            
            # Factor 1: Distancia/Ubicación
            distance_score = self._calculate_distance_score(driver, container)
            factors['distance'] = distance_score
            
            # Factor 2: Tiempo estimado
            time_score = self._calculate_time_score(driver, container)
            factors['time'] = time_score
            
            # Factor 3: Disponibilidad del conductor
            availability_score = self._calculate_availability_score(driver)
            factors['availability'] = availability_score
            
            # Factor 4: Prioridad del contenedor
            priority_score = self._calculate_priority_score(container)
            factors['priority'] = priority_score
            
            # Factor 5: Rendimiento histórico
            performance_score = self._calculate_performance_score(driver)
            factors['performance'] = performance_score
            
            # Calcular score total ponderado
            total_score = (
                distance_score * self.factors.distance_weight +
                time_score * self.factors.time_weight +
                availability_score * self.factors.driver_availability_weight +
                priority_score * self.factors.container_priority_weight +
                performance_score * self.factors.historical_performance_weight
            )
            
            # Calcular tiempo estimado
            estimated_time = self._calculate_estimated_time(driver, container)
            
            return DriverScore(
                driver_id=str(driver.id),
                driver_name=driver.nombre,
                total_score=total_score,
                factors=factors,
                estimated_time=estimated_time,
                confidence=min(0.95, total_score / 100)
            )
            
        except Exception as e:
            print(f"⚠️ Error calculando score para {driver.nombre}: {e}")
            return None
    
    def _calculate_distance_score(self, driver: Driver, container: Container) -> float:
        """Calcula puntuación basada en distancia"""
        try:
            # Ubicación actual del conductor
            driver_location = self._get_driver_location(driver)
            
            # Ubicación del contenedor
            container_location = self._get_container_location(container)
            
            if not driver_location or not container_location:
                return 50.0  # Score neutro
            
            # Buscar en matriz de tiempos
            time_key = f"{driver_location.id}_{container_location.id}"
            time_matrix = self.time_matrix_cache.get(time_key)
            
            if time_matrix:
                # Convertir tiempo a score (menos tiempo = más score)
                travel_time = time_matrix.travel_time
                if travel_time <= 30:
                    return 100.0
                elif travel_time <= 60:
                    return 80.0
                elif travel_time <= 90:
                    return 60.0
                elif travel_time <= 120:
                    return 40.0
                else:
                    return 20.0
            else:
                return 50.0  # Score neutro si no hay datos
                
        except Exception:
            return 50.0
    
    def _calculate_time_score(self, driver: Driver, container: Container) -> float:
        """Calcula puntuación basada en tiempo"""
        try:
            # Factor tiempo basado en ETA del contenedor
            if container.eta:
                days_until_eta = (container.eta - datetime.now().date()).days
                
                if days_until_eta < 0:
                    return 30.0  # Contenedor vencido - baja prioridad temporal
                elif days_until_eta == 0:
                    return 100.0  # Hoy - máxima prioridad
                elif days_until_eta == 1:
                    return 90.0  # Mañana - alta prioridad
                elif days_until_eta <= 3:
                    return 70.0  # Próximos días - buena prioridad
                else:
                    return 50.0  # Futuro lejano - prioridad normal
            else:
                return 50.0
                
        except Exception:
            return 50.0
    
    def _calculate_availability_score(self, driver: Driver) -> float:
        """Calcula puntuación basada en disponibilidad"""
        try:
            if driver.estado == 'OPERATIVO':
                # Verificar asignaciones del día
                today_assignments = Assignment.objects.filter(
                    conductor=driver,
                    fecha=datetime.now().date()
                ).count()
                
                if today_assignments == 0:
                    return 100.0  # Completamente disponible
                elif today_assignments == 1:
                    return 80.0   # Una asignación
                elif today_assignments == 2:
                    return 60.0   # Dos asignaciones
                else:
                    return 30.0   # Muy cargado
            else:
                return 0.0  # No disponible
                
        except Exception:
            return 50.0
    
    def _calculate_priority_score(self, container: Container) -> float:
        """Calcula puntuación basada en prioridad del contenedor"""
        try:
            # Basado en el tipo de contenedor y cliente
            base_score = 50.0
            
            # Aumentar score para ciertos tipos
            if container.container_type in ['REEFER', 'TANK']:
                base_score += 20.0
            
            # Aumentar score para clientes importantes (como Walmart)
            if container.client and 'WALMART' in container.client.name.upper():
                base_score += 15.0
            
            # Ajustar por estado
            if container.status == 'available':
                base_score += 10.0
            
            return min(100.0, base_score)
            
        except Exception:
            return 50.0
    
    def _calculate_performance_score(self, driver: Driver) -> float:
        """Calcula puntuación basada en rendimiento histórico"""
        try:
            # Obtener asignaciones completadas del último mes
            one_month_ago = datetime.now().date() - timedelta(days=30)
            
            completed_assignments = Assignment.objects.filter(
                conductor=driver,
                fecha__gte=one_month_ago,
                estado='completed'
            ).count()
            
            total_assignments = Assignment.objects.filter(
                conductor=driver,
                fecha__gte=one_month_ago
            ).count()
            
            if total_assignments == 0:
                return 70.0  # Nuevo conductor - score neutro-alto
            
            completion_rate = completed_assignments / total_assignments
            
            if completion_rate >= 0.95:
                return 100.0
            elif completion_rate >= 0.85:
                return 85.0
            elif completion_rate >= 0.70:
                return 70.0
            else:
                return 50.0
                
        except Exception:
            return 70.0
    
    def _calculate_estimated_time(self, driver: Driver, container: Container) -> int:
        """Calcula tiempo estimado total en minutos"""
        try:
            driver_location = self._get_driver_location(driver)
            container_location = self._get_container_location(container)
            
            if not driver_location or not container_location:
                return 120  # 2 horas por defecto
            
            time_key = f"{driver_location.id}_{container_location.id}"
            time_matrix = self.time_matrix_cache.get(time_key)
            
            if time_matrix:
                total_time = (
                    time_matrix.travel_time +
                    time_matrix.loading_time +
                    time_matrix.unloading_time
                )
                return total_time
            else:
                return 120  # 2 horas por defecto
                
        except Exception:
            return 120
    
    def _get_driver_location(self, driver: Driver) -> Optional[Location]:
        """Obtiene ubicación actual del conductor"""
        try:
            # Mapear ubicación del conductor a Location
            location_mapping = {
                'CCTI': 'CCTI - Base Maipú',
                'CD_QUILICURA': 'CD Quilicura',
                'CD_CAMPOS': 'CD Campos de Chile - Pudahuel',
                'CD_MADERO': 'CD Puerto Madero - Pudahuel',
                'CD_PENON': 'CD El Peñón - San Bernardo',
                'PUERTO_VALPARAISO': 'Puerto Valparaíso',
                'PUERTO_SAN_ANTONIO': 'Puerto San Antonio'
            }
            
            location_name = location_mapping.get(driver.ubicacion_actual, driver.ubicacion_actual)
            
            # Buscar en cache primero
            for location in self.locations_cache.values():
                if location.name == location_name:
                    return location
            
            # Si no está en cache, buscar en BD
            try:
                return Location.objects.get(name=location_name)
            except Location.DoesNotExist:
                return None
                
        except Exception:
            return None
    
    def _get_container_location(self, container: Container) -> Optional[Location]:
        """Obtiene ubicación del contenedor"""
        try:
            if container.terminal:
                return container.terminal
            elif container.current_location:
                return container.current_location
            else:
                return None
        except Exception:
            return None
    
    def _calculate_optimization_metrics(self, assignments: List[DriverScore], total_score: float, processed: int) -> Dict:
        """Calcula métricas de la optimización"""
        if not assignments:
            return {}
        
        average_score = total_score / len(assignments) if assignments else 0
        efficiency_percentage = (average_score / 100) * 100
        
        # Calcular distribución de scores
        scores = [a.total_score for a in assignments]
        
        return {
            'total_assignments': len(assignments),
            'average_score': average_score,
            'efficiency_percentage': efficiency_percentage,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'total_estimated_time': sum(a.estimated_time for a in assignments),
            'average_confidence': sum(a.confidence for a in assignments) / len(assignments) if assignments else 0,
            'processed_containers': processed
        }

def main():
    """Función principal para ejecutar la optimización"""
    optimizer = IntelligentOptimizer()
    
    # Ejecutar optimización
    result = optimizer.optimize_assignments(max_assignments=20)
    
    if result['success']:
        print(f"\n🎯 Optimización completada exitosamente!")
        print(f"📊 Métricas finales: {result['metrics']}")
        
        # Mostrar top 5 asignaciones
        if result['assignments']:
            print(f"\n🏆 TOP 5 ASIGNACIONES:")
            for i, assignment in enumerate(result['assignments'][:5], 1):
                print(f"{i}. {assignment.driver_name} - Score: {assignment.total_score:.2f}")
                
    else:
        print(f"❌ Error en optimización: {result['message']}")

if __name__ == "__main__":
    main()