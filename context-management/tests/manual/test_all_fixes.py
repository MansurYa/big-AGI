"""
Test all bugfixes implemented in Phase 1.
Verifies:
1. Formula is correct (need_to_free * 2.0)
2. Incremental compression (save/load compressed context)
3. Iterative compression (loop until 75% target)
4. Proxy offset accounting (-2400 tokens)
5. Tool descriptions accounting (-10k tokens)
6. Dynamic quotas calculation
7. Target is 75% (not 70%)
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.utils.token_counter import (
    TokenCounter,
    get_proxy_offset,
    calculate_dynamic_quotas,
    TOOL_DESCRIPTIONS_TOKENS,
    PROXY_OFFSETS
)
from src.proxy.storage import CompressionStorage


def test_proxy_offset():
    """Test proxy offset calculation"""
    print("\n=== Test 1: Proxy Offset ===")

    # Test with kiro.cheap
    offset = get_proxy_offset('https://api.kiro.cheap')
    assert offset == 2400, f"Expected 2400, got {offset}"
    print(f"✅ Proxy offset for api.kiro.cheap: {offset} tokens")

    # Test without proxy
    offset = get_proxy_offset('https://api.anthropic.com')
    assert offset == 0, f"Expected 0, got {offset}"
    print(f"✅ Proxy offset for anthropic.com: {offset} tokens")

    print("✅ PASS: Proxy offset accounting works")


def test_tool_descriptions():
    """Test tool descriptions constant"""
    print("\n=== Test 2: Tool Descriptions ===")

    assert TOOL_DESCRIPTIONS_TOKENS == 10000, f"Expected 10000, got {TOOL_DESCRIPTIONS_TOKENS}"
    print(f"✅ Tool descriptions: {TOOL_DESCRIPTIONS_TOKENS} tokens")
    print("✅ PASS: Tool descriptions accounting works")


def test_dynamic_quotas():
    """Test dynamic quota calculation"""
    print("\n=== Test 3: Dynamic Quotas ===")

    # Test case from spec: System 2k, Internet 50k, buffer 30k
    quotas = calculate_dynamic_quotas(
        system_size=2000,
        internet_size=50000,
        buffer_size=30000,
        api_base_url='https://api.kiro.cheap'
    )

    # Expected: 200k - 2.4k - 10k - 2k - 50k - 30k = 105.6k
    expected_dialogue = 200000 - 2400 - 10000 - 2000 - 50000 - 30000
    assert quotas['Dialogue'] == expected_dialogue, f"Expected {expected_dialogue}, got {quotas['Dialogue']}"

    print(f"✅ System quota: {quotas['System']} tokens")
    print(f"✅ Internet quota: {quotas['Internet']} tokens")
    print(f"✅ Dialogue quota: {quotas['Dialogue']} tokens (expected {expected_dialogue})")
    print("✅ PASS: Dynamic quotas calculation works")


def test_target_75_percent():
    """Test that target is 75% (not 70%)"""
    print("\n=== Test 4: Target 75% ===")

    counter = TokenCounter()
    counter.set_quota('Dialogue', 100000)
    counter.update_category('Dialogue', 95000)

    cat = counter.get_category('Dialogue')
    target = cat.target_after_compression

    expected_target = int(100000 * 0.75)
    assert target == expected_target, f"Expected {expected_target}, got {target}"

    print(f"✅ Quota: 100k tokens")
    print(f"✅ Current: 95k tokens")
    print(f"✅ Target after compression: {target} tokens (75%)")
    print("✅ PASS: Target is 75% (not 70%)")


def test_incremental_storage():
    """Test incremental compression storage"""
    print("\n=== Test 5: Incremental Storage ===")

    storage = CompressionStorage()
    test_chat_id = "test_chat_incremental"
    test_context = "This is a test compressed context with some content."

    # Save compressed context
    storage.save_compressed_context(test_chat_id, test_context)
    print(f"✅ Saved compressed context ({len(test_context)} chars)")

    # Load compressed context
    loaded = storage.load_compressed_context(test_chat_id)
    assert loaded == test_context, "Loaded context doesn't match saved"
    print(f"✅ Loaded compressed context ({len(loaded)} chars)")

    # Cleanup
    import shutil
    storage_dir = storage.storage_dir
    if (storage_dir / f"{test_chat_id}_compressed_context.json").exists():
        (storage_dir / f"{test_chat_id}_compressed_context.json").unlink()

    print("✅ PASS: Incremental storage works")


def test_formula_verification():
    """Verify the fallback formula is correct"""
    print("\n=== Test 6: Formula Verification ===")

    # Read agent1_selector.py and check formula
    with open('src/agents/agent1_selector.py', 'r') as f:
        content = f.read()

    # Check for correct formula
    assert 'target_tokens = int(need_to_free * 2.0)' in content, "Formula not found or incorrect"
    print("✅ Formula found: target_tokens = int(need_to_free * 2.0)")

    # Check for token-based buffers
    assert 'buffer_tokens = 10000' in content, "Token-based buffers not found"
    print("✅ Token-based buffers: 10k tokens")

    print("✅ PASS: Formula is correct")


def test_iterative_compression_code():
    """Verify iterative compression is implemented"""
    print("\n=== Test 7: Iterative Compression Code ===")

    # Read compression.py and check for while loop
    with open('src/proxy/compression.py', 'r') as f:
        content = f.read()

    # Check for iterative loop
    assert 'while current_tokens > target_tokens and iterations < max_iterations:' in content, "Iterative loop not found"
    print("✅ Iterative loop found in compress_context()")

    # Check for iteration tracking
    assert 'iterations = 0' in content, "Iteration counter not found"
    assert 'iterations += 1' in content, "Iteration increment not found"
    print("✅ Iteration tracking implemented")

    # Check for progress protection
    assert 'min_progress_percent' in content, "Progress protection not found"
    print("✅ Progress protection implemented")

    print("✅ PASS: Iterative compression implemented")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TESTING ALL PHASE 1 BUGFIXES")
    print("=" * 60)

    try:
        test_proxy_offset()
        test_tool_descriptions()
        test_dynamic_quotas()
        test_target_75_percent()
        test_incremental_storage()
        test_formula_verification()
        test_iterative_compression_code()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("1. ✅ Proxy offset accounting (-2400 tokens)")
        print("2. ✅ Tool descriptions accounting (-10k tokens)")
        print("3. ✅ Dynamic quotas calculation")
        print("4. ✅ Target is 75% (not 70%)")
        print("5. ✅ Incremental storage (save/load compressed context)")
        print("6. ✅ Formula is correct (need_to_free * 2.0)")
        print("7. ✅ Iterative compression implemented")
        print("\n🎉 Phase 1 implementation verified!")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
