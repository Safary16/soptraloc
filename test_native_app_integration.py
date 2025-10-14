#!/usr/bin/env python
"""
Test script to verify native app backend integration
Run this after the Django server is running
"""

import requests
import json

BASE_URL = "https://soptraloc.onrender.com"  # Change if testing locally

def test_verify_patente():
    """Test the verify-patente endpoint"""
    print("\n🧪 Testing POST /api/drivers/verify-patente/")
    
    # Test with a valid patente (adjust based on your data)
    test_cases = [
        {"patente": "ABCD12", "should_work": True},
        {"patente": "", "should_work": False},
        {"patente": "INVALID999", "should_work": False},
    ]
    
    for test in test_cases:
        print(f"\n  Testing patente: '{test['patente']}'")
        try:
            response = requests.post(
                f"{BASE_URL}/api/drivers/verify-patente/",
                json={"patente": test["patente"]},
                timeout=10
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
            
            if test["should_work"]:
                assert response.status_code == 200, "Expected 200 for valid patente"
                assert response.json()["success"] == True, "Expected success=true"
                print("  ✅ Test passed!")
            else:
                assert response.status_code in [400, 404], "Expected error for invalid patente"
                print("  ✅ Test passed (error expected)!")
                
        except requests.RequestException as e:
            print(f"  ❌ Request failed: {e}")
        except AssertionError as e:
            print(f"  ❌ Assertion failed: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")


def test_update_location():
    """Test the update-location endpoint"""
    print("\n🧪 Testing POST /api/drivers/{id}/update-location/")
    
    # Note: You'll need a valid driver_id for this test
    driver_id = 1  # Change this to a valid driver ID
    
    print(f"\n  Testing location update for driver {driver_id}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/drivers/{driver_id}/update-location/",
            json={
                "lat": -33.4569,
                "lng": -70.6483,
                "accuracy": 10.5
            },
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            assert response.json()["ok"] == True, "Expected ok=true"
            print("  ✅ Test passed!")
        else:
            print(f"  ⚠️  Test returned {response.status_code}")
            print("  Note: This might be expected if driver doesn't exist or auth is required")
            
    except requests.RequestException as e:
        print(f"  ❌ Request failed: {e}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_active_locations():
    """Test the active_locations endpoint"""
    print("\n🧪 Testing GET /api/drivers/active_locations/")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/drivers/active_locations/",
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Active drivers: {len(data)}")
        
        if len(data) > 0:
            print(f"  Sample driver: {json.dumps(data[0], indent=2)}")
        
        assert response.status_code == 200, "Expected 200"
        print("  ✅ Test passed!")
        
    except requests.RequestException as e:
        print(f"  ❌ Request failed: {e}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    print("=" * 60)
    print("🔍 SoptraLoc Native App - Backend Integration Tests")
    print("=" * 60)
    print(f"\nTesting against: {BASE_URL}")
    print("\nNote: Adjust driver_id and patente values based on your data")
    
    # Run tests
    test_verify_patente()
    test_update_location()
    test_active_locations()
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If tests passed → Compile mobile app APK")
    print("2. Install APK on Android device")
    print("3. Test GPS with screen locked")
    print("\nSee RESUMEN_APP_NATIVA.md for detailed instructions")


if __name__ == "__main__":
    main()
