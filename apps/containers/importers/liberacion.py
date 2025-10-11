"""
Importador de Excel de Liberación
Actualiza contenedores de 'por_arribar' a 'liberado'
Asigna posición física según reglas:
- TPS → ZEAL
- STI/PCE → CLEP
"""
import pandas as pd
from django.utils import timezone
from apps.containers.models import Container
from apps.events.models import Event


class LiberacionImporter:
    """
    Importa datos de liberación desde Excel
    
    Columnas esperadas:
    - Container ID / Contenedor
    - Posición Física (TPS, STI, PCE, etc.)
    - Comuna (opcional)
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
        mapeo = {
            'contenedor': 'container_id',
            'container': 'container_id',
            'id': 'container_id',
            'posicion': 'posicion_fisica',
            'posición': 'posicion_fisica',
            'ubicacion': 'posicion_fisica',
            'ubicación': 'posicion_fisica',
            'terminal': 'posicion_fisica',
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
            df = self.normalizar_columnas(df)
            
            # Validar columnas requeridas
            for col in self.COLUMNAS_REQUERIDAS:
                if col not in df.columns:
                    raise ValueError(f"Columna requerida '{col}' no encontrada en el Excel")
            
            # Procesar cada fila
            for idx, row in df.iterrows():
                try:
                    container_id = str(row['container_id']).strip().upper()
                    
                    if not container_id or container_id == 'NAN':
                        self.resultados['errores'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 2,
                            'error': 'Container ID vacío'
                        })
                        continue
                    
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
                    
                    # Actualizar contenedor
                    container.estado = 'liberado'
                    container.posicion_fisica = posicion_mapeada
                    container.fecha_liberacion = timezone.now()
                    
                    # Comuna si viene en el Excel
                    if 'comuna' in df.columns and pd.notna(row.get('comuna')):
                        container.comuna = str(row['comuna']).strip()
                    
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
