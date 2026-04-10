#!/usr/bin/env python3
"""
Clean single-run test for hone.vvvv.ee context window
Generates fresh random content and tests multiple sizes in one run
"""

import requests
import random
import string
import time

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"

print("=== Clean Context Window Test ===")
print("Testing with fresh random content to avoid caching effects")
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

# Binary search approach to find boundary
# Start low and work up
test_sequence = [
    (200000, "200k"),
    (400000, "400k"),
    (600000, "600k"),
    (800000, "800k"),
    (1000000, "1M"),
    (1200000, "1.2M"),
    (1400000, "1.4M"),
    (1600000, "1.6M"),
    (1800000, "1.8M"),
    (2000000, "2M"),
]

results = []
last_success_size = 0

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
                print(f"SERVER UNAVAILABLE - stopping tests")
                print(f"\nServer is rate-limiting or exhausted.")
                print(f"Last successful size was: {last_success_size:,} chars")
                break
            else:
                print(f"ERROR: {error_msg[:80]}")
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

    time.sleep(1)  # Small delay between tests

print("")
print("\n=== SUMMARY ===")
print("")

successes = [(s, m) for s, ok, m_type, m in results if ok]
context_limits = [(s, m) for s, ok, m_type, m in results if m_type == "context_limit"]

if successes:
    max_success = max(successes, key=lambda x: x[0])
    print(f"Largest successful: {max_success[0]:,} chars ({max_success[0]/1000000:.2f}M)")
    print(f"  {max_success[1]}")

if context_limits:
    min_fail = min(context_limits, key=lambda x: x[0])
    print(f"Smallest context-limit failure: {min_fail[0]:,} chars ({min_fail[0]/1000000:.2f}M)")

if successes and context_limits:
    max_success_size = max(s for s, _ in successes)
    min_fail_size = min(s for s, _ in context_limits)

    print("")
    print("CONCLUSION:")
    print(f"  The hone.vvvv.ee proxy context window limit is between:")
    print(f"    {max_success_size:,} chars ({max_success_size/1000000:.2f}M) and {min_fail_size:,} chars ({min_fail_size/1000000:.2f}M)")
    print("")
    print(f"  Estimated token limit: ~{max_success_size//3.5:,} - {min_fail_size//3.5:,} tokens")
    print(f"    (approximately {(max_success_size//3.5)/1000:.0f}k - {(min_fail_size//3.5)/1000:.0f}k tokens)")
    print("")

    # 1M tokens would be ~3.5M chars
    if min_fail_size >= 3000000:
        print("  ✓ CONFIRMED: 1M token context window IS supported")
    elif min_fail_size >= 2000000:
        print("  ~ PARTIAL: ~600-800k token context window (not full 1M)")
    else:
        print("  ✗ LIMITED: Context window less than advertised 1M tokens")
