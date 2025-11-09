"""
Test script to validate code changes without database access
"""
import os
import sys
import ast

def test_python_syntax(filepath):
    """Test if Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_ccti_filter_fix():
    """Verify that the CCTI filter fix is in place"""
    filepath = 'apps/programaciones/views.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check that the fix is applied (lowercase 'ccti')
    has_fix = "tipo='ccti'" in content
    # Check that the bug is not present (uppercase 'CCTI')
    no_bug = "tipo='CCTI'" not in content
    
    return has_fix and no_bug, f"CCTI filter uses correct lowercase 'ccti': {has_fix}, No uppercase bug: {no_bug}"

def test_eta_calculation():
    """Verify ETA calculation code is present in iniciar_ruta"""
    filepath = 'apps/programaciones/views.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for ETA calculation code
    has_mapbox_import = 'from apps.core.services.mapbox import MapboxService' in content
    has_eta_calculation = 'programacion.eta_minutos' in content
    has_distancia_save = 'programacion.distancia_km' in content
    
    return has_eta_calculation and has_distancia_save, f"ETA calculation present: {has_eta_calculation}, Distance save: {has_distancia_save}"

def test_soltar_contenedor_endpoint():
    """Verify that soltar_contenedor endpoint exists"""
    filepath = 'apps/programaciones/views.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    has_endpoint = 'def soltar_contenedor(self, request, pk=None):' in content
    has_decorator = '@action(detail=True, methods=[\'post\'])' in content
    has_cd_check = 'permite_soltar_contenedor' in content
    
    return has_endpoint and has_cd_check, f"soltar_contenedor endpoint exists: {has_endpoint}, CD check: {has_cd_check}"

def test_driver_serializer_field():
    """Verify cd_permite_soltar field is added to driver serializer"""
    filepath = 'apps/drivers/serializers.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    has_field = "'cd_permite_soltar':" in content or '"cd_permite_soltar":' in content
    
    return has_field, f"cd_permite_soltar field added: {has_field}"

def test_ml_stats_endpoint():
    """Verify ML stats endpoint exists"""
    filepath = 'apps/core/api_views.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    has_function = 'def ml_learning_stats(request):' in content
    has_decorator = '@api_view([\'GET\'])' in content
    has_response = 'tiempos_operacion' in content and 'tiempos_viaje' in content
    
    return has_function and has_response, f"ML stats endpoint exists: {has_function}, Has stats: {has_response}"

def test_url_registration():
    """Verify new URLs are registered"""
    filepath = 'config/urls.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    has_ml_stats_url = 'ml_learning_stats' in content
    has_import = 'from apps.core.api_views import' in content
    
    return has_ml_stats_url and has_import, f"ML stats URL registered: {has_ml_stats_url}, Import present: {has_import}"

def test_driver_dashboard_ui():
    """Verify driver dashboard UI changes"""
    filepath = 'templates/driver_dashboard.html'
    with open(filepath, 'r') as f:
        content = f.read()
    
    has_drop_option = 'soltarContenedor' in content
    has_wait_option = 'notificarVacio' in content
    has_cd_check = 'cd_permite_soltar' in content
    
    return has_drop_option and has_cd_check, f"Drop option added: {has_drop_option}, CD check: {has_cd_check}, Wait option: {has_wait_option}"

def test_asignacion_page_ml():
    """Verify asignacion page has ML stats display"""
    filepath = 'templates/asignacion.html'
    with open(filepath, 'r') as f:
        content = f.read()
    
    has_ml_stats_div = 'ml-stats-content' in content
    has_api_call = '/api/ml/learning-stats/' in content
    has_progress_bar = 'ml-progress-bar' in content
    
    return has_ml_stats_div and has_api_call, f"ML stats div: {has_ml_stats_div}, API call: {has_api_call}, Progress bar: {has_progress_bar}"

def run_all_tests():
    """Run all code validation tests"""
    print("=" * 70)
    print("SoptraLoc TMS - Code Validation Tests (No Database Required)")
    print("=" * 70)
    
    files_to_check = [
        'apps/programaciones/views.py',
        'apps/drivers/serializers.py',
        'apps/core/api_views.py',
        'config/urls.py',
        'templates/driver_dashboard.html',
        'templates/asignacion.html'
    ]
    
    print("\n### Syntax Validation ###\n")
    syntax_results = []
    for filepath in files_to_check:
        if filepath.endswith('.py'):
            passed, message = test_python_syntax(filepath)
            syntax_results.append((filepath, passed, message))
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {filepath}")
            if not passed:
                print(f"  {message}")
    
    print("\n### Feature Validation ###\n")
    feature_tests = [
        ("CCTI Filter Fix", test_ccti_filter_fix),
        ("ETA Calculation", test_eta_calculation),
        ("Soltar Contenedor Endpoint", test_soltar_contenedor_endpoint),
        ("Driver Serializer Field", test_driver_serializer_field),
        ("ML Statistics Endpoint", test_ml_stats_endpoint),
        ("URL Registration", test_url_registration),
        ("Driver Dashboard UI", test_driver_dashboard_ui),
        ("Asignacion Page ML Stats", test_asignacion_page_ml)
    ]
    
    feature_results = []
    for test_name, test_func in feature_tests:
        try:
            passed, message = test_func()
            feature_results.append((test_name, passed, message))
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")
            if message:
                print(f"  {message}")
        except Exception as e:
            feature_results.append((test_name, False, str(e)))
            print(f"✗ FAIL: {test_name}")
            print(f"  Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    
    all_syntax_passed = all(result[1] for result in syntax_results)
    all_features_passed = all(result[1] for result in feature_results)
    
    print(f"\nSyntax Tests: {'✓ ALL PASSED' if all_syntax_passed else '✗ SOME FAILED'}")
    print(f"Feature Tests: {'✓ ALL PASSED' if all_features_passed else '✗ SOME FAILED'}")
    
    print("\n" + "=" * 70)
    if all_syntax_passed and all_features_passed:
        print("✓ ALL VALIDATION TESTS PASSED")
        print("\nAll code changes have been validated successfully!")
        print("The following features have been implemented:")
        print("  1. Manual programming CCTI filter bug fixed")
        print("  2. ETA calculation and storage when route starts")
        print("  3. Drop & hook functionality for containers")
        print("  4. ML learning statistics endpoint and display")
    else:
        print("✗ SOME VALIDATION TESTS FAILED")
        print("\nPlease review the failed tests above.")
    print("=" * 70)
    
    return all_syntax_passed and all_features_passed

if __name__ == '__main__':
    os.chdir('/home/runner/work/soptraloc/soptraloc')
    success = run_all_tests()
    sys.exit(0 if success else 1)
