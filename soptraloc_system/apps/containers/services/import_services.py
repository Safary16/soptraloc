"""
Servicios de importación de contenedores desde archivos Excel.
"""
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
from django.db import transaction
from django.utils import timezone

from apps.containers.models import (
    Container, Vessel, ShippingLine, Agency
)
from apps.core.models import Company, Location

logger = logging.getLogger(__name__)


class ContainerNumberFormatter:
    """Formateador de números de contenedor al formato estándar AAAU 123456-1"""
    
    @staticmethod
    def format_container_number(container_number: str) -> str:
        """
        Formatea un número de contenedor al estándar AAAU 123456-1
        
        Args:
            container_number: Número de contenedor sin formato (ej: AAAU1234561)
            
        Returns:
            Número de contenedor formateado (ej: AAAU 123456-1)
        """
        if not container_number:
            return ""
        
        # Limpiar el número (remover espacios y guiones existentes)
        clean = re.sub(r'[\s-]', '', container_number.upper().strip())
        
        # Patrón: 4 letras + 7 dígitos
        pattern = r'^([A-Z]{4})(\d{6})(\d)$'
        match = re.match(pattern, clean)
        
        if match:
            prefix, number, check = match.groups()
            return f"{prefix} {number}-{check}"
        
        # Si no coincide con el patrón estándar, devolver tal cual
        logger.warning(f"Número de contenedor no estándar: {container_number}")
        return container_number
    
    @staticmethod
    def clean_container_number(container_number: str) -> str:
        """Limpia un número de contenedor removiendo espacios y guiones"""
        if not container_number:
            return ""
        return re.sub(r'[\s-]', '', container_number.upper().strip())


