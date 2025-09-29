import csv
import io
from datetime import datetime, time
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.containers.models import Container, ShippingLine, Vessel, Agency
from apps.core.models import Company, Location

User = get_user_model()


class Command(BaseCommand):
    help = 'Importa contenedores desde un archivo CSV basado en el formato del Excel de Walmart'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV')
        parser.add_argument('--user', type=str, help='ID del usuario que ejecuta la importación', default=1)
        parser.add_argument('--dry-run', action='store_true', help='Ejecuta sin guardar cambios')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        user_id = options['user']
        dry_run = options['dry_run']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f'Usuario con ID {user_id} no existe')

        if dry_run:
            self.stdout.write(self.style.WARNING('Ejecutando en modo DRY RUN - No se guardarán cambios'))

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                self.process_csv(file, user, dry_run)
        except FileNotFoundError:
            raise CommandError(f'Archivo {csv_file_path} no encontrado')
        except Exception as e:
            raise CommandError(f'Error procesando archivo: {str(e)}')

    def process_csv(self, file, user, dry_run):
        """Procesa el archivo CSV y crea los contenedores."""
        content = file.read()
        
        # Detectar el delimitador
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(content).delimiter
        
        # Reiniciar el archivo
        file_like = io.StringIO(content)
        reader = csv.DictReader(file_like, delimiter=delimiter)
        
        containers_created = 0
        containers_updated = 0
        errors = []

        # Mapeo de columnas del Excel a campos del modelo
        column_mapping = {
            'ID': 'sequence_id',
            'Cliente': 'client_name',
            'Puerto': 'port',
            'ETA': 'eta',
            'Nave': 'vessel_name',
            'Contenedor': 'container_number',
            'Status': 'status',
            'Sello': 'seal_number',
            'Medida': 'container_type',
            'Descripción': 'cargo_description',
            'Peso Carga': 'cargo_weight',
            'Peso Total': 'total_weight',
            'Terminal': 'terminal_name',
            'Fecha Liberación': 'release_date',
            'Hora Liberación': 'release_time',
            'Fecha Programación': 'scheduled_date',
            'Hora Programación': 'scheduled_time',
            'Fecha Arribo CD': 'cd_arrival_date',
            'Hora Arribo CD': 'cd_arrival_time',
            'CD': 'cd_location',
            'Fecha Descarga (GPS)': 'discharge_date',
            'Hora Descarga': 'discharge_time',
            'Fecha Devolución': 'return_date',
            'EIR': 'has_eir',
            'Agencia': 'agency_name',
            'Cía Naviera/Línea': 'shipping_line_name',
            'Dep/Dev': 'deposit_return',
            'Días Libres': 'free_days',
            'Demurrage': 'demurrage_date',
            'Sobreestadía Región (x ciclo 2 horas)': 'overtime_2h',
            'Sobreestadía (x ciclo de 4 horas)': 'overtime_4h',
            'Almc': 'storage_location',
            'Días Extras de Almacenaje': 'extra_storage_days',
            'E.CHASIS': 'chassis_status',
            'Tipo de Servicio': 'service_type',
            'Servicio Adicional': 'additional_service',
            'OBS 1': 'observation_1',
            'OBS 2': 'observation_2',
            'Servicio Directo': 'direct_service',
            'Fecha Actualización': 'last_update_date',
            'Hora Actualización': 'last_update_time',
            'Días Calculados': 'calculated_days',
        }

        for row_num, row in enumerate(reader, start=2):
            try:
                with transaction.atomic():
                    # Mapear columnas
                    mapped_data = {}
                    for excel_col, model_field in column_mapping.items():
                        if excel_col in row:
                            mapped_data[model_field] = row[excel_col].strip() if row[excel_col] else None

                    container_data = self.process_container_data(mapped_data, user)
                    
                    if not dry_run:
                        container, created = self.create_or_update_container(container_data, user)
                        if created:
                            containers_created += 1
                            self.stdout.write(f"Creado: {container.container_number}")
                        else:
                            containers_updated += 1
                            self.stdout.write(f"Actualizado: {container.container_number}")
                    else:
                        self.stdout.write(f"[DRY RUN] Procesaría: {mapped_data.get('container_number', 'SIN_NUMERO')}")

            except Exception as e:
                error_msg = f"Error en fila {row_num}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))

        # Resumen
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nImportación completada:\n'
                    f'- Contenedores creados: {containers_created}\n'
                    f'- Contenedores actualizados: {containers_updated}\n'
                    f'- Errores: {len(errors)}'
                )
            )
        else:
            self.stdout.write(self.style.WARNING('Modo DRY RUN completado'))

        if errors:
            self.stdout.write(self.style.ERROR('\nErrores encontrados:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))

    def process_container_data(self, data, user):
        """Procesa y valida los datos del contenedor."""
        processed_data = {}
        
        # Procesar campos básicos
        processed_data['sequence_id'] = self.parse_int(data.get('sequence_id'))
        processed_data['container_number'] = data.get('container_number', '').upper()
        processed_data['port'] = data.get('port', '')
        processed_data['cargo_description'] = data.get('cargo_description', '') or ''
        processed_data['seal_number'] = data.get('seal_number', '') or ''
        processed_data['cd_location'] = data.get('cd_location', '') or ''
        processed_data['deposit_return'] = data.get('deposit_return', '') or ''
        processed_data['storage_location'] = data.get('storage_location', '') or ''
        processed_data['additional_service'] = data.get('additional_service', '') or ''
        processed_data['observation_1'] = data.get('observation_1', '') or ''
        processed_data['observation_2'] = data.get('observation_2', '') or ''
        processed_data['direct_service'] = data.get('direct_service', '') or ''
        
        # Procesar status
        status_mapping = {
            'Por Arribar': 'POR_ARRIBAR',
            'En Secuencia': 'EN_SECUENCIA',
            'Descargado': 'DESCARGADO',
            'Liberado': 'LIBERADO',
            'Programado': 'PROGRAMADO',
            'Finalizado': 'FINALIZADO',
            'TRG': 'TRG',
            'Secuenciado': 'SECUENCIADO',
        }
        status = data.get('status', '')
        processed_data['status'] = status_mapping.get(status, 'available')
        
        # Procesar tipo de contenedor
        container_type_mapping = {
            '20': '20ft',
            '40': '40ft',
            '40HC': '40hc',
            '40HR': '40hr',
            '40HN': '40hn',
            '20ST': '20st',
            '40H': '40h',
        }
        container_type = data.get('container_type', '')
        processed_data['container_type'] = container_type_mapping.get(container_type, '40ft')
        
        # Procesar tipo de servicio
        service_type_mapping = {
            'Directo': 'DIRECTO',
            'Indirecto Depósito': 'INDIRECTO_DEPOSITO',
            'Reefer': 'REEFER',
        }
        service_type = data.get('service_type', '')
        processed_data['service_type'] = service_type_mapping.get(service_type, 'INDIRECTO_DEPOSITO')
        
        # Procesar pesos
        processed_data['cargo_weight'] = self.parse_decimal(data.get('cargo_weight'))
        processed_data['total_weight'] = self.parse_decimal(data.get('total_weight'))
        
        # Procesar números enteros
        processed_data['free_days'] = self.parse_int(data.get('free_days', '0'))
        processed_data['overtime_2h'] = self.parse_int(data.get('overtime_2h', '0'))
        processed_data['overtime_4h'] = self.parse_int(data.get('overtime_4h', '0'))
        processed_data['extra_storage_days'] = self.parse_int(data.get('extra_storage_days', '0'))
        processed_data['chassis_status'] = self.parse_int(data.get('chassis_status', '0'))
        processed_data['calculated_days'] = self.parse_int(data.get('calculated_days', '0'))
        
        # Procesar fechas
        processed_data['eta'] = self.parse_date(data.get('eta'))
        processed_data['release_date'] = self.parse_date(data.get('release_date'))
        processed_data['scheduled_date'] = self.parse_date(data.get('scheduled_date'))
        processed_data['cd_arrival_date'] = self.parse_date(data.get('cd_arrival_date'))
        processed_data['discharge_date'] = self.parse_date(data.get('discharge_date'))
        processed_data['return_date'] = self.parse_date(data.get('return_date'))
        processed_data['demurrage_date'] = self.parse_date(data.get('demurrage_date'))
        processed_data['last_update_date'] = self.parse_date(data.get('last_update_date'))
        
        # Procesar horas
        processed_data['release_time'] = self.parse_time(data.get('release_time'))
        processed_data['scheduled_time'] = self.parse_time(data.get('scheduled_time'))
        processed_data['cd_arrival_time'] = self.parse_time(data.get('cd_arrival_time'))
        processed_data['discharge_time'] = self.parse_time(data.get('discharge_time'))
        processed_data['last_update_time'] = self.parse_time(data.get('last_update_time'))
        
        # Procesar boolean
        processed_data['has_eir'] = self.parse_boolean(data.get('has_eir'))
        
        # Procesar relaciones
        processed_data['client'] = self.get_or_create_company(data.get('client_name'), user)
        processed_data['vessel'] = self.get_or_create_vessel(data.get('vessel_name'), user)
        processed_data['agency'] = self.get_or_create_agency(data.get('agency_name'), user)
        processed_data['shipping_line'] = self.get_or_create_shipping_line(data.get('shipping_line_name'), user)
        processed_data['terminal'] = self.get_or_create_location(data.get('terminal_name'), user)
        
        return processed_data

    def create_or_update_container(self, data, user):
        """Crea o actualiza un contenedor."""
        container_number = data['container_number']
        
        try:
            container = Container.objects.get(container_number=container_number)
            # Actualizar campos existentes
            for field, value in data.items():
                if value is not None:
                    setattr(container, field, value)
            container.updated_by = user
            container.save()
            return container, False
        except Container.DoesNotExist:
            # Crear nuevo contenedor
            data['created_by'] = user
            data['updated_by'] = user
            data['owner_company'] = data.get('client') or Company.objects.first()
            container = Container.objects.create(**data)
            return container, True

    def get_or_create_company(self, name, user):
        """Obtiene o crea una compañía."""
        if not name:
            return None
        
        company, created = Company.objects.get_or_create(
            name=name,
            defaults={
                'created_by': user,
                'updated_by': user,
                'rut': f'DEFAULT-{name[:10]}',  # RUT temporal
            }
        )
        return company

    def get_or_create_vessel(self, name, user):
        """Obtiene o crea una nave."""
        if not name:
            return None
        
        # Buscar shipping line por defecto
        default_shipping_line, _ = ShippingLine.objects.get_or_create(
            name='Sin Especificar',
            defaults={
                'code': 'DEFAULT',
                'created_by': user,
                'updated_by': user,
            }
        )
        
        vessel, created = Vessel.objects.get_or_create(
            name=name,
            defaults={
                'shipping_line': default_shipping_line,
                'created_by': user,
                'updated_by': user,
            }
        )
        return vessel

    def get_or_create_agency(self, name, user):
        """Obtiene o crea una agencia."""
        if not name:
            return None
        
        agency, created = Agency.objects.get_or_create(
            name=name,
            defaults={
                'code': name[:20].upper().replace(' ', '_'),
                'created_by': user,
                'updated_by': user,
            }
        )
        return agency

    def get_or_create_shipping_line(self, name, user):
        """Obtiene o crea una línea naviera."""
        if not name:
            return None
        
        shipping_line, created = ShippingLine.objects.get_or_create(
            name=name,
            defaults={
                'code': name[:20].upper().replace(' ', '_'),
                'created_by': user,
                'updated_by': user,
            }
        )
        return shipping_line

    def get_or_create_location(self, name, user):
        """Obtiene o crea una ubicación."""
        if not name:
            return None
        
        location, created = Location.objects.get_or_create(
            name=name,
            defaults={
                'city': 'Valparaíso',
                'region': 'Valparaíso',
                'country': 'Chile',
                'created_by': user,
                'updated_by': user,
            }
        )
        return location

    def parse_date(self, date_str):
        """Parsea una fecha desde string."""
        if not date_str:
            return None
        
        # Intentar varios formatos de fecha
        date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None

    def parse_time(self, time_str):
        """Parsea una hora desde string."""
        if not time_str:
            return None
        
        # Intentar varios formatos de hora
        time_formats = ['%H:%M', '%H:%M:%S', '%I:%M %p']
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        
        return None

    def parse_decimal(self, value_str):
        """Parsea un decimal desde string."""
        if not value_str:
            return None
        
        try:
            # Remover separadores de miles y reemplazar coma decimal
            cleaned = value_str.replace('.', '').replace(',', '.')
            return Decimal(cleaned)
        except:
            return None

    def parse_int(self, value_str):
        """Parsea un entero desde string."""
        if not value_str:
            return 0
        
        try:
            return int(float(value_str.replace(',', '.')))
        except:
            return 0

    def parse_boolean(self, value_str):
        """Parsea un boolean desde string."""
        if not value_str:
            return False
        
        return value_str.lower() in ['true', '1', 'yes', 'sí', 'si', 'x']