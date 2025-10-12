"""
Importador de Excel de Embarque
Crea contenedores con estado 'por_arribar'
"""
import pandas as pd
from django.utils import timezone
from apps.containers.models import Container
from apps.events.models import Event


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
    - Puerto (opcional, default: Valparaíso)
    """
    
    COLUMNAS_REQUERIDAS = ['container_id', 'tipo', 'nave']
    
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
        # Limpiar caracteres especiales en nombres de columnas
        df.columns = df.columns.str.replace('\xa0', ' ', regex=False)
        df.columns = df.columns.str.strip()
        
        mapeo = {
            # Container ID variations
            'contenedor': 'container_id',
            'container': 'container_id',
            'container numbers': 'container_id',
            'container number': 'container_id',
            'id': 'container_id',
            'nº contenedor': 'container_id',
            'n° contenedor': 'container_id',
            'numero contenedor': 'container_id',
            'container id': 'container_id',
            'container_id': 'container_id',
            
            # Tipo/Size variations
            'tipo contenedor': 'tipo',
            'tipo_contenedor': 'tipo',
            'container size': 'tipo',
            'size': 'tipo',
            'tamaño': 'tipo',
            'tipo': 'tipo',
            
            # Nave variations
            'buque': 'nave',
            'naviera': 'nave',
            'nave confirmado': 'nave',
            'nave': 'nave',
            'm/n': 'nave',
            'vessel': 'nave',
            
            # Peso variations
            'peso_kg': 'peso',
            'peso (kg)': 'peso',
            'weight kgs': 'peso',
            'peso unidades': 'peso',
            'peso': 'peso',
            'weight': 'peso',
            
            # Other fields
            'container seal': 'sello',
            'sello': 'sello',
            'eta confirmada': 'fecha_eta',
            'eta': 'fecha_eta',
            'fecha arribo': 'fecha_eta',
            'viaje confirmado': 'viaje',
            'viaje': 'viaje',
            'voyage': 'viaje',
            'destino': 'puerto',
            'puerto': 'puerto',
            'origin': 'origen',
            'origen': 'origen',
            'mbl': 'booking',
            'booking': 'booking',
            'bl': 'booking',
            'po': 'po',
            'vendor': 'vendor',
        }
        
        df.columns = df.columns.str.lower().str.strip()
        df.rename(columns=mapeo, inplace=True)
        return df
    
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
    
    def procesar(self):
        """Procesa el archivo Excel y crea/actualiza contenedores"""
        try:
            # Leer Excel
            df = pd.read_excel(self.archivo_path)
            
            # Eliminar filas completamente vacías
            df = df.dropna(how='all')
            
            # Normalizar columnas
            df = self.normalizar_columnas(df)
            
            # Debug: Log columnas encontradas
            print(f"DEBUG - Columnas encontradas: {list(df.columns)}")
            
            # Validar columnas requeridas
            columnas_faltantes = []
            for col in self.COLUMNAS_REQUERIDAS:
                if col not in df.columns:
                    columnas_faltantes.append(col)
            
            if columnas_faltantes:
                raise ValueError(
                    f"Columnas requeridas no encontradas: {columnas_faltantes}. "
                    f"Columnas disponibles: {list(df.columns)}"
                )
            
            # Filtrar filas donde las columnas requeridas estén vacías
            df_filtrado = df[
                df['container_id'].notna() & 
                (df['container_id'] != '') &
                (df['container_id'].astype(str).str.upper() != 'NAN')
            ]
            
            if len(df_filtrado) == 0:
                raise ValueError(
                    f"No se encontraron filas válidas con datos. "
                    f"Total filas en Excel: {len(df)}, "
                    f"Filas después de filtrar vacías: {len(df_filtrado)}"
                )
            
            print(f"DEBUG - Filas a procesar: {len(df_filtrado)} de {len(df)} totales")
            
            # Procesar cada fila
            for idx, row in df_filtrado.iterrows():
                try:
                    container_id = str(row['container_id']).strip().upper()
                    
                    # Datos del contenedor
                    datos = {
                        'tipo': self.validar_tipo(row.get('tipo')),
                        'nave': str(row['nave']).strip() if pd.notna(row['nave']) else 'N/A',
                        'viaje': str(row['viaje']).strip() if pd.notna(row.get('viaje')) else None,
                        'booking': str(row['booking']).strip() if pd.notna(row.get('booking')) or pd.notna(row.get('mbl')) else None,
                        'peso_carga': float(row['peso']) if pd.notna(row.get('peso')) else None,
                        'vendor': str(row['vendor']).strip() if pd.notna(row.get('vendor')) else None,
                        'sello': str(row['sello']).strip() if pd.notna(row.get('sello')) else None,
                        'puerto': str(row['puerto']).strip() if pd.notna(row.get('puerto')) else 'San Antonio',
                        'estado': 'por_arribar',
                    }
                    
                    # Agregar fecha_eta si está disponible
                    if 'fecha_eta' in row.index and pd.notna(row['fecha_eta']):
                        try:
                            # Convertir a datetime si no lo es ya
                            if isinstance(row['fecha_eta'], str):
                                fecha_eta = pd.to_datetime(row['fecha_eta'])
                            else:
                                fecha_eta = row['fecha_eta']
                            datos['fecha_eta'] = fecha_eta
                        except Exception:
                            pass  # Si falla la conversión, omitir fecha_eta
                    
                    # Crear o actualizar
                    container, created = Container.objects.update_or_create(
                        container_id=container_id,
                        defaults=datos
                    )
                    
                    if created:
                        self.resultados['creados'] += 1
                        # Registrar evento
                        Event.objects.create(
                            container=container,
                            event_type='import_embarque',
                            detalles={
                                'nave': datos['nave'],
                                'tipo': datos['tipo'],
                            },
                            usuario=self.usuario
                        )
                    else:
                        self.resultados['actualizados'] += 1
                    
                    self.resultados['detalles'].append({
                        'fila': idx + 2,
                        'container_id': container_id,
                        'accion': 'creado' if created else 'actualizado',
                        'nave': datos['nave']
                    })
                
                except Exception as e:
                    self.resultados['errores'] += 1
                    self.resultados['detalles'].append({
                        'fila': idx + 2,
                        'error': str(e)
                    })
            
            return self.resultados
        
        except Exception as e:
            raise Exception(f"Error al procesar archivo: {str(e)}")
