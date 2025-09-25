from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Limpiar cache del dashboard de certificados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpiar todo el cache del sistema',
        )

    def handle(self, *args, **options):
        if options['all']:
            # Limpiar todo el cache
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Todo el cache del sistema ha sido limpiado')
            )
        else:
            # Limpiar solo cache del dashboard
            dashboard_keys = []
            
            # Intentar limpiar patrones de cache del dashboard
            try:
                # Limpiar cache específico del dashboard
                cache.delete('certificates_dashboard')
                cache.delete('course_dashboard')
                
                # Limpiar cache de funciones auxiliares
                cache.delete_pattern('dashboard_*')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Cache del dashboard ha sido limpiado')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Algunas claves de cache no pudieron ser limpiadas: {e}')
                )
                # Fallback: limpiar todo el cache
                cache.clear()
                self.stdout.write(
                    self.style.SUCCESS('✅ Cache completo limpiado como fallback')
                )




