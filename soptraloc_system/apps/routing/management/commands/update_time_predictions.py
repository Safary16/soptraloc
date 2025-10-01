"""
Comando para actualizar predicciones ML de tiempos.
Ejecutar diariamente con cron o Celery Beat.

Uso:
    python manage.py update_time_predictions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.routing.ml_service import TimePredictionML


class Command(BaseCommand):
    help = 'Actualiza predicciones ML de tiempos de viaje y operaciones'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Mostrar análisis de precisión del modelo'
        )
        parser.add_argument(
            '--suggestions',
            action='store_true',
            help='Mostrar sugerencias de optimización'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write(self.style.HTTP_INFO('🤖 ACTUALIZACIÓN DE PREDICCIONES ML'))
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write('')
        
        # Actualizar predicciones
        self.stdout.write('Actualizando predicciones...')
        result = TimePredictionML.update_all_predictions()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Actualizadas {result['location_pairs']} rutas "
                f"y {result['operations']} operaciones"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"🕐 Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )
        self.stdout.write('')
        
        # Análisis de precisión
        if options['analyze']:
            self.stdout.write(self.style.HTTP_INFO('-'*60))
            self.stdout.write(self.style.HTTP_INFO('📊 ANÁLISIS DE PRECISIÓN'))
            self.stdout.write(self.style.HTTP_INFO('-'*60))
            self.stdout.write('')
            
            accuracy = TimePredictionML.analyze_prediction_accuracy()
            
            self.stdout.write(f"Total predicciones evaluadas: {accuracy['total_predictions']}")
            self.stdout.write(f"Error promedio: {accuracy['avg_error_minutes']} minutos")
            self.stdout.write(f"Tasa de precisión: {accuracy['accuracy_rate']}%")
            self.stdout.write('')
            
            if accuracy['recent_comparisons']:
                self.stdout.write('Últimas comparaciones:')
                for comp in accuracy['recent_comparisons'][:5]:
                    self.stdout.write(
                        f"  {comp['origin']} → {comp['destination']}: "
                        f"Predicho={comp['predicted']}min, "
                        f"Real={comp['actual']}min, "
                        f"Error={comp['error_percent']}%"
                    )
            self.stdout.write('')
        
        # Sugerencias
        if options['suggestions']:
            self.stdout.write(self.style.HTTP_INFO('-'*60))
            self.stdout.write(self.style.HTTP_INFO('💡 SUGERENCIAS DE OPTIMIZACIÓN'))
            self.stdout.write(self.style.HTTP_INFO('-'*60))
            self.stdout.write('')
            
            suggestions = TimePredictionML.suggest_route_optimizations()
            
            if suggestions:
                for i, sug in enumerate(suggestions, 1):
                    self.stdout.write(
                        self.style.WARNING(f"{i}. {sug['route']}")
                    )
                    self.stdout.write(f"   Problema: {sug['description']}")
                    self.stdout.write(f"   Sugerencia: {sug['suggestion']}")
                    self.stdout.write('')
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ No hay sugerencias. Todo está optimizado.')
                )
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ ACTUALIZACIÓN COMPLETADA'))
        self.stdout.write(self.style.SUCCESS('='*60))
