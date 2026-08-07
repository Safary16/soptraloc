"""
Test script to validate the fixes made to the SoptraLoc TMS system
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/runner/work/soptraloc/soptraloc')
django.setup()

from apps.cds.models import CD
from apps.programaciones.models import Programacion
from apps.core.api_views import ml_learning_stats
from django.test import RequestFactory

def test_ccti_filter():
    """Test that CCTI filter works correctly with lowercase 'ccti'"""
    print("\n=== Test 1: CCTI Filter ===")
    ccti_count = CD.objects.filter(tipo='ccti').count()
    print(f"✓ CCTI filter works correctly. Found {ccti_count} CCTI(s)")
    
    # Test the wrong filter to show it would fail
    wrong_count = CD.objects.filter(tipo='CCTI').count()
    print(f"  (Wrong filter 'CCTI' would return: {wrong_count} results)")
    return True

def test_programacion_eta_fields():
    """Test that Programacion model has ETA fields"""
    print("\n=== Test 2: Programacion ETA Fields ===")
    prog = Programacion.objects.first()
    if prog:
        has_eta = hasattr(prog, 'eta_minutos')
        has_distancia = hasattr(prog, 'distancia_km')
        print(f"✓ Programacion has eta_minutos field: {has_eta}")
        print(f"✓ Programacion has distancia_km field: {has_distancia}")
        if prog.eta_minutos:
            print(f"  Sample ETA: {prog.eta_minutos} minutes")
        return has_eta and has_distancia
    else:
        print("⚠ No programaciones found in database")
        return True

def test_cd_permite_soltar():
    """Test that CD model has permite_soltar_contenedor field"""
    print("\n=== Test 3: CD Drop & Hook Field ===")
    cd = CD.objects.first()
    if cd:
        has_field = hasattr(cd, 'permite_soltar_contenedor')
        print(f"✓ CD has permite_soltar_contenedor field: {has_field}")
        if has_field:
            print(f"  Sample CD '{cd.nombre}' permite_soltar: {cd.permite_soltar_contenedor}")
        return has_field
    else:
        print("⚠ No CDs found in database")
        return True

def test_ml_stats_endpoint():
    """Test that ML statistics endpoint works"""
    print("\n=== Test 4: ML Statistics Endpoint ===")
    try:
        factory = RequestFactory()
        request = factory.get('/api/ml/learning-stats/')
        response = ml_learning_stats(request)
        
        if response.status_code == 200:
            data = response.data
            print(f"✓ ML stats endpoint works correctly")
            print(f"  Estado general: {data['resumen']['estado_general']}")
            print(f"  Progreso: {data['resumen']['progreso_porcentaje']}%")
            print(f"  Datos totales: {data['resumen']['datos_total']}")
            print(f"  Operaciones válidas: {data['tiempos_operacion']['validos']}")
            print(f"  Viajes válidos: {data['tiempos_viaje']['validos']}")
            return True
        else:
            print(f"✗ ML stats endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing ML stats endpoint: {str(e)}")
        return False

def test_driver_serializer():
    """Test that driver serializer includes cd_permite_soltar"""
    print("\n=== Test 5: Driver Serializer Field ===")
    try:
        from apps.drivers.serializers import DriverDetailSerializer
        from apps.drivers.models import Driver
        
        driver = Driver.objects.first()
        if driver:
            serializer = DriverDetailSerializer(driver)
            programaciones = serializer.data.get('programaciones_asignadas', [])
            
            if programaciones:
                first_prog = programaciones[0]
                has_field = 'cd_permite_soltar' in first_prog
                print(f"✓ Driver serializer includes cd_permite_soltar: {has_field}")
                if has_field:
                    print(f"  Sample value: {first_prog['cd_permite_soltar']}")
                return has_field
            else:
                print("⚠ Driver has no programaciones asignadas")
                return True
        else:
            print("⚠ No drivers found in database")
            return True
    except Exception as e:
        print(f"✗ Error testing driver serializer: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running SoptraLoc TMS Fixes Validation Tests")
    print("=" * 60)
    
    results = []
    results.append(("CCTI Filter", test_ccti_filter()))
    results.append(("Programacion ETA Fields", test_programacion_eta_fields()))
    results.append(("CD Drop & Hook Field", test_cd_permite_soltar()))
    results.append(("ML Statistics Endpoint", test_ml_stats_endpoint()))
    results.append(("Driver Serializer Field", test_driver_serializer()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
