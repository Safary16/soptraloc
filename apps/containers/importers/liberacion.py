"""
Importador de Excel de Liberación
Actualiza contenedores de 'por_arribar' a 'liberado'
Asigna posición física según reglas:
- TPS → ZEAL
- STI/PCE → CLEP
"""
import pandas as pd
from django.utils import timezone
from datetime import datetime
from apps.containers.models import Container
from apps.events.models import Event


class LiberacionImporter:
    """
    Importa datos de liberación desde Excel
    
    Columnas esperadas (se normalizan automáticamente):
    - Contenedor / Container ID
    - Almacen / Posición Física (TPS, STI, PCE, etc.) - Se mapea según reglas
    - Devolucion Vacio / Depot (nombre del depósito para devolución)
    - Peso Unidades (opcional, actualiza peso si es más preciso)
    - Comuna (opcional)
    - Fecha Salida (opcional, puede usarse para cálculos)
    
    Mapeo automático de posiciones:
    - TPS → ZEAL
    - STI / PCE → CLEP
    """
    
    COLUMNAS_REQUERIDAS = ['container_id', 'posicion_fisica']
    
    MAPEO_POSICIONES = {
        'TPS': 'ZEAL',
        'STI': 'CLEP',
        'PCE': 'CLEP',
    }
    
    def __init__(self, archivo_path, usuario=None):
        self.archivo_path = archivo_path
        self.usuario = usuario
        self.resultados = {
            'liberados': 0,
            'no_encontrados': 0,
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
            'id': 'container_id',
            'nº contenedor': 'container_id',
            'n° contenedor': 'container_id',
            'numero contenedor': 'container_id',
            'container id': 'container_id',
            'container_id': 'container_id',
            
            # Posicion variations
            'posicion': 'posicion_fisica',
            'posición': 'posicion_fisica',
            'ubicacion': 'posicion_fisica',
            'ubicación': 'posicion_fisica',
            'terminal': 'posicion_fisica',
            'almacen': 'posicion_fisica',
            'almacén': 'posicion_fisica',
            'posicion fisica': 'posicion_fisica',
            'posicion_fisica': 'posicion_fisica',
            
            # Deposito variations
            'devolucion vacio': 'deposito_devolucion',
            'devolución vacio': 'deposito_devolucion',
            'devolucion vacío': 'deposito_devolucion',
            'devolución vacío': 'deposito_devolucion',
            'depot': 'deposito_devolucion',
            'deposito': 'deposito_devolucion',
            'depósito': 'deposito_devolucion',
            
            # Other fields
            'peso unidades': 'peso',
            'peso': 'peso',
            'fecha salida': 'fecha_liberacion',
            'fecha liberacion': 'fecha_liberacion',
            'fecha_liberacion': 'fecha_liberacion',
            'hora salida': 'hora_liberacion',
            'hora': 'hora_liberacion',
            'm/n': 'nave',
            'nave': 'nave',
            'cliente': 'cliente',
            'ref': 'referencia',
            'referencia': 'referencia',
            'despacho': 'despacho',
            'tipo cont- temperatura': 'tipo',
            'tipo': 'tipo',
            'comuna': 'comuna',
        }
        
        df.columns = df.columns.str.lower().str.strip()
        df.rename(columns=mapeo, inplace=True)
        return df
    
    def mapear_posicion(self, posicion_original):
        """Mapea la posición física según reglas de negocio"""
        if pd.isna(posicion_original):
            return None
        
        posicion = str(posicion_original).strip().upper()
        
        # Buscar en el mapeo
        for key, value in self.MAPEO_POSICIONES.items():
            if key in posicion:
                return value
        
        # Si no está en el mapeo, retornar la original
        return posicion
    
    def procesar(self):
        """Procesa el archivo Excel y actualiza contenedores a liberado"""
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
            # Para liberación, también necesitamos posicion_fisica
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
                    
                    # Buscar contenedor
                    try:
                        container = Container.objects.get(container_id=container_id)
                    except Container.DoesNotExist:
                        self.resultados['no_encontrados'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 2,
                            'container_id': container_id,
                            'error': 'Contenedor no encontrado en el sistema'
                        })
                        continue
                    
                    # Mapear posición física
                    posicion_original = row.get('posicion_fisica')
                    posicion_mapeada = self.mapear_posicion(posicion_original)
                    
                    # Parsear fecha y hora de liberación
                    fecha_liberacion = timezone.now()
                    if 'fecha_liberacion' in df.columns and pd.notna(row.get('fecha_liberacion')):
                        try:
                            fecha_lib = pd.to_datetime(row['fecha_liberacion'])
                            # Combinar con hora si está disponible
                            if 'hora_liberacion' in df.columns and pd.notna(row.get('hora_liberacion')):
                                hora_lib = pd.to_datetime(str(row['hora_liberacion']), format='%H:%M:%S').time()
                                fecha_liberacion = timezone.make_aware(datetime.combine(fecha_lib.date(), hora_lib))
                            else:
                                fecha_liberacion = timezone.make_aware(fecha_lib)
                        except Exception:
                            fecha_liberacion = timezone.now()
                    
                    # Actualizar contenedor
                    container.estado = 'liberado'
                    container.posicion_fisica = posicion_mapeada
                    container.fecha_liberacion = fecha_liberacion
                    
                    # Comuna si viene en el Excel
                    if 'comuna' in df.columns and pd.notna(row.get('comuna')):
                        container.comuna = str(row['comuna']).strip()
                    
                    # Depósito de devolución si viene en el Excel
                    if 'deposito_devolucion' in df.columns and pd.notna(row.get('deposito_devolucion')):
                        container.deposito_devolucion = str(row['deposito_devolucion']).strip()
                    
                    # Actualizar peso_carga si viene en el Excel (puede ser más preciso que el inicial)
                    if 'peso' in df.columns and pd.notna(row.get('peso')):
                        try:
                            container.peso_carga = float(row['peso'])
                        except (ValueError, TypeError):
                            pass
                    
                    # Cliente y referencia
                    if 'cliente' in df.columns and pd.notna(row.get('cliente')):
                        container.cliente = str(row['cliente']).strip()
                    
                    if 'referencia' in df.columns and pd.notna(row.get('referencia')):
                        container.referencia = str(row['referencia']).strip()
                    
                    # Fecha salida puede usarse para calcular fecha_demurrage
                    # Nota: La fecha_demurrage real vendrá del Excel de programación
                    # Aquí solo la guardamos si está disponible en este Excel
                    if 'fecha_salida' in df.columns and pd.notna(row.get('fecha_salida')):
                        try:
                            if isinstance(row['fecha_salida'], str):
                                fecha_salida = pd.to_datetime(row['fecha_salida'])
                            else:
                                fecha_salida = row['fecha_salida']
                            # Por ahora no calculamos demurrage aquí, esperamos el Excel de programación
                        except Exception:
                            pass
                    
                    container.save()
                    
                    # Registrar evento
                    Event.objects.create(
                        container=container,
                        event_type='import_liberacion',
                        detalles={
                            'posicion_original': str(posicion_original) if pd.notna(posicion_original) else None,
                            'posicion_mapeada': posicion_mapeada,
                            'comuna': container.comuna,
                        },
                        usuario=self.usuario
                    )
                    
                    self.resultados['liberados'] += 1
                    self.resultados['detalles'].append({
                        'fila': idx + 2,
                        'container_id': container_id,
                        'posicion': posicion_mapeada,
                        'accion': 'liberado'
                    })
                
                except Exception as e:
                    self.resultados['errores'] += 1
                    self.resultados['detalles'].append({
                        'fila': idx + 2,
                        'container_id': container_id if 'container_id' in locals() else 'N/A',
                        'error': str(e)
                    })
            
            return self.resultados
        
        except Exception as e:
            raise Exception(f"Error al procesar archivo: {str(e)}")
