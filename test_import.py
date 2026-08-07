import os
import sys
import django


def run_excel_import_smoke():
    sys.path.append('/workspaces/soptraloc')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from apps.containers.importers.embarque import EmbarqueImporter
    from apps.containers.importers.liberacion import LiberacionImporter
    from apps.containers.importers.programacion import ProgramacionImporter
    from apps.containers.models import Container

    print("\n" + "=" * 80)
    print("TEST DE IMPORTACIÓN DE ARCHIVOS EXCEL REALES")
    print("=" * 80)

    embarque_file = 'apps/APL CHARLESTON ETA 26-09 SERRANO CCTI.xlsx'
    if os.path.exists(embarque_file):
        EmbarqueImporter(embarque_file, 'test_user').procesar()
    print(f"Total contenedores en sistema: {Container.objects.count()}")

    liberacion_file = 'apps/liberacion.xlsx'
    if os.path.exists(liberacion_file):
        LiberacionImporter(liberacion_file, 'test_user').procesar()

    programacion_file = 'apps/programacion.xlsx'
    if os.path.exists(programacion_file):
        ProgramacionImporter(programacion_file, 'test_user').procesar()

    print("=" * 80)


if __name__ == '__main__':
    run_excel_import_smoke()
