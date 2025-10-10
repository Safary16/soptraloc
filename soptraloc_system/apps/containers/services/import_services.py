"""
Servicios de importación de contenedores desde archivos Excel.
Utiliza módulo compartido de utilidades para evitar duplicación.
"""
import logging
from typing import Dict
import pandas as pd
from django.db import transaction

from apps.containers.models import Container
from apps.containers.services.utils import (
    ContainerNumberFormatter,
    ContainerTypeNormalizer,
    CDLocationNormalizer,
    PortPositionMapper,
    DateTimeParser,
    EntityFactory,
    ExcelColumnDetector,
)

logger = logging.getLogger(__name__)


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
            
            # Detectar columnas clave (usando detector compartido)
            column_map = ExcelColumnDetector.detect(df)
            
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
    
    def _process_vessel_row(self, row: pd.Series, column_map: Dict, vessel_name: str = None):
        """Procesa una fila del Excel de nave"""
        
        # Obtener número de contenedor
        container_col = column_map.get('container')
        if not container_col or pd.isna(row.get(container_col)):
            return
        
        raw_container_number = str(row[container_col]).strip()
        formatted_number = self.formatter.format(raw_container_number)
        
        if not formatted_number:
            return
        
        # Buscar o crear contenedor
        container, created = Container.objects.get_or_create(
            container_number=formatted_number,
            defaults={'status': 'POR_ARRIBAR'}
        )
        
        # Tipo de contenedor (usando normalizador compartido)
        if column_map.get('type'):
            container.container_type = ContainerTypeNormalizer.normalize(row.get(column_map['type']))
        
        # Cliente (usando EntityFactory compartida)
        if column_map.get('client') and not pd.isna(row.get(column_map['client'])):
            client_name = str(row[column_map['client']]).strip()
            container.client = EntityFactory.get_or_create_company(client_name)
        
        # Puerto
        if column_map.get('port'):
            container.port = str(row.get(column_map['port'], '')).strip()
        
        # ETA (usando DateTimeParser compartido)
        if column_map.get('eta') and not pd.isna(row.get(column_map['eta'])):
            container.eta = DateTimeParser.parse_date(row[column_map['eta']])
        
        # Nave (usando EntityFactory compartida)
        if vessel_name:
            container.vessel = EntityFactory.get_or_create_vessel(vessel_name)
        
        # Pesos - CRÍTICO: Siempre intentar extraer
        peso_encontrado = False
        
        if column_map.get('tare') and not pd.isna(row.get(column_map['tare'])):
            try:
                container.weight_empty = float(row[column_map['tare']])
                peso_encontrado = True
            except (ValueError, TypeError) as e:
                logger.warning(f"Error convirtiendo tara para {formatted_number}: {e}")
        
        if column_map.get('cargo_weight') and not pd.isna(row.get(column_map['cargo_weight'])):
            try:
                container.cargo_weight = float(row[column_map['cargo_weight']])
                peso_encontrado = True
            except (ValueError, TypeError) as e:
                logger.warning(f"Error convirtiendo peso carga para {formatted_number}: {e}")
        
        if column_map.get('total_weight') and not pd.isna(row.get(column_map['total_weight'])):
            try:
                container.total_weight = float(row[column_map['total_weight']])
                peso_encontrado = True
            except (ValueError, TypeError) as e:
                logger.warning(f"Error convirtiendo peso total para {formatted_number}: {e}")
        
        # Advertencia si NO se encontró ningún peso
        if not peso_encontrado:
            logger.warning(f"⚠️ CONTENEDOR {formatted_number}: Sin datos de peso en Excel")
            self.results['messages'].append(f"⚠️ {formatted_number}: Sin datos de peso")
        
        # Sello
        if column_map.get('seal'):
            container.seal_number = str(row.get(column_map['seal'], '')).strip()
        
        # Descripción de carga
        if column_map.get('cargo_description'):
            container.cargo_description = str(row.get(column_map['cargo_description'], '')).strip()
        
        # Terminal (usando EntityFactory compartida)
        if column_map.get('terminal') and not pd.isna(row.get(column_map['terminal'])):
            terminal_name = str(row[column_map['terminal']]).strip()
            container.terminal = EntityFactory.get_or_create_location(terminal_name, 'Valparaíso', 'Valparaíso')
        
        # Agencia (usando EntityFactory compartida)
        if column_map.get('agency') and not pd.isna(row.get(column_map['agency'])):
            agency_name = str(row[column_map['agency']]).strip()
            container.agency = EntityFactory.get_or_create_agency(agency_name)
        
        # Línea naviera (usando EntityFactory compartida)
        if column_map.get('shipping_line') and not pd.isna(row.get(column_map['shipping_line'])):
            line_name = str(row[column_map['shipping_line']]).strip()
            container.shipping_line = EntityFactory.get_or_create_shipping_line(line_name)
        
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
            
            column_map = ExcelColumnDetector.detect(df)
            
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
    
    def _process_release_row(self, row: pd.Series, column_map: Dict):
        """Procesa una fila de liberación"""
        container_col = column_map.get('container')
        if not container_col or pd.isna(row.get(container_col)):
            return
        
        raw_number = str(row[container_col]).strip()
        formatted_number = self.formatter.format(raw_number)
        
        try:
            container = Container.objects.get(container_number=formatted_number)
        except Container.DoesNotExist:
            self.results['not_found'] += 1
            self.results['messages'].append(f"Contenedor no encontrado: {formatted_number}")
            return
        
        # Actualizar fecha de liberación (usando DateTimeParser compartido)
        if column_map.get('release_date') and not pd.isna(row.get(column_map['release_date'])):
            container.release_date = DateTimeParser.parse_date(row[column_map['release_date']])
        
        # Actualizar hora de liberación (usando DateTimeParser compartido)
        if column_map.get('release_time') and not pd.isna(row.get(column_map['release_time'])):
            container.release_time = DateTimeParser.parse_time(row[column_map['release_time']])
        
        # Cambiar estado a LIBERADO
        container.status = 'LIBERADO'
        container.save()
        
        self.results['success'] += 1


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
            
            column_map = ExcelColumnDetector.detect(df)
            
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
    
    def _process_programming_row(self, row: pd.Series, column_map: Dict):
        """Procesa una fila de programación"""
        container_col = column_map.get('container')
        if not container_col or pd.isna(row.get(container_col)):
            return
        
        raw_number = str(row[container_col]).strip()
        formatted_number = self.formatter.format(raw_number)
        
        try:
            container = Container.objects.get(container_number=formatted_number)
        except Container.DoesNotExist:
            self.results['not_found'] += 1
            self.results['messages'].append(f"Contenedor no encontrado: {formatted_number}")
            return
        
        # Actualizar fecha programada (usando DateTimeParser compartido)
        if column_map.get('scheduled_date') and not pd.isna(row.get(column_map['scheduled_date'])):
            container.scheduled_date = DateTimeParser.parse_date(row[column_map['scheduled_date']])
        
        # Actualizar hora programada (usando DateTimeParser compartido)
        if column_map.get('scheduled_time') and not pd.isna(row.get(column_map['scheduled_time'])):
            container.scheduled_time = DateTimeParser.parse_time(row[column_map['scheduled_time']])
        
        # CD de destino (usando CDLocationNormalizer compartido)
        if column_map.get('cd_location') and not pd.isna(row.get(column_map['cd_location'])):
            cd_raw = str(row[column_map['cd_location']]).strip()
            container.cd_location = CDLocationNormalizer.normalize(cd_raw)
        
        # Fecha de demurrage (usando DateTimeParser compartido)
        if column_map.get('demurrage_date') and not pd.isna(row.get(column_map['demurrage_date'])):
            container.demurrage_date = DateTimeParser.parse_date(row[column_map['demurrage_date']])
        
        # Determinar posición según puerto (usando PortPositionMapper compartido)
        if container.port:
            container.current_position = PortPositionMapper.get_position(container.port)
        
        # Cambiar estado a PROGRAMADO
        container.status = 'PROGRAMADO'
        container.save()
        
        self.results['success'] += 1
