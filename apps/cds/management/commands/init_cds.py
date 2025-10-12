"""
Comando para inicializar los Centros de Distribución con datos reales
"""
from django.core.management.base import BaseCommand
from apps.cds.models import CD


class Command(BaseCommand):
    help = 'Inicializa los Centros de Distribución con direcciones y coordenadas reales'

    def handle(self, *args, **options):
        """
        Inicializa los 4 CDs principales + CCTI con direcciones exactas
        """
        
        cds_data = [
            {
                'nombre': 'CD El Peñón',
                'codigo': 'PENON',
                'direccion': 'Avenida Presidente Jorge Alessandri Rodriguez 18899, San Bernardo, Región Metropolitana',
                'comuna': 'San Bernardo',
                'tipo': 'cliente',
                'lat': -33.6223,  # Coordenadas aproximadas
                'lng': -70.7089,
                'requiere_espera_carga': False,  # Drop & Hook
                'permite_soltar_contenedor': True,  # Puede soltar y seguir
                'tiempo_promedio_descarga_min': 30,  # Rápido por drop & hook
                'activo': True,
            },
            {
                'nombre': 'CD Puerto Madero',
                'codigo': 'MADERO',
                'direccion': 'Puerto Madero 9710, Pudahuel, Región Metropolitana',
                'comuna': 'Pudahuel',
                'tipo': 'cliente',
                'lat': -33.3947,
                'lng': -70.7642,
                'requiere_espera_carga': True,  # Conductor espera
                'permite_soltar_contenedor': False,
                'tiempo_promedio_descarga_min': 90,  # Espera completa
                'activo': True,
            },
            {
                'nombre': 'CD Campos de Chile',
                'codigo': 'CAMPOS',
                'direccion': 'Av. El Parque 1000, Pudahuel, Región Metropolitana',
                'comuna': 'Pudahuel',
                'tipo': 'cliente',
                'lat': -33.3986,
                'lng': -70.7489,
                'requiere_espera_carga': True,  # Conductor espera
                'permite_soltar_contenedor': False,
                'tiempo_promedio_descarga_min': 90,
                'activo': True,
            },
            {
                'nombre': 'CD Quilicura',
                'codigo': 'QUILICURA',
                'direccion': 'Eduardo Frei Montalva 8301, Quilicura, Región Metropolitana',
                'comuna': 'Quilicura',
                'tipo': 'cliente',
                'lat': -33.3511,
                'lng': -70.7282,
                'requiere_espera_carga': True,  # Conductor espera
                'permite_soltar_contenedor': False,
                'tiempo_promedio_descarga_min': 90,
                'activo': True,
            },
            {
                'nombre': 'CCTI Base de Operaciones',
                'codigo': 'CCTI',
                'direccion': 'Camino Los Agricultores, Parcela 41, Maipú, Región Metropolitana',
                'comuna': 'Maipú',
                'tipo': 'ccti',
                'lat': -33.5104,
                'lng': -70.8284,
                'requiere_espera_carga': False,
                'permite_soltar_contenedor': True,
                'tiempo_promedio_descarga_min': 20,
                'capacidad_vacios': 200,  # Capacidad de contenedores vacíos
                'vacios_actuales': 0,
                'activo': True,
            },
        ]
        
        created = 0
        updated = 0
        
        for cd_data in cds_data:
            cd, created_flag = CD.objects.update_or_create(
                codigo=cd_data['codigo'],
                defaults={
                    k: v for k, v in cd_data.items() if k != 'codigo'
                }
            )
            
            if created_flag:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Creado: {cd.nombre}')
                )
            else:
                updated += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Actualizado: {cd.nombre}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✨ Proceso completado: {created} creados, {updated} actualizados'
            )
        )
        
        # Mostrar resumen
        self.stdout.write('\n📊 Resumen de CDs:')
        self.stdout.write('-' * 80)
        for cd in CD.objects.all().order_by('tipo', 'nombre'):
            tipo_icon = '🏢' if cd.tipo == 'cliente' else '🏭'
            drop_hook = '✅ Drop & Hook' if cd.permite_soltar_contenedor else '❌ Espera descarga'
            self.stdout.write(
                f'{tipo_icon} {cd.codigo:12} | {cd.nombre:30} | {drop_hook} | {cd.tiempo_promedio_descarga_min} min'
            )
        self.stdout.write('-' * 80)
