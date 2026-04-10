#!/usr/bin/env python3
"""
Test upper boundary of hone.vvvv.ee context window
Testing sizes above 2M chars to find the exact limit
"""

import requests
import random
import string
import time

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"

print("=== Upper Boundary Test ===")
print("Testing context sizes above 2M chars")
print("")

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

def generate_random_text(size):
    """Generate random text of specified size"""
    words = []
    current_size = 0
    while current_size < size:
        word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        words.append(word)
        current_size += len(word) + 1
    return ' '.join(words)[:size]

# Test sizes from 2M to 4M (1M tokens ~= 3.5M chars)
test_sequence = [
    (2200000, "2.2M"),
    (2400000, "2.4M"),
    (2600000, "2.6M"),
    (2800000, "2.8M"),
    (3000000, "3.0M"),
    (3200000, "3.2M"),
    (3400000, "3.4M"),
    (3500000, "3.5M (~1M tokens)"),
]

results = []
last_success_size = 2000000  # From previous test

for size, description in test_sequence:
    print(f"Testing {description} ({size:,} chars)...", end=" ", flush=True)

    test_content = generate_random_text(size)

    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 100,
        "messages": [{
            "role": "user",
            "content": f"Context:\n\n{test_content}\n\nRespond: OK"
        }]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response_data = response.json()

        if "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")

            if "上下文过长" in error_msg:
                print(f"CONTEXT LIMIT")
                results.append((size, False, "context_limit", error_msg))
            elif "供应商" in error_msg or "unavailable" in error_msg.lower():
                print(f"SERVER UNAVAILABLE")
                print(f"\nServer rate-limiting. Last success: {last_success_size:,} chars")
                break
            else:
                print(f"ERROR: {error_msg[:60]}")
                results.append((size, False, "error", error_msg))
        else:
            usage = response_data.get("usage", {})
            input_tokens = usage.get("input_tokens", "N/A")
            print(f"OK (tokens: {input_tokens:,})")
            results.append((size, True, "ok", f"tokens: {input_tokens}"))
            last_success_size = size

    except requests.exceptions.Timeout:
        print("TIMEOUT")
        results.append((size, False, "timeout", "Request timeout"))
    except Exception as e:
        print(f"EXCEPTION: {e}")
        results.append((size, False, "exception", str(e)))

    time.sleep(1)

print("")
print("\n=== FINAL RESULTS ===")
print("")

all_successes = [(s, m) for s, ok, m_type, m in results if ok]
context_limits = [(s, m) for s, ok, m_type, m in results if m_type == "context_limit"]

# Include previous result
print(f"Previous test confirmed: 2,000,000 chars (~982k tokens) SUCCESS")
print("")

if all_successes:
    max_success = max(all_successes, key=lambda x: x[0])
    print(f"New largest successful: {max_success[0]:,} chars ({max_success[0]/1000000:.2f}M)")
    print(f"  {max_success[1]}")
    last_success_size = max_success_size = max_success[0]

if context_limits:
    min_fail = min(context_limits, key=lambda x: x[0])
    print(f"Smallest context-limit failure: {min_fail[0]:,} chars ({min_fail[0]/1000000:.2f}M)")

print("")

if all_successes and context_limits:
    max_success_size = max(s for s, _ in all_successes)
    min_fail_size = min(s for s, _ in context_limits)

    print("CONCLUSION:")
    print(f"  Context window limit is between:")
    print(f"    {max_success_size:,} chars ({max_success_size/1000000:.2f}M) and {min_fail_size:,} chars ({min_fail_size/1000000:.2f}M)")
    print("")

    # Convert to tokens (~3.5 chars/token for random ASCII)
    max_tokens = max_success_size // 4  # Random text is closer to 4 chars/token
    min_tokens = min_fail_size // 4

    print(f"  Estimated token limit: ~{max_tokens:,} - {min_tokens:,} tokens")
    print(f"    (approximately {max_tokens//1000}k - {min_tokens//1000}k tokens)")
    print("")

    if min_fail_size >= 3400000:
        print("  ✓ 1M TOKEN WINDOW CONFIRMED (claude-opus-4-6 full context)")
    elif min_fail_size >= 2800000:
        print(f"  ~ ~800k token context window supported")
    else:
        print(f"  ✗ Less than 1M tokens ({max_tokens//1000}k confirmed)")
elif all_successes:
    print(f"  All tests up to {last_success_size:,} chars succeeded!")
    print("  Need to test higher to find the limit.")
