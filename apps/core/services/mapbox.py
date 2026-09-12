import hashlib
import json
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class MapboxService:
    """
    Servicio de integración con Mapbox API para cálculos de rutas y geocodificación.
    """
    
    @classmethod
    def get_access_token(cls):
        """Obtiene el token de acceso desde los settings, soportando ambos nombres."""
        return getattr(settings, 'MAPBOX_API_KEY', getattr(settings, 'MAPBOX_ACCESS_TOKEN', None))

    @classmethod
    def get_route_signature(cls, geometry):
        """Genera una firma SHA-256 única para una geometría de ruta."""
        if not geometry:
            return None
        if isinstance(geometry, (dict, list)):
            geometry = json.dumps(geometry, sort_keys=True)
        return hashlib.sha256(geometry.encode()).hexdigest()

    @classmethod
    def calcular_ruta(cls, origin_lng, origin_lat, dest_lng, dest_lat):
        """
        Calcula una ruta simple entre dos puntos.
        Utilizado por MLTimePredictor y vistas de monitoreo.
        """
        token = cls.get_access_token()
        if not token:
            return {"success": False, "error": "MAPBOX_API_KEY no configurado"}

        # Coordenadas en formato Mapbox: lng,lat
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
        params = {
            "access_token": token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "false"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("routes"):
                route = data["routes"][0]
                return {
                    "success": True,
                    "distance_km": round(route["distance"] / 1000, 2),
                    "duration_minutes": round(route["duration"] / 60, 2),
                    "geometry": route["geometry"],
                    "route_signature": cls.get_route_signature(route["geometry"]),
                    "route_index": 0
                }
            return {"success": False, "error": "No se encontraron rutas"}
        except Exception as e:
            logger.error(f"Error en MapboxService.calcular_ruta: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def calcular_rutas_alternativas(cls, origin_lng, origin_lat, dest_lng, dest_lat, alternatives=True):
        """
        Calcula múltiples rutas alternativas para procesos de optimización.
        """
        token = cls.get_access_token()
        if not token:
            return {"success": False, "error": "MAPBOX_API_KEY no configurado"}

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
        params = {
            "access_token": token,
            "geometries": "geojson",
            "overview": "full",
            "alternatives": "true" if alternatives else "false",
            "steps": "false"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("routes"):
                processed_routes = []
                for i, route in enumerate(data["routes"]):
                    processed_routes.append({
                        "route_index": i,
                        "distance_km": round(route["distance"] / 1000, 2),
                        "duration_minutes": round(route["duration"] / 60, 2),
                        "geometry": route["geometry"],
                        "route_signature": cls.get_route_signature(route["geometry"])
                    })
                return {
                    "success": True,
                    "routes": processed_routes
                }
            return {"success": False, "error": "No se encontraron rutas"}
        except Exception as e:
            logger.error(f"Error en MapboxService.calcular_rutas_alternativas: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def geocode(cls, address):
        """
        Busca coordenadas para una dirección de texto.
        """
        token = cls.get_access_token()
        if not token:
            return {"success": False, "error": "MAPBOX_API_KEY no configurado"}

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json"
        params = {
            "access_token": token,
            "limit": 1
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("features"):
                feature = data["features"][0]
                return {
                    "success": True,
                    "address": feature["place_name"],
                    "lng": feature["center"][0],
                    "lat": feature["center"][1]
                }
            return {"success": False, "error": "Dirección no encontrada"}
        except Exception as e:
            logger.error(f"Error en MapboxService.geocode: {e}")
            return {"success": False, "error": str(e)}
