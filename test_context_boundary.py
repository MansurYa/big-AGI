#!/usr/bin/env python3
"""
Narrow down the exact context window boundary for hone.vvvv.ee proxy
"""

import requests
import json

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"
SOURCE_FILE = "/Users/mansurzainullin/MyCode/big-AGI/190k_file.txt"

# Read source file
with open(SOURCE_FILE, 'r') as f:
    source_content = f.read()

print("=== Hone.vvvv.ee Exact Context Boundary Test ===")
print(f"Source file size: {len(source_content):,} characters")
print("")

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

# Based on previous results, boundary is between 2M and 2.5M
# Test at 250k intervals
test_sizes = [
    (2000000, "2.0M chars"),
    (2100000, "2.1M chars"),
    (2200000, "2.2M chars"),
    (2300000, "2.3M chars"),
    (2400000, "2.4M chars"),
    (2500000, "2.5M chars"),
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
            is_context_error = "上下文过长" in error_msg

            if is_context_error:
                print(f"  CONTEXT LIMIT: {error_msg}")
            else:
                print(f"  OTHER ERROR: {error_msg}")

            results.append((size, description, False, error_msg, is_context_error))
        else:
            print(f"  SUCCESS")
            results.append((size, description, True, "OK", False))

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

# Find exact boundary
working = [s for s, d, success, _, _ in results if success]
failing = [s for s, d, _, _, is_ctx in results if is_ctx]

print("")
if working and failing:
    max_working = max(working)
    min_failing = min(failing)
    print(f"Maximum working: {max_working:,} chars ({max_working/1000000:.2f}M)")
    print(f"Minimum failing: {min_failing:,} chars ({min_failing/1000000:.2f}M)")
    print(f"Boundary is between {max_working/1000000:.2f}M and {min_failing/1000000:.2f}M characters")

    # Rough token estimate (1 token ~ 3.5 chars for mixed text)
    print(f"")
    print(f"Estimated token limit: ~{max_working//3.5:,} - {min_failing//3.5:,} tokens")
    print(f"  = approximately {(max_working//3.5)/1000:.0f}k - {(min_failing//3.5)/1000:.0f}k tokens")
