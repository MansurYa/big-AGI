#!/usr/bin/env python3
"""
Test with fresh content and no session continuity
"""

import requests
import random
import string

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"

print("=== Fresh Content Test ===")
print("")

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

# Generate random text to avoid any caching or session effects
def generate_random_text(size):
    words = []
    current_size = 0
    while current_size < size:
        word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
        words.append(word)
        current_size += len(word) + 1  # +1 for space
    return ' '.join(words)[:size]

# Test with different sizes using completely fresh random content each time
test_sizes = [
    (100000, "100k chars"),
    (300000, "300k chars"),
    (500000, "500k chars"),
    (700000, "700k chars"),
    (1000000, "1M chars"),
]

results = []

for size, description in test_sizes:
    print(f"Testing {description} ({size:,} chars)...")

    # Generate fresh random content
    test_content = generate_random_text(size)

    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 100,
        "messages": [{
            "role": "user",
            "content": f"Here is context:\n\n{test_content[:size]}\n\nRespond with only 'OK'."
        }]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response_data = response.json()

        if "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            is_context_error = "上下文过长" in error_msg

            if is_context_error:
                print(f"  CONTEXT LIMIT: {error_msg}")
            else:
                print(f"  ERROR: {error_msg}")

            results.append((size, description, False, error_msg, is_context_error))
        else:
            usage = response_data.get("usage", {})
            input_tokens = usage.get("input_tokens", "N/A")
            print(f"  SUCCESS (input_tokens: {input_tokens})")
            results.append((size, description, True, f"OK, tokens: {input_tokens}", False))

    except Exception as e:
        error_msg = str(e)
        print(f"  ERROR: {error_msg}")
        results.append((size, description, False, error_msg, False))

print("")
print("=== Results ===")
print("")

for size, description, success, message, is_context_error in results:
    status = "✓" if success else ("✗ CONTEXT" if is_context_error else "✗ ERROR")
    print(f"{status} {description}")
