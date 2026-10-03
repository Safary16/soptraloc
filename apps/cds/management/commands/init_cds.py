"""
Comando para inicializar los Centros de Distribución con un catálogo
GENÉRICO y ficticio (sin referencias a ninguna operación real).

SoptraLoc es un producto independiente: los nombres, direcciones y
coordenadas de este catálogo son ejemplos neutrales reemplazables por
cualquier deployment. El objetivo es dejar el sistema utilizable sin
arrastrar datos de clientes reales.
"""
from django.core.management.base import BaseCommand
from apps.cds.models import CD


class Command(BaseCommand):
    help = 'Inicializa los Centros de Distribución con un catálogo genérico ficticio'

    def handle(self, *args, **options):
        """
        Crea el catálogo base: CDs de cliente (con distintas mecánicas de
        descarga) + patios propios para retorno de vacíos.
        """
        cds_data = [
            {
                'nombre': 'CD Bodega Norte',
                'codigo': 'BODNORTE',
                'direccion': 'Av. Longitudinal 18899, San Bernardo, Región Metropolitana',
                'comuna': 'San Bernardo',
                'tipo': 'cliente',
                'lat': -33.6223,
                'lng': -70.7089,
                'requiere_espera_carga': False,  # Drop & Hook
                'permite_soltar_contenedor': True,
                'tiempo_promedio_descarga_min': 30,
                'activo': True,
            },
            {
                'nombre': 'CD Distribución Poniente',
                'codigo': 'DISPON',
                'direccion': 'Camino Industrial 9710, Pudahuel, Región Metropolitana',
                'comuna': 'Pudahuel',
                'tipo': 'cliente',
                'lat': -33.3947,
                'lng': -70.7642,
                'requiere_espera_carga': True,  # Conductor espera
                'permite_soltar_contenedor': False,
                'tiempo_promedio_descarga_min': 90,
                'activo': True,
            },
            {
                'nombre': 'CD Alimentos Sur',
                'codigo': 'ALIMSUR',
                'direccion': 'Av. El Parque 1000, Pudahuel, Región Metropolitana',
                'comuna': 'Pudahuel',
                'tipo': 'cliente',
                'lat': -33.3986,
                'lng': -70.7489,
                'requiere_espera_carga': True,
                'permite_soltar_contenedor': False,
                'tiempo_promedio_descarga_min': 90,
                'activo': True,
            },
            {
                'nombre': 'CD Retail Quilicura',
                'codigo': 'RETAILQ',
                'direccion': 'Eduardo Frei Montalva 8301, Quilicura, Región Metropolitana',
                'comuna': 'Quilicura',
                'tipo': 'cliente',
                'lat': -33.3511,
                'lng': -70.7282,
                'requiere_espera_carga': True,
                'permite_soltar_contenedor': False,
                'tiempo_promedio_descarga_min': 90,
                'activo': True,
            },
            {
                'nombre': 'Patio Central',
                'codigo': 'PATIOCEN',
                'direccion': 'Camino Los Agricultores, Parcela 41, Maipú, Región Metropolitana',
                'comuna': 'Maipú',
                'tipo': 'patio',
                'lat': -33.5104,
                'lng': -70.8284,
                'requiere_espera_carga': False,
                'permite_soltar_contenedor': True,
                'tiempo_promedio_descarga_min': 20,
                'capacidad_vacios': 200,
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