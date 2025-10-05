"""
Utilidades compartidas para servicios de contenedores.
Evita duplicación de código entre diferentes importadores.
"""
import re
import logging
from typing import Optional
from datetime import datetime, date, time

import pandas as pd
from django.contrib.auth.models import User

from apps.containers.models import Container, Vessel, ShippingLine, Agency
from apps.core.models import Company, Location

logger = logging.getLogger(__name__)


# ============================================================================
# Formateadores y Normalizadores
# ============================================================================

class ContainerNumberFormatter:
    """Formateador de números de contenedor al formato estándar AAAU 123456-1"""
    
    @staticmethod
    def format(container_number: str) -> str:
        """
        Formatea un número de contenedor al estándar AAAU 123456-1
        
        Args:
            container_number: Número sin formato (ej: AAAU1234561)
            
        Returns:
            Número formateado (ej: AAAU 123456-1)
        """
        if not container_number:
            return ""
        
        # Limpiar
        clean = re.sub(r'[\s-]', '', container_number.upper().strip())
        
        # Patrón: 4 letras + 7 dígitos
        pattern = r'^([A-Z]{4})(\d{6})(\d)$'
        match = re.match(pattern, clean)
        
        if match:
            prefix, number, check = match.groups()
            return f"{prefix} {number}-{check}"
        
        logger.warning(f"Número de contenedor no estándar: {container_number}")
        return container_number
    
    @staticmethod
    def clean(container_number: str) -> str:
        """Limpia un número de contenedor removiendo espacios y guiones"""
        if not container_number:
            return ""
        return re.sub(r'[\s-]', '', container_number.upper().strip())


class ContainerTypeNormalizer:
    """Normaliza tipos de contenedor"""
    
    TYPE_MAP = {
        '20': '20ft',
        '40': '40ft',
        '40HC': '40hc',
        '40 HC': '40hc',
        '40HR': '40hr',
        '40HN': '40hn',
        '45': '45ft',
    }
    
    @classmethod
    def normalize(cls, type_str) -> str:
        """Normaliza el tipo de contenedor"""
        if pd.isna(type_str):
            return '40ft'
        
        type_str = str(type_str).upper().strip()
        return cls.TYPE_MAP.get(type_str, '40ft')


class CDLocationNormalizer:
    """Normaliza nombres de CD"""
    
    CD_MAP = {
        'QUILICURA': 'CD_QUILICURA',
        'CAMPOS': 'CD_CAMPOS',
        'MADERO': 'CD_MADERO',
        'PUERTO MADERO': 'CD_MADERO',
        'PEÑON': 'CD_PENON',
        'EL PEÑON': 'CD_PENON',
    }
    
    @classmethod
    def normalize(cls, cd_str: str) -> str:
        """Normaliza el nombre del CD"""
        if not cd_str:
            return ''
        
        cd_upper = cd_str.upper().strip()
        
        for key, value in cls.CD_MAP.items():
            if key in cd_upper:
                return value
        
        return cd_str


class PortPositionMapper:
    """Mapea puerto a posición inicial del contenedor"""
    
    @staticmethod
    def get_position(port: str) -> str:
        """
        Determina posición inicial según puerto:
        - SAN ANTONIO → CLEP
        - VALPARAÍSO → ZEAL
        """
        if not port:
            return 'EN_PISO'
        
        port_upper = port.upper().strip()
        
        if 'SAN ANTONIO' in port_upper or 'SAI' in port_upper:
            return 'CLEP'
        elif 'VALPARAISO' in port_upper or 'VAP' in port_upper:
            return 'ZEAL'
        
        return 'EN_PISO'


# ============================================================================
# Parseadores de Fechas y Horas
# ============================================================================

