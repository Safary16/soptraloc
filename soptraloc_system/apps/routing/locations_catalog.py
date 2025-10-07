"""
Catálogo de ubicaciones fijas para el sistema SOPTRALOC.
Incluye direcciones completas para consultas a Google Maps API.
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class LocationInfo:
    """Información completa de una ubicación."""
    code: str
    name: str
    full_name: str
    address: str
    city: str
    region: str
    # Coordenadas aproximadas (se pueden ajustar con geocoding)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    def get_google_maps_query(self) -> str:
        """Retorna la dirección formateada para Google Maps API."""
        return f"{self.address}, {self.city}, {self.region}, Chile"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# Catálogo de Centros de Distribución y Ubicaciones
LOCATIONS_CATALOG = {
    'CD_PENON': LocationInfo(
        code='CD_PENON',
        name='CD El Peñón',
        full_name='Centro de Distribución El Peñón',
        address='Avenida Presidente Jorge Alessandri 18899',
        city='San Bernardo',
        region='Región Metropolitana',
        latitude=-33.6370,
        longitude=-70.7050
    ),
    
    'CD_QUILICURA': LocationInfo(
        code='CD_QUILICURA',
        name='CD Quilicura',
        full_name='Centro de Distribución Quilicura',
        address='Eduardo Frei Montalva 8301',
        city='Quilicura',
        region='Región Metropolitana',
        latitude=-33.3609,
        longitude=-70.7266
    ),
    
    'CD_PUERTO_MADERO': LocationInfo(
        code='CD_PUERTO_MADERO',
        name='CD Puerto Madero',
        full_name='Centro de Distribución Puerto Madero (Puerto Santiago)',
        address='Puerto Madero 9710',
        city='Pudahuel',
        region='Región Metropolitana',
        latitude=-33.3980,
        longitude=-70.7860
    ),
    
    'CD_CAMPOS_CHILE': LocationInfo(
        code='CD_CAMPOS_CHILE',
        name='CD Campos de Chile',
        full_name='Centro de Distribución Campos de Chile',
        address='Av. El Parque 1000',
        city='Pudahuel',
        region='Región Metropolitana',
        latitude=-33.4415,
        longitude=-70.7593
    ),
    
    'CCTI': LocationInfo(
        code='CCTI',
        name='CCTI',
        full_name='Centro de Contenedores Terrestres Internacionales',
        address='Camino Los Agricultores, Parcela 41',
        city='Maipú',
        region='Región Metropolitana',
        latitude=-33.5167,
        longitude=-70.8667
    ),
    
    'CLEP_SAI': LocationInfo(
        code='CLEP_SAI',
        name='CLEP San Antonio',
        full_name='CLEP San Antonio - Centro de Liberación de Productos',
        address='Av. Las Factorías 7373',
        city='San Antonio',
        region='Región de Valparaíso',
        latitude=-33.5851,
        longitude=-71.6035
    ),
}


# Aliases comunes para búsqueda flexible
LOCATION_ALIASES = {
    'CD_QL': 'CD_QUILICURA',
    'QUILICURA': 'CD_QUILICURA',
    'CD QUILICURA': 'CD_QUILICURA',
    
    'CD_PUERTO_STGO': 'CD_PUERTO_MADERO',
    'PUERTO_MADERO': 'CD_PUERTO_MADERO',
    'PUERTO MADERO': 'CD_PUERTO_MADERO',
    'PUERTO_SANTIAGO': 'CD_PUERTO_MADERO',
    'CD PUERTO STGO': 'CD_PUERTO_MADERO',
    
    'CD_CDCH': 'CD_CAMPOS_CHILE',
    'CAMPOS_CHILE': 'CD_CAMPOS_CHILE',
    'CAMPOS DE CHILE': 'CD_CAMPOS_CHILE',
    'CD CAMPOS DE CHILE': 'CD_CAMPOS_CHILE',
    'CD CDCH': 'CD_CAMPOS_CHILE',
    
    'EL_PENON': 'CD_PENON',
    'PENON': 'CD_PENON',
    'EL PEÑON': 'CD_PENON',
    'CD EL PEÑON': 'CD_PENON',
    'CD EL PENON': 'CD_PENON',
    
    'SAI': 'CLEP_SAI',
    'SAN_ANTONIO': 'CLEP_SAI',
    'CLEP': 'CLEP_SAI',
    'LIBERADO': 'CLEP_SAI',
}


def get_location(code_or_alias: str) -> Optional[LocationInfo]:
    """
    Obtiene información de una ubicación por código o alias.
    
    Args:
        code_or_alias: Código de ubicación o alias (case-insensitive)
    
    Returns:
        LocationInfo si existe, None si no se encuentra
    
    Examples:
        >>> loc = get_location('CD_PENON')
        >>> loc = get_location('QUILICURA')
        >>> loc = get_location('cd puerto madero')
    """
    # Normalizar búsqueda
    search_key = code_or_alias.upper().replace(' ', '_').strip()
    
    # Buscar directamente en catálogo
    if search_key in LOCATIONS_CATALOG:
        return LOCATIONS_CATALOG[search_key]
    
    # Buscar en aliases
    if search_key in LOCATION_ALIASES:
        canonical_code = LOCATION_ALIASES[search_key]
        return LOCATIONS_CATALOG.get(canonical_code)
    
    return None


def list_all_locations() -> Dict[str, LocationInfo]:
    """Retorna todas las ubicaciones disponibles."""
    return LOCATIONS_CATALOG.copy()


def get_location_choices() -> list:
    """
    Retorna lista de tuplas (code, name) para usar en Django forms/admin.
    
    Returns:
        List[Tuple[str, str]]: [(code, display_name), ...]
    """
    return [(code, loc.full_name) for code, loc in LOCATIONS_CATALOG.items()]


def format_route_name(origin_code: str, destination_code: str) -> str:
    """
    Formatea nombre legible de una ruta.
    
    Args:
        origin_code: Código de origen
        destination_code: Código de destino
    
    Returns:
        String formateado, ej: "CCTI → CD El Peñón"
    
    Examples:
        >>> format_route_name('CCTI', 'CD_PENON')
        'CCTI → CD El Peñón'
    """
    origin = get_location(origin_code)
    destination = get_location(destination_code)
    
    if not origin or not destination:
        return f"{origin_code} → {destination_code}"
    
    return f"{origin.name} → {destination.name}"


# Tiempos estáticos aproximados (minutos) - Fallback si API no disponible
# Basados en tiempos típicos sin tráfico
STATIC_TRAVEL_TIMES = {
    ('CCTI', 'CD_PENON'): 45,
    ('CCTI', 'CD_QUILICURA'): 35,
    ('CCTI', 'CD_PUERTO_MADERO'): 25,
    ('CCTI', 'CD_CAMPOS_CHILE'): 20,
    ('CCTI', 'CLEP_SAI'): 120,
    
    ('CD_PENON', 'CCTI'): 45,
    ('CD_QUILICURA', 'CCTI'): 35,
    ('CD_PUERTO_MADERO', 'CCTI'): 25,
    ('CD_CAMPOS_CHILE', 'CCTI'): 20,
    ('CLEP_SAI', 'CCTI'): 120,
    
    # Entre CDs
    ('CD_PENON', 'CD_QUILICURA'): 50,
    ('CD_QUILICURA', 'CD_PENON'): 50,
    ('CD_QUILICURA', 'CD_PUERTO_MADERO'): 20,
    ('CD_PUERTO_MADERO', 'CD_QUILICURA'): 20,
    ('CD_PUERTO_MADERO', 'CD_CAMPOS_CHILE'): 15,
    ('CD_CAMPOS_CHILE', 'CD_PUERTO_MADERO'): 15,
}


def get_static_travel_time(origin_code: str, destination_code: str) -> int:
    """
    Obtiene tiempo de viaje estático entre dos ubicaciones.
    
    Args:
        origin_code: Código de origen
        destination_code: Código de destino
    
    Returns:
        Tiempo en minutos (default: 60 si no existe en tabla)
    """
    # Normalizar códigos
    origin = origin_code.upper().replace(' ', '_')
    destination = destination_code.upper().replace(' ', '_')
    
    # Resolver aliases
    if origin in LOCATION_ALIASES:
        origin = LOCATION_ALIASES[origin]
    if destination in LOCATION_ALIASES:
        destination = LOCATION_ALIASES[destination]
    
    # Buscar tiempo
    time = STATIC_TRAVEL_TIMES.get((origin, destination))
    
    if time:
        return time
    
    # Si no existe, retornar tiempo genérico
    return 60  # 1 hora por defecto
