"""
Comando para cargar automáticamente conductores del sistema
Se ejecuta automáticamente en el deploy de Render
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.drivers.models import Driver
import random


class Command(BaseCommand):
    help = 'Carga automáticamente conductores con datos realistas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=82,
            help='Número de conductores a crear (default: 82)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recarga incluso si ya existen conductores',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Verificar si ya existen conductores
        if Driver.objects.count() > 0 and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Ya existen {Driver.objects.count()} conductores en el sistema')
            )
            return

        self.stdout.write(f'🚗 Creando {count} conductores...')

        drivers_data = self.generate_drivers_data(count)
        
        with transaction.atomic():
            drivers_created = 0
            
            for data in drivers_data:
                driver = Driver.objects.create(
                    nombre=data['nombre'],
                    rut=data['rut'],
                    telefono=data['telefono'],
                    ppu=data['ppu'],
                    tracto=data['tracto'],
                    tipo_conductor=data['tipo_conductor'],
                    estado=data['estado'],
                    ubicacion_actual=data['ubicacion_actual']
                )
                drivers_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ ¡Completado! Se crearon {drivers_created} conductores')
        )

    def generate_drivers_data(self, count):
        """Generar datos realistas para conductores"""
        first_names = [
            'Carlos', 'Miguel', 'Juan', 'Luis', 'José', 'Antonio', 'Francisco',
            'Manuel', 'David', 'Daniel', 'Roberto', 'Rafael', 'Eduardo', 'Fernando',
            'Jorge', 'Alejandro', 'Ricardo', 'Andrés', 'Javier', 'Pedro',
            'María', 'Ana', 'Carmen', 'Rosa', 'Patricia', 'Laura', 'Elena',
            'Sandra', 'Mónica', 'Claudia', 'Silvia', 'Adriana', 'Gabriela',
            'Sergio', 'Raúl', 'Óscar', 'Pablo', 'Ramón', 'Enrique', 'Héctor',
            'Víctor', 'Arturo', 'Ignacio', 'Diego', 'Rubén', 'Felipe', 'Mario',
            'Alberto', 'Cristian', 'Rodrigo', 'Mauricio', 'Sebastián', 'Marcelo',
            'Lucía', 'Isabel', 'Beatriz', 'Pilar', 'Teresa', 'Cristina', 'Marta',
            'Verónica', 'Natalia', 'Daniela', 'Carolina', 'Valentina', 'Camila'
        ]
        
        last_names = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez',
            'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
            'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez',
            'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez',
            'Serrano', 'Blanco', 'Suárez', 'Molina', 'Castro', 'Ortiz', 'Rubio',
            'Marín', 'Sanz', 'Iglesias', 'Núñez', 'Medina', 'Garrido'
        ]
        
        tipos_conductor = ['LEASING', 'LOCALERO', 'TRONCO_PM', 'TRONCO']
        estados = ['OPERATIVO', 'OPERATIVO', 'OPERATIVO', 'PANNE', 'PERMISO']  # Más operativos
        ubicaciones = ['CCTI', 'CD_QUILICURA', 'CD_CAMPOS', 'CD_MADERO', 'CD_PENON']
        
        drivers = []
        used_ruts = set()
        used_ppus = set()
        
        for i in range(count):
            # Generar nombre
            first_name = random.choice(first_names)
            last_name1 = random.choice(last_names)
            last_name2 = random.choice(last_names)
            nombre = f"{first_name} {last_name1} {last_name2}"
            
            # Generar RUT único (formato chileno)
            while True:
                rut = f"{random.randint(10000000, 25000000)}-{random.choice('0123456789K')}"
                if rut not in used_ruts:
                    used_ruts.add(rut)
                    break
            
            # Generar PPU única
            while True:
                letters = ''.join(random.choices('BCDFGHJKLMNPQRSTVWXYZ', k=2))
                numbers = ''.join(random.choices('0123456789', k=2))
                suffix = random.choice(['12', '23', '34', '45', '56', '67', '78', '89'])
                ppu = f"{letters}{numbers}{suffix}"
                if ppu not in used_ppus:
                    used_ppus.add(ppu)
                    break
            
            # Generar teléfono chileno
            telefono = f"+56{random.randint(900000000, 999999999)}"
            
            drivers.append({
                'nombre': nombre,
                'rut': rut,
                'telefono': telefono,
                'ppu': ppu,
                'tracto': f"TR{random.randint(100, 999)}",
                'tipo_conductor': random.choice(tipos_conductor),
                'estado': random.choice(estados),
                'ubicacion_actual': random.choice(ubicaciones)
            })
            
        return drivers