class DateTimeParser:
    """Parsea fechas y horas desde diferentes formatos"""
    
    @staticmethod
    def parse_date(value) -> Optional[date]:
        """Parsea una fecha desde Excel o string con múltiples formatos"""
        if pd.isna(value) or value is None or value == "":
            return None
        
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        try:
            # Formatos comunes de fecha en español
            date_formats = [
                "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
                "%d/%m/%y", "%d-%m-%y", 
                "%d.%m.%Y", "%d.%m.%y"
            ]
            
            # Si es string, intentar formatos explícitos primero
            if isinstance(value, str):
                value_clean = value.strip()
                for fmt in date_formats:
                    try:
                        return datetime.strptime(value_clean, fmt).date()
                    except ValueError:
                        continue
            
            # Fallback a pandas con dayfirst=True para formato español
            return pd.to_datetime(value, dayfirst=True, errors='coerce').date()
        except Exception as e:
            logger.warning(f"Error parsing date '{value}': {e}")
            return None
    
    @staticmethod
    def parse_time(value) -> Optional[time]:
        """Parsea una hora desde Excel o string con múltiples formatos"""
        if pd.isna(value) or value is None or value == "":
            return None
        
        if isinstance(value, time):
            return value
        
        if isinstance(value, datetime):
            return value.time()
        
        try:
            # Formatos comunes de hora
            time_formats = [
                "%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p",
                "%H.%M", "%H,%M"
            ]
            
            if isinstance(value, str):
                value_clean = value.strip()
                for fmt in time_formats:
                    try:
                        return datetime.strptime(value_clean, fmt).time()
                    except ValueError:
                        continue
            
            # Manejar valores numéricos (tiempo serial de Excel)
            elif isinstance(value, (int, float)):
                # Excel guarda tiempos como fracciones de día
                total_seconds = value * 86400  # 24 * 60 * 60
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                return time(hours, minutes, seconds)
            
            # Fallback a pandas
            return pd.to_datetime(value).time()
        except Exception as e:
            logger.warning(f"Error parsing time '{value}': {e}")
            return None


# ============================================================================
# Fábrica de Entidades (Get or Create)
# ============================================================================

