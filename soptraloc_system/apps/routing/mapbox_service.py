"""
Servicio de integración con Mapbox Directions API
Para obtener tiempos de viaje en tiempo real considerando tráfico actual
"""
import requests
from typing import Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
import logging
from .locations_catalog import get_location, get_static_travel_time

logger = logging.getLogger(__name__)


class MapboxService:
    """
    Servicio para obtener información de tráfico en tiempo real usando Mapbox Directions API.
    
    GitHub Student Pack incluye $75 de crédito + 50,000 requests gratis/mes permanentemente.
    Directions API costo: $0.50 por 1,000 requests después del límite gratis (muy económico).
    
    Documentación: https://docs.mapbox.com/api/navigation/directions/
    """
    
    BASE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving-traffic"
    
    def __init__(self):
        self.api_key = getattr(settings, 'MAPBOX_API_KEY', None)
        if not self.api_key:
            logger.warning("⚠️  MAPBOX_API_KEY no configurada. Usando tiempos estáticos.")
    
    def _process_location(self, location: Union[str, Tuple[float, float]]) -> Tuple[str, str, float, float]:
        """
        Procesa una ubicación y retorna (query_string, display_name, lat, lng).
        
        Args:
            location: Código de ubicación o tupla (lat, lng)
        
        Returns:
            Tuple de (query_string para API, nombre para mostrar, lat, lng)
        """
        if isinstance(location, str):
            # Es un código de ubicación
            loc_info = get_location(location)
            if loc_info and loc_info.latitude and loc_info.longitude:
                # Mapbox usa formato: longitude,latitude (al revés de lo normal)
                return f"{loc_info.longitude},{loc_info.latitude}", loc_info.name, float(loc_info.latitude), float(loc_info.longitude)
            else:
                raise ValueError(f"Ubicación '{location}' no encontrada o sin coordenadas")
        else:
            # Es una tupla de coordenadas (lat, lng)
            lat, lng = location
            # Mapbox usa formato: longitude,latitude
            return f"{lng},{lat}", f"({lat}, {lng})", lat, lng
    
    def get_travel_time_with_traffic(
        self,
        origin: Union[str, Tuple[float, float]],
        destination: Union[str, Tuple[float, float]],
        departure_time: Optional[datetime] = None
    ) -> Dict:
        """
        Obtiene tiempo de viaje considerando tráfico actual.
        
        Args:
            origin: Código de ubicación (ej: 'CCTI', 'CD_PENON') o tupla (lat, lng)
            destination: Código de ubicación o tupla (lat, lng)
            departure_time: Hora de salida (None = ahora)
        
        Returns:
            Dict con:
            - duration_minutes: Tiempo estimado en minutos
            - duration_in_traffic_minutes: Tiempo con tráfico en minutos
            - distance_km: Distancia en kilómetros
            - traffic_level: 'low', 'medium', 'high', 'very_high', 'unknown'
            - warnings: Lista de advertencias
            - alternative_routes: Rutas alternativas si las hay
            - origin_name: Nombre de origen
            - destination_name: Nombre de destino
        
        Examples:
            >>> service.get_travel_time_with_traffic('CCTI', 'CD_PENON')
            >>> service.get_travel_time_with_traffic((-33.5167, -70.8667), (-33.6370, -70.7050))
        """
        # Procesar origen y destino
        origin_query, origin_name, origin_lat, origin_lng = self._process_location(origin)
        dest_query, dest_name, dest_lat, dest_lng = self._process_location(destination)
        
        if not self.api_key:
            return self._fallback_response(origin, destination, origin_name, dest_name)
        
        # Crear cache key
        cache_key = f"mapbox_travel:{origin_query}:{dest_query}"
        
        # Buscar en caché (válido por 5 minutos)
        cached = cache.get(cache_key)
        if cached and not departure_time:
            logger.info(f"✅ Usando datos en caché para ruta")
            return cached
        
        try:
            # Mapbox Directions API
            # Formato: /driving-traffic/{longitude,latitude};{longitude,latitude}
            url = f"{self.BASE_URL}/{origin_query};{dest_query}"
            
            params = {
                'access_token': self.api_key,
                'overview': 'simplified',
                'geometries': 'geojson',
                'steps': 'false',
                'annotations': 'duration,distance,speed',
                'language': 'es',
                'alternatives': 'true',  # Obtener rutas alternativas
                'continue_straight': 'false',
            }
            
            # Si hay hora de salida, usar depart_at
            if departure_time:
                params['depart_at'] = departure_time.isoformat()
            
            # Eliminar parámetros None
            params = {k: v for k, v in params.items() if v is not None}
            
            logger.info(f"🌐 Consultando Mapbox API: {origin_name} → {dest_name}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' not in data or not data['routes']:
                logger.error(f"❌ No se pudo calcular ruta con Mapbox")
                return self._fallback_response(origin, destination, origin_name, dest_name)
            
            # Ruta principal
            route = data['routes'][0]
            
            # Tiempo y distancia
            duration_seconds = route['duration']
            distance_meters = route['distance']
            
            duration_minutes = duration_seconds / 60
            distance_km = distance_meters / 1000
            
            # Mapbox Directions con 'driving-traffic' ya incluye tráfico en duration
            # No hay un "tiempo sin tráfico" explícito, pero podemos estimarlo
            
            result = {
                'duration_minutes': int(round(duration_minutes)),
                'duration_in_traffic_minutes': int(round(duration_minutes)),
                'distance_km': round(distance_km, 2),
                'traffic_level': 'unknown',  # Mapbox no da nivel explícito
                'traffic_ratio': 1.0,
                'delay_minutes': 0,
                'warnings': [],
                'alternative_routes': [],
                'timestamp': datetime.now().isoformat(),
                'source': 'mapbox_api',
                'origin_name': origin_name,
                'destination_name': dest_name
            }
            
            # Procesar rutas alternativas
            if len(data['routes']) > 1:
                for alt_route in data['routes'][1:]:
                    alt_duration = alt_route['duration'] / 60
                    alt_distance = alt_route['distance'] / 1000
                    
                    result['alternative_routes'].append({
                        'duration_minutes': int(round(alt_duration)),
                        'distance_km': round(alt_distance, 2),
                        'summary': 'Ruta alternativa'
                    })
            
            # Guardar en caché por 5 minutos
            cache.set(cache_key, result, 300)
            
            logger.info(f"✅ Tiempo estimado: {result['duration_in_traffic_minutes']}min "
                       f"(distancia: {result['distance_km']}km, fuente: mapbox)")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error conectando a Mapbox API: {e}")
            return self._fallback_response(origin, destination, origin_name, dest_name)
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return self._fallback_response(origin, destination, origin_name, dest_name)
    
    def _fallback_response(
        self, 
        origin: Union[str, Tuple[float, float]], 
        destination: Union[str, Tuple[float, float]],
        origin_name: str,
        dest_name: str
    ) -> Dict:
        """
        Respuesta de fallback cuando la API no está disponible.
        Usa tiempos estáticos del catálogo.
        """
        # Intentar obtener tiempo estático si son códigos de ubicación
        static_time = 60  # Default 60 minutos
        
        if isinstance(origin, str) and isinstance(destination, str):
            static_time = get_static_travel_time(origin, destination)
        
        return {
            'duration_minutes': static_time,
            'duration_in_traffic_minutes': static_time,
            'distance_km': 0,
            'traffic_level': 'unknown',
            'traffic_ratio': 1.0,
            'delay_minutes': 0,
            'warnings': ['No se pudo obtener información de tráfico en tiempo real. Usando tiempo estimado.'],
            'alternative_routes': [],
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback',
            'origin_name': origin_name,
            'destination_name': dest_name
        }
    
    def get_eta(
        self,
        origin: Union[str, Tuple[float, float]],
        destination: Union[str, Tuple[float, float]],
        departure_time: Optional[datetime] = None
    ) -> Tuple[datetime, Dict]:
        """
        Calcula la hora estimada de llegada (ETA) considerando tráfico.
        
        Args:
            origin: Código de ubicación o tupla (lat, lng)
            destination: Código de ubicación o tupla (lat, lng)
            departure_time: Hora de salida (None = ahora)
        
        Returns:
            Tuple de (ETA datetime, datos completos de tráfico)
        
        Examples:
            >>> eta, data = service.get_eta('CCTI', 'CD_PENON')
            >>> eta, data = service.get_eta((-33.5167, -70.8667), 'CD_QUILICURA')
        """
        travel_data = self.get_travel_time_with_traffic(
            origin, destination, departure_time
        )
        
        if not departure_time:
            departure_time = datetime.now()
        
        eta = departure_time + timedelta(minutes=travel_data['duration_in_traffic_minutes'])
        
        return eta, travel_data


# Instancia global del servicio
mapbox_service = MapboxService()
