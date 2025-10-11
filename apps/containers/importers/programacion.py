"""
Importador de Excel de Programación
Crea programaciones y actualiza contenedores a 'programado'
Verifica si requieren alerta de 48h sin conductor
"""
import pandas as pd
from django.utils import timezone
from datetime import datetime, timedelta
from apps.containers.models import Container
from apps.programaciones.models import Programacion
from apps.cds.models import CD
from apps.events.models import Event


class ProgramacionImporter:
    """
    Importa datos de programación desde Excel
    
    Columnas esperadas:
    - Container ID / Contenedor
    - Fecha Programada
    - Cliente
    - CD / Centro Distribución (nombre o código)
    - Dirección (opcional)
    - Observaciones (opcional)
    """
    
    COLUMNAS_REQUERIDAS = ['container_id', 'fecha_programada', 'cliente', 'cd']
    
    def __init__(self, archivo_path, usuario=None):
        self.archivo_path = archivo_path
        self.usuario = usuario
        self.resultados = {
            'programados': 0,
            'no_encontrados': 0,
            'cd_no_encontrado': 0,
            'errores': 0,
            'alertas_generadas': 0,
            'detalles': []
        }
    
    def normalizar_columnas(self, df):
        """Normaliza los nombres de columnas a los esperados"""
        mapeo = {
            'contenedor': 'container_id',
            'container': 'container_id',
            'id': 'container_id',
            'fecha': 'fecha_programada',
            'fecha programacion': 'fecha_programada',
            'fecha_programacion': 'fecha_programada',
            'centro distribucion': 'cd',
            'centro_distribucion': 'cd',
            'destino': 'cd',
            'direccion': 'direccion_entrega',
            'dirección': 'direccion_entrega',
        }
        
        df.columns = df.columns.str.lower().str.strip()
        df.rename(columns=mapeo, inplace=True)
        return df
    
    def parsear_fecha(self, fecha_str):
        """Parsea diferentes formatos de fecha"""
        if pd.isna(fecha_str):
            return None
        
        # Si ya es datetime
        if isinstance(fecha_str, datetime):
            return timezone.make_aware(fecha_str) if timezone.is_naive(fecha_str) else fecha_str
        
        # Intentar parsear string
        fecha_str = str(fecha_str).strip()
        
        formatos = [
            '%d/%m/%Y %H:%M',
            '%d-%m-%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
        ]
        
        for formato in formatos:
            try:
                dt = datetime.strptime(fecha_str, formato)
                return timezone.make_aware(dt)
            except ValueError:
                continue
        
        raise ValueError(f"Formato de fecha no reconocido: {fecha_str}")
    
    def buscar_cd(self, cd_str):
        """Busca un CD por nombre o código"""
        if pd.isna(cd_str):
            return None
        
        cd_str = str(cd_str).strip()
        
        # Buscar por código exacto
        cd = CD.objects.filter(codigo__iexact=cd_str, activo=True).first()
        if cd:
            return cd
        
        # Buscar por nombre (contiene)
        cd = CD.objects.filter(nombre__icontains=cd_str, activo=True).first()
        if cd:
            return cd
        
        return None
    
    def procesar(self):
        """Procesa el archivo Excel y crea programaciones"""
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
                    
                    # Parsear fecha
                    fecha_programada = self.parsear_fecha(row['fecha_programada'])
                    if not fecha_programada:
                        self.resultados['errores'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 2,
                            'container_id': container_id,
                            'error': 'Fecha programada inválida'
                        })
                        continue
                    
                    # Buscar CD
                    cd = self.buscar_cd(row['cd'])
                    if not cd:
                        self.resultados['cd_no_encontrado'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 2,
                            'container_id': container_id,
                            'error': f"CD no encontrado: {row['cd']}"
                        })
                        continue
                    
                    # Cliente
                    cliente = str(row['cliente']).strip() if pd.notna(row['cliente']) else 'N/A'
                    
                    # Crear o actualizar programación
                    programacion, created = Programacion.objects.update_or_create(
                        container=container,
                        defaults={
                            'cd': cd,
                            'fecha_programada': fecha_programada,
                            'cliente': cliente,
                            'direccion_entrega': str(row.get('direccion_entrega', '')).strip() if pd.notna(row.get('direccion_entrega')) else '',
                            'observaciones': str(row.get('observaciones', '')).strip() if pd.notna(row.get('observaciones')) else '',
                        }
                    )
                    
                    # Actualizar estado del contenedor
                    if container.estado in ['por_arribar', 'liberado', 'secuenciado']:
                        container.cambiar_estado('programado', self.usuario)
                    
                    # Verificar si requiere alerta 48h
                    if programacion.verificar_alerta():
                        self.resultados['alertas_generadas'] += 1
                        Event.objects.create(
                            container=container,
                            event_type='alerta_48h',
                            detalles={
                                'fecha_programada': fecha_programada.isoformat(),
                                'horas_restantes': programacion.horas_hasta_programacion,
                            },
                            usuario=self.usuario
                        )
                    
                    # Registrar evento de importación
                    if created:
                        Event.objects.create(
                            container=container,
                            event_type='import_programacion',
                            detalles={
                                'fecha_programada': fecha_programada.isoformat(),
                                'cliente': cliente,
                                'cd': cd.nombre,
                            },
                            usuario=self.usuario
                        )
                    
                    self.resultados['programados'] += 1
                    self.resultados['detalles'].append({
                        'fila': idx + 2,
                        'container_id': container_id,
                        'fecha': fecha_programada.strftime('%Y-%m-%d %H:%M'),
                        'cd': cd.nombre,
                        'alerta': programacion.requiere_alerta,
                        'accion': 'creado' if created else 'actualizado'
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
