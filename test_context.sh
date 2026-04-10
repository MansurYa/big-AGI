#!/bin/bash

# Test script for hone.vvvv.ee proxy context window testing

API_KEY="sk-f1L1d0JlzugwtBkJQLPnYC5a1khV9q6eGo0OCXUlAvRywsg0"
API_URL="https://hone.vvvv.ee/v1/messages"
SOURCE_FILE="/Users/mansurzainullin/MyCode/big-AGI/190k_file.txt"

echo "=== Hone.vvvv.ee Context Window Test ==="
echo ""

# Function to test a specific size
test_size() {
    local size=$1
    local description=$2

    echo "Testing $description (~${size} bytes)..."

    # Read specified bytes from source file
    local content=$(head -c $size "$SOURCE_FILE")

    # Create JSON payload using jq for proper escaping
    local payload=$(jq -n \
        --arg model "claude-opus-4-6" \
        --argjson max_tokens 1000 \
        --arg content "Here is a large context document:\n\n$content\n\nPlease confirm you received this context by summarizing what this document is about in 2-3 sentences." \
        '{
            model: $model,
            max_tokens: $max_tokens,
            messages: [{
                role: "user",
                content: $content
            }]
        }')

    # Make the request
    local response=$(curl -s "$API_URL" \
        -H "Content-Type: application/json" \
        -H "x-api-key: $API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -d "$payload")

    # Check for error
    if echo "$response" | grep -q '"error"'; then
        local error_msg=$(echo "$response" | jq -r '.error.message // "Unknown error"')
        echo "  ERROR: $error_msg"
        return 1
    else
        echo "  SUCCESS: Received response"
        echo "  Response preview: $(echo "$response" | jq -r '.content[0].text // .content[0]?.text' | head -c 200)..."
        return 0
    fi
}

# Test with different sizes
echo "Starting tests with increasing context sizes..."
echo ""

# Test 1: ~250k bytes
test_size 250000 "250k bytes"
echo ""

# Test 2: ~500k bytes
test_size 500000 "500k bytes"
echo ""

# Test 3: ~750k bytes
test_size 750000 "750k bytes"
echo ""

# Test 4: ~1M bytes
test_size 1000000 "1M bytes"
echo ""

# Test 5: Full file
full_size=$(wc -c < "$SOURCE_FILE")
test_size $full_size "Full file ($full_size bytes)"
echo ""

echo "=== Tests Complete ==="
