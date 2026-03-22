"""
S0.1 - Proxy Server Boot Test
Evidence for baseline functionality verification.
"""
import requests
import json
from datetime import datetime

def test_proxy_boot():
    """Test that proxy server boots and responds to health checks."""

    print("=== S0.1: PROXY SERVER BOOT TEST ===\n")

    base_url = "http://localhost:8000"

    # Test 1: Health endpoint
    print("Test 1: Health endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("  ✓ PASS: Health endpoint working")
            else:
                print("  ✗ FAIL: Unexpected response")
                return False
        else:
            print(f"  ✗ FAIL: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False

    # Test 2: Status endpoint
    print("\nTest 2: Status endpoint...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            data = response.json()
            if 'categories' in data:
                print("  ✓ PASS: Status endpoint working")
            else:
                print("  ✗ FAIL: Missing categories in response")
                return False
        else:
            print(f"  ✗ FAIL: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False

    print("\n=== S0.1 RESULT: PASS ===")
    return True

if __name__ == "__main__":
    success = test_proxy_boot()
    exit(0 if success else 1)
