"""
Servicio de integración con Mapbox API
Proporciona cálculo de rutas, ETAs y distancias
"""
import requests
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class MapboxService:
    """
    Cliente para Mapbox Directions API
    Documentación: https://docs.mapbox.com/api/navigation/directions/
    """
    
    API_KEY = settings.MAPBOX_API_KEY
    BASE_URL = "https://api.mapbox.com/directions/v5/mapbox"
    
    @classmethod
    def calcular_ruta(cls, origen_lng, origen_lat, destino_lng, destino_lat, profile='driving-traffic'):
        """
        Calcula la ruta óptima entre dos puntos
        
        Args:
            origen_lng: Longitud del origen
            origen_lat: Latitud del origen
            destino_lng: Longitud del destino
            destino_lat: Latitud del destino
            profile: Tipo de ruta (driving, driving-traffic, walking, cycling)
        
        Returns:
            dict: {
                'duration_minutes': float,  # Duración en minutos
                'distance_km': float,       # Distancia en kilómetros
                'geometry': dict,           # GeoJSON de la ruta
                'success': bool,
                'error': str (opcional)
            }
        """
        try:
            # Construir URL
            coordinates = f"{origen_lng},{origen_lat};{destino_lng},{destino_lat}"
            url = f"{cls.BASE_URL}/{profile}/{coordinates}"
            
            # Parámetros
            params = {
                'access_token': cls.API_KEY,
                'geometries': 'geojson',
                'overview': 'full',
                'steps': 'false',
            }
            
            # Hacer request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 'Ok':
                return {
                    'success': False,
                    'error': data.get('message', 'Error desconocido en Mapbox')
                }
            
            # Extraer datos de la ruta
            route = data['routes'][0]
            
            return {
                'success': True,
                'duration_minutes': round(route['duration'] / 60, 2),  # Convertir a minutos
                'distance_km': round(route['distance'] / 1000, 2),     # Convertir a km
                'geometry': route['geometry'],
                'raw_response': data
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Mapbox API: {str(e)}")
            return {
                'success': False,
                'error': f"Error de conexión con Mapbox: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error inesperado en calcular_ruta: {str(e)}")
            return {
                'success': False,
                'error': f"Error inesperado: {str(e)}"
            }
    
    @classmethod
    def calcular_distancia_simple(cls, origen_lng, origen_lat, destino_lng, destino_lat):
        """
        Calcula solo la distancia y duración sin geometría completa (más rápido)
        
        Returns:
            dict: {
                'duration_minutes': float,
                'distance_km': float,
                'success': bool
            }
        """
        resultado = cls.calcular_ruta(origen_lng, origen_lat, destino_lng, destino_lat)
        
        if resultado['success']:
            return {
                'success': True,
                'duration_minutes': resultado['duration_minutes'],
                'distance_km': resultado['distance_km']
            }
        
        return resultado
    
    @classmethod
    def calcular_matriz_distancias(cls, origen, destinos):
        """
        Calcula distancias desde un origen a múltiples destinos
        
        Args:
            origen: dict con {'lat': float, 'lng': float}
            destinos: lista de dicts con {'id': str, 'lat': float, 'lng': float}
        
        Returns:
            list: Lista de dicts con {
                'destino_id': str,
                'distance_km': float,
                'duration_minutes': float,
                'success': bool
            }
        """
        resultados = []
        
        for destino in destinos:
            resultado = cls.calcular_distancia_simple(
                origen['lng'], 
                origen['lat'],
                destino['lng'],
                destino['lat']
            )
            
            resultados.append({
                'destino_id': destino.get('id'),
                'distance_km': resultado.get('distance_km'),
                'duration_minutes': resultado.get('duration_minutes'),
                'success': resultado.get('success', False)
            })
        
        return resultados
    
    @classmethod
    def calcular_score_proximidad(cls, driver_lat, driver_lng, cd_lat, cd_lng, max_km=100):
        """
        Calcula un score de proximidad (0-100) basado en la distancia
        100 = muy cerca (0 km)
        0 = muy lejos (>= max_km)
        
        Args:
            driver_lat: Latitud del conductor
            driver_lng: Longitud del conductor
            cd_lat: Latitud del CD
            cd_lng: Longitud del CD
            max_km: Distancia máxima para el score (default 100km)
        
        Returns:
            float: Score de 0 a 100
        """
        try:
            resultado = cls.calcular_distancia_simple(driver_lng, driver_lat, cd_lng, cd_lat)
            
            if not resultado['success']:
                return Decimal('50.0')  # Score medio si falla
            
            distancia = Decimal(str(resultado['distance_km']))
            
            # Score inversamente proporcional a la distancia
            if distancia >= max_km:
                return Decimal('0.0')
            
            score = (1 - (distancia / Decimal(str(max_km)))) * 100
            return round(score, 2)
        
        except Exception as e:
            logger.error(f"Error calculando score de proximidad: {str(e)}")
            return Decimal('50.0')  # Score medio en caso de error
