"""
Importador de Conductores desde Excel
Crea objetos Driver con datos de conductores.xlsx
"""
import pandas as pd
from django.utils import timezone
from apps.drivers.models import Driver


class ConductorImporter:
    """
    Importa conductores desde Excel
    
    Columnas esperadas (header en fila 1):
    - N°
    - Conductor (nombre completo)
    - PPU (Patente del vehículo)
    - RUT
    - Teléfono
    - Tracto
    - COORDINADOR
    - FAENA
    - ASISTENCIA 06-10
    - OBSERVACIONES
    """
    
    def __init__(self, archivo_path, usuario=None):
        self.archivo_path = archivo_path
        self.usuario = usuario
        self.resultados = {
            'creados': 0,
            'actualizados': 0,
            'errores': 0,
            'detalles': []
        }
    
    def limpiar_rut(self, rut):
        """Limpia y formatea RUT chileno"""
        if pd.isna(rut):
            return None
        
        # Convertir a string y quitar espacios
        rut_str = str(rut).strip().upper()
        
        # Quitar puntos y guiones
        rut_str = rut_str.replace('.', '').replace('-', '')
        
        # Si tiene K al final, es válido
        if not rut_str:
            return None
        
        return rut_str
    
    def limpiar_telefono(self, telefono):
        """Limpia y formatea teléfono"""
        if pd.isna(telefono):
            return None
        
        # Convertir a string y quitar espacios
        tel_str = str(telefono).strip()
        
        # Quitar caracteres no numéricos excepto +
        tel_str = ''.join(c for c in tel_str if c.isdigit() or c == '+')
        
        # Agregar +56 si es teléfono chileno sin código
        if tel_str and not tel_str.startswith('+'):
            if len(tel_str) == 9:  # Teléfono móvil chileno
                tel_str = '+56' + tel_str
        
        return tel_str if tel_str else None
    
    def es_operativo(self, asistencia):
        """Determina si el conductor está operativo según asistencia"""
        if pd.isna(asistencia):
            return False
        
        asistencia_str = str(asistencia).upper().strip()
        return 'OPERATIVO' in asistencia_str or 'SI' in asistencia_str
    
    def procesar(self):
        """Procesa el archivo Excel y crea/actualiza conductores"""
        try:
            # Leer Excel (header en fila 1)
            df = pd.read_excel(self.archivo_path, header=1)
            
            # Verificar columnas requeridas
            columnas_requeridas = ['Conductor', 'PPU']
            for col in columnas_requeridas:
                if col not in df.columns:
                    raise ValueError(f"Columna requerida '{col}' no encontrada en el Excel")
            
            # Procesar cada fila
            for idx, row in df.iterrows():
                try:
                    nombre = str(row['Conductor']).strip()
                    
                    # Saltar filas vacías
                    if not nombre or nombre == 'nan' or pd.isna(row['Conductor']):
                        continue
                    
                    # Extraer datos
                    ppu = str(row['PPU']).strip().upper() if pd.notna(row.get('PPU')) else None
                    rut = self.limpiar_rut(row.get('RUT'))
                    telefono = self.limpiar_telefono(row.get('Teléfono'))
                    
                    # Determinar si está presente (operativo)
                    presente = self.es_operativo(row.get('ASISTENCIA 06-10'))
                    
                    # Buscar o crear conductor
                    driver, created = Driver.objects.get_or_create(
                        nombre=nombre,
                        defaults={
                            'rut': rut or '',
                            'telefono': telefono or '',
                            'presente': presente,
                            'activo': True,
                            'max_entregas_dia': 8,  # Valor por defecto
                        }
                    )
                    
                    if created:
                        self.resultados['creados'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 3,  # +3 porque hay 2 filas de header
                            'accion': 'creado',
                            'conductor': nombre,
                            'presente': presente
                        })
                    else:
                        # Actualizar datos existentes
                        if rut:
                            driver.rut = rut
                        if telefono:
                            driver.telefono = telefono
                        driver.presente = presente
                        driver.activo = True
                        driver.save()
                        
                        self.resultados['actualizados'] += 1
                        self.resultados['detalles'].append({
                            'fila': idx + 3,
                            'accion': 'actualizado',
                            'conductor': nombre,
                            'presente': presente
                        })
                
                except Exception as e:
                    self.resultados['errores'] += 1
                    self.resultados['detalles'].append({
                        'fila': idx + 3,
                        'error': str(e),
                        'conductor': nombre if 'nombre' in locals() else 'Desconocido'
                    })
            
            return self.resultados
        
        except Exception as e:
            raise Exception(f"Error al procesar archivo: {str(e)}")
