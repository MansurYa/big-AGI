#!/usr/bin/env python3
"""
Final context window test for hone.vvvv.ee proxy
Testing with properly sized contexts to find the actual limit
"""

import requests
import json

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"
SOURCE_FILE = "/Users/mansurzainullin/MyCode/big-AGI/190k_file.txt"

# Read source file
with open(SOURCE_FILE, 'r') as f:
    source_content = f.read()

print("=== Hone.vvvv.ee Context Window Limit Test ===")
print(f"Source file size: {len(source_content):,} characters")
print("")

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

# Test with progressively larger sizes to find the boundary
# Using the actual file content repeated
test_sizes = [
    (400000, "400k chars"),
    (600000, "600k chars"),
    (800000, "800k chars"),
    (1000000, "1M chars"),
    (1500000, "1.5M chars"),
    (2000000, "2M chars"),
    (2500000, "2.5M chars"),
    (3000000, "3M chars"),
    (3500000, "3.5M chars ~1M tokens"),
]

results = []

for size, description in test_sizes:
    print(f"Testing {description} ({size:,} chars)...")

    # Create content by repeating source file
    repetitions = (size // len(source_content)) + 1
    test_content = (source_content * repetitions)[:size]

    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": f"Here is context:\n\n{test_content}\n\nSummarize in 2-3 sentences."
        }]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response_data = response.json()

        if "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")

            # Check for context length error
            is_context_error = any(keyword in error_msg.lower() for keyword in [
                "上下文过长", "context", "too long", "window", "length", "token limit"
            ])

            if is_context_error:
                print(f"  CONTEXT LIMIT ERROR: {error_msg}")
            else:
                print(f"  FORMAT ERROR: {error_msg}")

            results.append((size, description, False, error_msg, is_context_error))
        else:
            print(f"  SUCCESS")
            results.append((size, description, True, "OK", False))

    except requests.exceptions.Timeout:
        error_msg = "Timeout (300s)"
        print(f"  TIMEOUT: {error_msg}")
        results.append((size, description, False, error_msg, False))
    except Exception as e:
        error_msg = str(e)
        print(f"  ERROR: {error_msg}")
        results.append((size, description, False, error_msg, False))

print("")
print("=== Test Results Summary ===")
print("")

for size, description, success, message, is_context_error in results:
    status = "✓ SUCCESS" if success else ("✗ CONTEXT LIMIT" if is_context_error else "✗ ERROR")
    print(f"{description}: {status}")
    if not success:
        print(f"  Message: {message}")

# Find maximum working size
working_sizes = [(s, d) for s, d, success, _, _ in results if success]
context_errors = [(s, d) for s, d, _, _, is_ctx in results if is_ctx]

print("")
if working_sizes:
    max_working = max(working_sizes, key=lambda x: x[0])
    print(f"Maximum working context: {max_working[1]} ({max_working[0]:,} chars)")
else:
    print("No tests succeeded")

if context_errors:
    print(f"Context limit detected at: {context_errors[0][1]}")
