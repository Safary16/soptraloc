"""
Importador de Excel de Embarque
Crea contenedores con estado 'por_arribar'
"""
import pandas as pd
from django.utils import timezone
from django.db import transaction
import logging
from apps.containers.models import Container
from apps.events.models import Event
from apps.core.services.excel import normalize_columns, read_excel_with_header_detection
from apps.clientes.matching import resolve_customer


logger = logging.getLogger(__name__)


class EmbarqueImporter:
    """
    Importa datos de embarque desde Excel
    
    Columnas esperadas (se normalizan automáticamente):
    - Container Numbers / Contenedor / Container ID
    - Container Size / Tipo (20', 40', 40HC, etc.)
    - Nave Confirmado / Nave / Buque
    - ETA Confirmada (opcional, fecha estimada de arribo)
    - Weight Kgs / Peso (opcional)
    - Vendor (opcional)
    - Container Seal / Sello (opcional)
    - Cliente / Customer / Consignee / Importador (requerido para Portal Cliente)
    - Puerto (opcional, default: Valparaíso)
    """
    
    COLUMNAS_REQUERIDAS = ['container_id', 'tipo', 'nave', 'cliente']
    
    def __init__(self, archivo_path, usuario=None):
        self.archivo_path = archivo_path
        self.usuario = usuario
        self.resultados = {
            'creados': 0,
            'actualizados': 0,
            'errores': 0,
            'detalles': []
        }
    
    def normalizar_columnas(self, df):
        """Normaliza los nombres de columnas a los esperados"""
        mapeo = {
            'contenedor': 'container_id',
            'container': 'container_id',
            'container numbers': 'container_id',
            'id': 'container_id',
            'tipo contenedor': 'tipo',
            'tipo_contenedor': 'tipo',
            'tipo cont- temperatura': 'tipo',
            'tipo cont-temperatura': 'tipo',
            'container size': 'tipo',
            'buque': 'nave',
            'naviera': 'nave',
            'nave confirmado': 'nave',
            'm/n': 'nave',
            'peso_kg': 'peso',
            'peso (kg)': 'peso',
            'weight kgs': 'peso',
            'peso unidades': 'peso',
            'container seal': 'sello',
            'eta confirmada': 'fecha_eta',
            'viaje confirmado': 'viaje',
            'destino': 'puerto',
            'origin': 'origen',
            'mbl': 'booking',
            'po': 'po',
            'import file': 'import_file',
            'place of receipt': 'place_receipt',
            'cliente': 'cliente',
            'customer': 'cliente',
            'customer name': 'cliente',
            'consignee': 'cliente',
            'consignatario': 'cliente',
            'importador': 'cliente',
            'empresa cliente': 'cliente',
            'rut cliente': 'cliente',
        }
        
        return normalize_columns(df, mapeo)
    
    def validar_tipo(self, tipo):
        """Valida y normaliza el tipo de contenedor"""
        if pd.isna(tipo):
            return '40'
        
        tipo_str = str(tipo).upper().strip().replace("'", "").replace('"', '')
        
        if '20' in tipo_str:
            return '20'
        elif '45' in tipo_str:
            return '45'
        elif 'HC' in tipo_str or 'HIGH' in tipo_str:
            return '40HC'
        else:
            return '40'

    def validar_peso(self, peso):
        """Valida peso de carga y retorna float"""
        if pd.isna(peso):
            return None

        peso_val = float(peso)
        if peso_val <= 0:
            raise ValueError('Peso inválido: debe ser mayor a 0')

        return peso_val
    
    def procesar(self):
        """Procesa el archivo Excel y crea/actualiza contenedores"""
        try:
            # Leer Excel
            df = read_excel_with_header_detection(
                self.archivo_path,
                ['contenedor', 'container numbers', 'container size', 'nave confirmado', 'buque'],
            )
            df = self.normalizar_columnas(df)
            
            # Validar columnas requeridas
            for col in self.COLUMNAS_REQUERIDAS:
                if col not in df.columns:
                    raise ValueError(f"Columna requerida '{col}' no encontrada en el Excel")
            
            # Filtrar filas vacías (donde container_id es NaN o vacío)
            df = df[df['container_id'].notna()]
            df = df[df['container_id'].astype(str).str.strip() != '']
            df = df.reset_index(drop=True)
            
            logger.info(
                'import_embarque_start',
                extra={'archivo': self.archivo_path, 'filas': len(df), 'usuario': self.usuario}
            )

            # Procesar cada fila
            for idx, row in df.iterrows():
                try:
                    with transaction.atomic():
                        # Normalizar container_id (eliminar espacios y guiones)
                        container_id_raw = str(row['container_id']).strip().upper()
                        container_id = Container.normalize_container_id(container_id_raw)

                        if not container_id or container_id == 'NAN':
                            self.resultados['errores'] += 1
                            self.resultados['detalles'].append({
                                'fila': idx + 2,
                                'error': 'Container ID vacío'
                            })
                            continue

                        nave = str(row['nave']).strip() if pd.notna(row['nave']) else ''
                        if not nave:
                            raise ValueError('Nave vacía o inválida')

                        # Datos del contenedor
                        datos = {
                            'tipo': self.validar_tipo(row.get('tipo')),
                            'nave': nave,
                            'viaje': str(row.get('viaje')).strip() if pd.notna(row.get('viaje')) else None,
                            'booking': str(row.get('booking')).strip() if pd.notna(row.get('booking')) else None,
                            'peso_carga': self.validar_peso(row.get('peso')),
                            'vendor': str(row.get('vendor')).strip() if pd.notna(row.get('vendor')) else None,
                            'sello': str(row.get('sello')).strip() if pd.notna(row.get('sello')) else None,
                            'puerto': str(row.get('puerto')).strip() if pd.notna(row.get('puerto')) else 'San Antonio',
                            'estado': 'por_arribar',
                        }

                        # La nave define la empresa propietaria del stock. El CD se
                        # elige después desde Portal Cliente al solicitar horario.
                        cliente_raw = str(row['cliente']).strip() if pd.notna(row['cliente']) else ''
                        empresa = resolve_customer(cliente_raw)
                        datos['cliente'] = cliente_raw
                        datos['cliente_empresa'] = empresa
                        datos['cd_entrega'] = None

                        # Agregar fecha_eta si está disponible
                        if 'fecha_eta' in row.index and pd.notna(row['fecha_eta']):
                            try:
                                # Convertir a datetime si no lo es ya
                                if isinstance(row['fecha_eta'], str):
                                    fecha_eta = pd.to_datetime(row['fecha_eta'])
                                else:
                                    fecha_eta = row['fecha_eta']
                                datos['fecha_eta'] = fecha_eta
                            except Exception as fecha_error:
                                raise ValueError(
                                    f"Fecha ETA inválida '{row['fecha_eta']}': {str(fecha_error)}"
                                )

                        # Crear o actualizar sin retroceder el ciclo de vida de
                        # un contenedor que ya avanzó más allá de por_arribar.
                        estado_inicial = datos.pop('estado')
                        container, created = Container.objects.get_or_create(
                            container_id=container_id,
                            defaults={**datos, 'estado': estado_inicial},
                        )
                        if not created:
                            for field, value in datos.items():
                                if value is not None:
                                    setattr(container, field, value)
                            container.save()

                        if created:
                            self.resultados['creados'] += 1
                            # Registrar evento
                            Event.objects.create(
                                container=container,
                                event_type='import_embarque',
                                detalles={
                                    'nave': datos['nave'],
                                    'tipo': datos['tipo'],
                                    'cliente': datos['cliente'],
                                    'cliente_empresa_id': datos['cliente_empresa'].pk,
                                },
                                usuario=self.usuario
                            )
                        else:
                            self.resultados['actualizados'] += 1

                        self.resultados['detalles'].append({
                            'fila': idx + 2,
                            'container_id': container_id,
                            'accion': 'creado' if created else 'actualizado',
                            'nave': datos['nave'],
                            'cliente': datos['cliente'],
                            'cliente_empresa_id': datos['cliente_empresa'].pk,
                            'cd_entrega': None,
                        })
                
                except Exception as e:
                    logger.warning(
                        'import_embarque_row_error',
                        extra={'fila': idx + 2, 'error': str(e), 'usuario': self.usuario}
                    )
                    self.resultados['errores'] += 1
                    self.resultados['detalles'].append({
                        'fila': idx + 2,
                        'error': str(e)
                    })
            logger.info(
                'import_embarque_finished',
                extra={
                    'creados': self.resultados['creados'],
                    'actualizados': self.resultados['actualizados'],
                    'errores': self.resultados['errores'],
                    'usuario': self.usuario,
                }
            )

            return self.resultados
        
        except Exception as e:
            logger.exception('import_embarque_failed', extra={'usuario': self.usuario})
            raise Exception(f"Error al procesar archivo de embarque: {str(e)}")
