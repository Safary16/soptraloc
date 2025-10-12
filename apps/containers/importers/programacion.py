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
    
    Columnas esperadas (se normalizan automáticamente):
    - Contenedor / Container ID
    - Fecha de Programacion / Fecha Programada
    - Cliente
    - Bodega / CD / Centro Distribución (puede venir en formato "6020 - PEÑÓN")
    - Fecha Demurrage (opcional, fecha de vencimiento)
    - WK Demurrage (opcional, días desde liberación, ej: "45 días")
    - Dirección (opcional)
    - Observaciones (opcional)
    
    Nota: Si existe Fecha Demurrage, se usa directamente. 
    Si existe WK Demurrage, se calcula desde fecha_liberacion.
    """
    
    COLUMNAS_REQUERIDAS = ['container_id', 'fecha_programada', 'cd']
    
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
        # Limpiar caracteres especiales en nombres de columnas
        df.columns = df.columns.str.replace('\xa0', ' ', regex=False)
        df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)  # Múltiples espacios a uno
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.lower()
        
        mapeo = {
            'contenedor': 'container_id',
            'container': 'container_id',
            'id': 'container_id',
            'fecha': 'fecha_programada',
            'fecha programacion': 'fecha_programada',
            'fecha_programacion': 'fecha_programada',
            'fecha de programacion': 'fecha_programada',
            'centro distribucion': 'cd',
            'centro_distribucion': 'cd',
            'destino': 'cd',
            'bodega': 'cd',
            'direccion': 'direccion_entrega',
            'dirección': 'direccion_entrega',
            'fecha demurrage': 'fecha_demurrage',
            'wk demurrage': 'dias_demurrage',
            'ransportista': 'transportista',  # Nota: en Excel falta la T
            'transportista': 'transportista',
            'hora': 'hora_programada',
            'producto': 'contenido',
            'referencia': 'referencia',
            'nave': 'nave',
            'med': 'medida',
            'tipo': 'tipo_contenedor',
            'cajas': 'cantidad_cajas',
        }
        
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
        """Busca un CD por nombre o código, extrayendo nombre de formato 'codigo - nombre'"""
        if pd.isna(cd_str):
            return None
        
        cd_str = str(cd_str).strip()
        
        # Si viene en formato "6020 - PEÑÓN", extraer la parte del nombre
        if ' - ' in cd_str:
            partes = cd_str.split(' - ')
            codigo_parte = partes[0].strip()
            nombre_parte = partes[1].strip()
            
            # Buscar primero por código
            cd = CD.objects.filter(codigo__iexact=codigo_parte, activo=True).first()
            if cd:
                return cd
            
            # Si no, buscar por nombre
            cd = CD.objects.filter(nombre__icontains=nombre_parte, activo=True).first()
            if cd:
                return cd
        
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
            
            # Filtrar filas vacías (donde container_id es NaN o vacío)
            df = df[df['container_id'].notna()]
            df = df[df['container_id'].astype(str).str.strip() != '']
            df = df.reset_index(drop=True)
            
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
                    
                    # Parsear fecha y combinar con hora si está disponible
                    fecha_programada = self.parsear_fecha(row['fecha_programada'])
                    if not fecha_programada:
                        self.resultados['errores'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 2,
                            'container_id': container_id,
                            'error': 'Fecha programada inválida'
                        })
                        continue
                    
                    # Combinar con hora si está disponible
                    if 'hora_programada' in df.columns and pd.notna(row.get('hora_programada')):
                        try:
                            # Intentar parsear hora (puede venir como datetime, time, o string)
                            hora_prog = row['hora_programada']
                            if isinstance(hora_prog, str):
                                # Si es string, intentar parsear
                                hora_time = pd.to_datetime(hora_prog, format='%H:%M:%S').time()
                            elif hasattr(hora_prog, 'time'):
                                # Si es datetime, extraer time
                                hora_time = hora_prog.time()
                            else:
                                # Si es time object, usar directamente
                                hora_time = hora_prog
                            
                            # Combinar fecha con hora
                            fecha_programada = timezone.make_aware(
                                datetime.combine(fecha_programada.date(), hora_time)
                            )
                        except Exception:
                            # Si falla, mantener fecha_programada original (sin hora)
                            pass
                    
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
                    
                    # Cliente (puede venir de Programacion pero actualizar Container)
                    cliente = str(row.get('cliente', 'N/A')).strip() if pd.notna(row.get('cliente')) else 'N/A'
                    
                    # Actualizar datos del contenedor desde programación
                    if 'contenido' in df.columns and pd.notna(row.get('contenido')):
                        container.contenido = str(row['contenido']).strip()
                    
                    if 'referencia' in df.columns and pd.notna(row.get('referencia')):
                        container.referencia = str(row['referencia']).strip()
                    
                    # Actualizar nave si viene en el Excel de programación
                    if 'nave' in df.columns and pd.notna(row.get('nave')):
                        nave_prog = str(row['nave']).strip()
                        if nave_prog:
                            container.nave = nave_prog
                    
                    # Combinar MED y TIPO para obtener tipo completo (ej: 40H = 40HC)
                    if 'medida' in df.columns and 'tipo_contenedor' in df.columns:
                        medida = str(row.get('medida', '')).strip()
                        tipo = str(row.get('tipo_contenedor', '')).strip().upper()
                        if medida and tipo:
                            tipo_completo = f"{medida}{tipo}"
                            if 'H' in tipo and medida == '40':
                                container.tipo = '40HC'
                            elif medida == '20':
                                container.tipo = '20'
                            elif medida == '45':
                                container.tipo = '45'
                    
                    container.save()
                    
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
                    
                    # Actualizar fecha_demurrage si está disponible en el Excel
                    if 'fecha_demurrage' in df.columns and pd.notna(row.get('fecha_demurrage')):
                        try:
                            fecha_demurrage = self.parsear_fecha(row['fecha_demurrage'])
                            if fecha_demurrage:
                                container.fecha_demurrage = fecha_demurrage
                                container.save()
                        except Exception:
                            pass  # Si falla el parseo, continuar sin fecha_demurrage
                    
                    # Alternativamente, calcular desde WK DEMURRAGE (días)
                    elif 'dias_demurrage' in df.columns and pd.notna(row.get('dias_demurrage')):
                        try:
                            dias = int(str(row['dias_demurrage']).replace(' días', '').replace('días', '').strip())
                            if container.fecha_liberacion:
                                container.fecha_demurrage = container.fecha_liberacion + timedelta(days=dias)
                                container.save()
                        except (ValueError, TypeError):
                            pass  # Si falla la conversión, continuar sin fecha_demurrage
                    
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
