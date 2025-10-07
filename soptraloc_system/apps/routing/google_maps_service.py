"""
Servicio de integración con Google Maps Distance Matrix API
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


class GoogleMapsService:
    """
    Servicio para obtener información de tráfico en tiempo real usando Google Maps API.
    
    GitHub Student Pack incluye $200 de crédito en Google Cloud Platform.
    Distance Matrix API costo: $0.005 por elemento (muy económico)
    """
    
    BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
    DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
    
    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if not self.api_key:
            logger.warning("⚠️  GOOGLE_MAPS_API_KEY no configurada. Usando tiempos estáticos.")
    
    def _process_location(self, location: Union[str, Tuple[float, float]]) -> Tuple[str, str]:
        """
        Procesa una ubicación y retorna (query_string, display_name).
        
        Args:
            location: Código de ubicación o tupla (lat, lng)
        
        Returns:
            Tuple de (query_string para API, nombre para mostrar)
        """
        if isinstance(location, str):
            # Es un código de ubicación
            loc_info = get_location(location)
            if loc_info:
                # Usar dirección completa
                return loc_info.get_google_maps_query(), loc_info.name
            else:
                # Asumir que es una dirección directa
                return location, location
        else:
            # Es una tupla de coordenadas
            lat, lng = location
            return f"{lat},{lng}", f"({lat}, {lng})"
    
    def get_travel_time_with_traffic(
        self,
        origin: Union[str, Tuple[float, float]],
        destination: Union[str, Tuple[float, float]],
        departure_time: Optional[datetime] = None
    ) -> Dict:
        """
        Obtiene tiempo de viaje considerando tráfico actual o en un tiempo específico.
        
        Args:
            origin: Código de ubicación (ej: 'CCTI', 'CD_PENON') o tupla (lat, lng)
            destination: Código de ubicación o tupla (lat, lng)
            departure_time: Hora de salida (None = ahora)
        
        Returns:
            Dict con:
            - duration_minutes: Tiempo estimado en minutos
            - duration_in_traffic_minutes: Tiempo con tráfico en minutos
            - distance_km: Distancia en kilómetros
            - traffic_level: 'low', 'medium', 'high', 'very_high'
            - warnings: Lista de advertencias (accidentes, cierres, etc.)
            - alternative_routes: Rutas alternativas si las hay
            - origin_name: Nombre de origen
            - destination_name: Nombre de destino
        
        Examples:
            >>> service.get_travel_time_with_traffic('CCTI', 'CD_PENON')
            >>> service.get_travel_time_with_traffic((-33.5167, -70.8667), (-33.6370, -70.7050))
        """
        # Procesar origen y destino
        origin_query, origin_name = self._process_location(origin)
        dest_query, dest_name = self._process_location(destination)
        
        if not self.api_key:
            return self._fallback_response(origin, destination, origin_name, dest_name)
        
        # Crear cache key
        cache_key = f"gmaps_travel:{origin_query}:{dest_query}"
        
        # Buscar en caché (válido por 5 minutos)
        cached = cache.get(cache_key)
        if cached and not departure_time:
            logger.info(f"✅ Usando datos en caché para ruta")
            return cached
        
        try:
            # Parámetros para Distance Matrix API
            params = {
                'origins': origin_query,
                'destinations': dest_query,
                'mode': 'driving',
                'language': 'es',
                'units': 'metric',
                'key': self.api_key,
            }
            
            # Si hay hora de salida, usar departure_time para considerar tráfico
            if departure_time:
                # Google Maps requiere timestamp Unix
                params['departure_time'] = int(departure_time.timestamp())
            else:
                # 'now' para tráfico actual
                params['departure_time'] = 'now'
            
            # Solicitar información de tráfico
            params['traffic_model'] = 'best_guess'  # o 'pessimistic' / 'optimistic'
            
            logger.info(f"🌐 Consultando Google Maps API: {origin_name} → {dest_name}")
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'OK':
                logger.error(f"❌ Error en Google Maps API: {data['status']}")
                return self._fallback_response()
            
            # Extraer información
            element = data['rows'][0]['elements'][0]
            
            if element['status'] != 'OK':
                logger.error(f"❌ No se pudo calcular ruta: {element['status']}")
                return self._fallback_response()
            
            # Tiempo sin tráfico
            duration_seconds = element['duration']['value']
            duration_minutes = duration_seconds / 60
            
            # Tiempo con tráfico (si está disponible)
            duration_in_traffic_seconds = element.get('duration_in_traffic', {}).get('value', duration_seconds)
            duration_in_traffic_minutes = duration_in_traffic_seconds / 60
            
            # Distancia
            distance_meters = element['distance']['value']
            distance_km = distance_meters / 1000
            
            # Calcular nivel de tráfico
            traffic_ratio = duration_in_traffic_minutes / duration_minutes if duration_minutes > 0 else 1.0
            traffic_level = self._calculate_traffic_level(traffic_ratio)
            
            result = {
                'duration_minutes': int(round(duration_minutes)),
                'duration_in_traffic_minutes': int(round(duration_in_traffic_minutes)),
                'distance_km': round(distance_km, 2),
                'traffic_level': traffic_level,
                'traffic_ratio': round(traffic_ratio, 2),
                'delay_minutes': int(round(duration_in_traffic_minutes - duration_minutes)),
                'warnings': [],
                'alternative_routes': [],
                'timestamp': datetime.now().isoformat(),
                'source': 'google_maps_api',
                'origin_name': origin_name,
                'destination_name': dest_name
            }
            
            # Obtener detalles adicionales con Directions API
            directions_data = self._get_directions_details(origin_query, dest_query)
            if directions_data:
                result['warnings'] = directions_data.get('warnings', [])
                result['alternative_routes'] = directions_data.get('alternatives', [])
            
            # Guardar en caché por 5 minutos
            cache.set(cache_key, result, 300)
            
            logger.info(f"✅ Tiempo estimado: {result['duration_in_traffic_minutes']}min "
                       f"(sin tráfico: {result['duration_minutes']}min, nivel: {traffic_level})")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error conectando a Google Maps API: {e}")
            return self._fallback_response(origin, destination, origin_name, dest_name)
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return self._fallback_response(origin, destination, origin_name, dest_name)
    
    def _get_directions_details(
        self,
        origin_query: str,
        dest_query: str
    ) -> Optional[Dict]:
        """
        Obtiene detalles de la ruta incluyendo advertencias y rutas alternativas.
        
        Args:
            origin_query: Query de origen (coordenadas o dirección)
            dest_query: Query de destino (coordenadas o dirección)
        """
        try:
            params = {
                'origin': origin_query,
                'destination': dest_query,
                'mode': 'driving',
                'language': 'es',
                'alternatives': 'true',  # Obtener rutas alternativas
                'departure_time': 'now',
                'key': self.api_key,
            }
            
            response = requests.get(self.DIRECTIONS_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'OK':
                return None
            
            warnings = []
            alternatives = []
            
            # Extraer advertencias de la ruta principal
            if data['routes']:
                main_route = data['routes'][0]
                
                # Warnings generales
                if 'warnings' in main_route:
                    warnings.extend(main_route['warnings'])
                
                # Buscar advertencias en cada paso
                for leg in main_route.get('legs', []):
                    for step in leg.get('steps', []):
                        instructions = step.get('html_instructions', '')
                        # Detectar palabras clave de problemas
                        if any(word in instructions.lower() for word in 
                               ['accidente', 'cerrado', 'obras', 'atasco', 'congestion', 
                                'tráfico denso', 'traffic', 'closed', 'accident']):
                            warnings.append(instructions)
                
                # Rutas alternativas
                for route in data['routes'][1:]:  # Saltar la principal
                    alt_duration = route['legs'][0]['duration']['value'] / 60
                    alt_distance = route['legs'][0]['distance']['value'] / 1000
                    alternatives.append({
                        'duration_minutes': int(round(alt_duration)),
                        'distance_km': round(alt_distance, 2),
                        'summary': route.get('summary', 'Ruta alternativa')
                    })
            
            return {
                'warnings': warnings,
                'alternatives': alternatives
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo direcciones: {e}")
            return None
    
    def _calculate_traffic_level(self, ratio: float) -> str:
        """
        Calcula el nivel de tráfico basado en el ratio tiempo_con_trafico/tiempo_sin_trafico.
        
        ratio < 1.1  = Tráfico bajo
        1.1-1.3      = Tráfico medio
        1.3-1.6      = Tráfico alto
        > 1.6        = Tráfico muy alto
        """
        if ratio < 1.1:
            return 'low'
        elif ratio < 1.3:
            return 'medium'
        elif ratio < 1.6:
            return 'high'
        else:
            return 'very_high'
    
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
gmaps_service = GoogleMapsService()
