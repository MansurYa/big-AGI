#!/usr/bin/env python3
"""
Verify context window boundary with fresh tests
"""

import requests
import time

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"
SOURCE_FILE = "/Users/mansurzainullin/MyCode/big-AGI/190k_file.txt"

# Read source file
with open(SOURCE_FILE, 'r') as f:
    source_content = f.read()

print("=== Verification Test ===")
print(f"Source file size: {len(source_content):,} characters")
print("")

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

# Test sizes focusing on the boundary region
test_sizes = [
    (500000, "500k chars"),
    (1000000, "1M chars"),
    (1500000, "1.5M chars"),
    (1800000, "1.8M chars"),
    (2000000, "2.0M chars"),
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
            is_context_error = "上下文过长" in error_msg

            if is_context_error:
                print(f"  CONTEXT LIMIT: {error_msg}")
            else:
                print(f"  ERROR: {error_msg}")

            results.append((size, description, False, error_msg, is_context_error))
        else:
            # Get token usage if available
            usage = response_data.get("usage", {})
            input_tokens = usage.get("input_tokens", "N/A")
            print(f"  SUCCESS (input_tokens: {input_tokens})")
            results.append((size, description, True, f"OK, input_tokens: {input_tokens}", False))

    except Exception as e:
        error_msg = str(e)
        print(f"  ERROR: {error_msg}")
        results.append((size, description, False, error_msg, False))

    # Small delay to avoid rate limiting
    time.sleep(2)

print("")
print("=== Results ===")
print("")

for size, description, success, message, is_context_error in results:
    status = "✓" if success else ("✗ CONTEXT" if is_context_error else "✗ ERROR")
    print(f"{status} {description}")

# Find boundary
working = [(s, m) for s, d, success, m, _ in results if success]
failing = [(s, m) for s, d, _, m, is_ctx in results if is_ctx]

print("")
if working:
    max_working = max(working, key=lambda x: x[0])
    print(f"Maximum working: {description} at {max_working[0]:,} chars")
    print(f"  Message: {max_working[1]}")

if failing:
    min_failing = min(failing, key=lambda x: x[0])
    print(f"Minimum failing: {description} at {min_failing[0]:,} chars")
    print(f"  Error: {min_failing[1]}")
