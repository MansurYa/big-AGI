"""
S0.2 - Simple API Passthrough Test
Tests basic proxy functionality: request → proxy → API → response
"""
import os
import requests
import json
from datetime import datetime

def test_simple_passthrough():
    """Test that proxy can forward a simple request to Anthropic API."""

    print("=== S0.2: SIMPLE API PASSTHROUGH TEST ===\n")

    proxy_url = "http://localhost:8000/v1/messages"
    api_key = os.getenv("ANTHROPIC_API_KEY", "sk-aw-f157875b77785becb3514fb6ae770e50")

    # Minimal request
    request_body = {
        "model": "claude-sonnet-4.5",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "Say 'test' and nothing else."}
        ]
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    print("Sending minimal request through proxy...")
    print(f"Request: {json.dumps(request_body, indent=2)}\n")

    try:
        response = requests.post(
            proxy_url,
            json=request_body,
            headers=headers,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}\n")

            # Check response structure
            if 'content' in data and len(data['content']) > 0:
                content = data['content'][0].get('text', '')
                print(f"Model response: {content}")
                print("\n✓ PASS: Proxy successfully forwarded request and returned response")
                return True
            else:
                print("✗ FAIL: Response missing expected content structure")
                return False
        else:
            print(f"Response: {response.text}")
            print(f"\n✗ FAIL: Non-200 status code")
            return False

    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_passthrough()
    exit(0 if success else 1)
