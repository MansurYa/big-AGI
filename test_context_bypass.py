#!/usr/bin/env python3
"""
Test script for hone.vvvv.ee proxy - bypass test to check if errors are real
"""

import requests
import json

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"
SOURCE_FILE = "/Users/mansurzainullin/MyCode/big-AGI/190k_file.txt"

# Read source file
with open(SOURCE_FILE, 'r') as f:
    source_content = f.read()

print("=== Bypass Test: Direct small request ===")
print("")

# First test with a small clean request to verify API works
payload = {
    "model": "claude-opus-4-6",
    "max_tokens": 100,
    "messages": [{
        "role": "user",
        "content": "Hello, please respond with just 'OK' to test the connection."
    }]
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("")
print("=== Testing content repetition issue ===")

# The issue might be that repeating content creates invalid structure
# Let's test with the actual file content at different sizes

test_sizes_chars = [
    100000,
    300000,
    500000,
]

for size in test_sizes_chars:
    print(f"\nTesting {size} characters...")

    # Use actual content without repetition
    test_content = source_content * (size // len(source_content) + 1)
    test_content = test_content[:size]

    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": f"Context:\n\n{test_content}\n\nSummarize in 2 sentences."
        }]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        response_data = response.json()

        if "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"  ERROR: {error_msg}")
        else:
            print(f"  SUCCESS")
    except Exception as e:
        print(f"  ERROR: {e}")