class EntityFactory:
    """Fábrica centralizada para crear o obtener entidades relacionadas"""
    
    @staticmethod
    def get_or_create_company(name: str, user: Optional[User] = None) -> Company:
        """Obtiene o crea una compañía"""
        if not name or not name.strip():
            name = "Sin Especificar"
        
        cleaned = name.strip()
        code = re.sub(r'[^A-Z0-9]', '', cleaned.upper())[:50] or 'COMPANY'
        
        company, created = Company.objects.get_or_create(
            code=code,
            defaults={
                'name': cleaned,
                'rut': f'{code[:8] or "00000000"}-{code[-1] if len(code) > 8 else "0"}',
                'email': f'{code.lower()}@placeholder.local',
                'phone': '+56 2 0000 0000',
                'address': 'Dirección no especificada',
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if created:
            logger.info(f"Compañía creada: {cleaned}")
        
        return company
    
    @staticmethod
    def get_or_create_shipping_line(name: str, user: Optional[User] = None) -> ShippingLine:
        """Obtiene o crea una línea naviera"""
        if not name or not name.strip():
            name = "Sin Especificar"
        
        cleaned = name.strip()
        code = re.sub(r'[^A-Z0-9]', '', cleaned.upper())[:20] or 'SHIP'
        
        line, created = ShippingLine.objects.get_or_create(
            code=code,
            defaults={
                'name': cleaned,
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if created:
            logger.info(f"Línea naviera creada: {cleaned}")
        
        return line
    
    @staticmethod
    def get_or_create_vessel(name: str, shipping_line: Optional[ShippingLine] = None, 
                            user: Optional[User] = None) -> Optional[Vessel]:
        """Obtiene o crea una nave"""
        if not name or not name.strip():
            return None
        
        cleaned = name.strip()
        
        # Si no hay línea naviera, crear una por defecto
        if not shipping_line:
            shipping_line = EntityFactory.get_or_create_shipping_line('APL', user)
        
        vessel, created = Vessel.objects.get_or_create(
            name=cleaned.upper(),
            defaults={
                'shipping_line': shipping_line,
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if created:
            logger.info(f"Nave creada: {cleaned}")
        
        return vessel
    
    @staticmethod
    def get_or_create_agency(name: str, user: Optional[User] = None) -> Optional[Agency]:
        """Obtiene o crea una agencia"""
        if not name or not name.strip():
            return None
        
        cleaned = name.strip()
        code = re.sub(r'[^A-Z0-9]', '', cleaned.upper())[:20] or 'AG'
        
        agency, created = Agency.objects.get_or_create(
            code=code,
            defaults={
                'name': cleaned,
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if created:
            logger.info(f"Agencia creada: {cleaned}")
        
        return agency
    
    @staticmethod
    def get_or_create_location(name: str, city: str = 'Santiago', 
                               region: str = 'Metropolitana', 
                               user: Optional[User] = None) -> Location:
        """Obtiene o crea una ubicación"""
        if not name or not name.strip():
            name = "Sin Especificar"
        
        cleaned = name.strip().upper()
        
        location, created = Location.objects.get_or_create(
            name=cleaned,
            defaults={
                'address': cleaned,
                'city': city,
                'region': region,
                'country': 'Chile',
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if created:
            logger.info(f"Ubicación creada: {cleaned}")
        
        return location


# ============================================================================
# Detector de Columnas en Excel
# ============================================================================

class ExcelColumnDetector:
    """Detecta columnas en archivos Excel de forma flexible"""
    
    # Mapeos de palabras clave a nombre de columna estándar
    COLUMN_KEYWORDS = {
        'container': ['contenedor', 'container', 'cont'],
        'client': ['cliente', 'client', 'customer'],
        'port': ['puerto', 'port'],
        'eta': ['eta', 'arribo'],
        'type': ['tipo', 'type', 'tamaño', 'size'],
        'tare': ['tara', 'peso vacio', 'tare', 'empty weight'],
        'cargo_weight': ['peso carga', 'cargo weight', 'carga'],
        'total_weight': ['peso total', 'total weight', 'bruto'],
        'seal': ['sello', 'seal', 'precinto'],
        'cargo_description': ['descripcion', 'mercaderia', 'cargo', 'description'],
        'terminal': ['terminal'],
        'agency': ['agencia', 'agency'],
        'shipping_line': ['linea', 'naviera', 'shipping', 'carrier'],
        'release_date': ['fecha liberacion', 'fecha salida', 'release date'],
        'release_time': ['hora liberacion', 'hora salida', 'release time'],
        'scheduled_date': ['fecha programacion', 'fecha entrega', 'scheduled date'],
        'scheduled_time': ['hora programacion', 'hora entrega', 'scheduled time'],
        'cd_location': ['cd', 'destino', 'destination'],
        'demurrage_date': ['demurrage', 'devolucion', 'fecha devolucion'],
    }
    
    @classmethod
    def detect(cls, df: pd.DataFrame) -> dict:
        """
        Detecta columnas en un DataFrame de forma inteligente
        
        Returns:
            Dict con mapeo {nombre_estandar: nombre_columna_real}
        """
        columns = df.columns.tolist()
        detected = {}
        
        for col in columns:
            col_normalized = cls._normalize_column_name(col)
            
            for standard_name, keywords in cls.COLUMN_KEYWORDS.items():
                if any(keyword in col_normalized for keyword in keywords):
                    detected[standard_name] = col
                    break
        
        return detected
    
    @staticmethod
    def _normalize_column_name(col_name: str) -> str:
        """Normaliza nombre de columna para comparación"""
        if not col_name:
            return ""
        
        # Remover BOM, convertir a minúsculas, quitar acentos
        normalized = str(col_name).replace('\ufeff', '').strip().lower()
        
        # Remover caracteres especiales
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        return normalized


# ============================================================================
# Validadores
# ============================================================================

class ContainerValidator:
    """Valida datos de contenedores"""
    
    @staticmethod
    def is_valid_container_number(container_number: str) -> bool:
        """Valida que el número de contenedor sea válido"""
        if not container_number:
            return False
        
        clean = re.sub(r'[\s-]', '', container_number.upper().strip())
        pattern = r'^[A-Z]{4}\d{7}$'
        
        return bool(re.match(pattern, clean))
    
    @staticmethod
    def validate_weight(weight_value) -> bool:
        """Valida que un peso sea válido"""
        if pd.isna(weight_value):
            return False
        
        try:
            weight = float(weight_value)
            return 0 < weight < 100000  # Peso razonable en kg
        except:
            return False