class VesselImportService:
    """
    Servicio para importar contenedores de una nave desde Excel.
    Estado inicial: POR_ARRIBAR
    """
    
    def __init__(self):
        self.formatter = ContainerNumberFormatter()
        self.results = {
            'success': 0,
            'errors': 0,
            'updated': 0,
            'created': 0,
            'messages': []
        }
    
    @transaction.atomic
    def import_from_excel(self, file_path: str, vessel_name: str = None) -> Dict:
        """
        Importa contenedores desde archivo Excel de nave.
        
        Args:
            file_path: Ruta al archivo Excel
            vessel_name: Nombre de la nave (opcional, se puede extraer del Excel)
            
        Returns:
            Diccionario con resultados de la importación
        """
        try:
            # Leer Excel
            df = pd.read_excel(file_path)
            logger.info(f"Leyendo {len(df)} filas del archivo {file_path}")
            
            # Detectar columnas clave (pueden variar entre archivos)
            column_map = self._detect_columns(df)
            
            # Procesar cada fila
            for idx, row in df.iterrows():
                try:
                    self._process_vessel_row(row, column_map, vessel_name)
                except Exception as e:
                    self.results['errors'] += 1
                    self.results['messages'].append(f"Error en fila {idx + 2}: {str(e)}")
                    logger.error(f"Error procesando fila {idx}: {e}", exc_info=True)
            
            self.results['messages'].insert(
                0,
                f"Importación completada: {self.results['created']} creados, "
                f"{self.results['updated']} actualizados, {self.results['errors']} errores"
            )
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error en importación de nave: {e}", exc_info=True)
            self.results['messages'].append(f"Error general: {str(e)}")
            return self.results
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detecta los nombres de las columnas en el DataFrame"""
        columns = df.columns.tolist()
        
        # Mapeo flexible de columnas
        column_map = {}
        
        for col in columns:
            col_lower = str(col).lower()
            
            if 'contenedor' in col_lower or 'container' in col_lower:
                column_map['container'] = col
            elif 'cliente' in col_lower or 'client' in col_lower:
                column_map['client'] = col
            elif 'puerto' in col_lower or 'port' in col_lower:
                column_map['port'] = col
            elif 'eta' in col_lower:
                column_map['eta'] = col
            elif 'tipo' in col_lower or 'type' in col_lower:
                column_map['type'] = col
            elif 'peso' in col_lower and 'vacio' in col_lower:
                column_map['tare'] = col
            elif 'peso' in col_lower and ('carga' in col_lower or 'cargo' in col_lower):
                column_map['cargo_weight'] = col
            elif 'peso' in col_lower and 'total' in col_lower:
                column_map['total_weight'] = col
            elif 'sello' in col_lower or 'seal' in col_lower:
                column_map['seal'] = col
            elif 'descripcion' in col_lower or 'mercaderia' in col_lower:
                column_map['cargo_description'] = col
            elif 'terminal' in col_lower:
                column_map['terminal'] = col
            elif 'agencia' in col_lower or 'agency' in col_lower:
                column_map['agency'] = col
            elif 'linea' in col_lower or 'naviera' in col_lower or 'shipping' in col_lower:
                column_map['shipping_line'] = col
        
        return column_map
    
    def _process_vessel_row(self, row: pd.Series, column_map: Dict, vessel_name: str = None):
        """Procesa una fila del Excel de nave"""
        
        # Obtener número de contenedor
        container_col = column_map.get('container')
        if not container_col or pd.isna(row.get(container_col)):
            return
        
        raw_container_number = str(row[container_col]).strip()
        formatted_number = self.formatter.format_container_number(raw_container_number)
        
        if not formatted_number:
            return
        
        # Buscar o crear contenedor
        container, created = Container.objects.get_or_create(
            container_number=formatted_number,
            defaults={'status': 'POR_ARRIBAR'}
        )
        
        # Actualizar campos
        if column_map.get('type'):
            container.container_type = self._normalize_container_type(row.get(column_map['type']))
        
        # Cliente
        if column_map.get('client') and not pd.isna(row.get(column_map['client'])):
            client_name = str(row[column_map['client']]).strip()
            client = self._get_or_create_client(client_name)
            container.client = client
        
        # Puerto
        if column_map.get('port'):
            container.port = str(row.get(column_map['port'], '')).strip()
        
        # ETA
        if column_map.get('eta') and not pd.isna(row.get(column_map['eta'])):
            container.eta = self._parse_date(row[column_map['eta']])
        
        # Nave
        if vessel_name:
            vessel = self._get_or_create_vessel(vessel_name)
            container.vessel = vessel
        
        # Pesos
        if column_map.get('tare') and not pd.isna(row.get(column_map['tare'])):
            container.weight_empty = float(row[column_map['tare']])
        
        if column_map.get('cargo_weight') and not pd.isna(row.get(column_map['cargo_weight'])):
            container.cargo_weight = float(row[column_map['cargo_weight']])
        
        if column_map.get('total_weight') and not pd.isna(row.get(column_map['total_weight'])):
            container.total_weight = float(row[column_map['total_weight']])
        
        # Sello
        if column_map.get('seal'):
            container.seal_number = str(row.get(column_map['seal'], '')).strip()
        
        # Descripción de carga
        if column_map.get('cargo_description'):
            container.cargo_description = str(row.get(column_map['cargo_description'], '')).strip()
        
        # Terminal
        if column_map.get('terminal') and not pd.isna(row.get(column_map['terminal'])):
            terminal_name = str(row[column_map['terminal']]).strip()
            terminal = self._get_or_create_terminal(terminal_name)
            container.terminal = terminal
        
        # Agencia
        if column_map.get('agency') and not pd.isna(row.get(column_map['agency'])):
            agency_name = str(row[column_map['agency']]).strip()
            agency = self._get_or_create_agency(agency_name)
            container.agency = agency
        
        # Línea naviera
        if column_map.get('shipping_line') and not pd.isna(row.get(column_map['shipping_line'])):
            line_name = str(row[column_map['shipping_line']]).strip()
            shipping_line = self._get_or_create_shipping_line(line_name)
            container.shipping_line = shipping_line
        
        # Estado inicial: POR_ARRIBAR
        if created:
            container.status = 'POR_ARRIBAR'
            container.current_position = 'EN_PISO'
        
        container.save()
        
        if created:
            self.results['created'] += 1
        else:
            self.results['updated'] += 1
        
        self.results['success'] += 1
    
    def _normalize_container_type(self, type_str) -> str:
        """Normaliza el tipo de contenedor"""
        if pd.isna(type_str):
            return '40ft'
        
        type_str = str(type_str).upper().strip()
        
        type_map = {
            '20': '20ft',
            '40': '40ft',
            '40HC': '40hc',
            '40 HC': '40hc',
            '40HR': '40hr',
            '40HN': '40hn',
            '45': '45ft',
        }
        
        return type_map.get(type_str, '40ft')
    
    def _parse_date(self, date_value):
        """Parsea una fecha desde el Excel"""
        if pd.isna(date_value):
            return None
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        try:
            return pd.to_datetime(date_value).date()
        except:
            return None
    
    def _get_or_create_client(self, name: str) -> Company:
        """Obtiene o crea un cliente"""
        code = name.upper().replace(' ', '_')[:50]
        client, _ = Company.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'rut': f'{code}-0',
                'email': f'{code.lower()}@example.com',
                'phone': '+56900000000',
                'address': 'Chile'
            }
        )
        return client
    
    def _get_or_create_vessel(self, name: str) -> Vessel:
        """Obtiene o crea una nave"""
        # Intentar obtener una línea naviera por defecto
        shipping_line, _ = ShippingLine.objects.get_or_create(
            code='APL',
            defaults={'name': 'American President Lines'}
        )
        
        vessel, _ = Vessel.objects.get_or_create(
            name=name.upper().strip(),
            defaults={'shipping_line': shipping_line}
        )
        return vessel
    
    def _get_or_create_terminal(self, name: str) -> Location:
        """Obtiene o crea un terminal"""
        terminal, _ = Location.objects.get_or_create(
            name=name.upper().strip(),
            defaults={
                'address': name,
                'city': 'Valparaíso',
                'region': 'Valparaíso',
                'country': 'Chile'
            }
        )
        return terminal
    
    def _get_or_create_agency(self, name: str) -> Agency:
        """Obtiene o crea una agencia"""
        code = name.upper().replace(' ', '_')[:20]
        agency, _ = Agency.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        return agency
    
    def _get_or_create_shipping_line(self, name: str) -> ShippingLine:
        """Obtiene o crea una línea naviera"""
        code = name.upper().replace(' ', '_')[:20]
        line, _ = ShippingLine.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        return line


class ReleaseScheduleImportService:
    """
    Servicio para importar horarios de liberación desde Excel.
    Actualiza release_date y release_time de contenedores existentes.
    Cambia estado a LIBERADO.
    """
    
    def __init__(self):
        self.formatter = ContainerNumberFormatter()
        self.results = {
            'success': 0,
            'errors': 0,
            'not_found': 0,
            'messages': []
        }
    
    @transaction.atomic
    def import_from_excel(self, file_path: str) -> Dict:
        """Importa horarios de liberación desde Excel"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Procesando liberaciones: {len(df)} filas")
            
            column_map = self._detect_columns(df)
            
            for idx, row in df.iterrows():
                try:
                    self._process_release_row(row, column_map)
                except Exception as e:
                    self.results['errors'] += 1
                    self.results['messages'].append(f"Error en fila {idx + 2}: {str(e)}")
                    logger.error(f"Error procesando liberación fila {idx}: {e}")
            
            self.results['messages'].insert(
                0,
                f"Liberaciones procesadas: {self.results['success']} actualizados, "
                f"{self.results['not_found']} no encontrados, {self.results['errors']} errores"
            )
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error en importación de liberaciones: {e}", exc_info=True)
            self.results['messages'].append(f"Error general: {str(e)}")
            return self.results
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detecta columnas del Excel de liberación"""
        columns = df.columns.tolist()
        column_map = {}
        
        for col in columns:
            col_lower = str(col).lower()
            
            if 'contenedor' in col_lower or 'container' in col_lower:
                column_map['container'] = col
            elif 'fecha' in col_lower and 'liberacion' in col_lower:
                column_map['release_date'] = col
            elif 'hora' in col_lower and 'liberacion' in col_lower:
                column_map['release_time'] = col
            elif 'fecha' in col_lower:
                column_map['release_date'] = col
            elif 'hora' in col_lower:
                column_map['release_time'] = col
        
        return column_map
    
    def _process_release_row(self, row: pd.Series, column_map: Dict):
        """Procesa una fila de liberación"""
        container_col = column_map.get('container')
        if not container_col or pd.isna(row.get(container_col)):
            return
        
        raw_number = str(row[container_col]).strip()
        formatted_number = self.formatter.format_container_number(raw_number)
        
        try:
            container = Container.objects.get(container_number=formatted_number)
        except Container.DoesNotExist:
            self.results['not_found'] += 1
            self.results['messages'].append(f"Contenedor no encontrado: {formatted_number}")
            return
        
        # Actualizar fecha de liberación
        if column_map.get('release_date') and not pd.isna(row.get(column_map['release_date'])):
            container.release_date = self._parse_date(row[column_map['release_date']])
        
        # Actualizar hora de liberación
        if column_map.get('release_time') and not pd.isna(row.get(column_map['release_time'])):
            container.release_time = self._parse_time(row[column_map['release_time']])
        
        # Cambiar estado a LIBERADO
        container.status = 'LIBERADO'
        container.save()
        
        self.results['success'] += 1
    
    def _parse_date(self, date_value):
        """Parsea fecha"""
        if pd.isna(date_value):
            return None
        if isinstance(date_value, datetime):
            return date_value.date()
        try:
            return pd.to_datetime(date_value).date()
        except:
            return None
    
    def _parse_time(self, time_value):
        """Parsea hora"""
        if pd.isna(time_value):
            return None
        if isinstance(time_value, datetime):
            return time_value.time()
        try:
            return pd.to_datetime(time_value).time()
        except:
            return None


class ProgrammingImportService:
    """
    Servicio para importar programación de contenedores desde Excel.
    Actualiza scheduled_date, scheduled_time, cd_location, demurrage_date.
    Cambia estado a PROGRAMADO.
    Determina la posición actual según el puerto de la nave.
    """
    
    def __init__(self):
        self.formatter = ContainerNumberFormatter()
        self.results = {
            'success': 0,
            'errors': 0,
            'not_found': 0,
            'messages': []
        }
    
    @transaction.atomic
    def import_from_excel(self, file_path: str) -> Dict:
        """Importa programación desde Excel"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Procesando programación: {len(df)} filas")
            
            column_map = self._detect_columns(df)
            
            for idx, row in df.iterrows():
                try:
                    self._process_programming_row(row, column_map)
                except Exception as e:
                    self.results['errors'] += 1
                    self.results['messages'].append(f"Error en fila {idx + 2}: {str(e)}")
                    logger.error(f"Error procesando programación fila {idx}: {e}")
            
            self.results['messages'].insert(
                0,
                f"Programación procesada: {self.results['success']} actualizados, "
                f"{self.results['not_found']} no encontrados, {self.results['errors']} errores"
            )
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error en importación de programación: {e}", exc_info=True)
            self.results['messages'].append(f"Error general: {str(e)}")
            return self.results
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detecta columnas del Excel de programación"""
        columns = df.columns.tolist()
        column_map = {}
        
        for col in columns:
            col_lower = str(col).lower()
            
            if 'contenedor' in col_lower or 'container' in col_lower:
                column_map['container'] = col
            elif 'fecha' in col_lower and ('programacion' in col_lower or 'entrega' in col_lower):
                column_map['scheduled_date'] = col
            elif 'hora' in col_lower and ('programacion' in col_lower or 'entrega' in col_lower):
                column_map['scheduled_time'] = col
            elif 'cd' in col_lower or 'destino' in col_lower:
                column_map['cd_location'] = col
            elif 'demurrage' in col_lower or 'devolucion' in col_lower:
                column_map['demurrage_date'] = col
            elif 'tipo' in col_lower:
                column_map['type'] = col
        
        return column_map
    
    def _process_programming_row(self, row: pd.Series, column_map: Dict):
        """Procesa una fila de programación"""
        container_col = column_map.get('container')
        if not container_col or pd.isna(row.get(container_col)):
            return
        
        raw_number = str(row[container_col]).strip()
        formatted_number = self.formatter.format_container_number(raw_number)
        
        try:
            container = Container.objects.get(container_number=formatted_number)
        except Container.DoesNotExist:
            self.results['not_found'] += 1
            self.results['messages'].append(f"Contenedor no encontrado: {formatted_number}")
            return
        
        # Actualizar fecha programada
        if column_map.get('scheduled_date') and not pd.isna(row.get(column_map['scheduled_date'])):
            container.scheduled_date = self._parse_date(row[column_map['scheduled_date']])
        
        # Actualizar hora programada
        if column_map.get('scheduled_time') and not pd.isna(row.get(column_map['scheduled_time'])):
            container.scheduled_time = self._parse_time(row[column_map['scheduled_time']])
        
        # CD de destino
        if column_map.get('cd_location') and not pd.isna(row.get(column_map['cd_location'])):
            cd_raw = str(row[column_map['cd_location']]).strip().upper()
            container.cd_location = self._normalize_cd_location(cd_raw)
        
        # Fecha de demurrage
        if column_map.get('demurrage_date') and not pd.isna(row.get(column_map['demurrage_date'])):
            container.demurrage_date = self._parse_date(row[column_map['demurrage_date']])
        
        # Determinar posición según puerto de la nave
        container.current_position = self._determine_position_by_port(container)
        
        # Cambiar estado a PROGRAMADO
        container.status = 'PROGRAMADO'
        container.save()
        
        self.results['success'] += 1
    
    def _determine_position_by_port(self, container: Container) -> str:
        """
        Determina la posición inicial según el puerto:
        - SAN ANTONIO -> CLEP SAI
        - VALPARAISO -> ZEAL VAP (puede ir directo a CCTI, pero es decisión manual)
        """
        if not container.port:
            return 'EN_PISO'
        
        port = container.port.upper().strip()
        
        if 'SAN ANTONIO' in port or 'SAI' in port:
            return 'CLEP'
        elif 'VALPARAISO' in port or 'VAP' in port:
            return 'ZEAL'
        
        return 'EN_PISO'
    
    def _normalize_cd_location(self, cd_str: str) -> str:
        """Normaliza el nombre del CD"""
        cd_map = {
            'QUILICURA': 'CD_QUILICURA',
            'CAMPOS': 'CD_CAMPOS',
            'MADERO': 'CD_MADERO',
            'PUERTO MADERO': 'CD_MADERO',
            'PEÑON': 'CD_PENON',
            'EL PEÑON': 'CD_PENON',
        }
        
        for key, value in cd_map.items():
            if key in cd_str:
                return value
        
        return cd_str
    
    def _parse_date(self, date_value):
        """Parsea fecha"""
        if pd.isna(date_value):
            return None
        if isinstance(date_value, datetime):
            return date_value.date()
        try:
            return pd.to_datetime(date_value).date()
        except:
            return None
    
    def _parse_time(self, time_value):
        """Parsea hora"""
        if pd.isna(time_value):
            return None
        if isinstance(time_value, datetime):
            return time_value.time()
        try:
            return pd.to_datetime(time_value).time()
        except:
            return None
