"""
S0.3 - Token Counting Test
Tests that token counter works correctly with category support.
"""
import sys
sys.path.insert(0, '/Users/mansurzainullin/MyCode/big-AGI/context-management')

from src.utils.token_counter import TokenCounter, calculate_dynamic_quotas, get_proxy_offset

def test_token_counting():
    """Test token counting functionality."""

    print("=== S0.3: TOKEN COUNTING TEST ===\n")

    # Test 1: Basic token counting
    print("Test 1: Basic token counting...")
    counter = TokenCounter()

    test_text = "Hello, world! This is a test message."
    tokens = counter.count_tokens(test_text)
    print(f"  Text: '{test_text}'")
    print(f"  Tokens: {tokens}")

    if tokens > 0:
        print("  ✓ PASS: Token counting works")
    else:
        print("  ✗ FAIL: Token count is 0")
        return False

    # Test 2: Category quota management
    print("\nTest 2: Category quota management...")
    counter.set_quota("System", 5000)
    counter.set_quota("Internet", 60000)
    counter.set_quota("Dialogue", 100000)

    counter.update_category("System", 2000)
    counter.update_category("Internet", 54000)  # 90% of 60k
    counter.update_category("Dialogue", 50000)

    summary = counter.get_summary()
    print(f"  Summary: {summary}")

    # Check Internet at 90%
    internet_cat = counter.get_category("Internet")
    if internet_cat and internet_cat.needs_compression:
        print(f"  ✓ PASS: Internet at {internet_cat.fill_percent:.1f}% triggers compression")
    else:
        print(f"  ✗ FAIL: Internet at 90% should trigger compression")
        return False

    # Test 3: Dynamic quota calculation
    print("\nTest 3: Dynamic quota calculation...")
    quotas = calculate_dynamic_quotas(
        system_size=2000,
        internet_size=50000,
        buffer_size=30000,
        api_base_url="https://api.kiro.cheap"
    )

    print(f"  Dynamic quotas: {quotas}")

    expected_dialogue = 200000 - 2400 - 10000 - 2000 - 50000 - 30000
    actual_dialogue = quotas['Dialogue']

    print(f"  Expected Dialogue: {expected_dialogue}")
    print(f"  Actual Dialogue: {actual_dialogue}")

    if actual_dialogue == expected_dialogue:
        print("  ✓ PASS: Dynamic quota calculation correct")
    else:
        print(f"  ✗ FAIL: Expected {expected_dialogue}, got {actual_dialogue}")
        return False

    # Test 4: Proxy offset detection
    print("\nTest 4: Proxy offset detection...")
    offset = get_proxy_offset("https://api.kiro.cheap")
    print(f"  Proxy offset for api.kiro.cheap: {offset}")

    if offset == 2400:
        print("  ✓ PASS: Proxy offset detected correctly")
    else:
        print(f"  ✗ FAIL: Expected 2400, got {offset}")
        return False

    print("\n=== S0.3 RESULT: PASS ===")
    return True

if __name__ == "__main__":
    success = test_token_counting()
    exit(0 if success else 1)
