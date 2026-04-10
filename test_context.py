#!/usr/bin/env python3
"""
Test script for hone.vvvv.ee proxy context window testing
Testing actual token limits with larger contexts
"""

import requests
import json
import sys

API_KEY = "sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL = "https://hone.vvvv.ee/v1/messages"
SOURCE_FILE = "/Users/mansurzainullin/MyCode/big-AGI/190k_file.txt"

# Read source file
with open(SOURCE_FILE, 'r') as f:
    source_content = f.read()

print("=== Hone.vvvv.ee Context Window Test ===")
print(f"Source file size: {len(source_content)} characters")
print("")

# Rough estimation: 1 token ~= 4 characters in English text
# For mixed Russian/English with code, ~3.5 chars/token
# 200k tokens ~= 700k-800k characters
# 1M tokens ~= 3.5M characters

# Create expanded content by repeating source
expanded_content = (source_content * 5)[:3500000]  # ~1M tokens worth

# Test sizes (in characters)
test_sizes = [
    (700000, "~200k tokens"),
    (1400000, "~400k tokens"),
    (2100000, "~600k tokens"),
    (2800000, "~800k tokens"),
    (3500000, "~1M tokens"),
]

results = []

for size, description in test_sizes:
    print(f"Testing {description} ({size} chars)...")

    # Truncate content to test size
    test_content = expanded_content[:size]

    # Create payload
    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": f"Here is a large context document:\n\n{test_content}\n\nPlease confirm you received this context by summarizing what this document is about in 2-3 sentences."
        }]
    }

    # Make request
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response_data = response.json()

        if "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"  ERROR: {error_msg}")
            results.append((size, description, False, error_msg))
        else:
            print(f"  SUCCESS: Received response")
            content_text = response_data.get("content", [{}])[0].get("text", "")[:200]
            print(f"  Response preview: {content_text}...")
            results.append((size, description, True, "OK"))
    except requests.exceptions.Timeout:
        error_msg = "Request timeout (300s)"
        print(f"  TIMEOUT: {error_msg}")
        results.append((size, description, False, error_msg))
    except Exception as e:
        error_msg = str(e)
        print(f"  ERROR: {error_msg}")
        results.append((size, description, False, error_msg))

    print("")

print("=== Test Results Summary ===")
print("")

for size, description, success, message in results:
    status = "✓ SUCCESS" if success else "✗ ERROR"
    print(f"{description}: {status}")
    if not success:
        print(f"  Error: {message}")
    print("")

# Find maximum working size
working_sizes = [(s, d) for s, d, success, _ in results if success]
if working_sizes:
    max_working = max(working_sizes, key=lambda x: x[0])
    print(f"Maximum working context size: {max_working[1]} ({max_working[0]} chars)")
else:
    print("No tests succeeded - checking error messages for context limit info...")
    all_errors = [m for _, _, _, m in results if not m == "OK"]
    for err in all_errors:
        if "上下文过长" in err or "context" in err.lower() or "too long" in err.lower() or "window" in err.lower():
            print(f"  Context length error detected: {err}")
