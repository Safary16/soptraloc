"""
Utilidades centralizadas para manejo de ubicaciones.
Evita duplicación de código en todo el sistema.
"""
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import User
else:
    from django.contrib.auth import get_user_model
    User = get_user_model()

from apps.drivers.models import Location

logger = logging.getLogger(__name__)


def get_or_create_location(
    name: str, 
    city: str = 'Santiago',
    region: str = 'Metropolitana',
    country: str = 'Chile',
    user: Optional[User] = None,
    code: Optional[str] = None
) -> Location:
    """
    Obtiene o crea una ubicación de forma centralizada.
    
    ÚNICA FUENTE DE VERDAD para creación de ubicaciones en todo el sistema.
    
    Args:
        name: Nombre de la ubicación
        city: Ciudad (default: Santiago)
        region: Región (default: Metropolitana)
        country: País (default: Chile)
        user: Usuario que crea la ubicación
        code: Código único (se genera automáticamente si no se provee)
    
    Returns:
        Location: Ubicación existente o recién creada
    """
    if not name or not name.strip():
        name = "Sin Especificar"
    
    cleaned_name = name.strip()
    
    # Buscar primero por código si existe
    if code:
        location = Location.objects.filter(code=code).first()
        if location:
            logger.debug(f"Ubicación encontrada por código: {code}")
            return location
    
    # Buscar por nombre (case insensitive)
    location = Location.objects.filter(name__iexact=cleaned_name).first()
    if location:
        logger.debug(f"Ubicación encontrada por nombre: {cleaned_name}")
        return location
    
    # Si no existe, crear nueva
    # Generar código único si no se proveyó
    if not code:
        code = _generate_unique_code(cleaned_name)
    
    create_kwargs = {
        "name": cleaned_name,
        "code": code,
        "address": cleaned_name,
        "city": city,
        "region": region,
        "country": country,
    }

    # Solo incluir metadata si el modelo la expone (compatibilidad legacy).
    if hasattr(Location, "created_by"):
        create_kwargs["created_by"] = user
    if hasattr(Location, "updated_by"):
        create_kwargs["updated_by"] = user

    location = Location.objects.create(**create_kwargs)
    
    logger.info(f"Ubicación creada: {cleaned_name} (código: {code})")
    return location


def _generate_unique_code(name: str, max_length: int = 20) -> str:
    """
    Genera un código único basado en el nombre de la ubicación.
    
    Args:
        name: Nombre base para generar el código
        max_length: Longitud máxima del código (default: 20)
    
    Returns:
        str: Código único que no existe en la base de datos
    """
    # Limpiar nombre: solo alfanuméricos y guiones bajos
    base_code = ''.join(c if c.isalnum() else '_' for c in name.upper())
    base_code = base_code[:max_length - 3]  # Dejar espacio para sufijo
    
    # Verificar si ya existe
    candidate = base_code
    suffix = 1
    
    while Location.objects.filter(code=candidate).exists():
        suffix += 1
        suffix_str = f"_{suffix}"
        candidate = f"{base_code[:max_length - len(suffix_str)]}{suffix_str}"
    
    return candidate


def fetch_or_create_location_simple(value: Optional[str]) -> Optional[Location]:
    """
    Versión simplificada para casos donde solo se tiene el nombre.
    
    Args:
        value: Nombre de la ubicación (puede ser None)
    
    Returns:
        Location o None si value es None/vacío
    """
    if not value:
        return None
    
    normalized = value.strip()
    if not normalized:
        return None
    
    return get_or_create_location(name=normalized)


def resolve_location_by_code_or_name(identifier: str) -> Optional[Location]:
    """
    Busca ubicación por código primero, luego por nombre.
    
    Args:
        identifier: Código o nombre de ubicación
    
    Returns:
        Location encontrada o None
    """
    if not identifier:
        return None
    
    # Intentar por código primero
    location = Location.objects.filter(code=identifier).first()
    if location:
        return location
    
    # Intentar por nombre (case insensitive)
    location = Location.objects.filter(name__iexact=identifier).first()
    return location
