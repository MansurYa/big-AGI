"""
Manual test script for proxy server.
Tests proxy server with real API calls.
"""
import requests
import json
import time


def test_proxy_basic():
    """Test basic proxy functionality"""
    print("\n=== PROXY SERVER BASIC TEST ===\n")

    base_url = "http://localhost:8000"

    # Test 1: Health check
    print("Test 1: Health check...")
    response = requests.get(f"{base_url}/")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    assert response.status_code == 200
    print("  ✅ PASS\n")

    # Test 2: Status
    print("Test 2: Status endpoint...")
    response = requests.get(f"{base_url}/status")
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Total tokens: {data['total_tokens']}")
    print(f"  Total quota: {data['total_quota']}")
    print(f"  Fill: {data['overall_fill_percent']:.1f}%")
    assert response.status_code == 200
    print("  ✅ PASS\n")

    # Test 3: Set quotas
    print("Test 3: Set quotas...")
    response = requests.post(f"{base_url}/api/quotas/set", json={
        'quotas': {
            'System': 5000,
            'Internet': 60000,
            'Dialogue': 100000
        }
    })
    print(f"  Status: {response.status_code}")
    print(f"  Quotas: {response.json()['quotas']}")
    assert response.status_code == 200
    print("  ✅ PASS\n")

    # Test 4: Compression stats
    print("Test 4: Compression stats...")
    response = requests.get(f"{base_url}/api/compression/stats/test_chat")
    print(f"  Status: {response.status_code}")
    print(f"  Stats: {response.json()}")
    assert response.status_code == 200
    print("  ✅ PASS\n")

    print("=== ALL TESTS PASSED ===\n")


def test_proxy_with_anthropic():
    """Test proxy with real Anthropic API call"""
    print("\n=== PROXY WITH ANTHROPIC API TEST ===\n")

    base_url = "http://localhost:8000"

    # Simple test message
    request_body = {
        "model": "claude-sonnet-4.5",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from proxy!' and nothing else.",
                "category": "Dialogue"
            }
        ],
        "metadata": {
            "chat_id": "test_chat_001"
        }
    }

    print("Sending request to proxy...")
    print(f"  Model: {request_body['model']}")
    print(f"  Message: {request_body['messages'][0]['content'][:50]}...")

    start = time.time()
    response = requests.post(
        f"{base_url}/v1/messages",
        json=request_body,
        headers={
            "anthropic-version": "2023-06-01"
        }
    )
    elapsed = time.time() - start

    print(f"\nResponse received in {elapsed:.2f}s")
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  Response type: {data.get('type')}")
        if 'content' in data and len(data['content']) > 0:
            print(f"  Content: {data['content'][0].get('text', '')[:100]}")
        print("  ✅ PASS\n")
    else:
        print(f"  Error: {response.text}")
        print("  ❌ FAIL\n")


if __name__ == "__main__":
    print("Starting proxy server tests...")
    print("Make sure proxy server is running: python src/proxy/server.py")
    print()

    try:
        test_proxy_basic()

        # Uncomment to test with real API
        # test_proxy_with_anthropic()

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to proxy server")
        print("Start the server with: python src/proxy/server.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")
