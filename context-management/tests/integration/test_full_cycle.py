"""
Full compression cycle integration test.
Tests: Agent 1 selection → Agent 2 compression → Context assembly.
"""
from pathlib import Path
from src.agents.agent1_selector import Agent1Selector
from src.agents.agent2_compressor import Agent2Compressor
from src.utils.data_loader import ConversationLoader, add_line_numbers, remove_line_numbers

def stitch_compressed_blocks(original_context: str, blocks_with_compression: list) -> str:
    """
    Assemble compressed blocks back into context.

    Algorithm: Process blocks from END to START (bottom-up) to avoid line shift issues.

    Args:
        original_context: Original context with line numbers
        blocks_with_compression: List of dicts with 'start_line', 'end_line', 'compressed_text'

    Returns:
        Assembled context with compressed blocks
    """
    # Sort blocks by start_line in reverse order (bottom-up)
    sorted_blocks = sorted(blocks_with_compression, key=lambda b: b['start_line'], reverse=True)

    # Split context into lines
    lines = original_context.split('\n')

    # Process each block from bottom to top
    for block in sorted_blocks:
        start_idx = block['start_line'] - 1  # Convert to 0-indexed
        end_idx = block['end_line']  # Exclusive end

        # Extract before and after
        before = lines[:start_idx]
        after = lines[end_idx:]

        # Insert compressed block (split into lines)
        compressed_lines = block['compressed_text'].split('\n')

        # Reassemble
        lines = before + compressed_lines + after

    return '\n'.join(lines)

def test_full_compression_cycle():
    """
    Test complete compression workflow:
    1. Agent 1 selects blocks
    2. Agent 2 compresses each block
    3. Stitch compressed blocks back into context
    4. Validate result
    """
    print("=== FULL COMPRESSION CYCLE TEST ===\n")

    # Load test data
    conv_path = Path(__file__).parent.parent.parent.parent / "references" / "conversation_-2--sensetivity_2026-03-12-1103.agi.json"
    loader = ConversationLoader(str(conv_path))

    # Use messages 1-2 (~65k tokens)
    messages = loader.get_messages()
    context_messages = messages[:2]
    context = "\n\n".join([loader._extract_content(msg) for msg in context_messages])
    original_tokens = loader.count_tokens(context)
    numbered_context = add_line_numbers(context)

    print(f"Original context: {original_tokens} tokens")
    print(f"Total lines: {len(numbered_context.split(chr(10)))}\n")

    # Step 1: Agent 1 selects blocks
    print("STEP 1: Agent 1 selecting blocks...")
    agent1 = Agent1Selector()
    need_to_free = int(original_tokens * 0.2)  # Free 20%

    selection_result = agent1.select_blocks(
        context=numbered_context,
        need_to_free=need_to_free
    )

    print(f"  Blocks selected: {len(selection_result['blocks'])}")
    print(f"  Target tokens to free: {need_to_free}")
    print(f"  Estimated tokens to free: {selection_result.get('total_tokens_to_free', 0)}\n")

    if not selection_result['blocks']:
        print("ERROR: No blocks selected")
        return

    # Step 2: Agent 2 compresses each block
    print("STEP 2: Agent 2 compressing blocks...")
    agent2 = Agent2Compressor()

    blocks_with_compression = []
    total_original = 0
    total_compressed = 0

    for i, block in enumerate(selection_result['blocks'], 1):
        print(f"  Compressing block {i}/{len(selection_result['blocks'])}...")

        compression_result = agent2.compress_block(
            context=numbered_context,
            start_line=block['start_line'],
            end_line=block['end_line'],
            estimated_tokens=block['estimated_tokens']
        )

        blocks_with_compression.append({
            'start_line': block['start_line'],
            'end_line': block['end_line'],
            'compressed_text': compression_result['compressed_text'],
            'original_tokens': compression_result['original_tokens'],
            'compressed_tokens': compression_result['compressed_tokens'],
            'ratio': compression_result['ratio']
        })

        total_original += compression_result['original_tokens']
        total_compressed += compression_result['compressed_tokens']

        print(f"    {compression_result['original_tokens']} → {compression_result['compressed_tokens']} tokens ({compression_result['ratio']:.2f}x)")

    print(f"\n  Total: {total_original} → {total_compressed} tokens")
    print(f"  Overall compression ratio: {total_original / total_compressed:.2f}x\n")

    # Step 3: Stitch compressed blocks back
    print("STEP 3: Assembling compressed context...")
    compressed_context = stitch_compressed_blocks(numbered_context, blocks_with_compression)

    # Remove line numbers for final result
    final_context = remove_line_numbers(compressed_context)
    final_tokens = loader.count_tokens(final_context)

    print(f"  Final context: {final_tokens} tokens")
    print(f"  Original: {original_tokens} tokens")
    print(f"  Saved: {original_tokens - final_tokens} tokens ({(original_tokens - final_tokens) / original_tokens * 100:.1f}%)")
    print(f"  Target was: {need_to_free} tokens ({need_to_free / original_tokens * 100:.1f}%)\n")

    # Step 4: Validation
    print("STEP 4: Validation...")

    # Check that context is valid
    if len(final_context) == 0:
        print("  ❌ FAIL: Final context is empty")
        return

    if final_tokens >= original_tokens:
        print(f"  ⚠️ WARNING: Final context is larger than original ({final_tokens} >= {original_tokens})")

    # Check compression effectiveness
    actual_savings = original_tokens - final_tokens
    target_savings = need_to_free
    effectiveness = actual_savings / target_savings if target_savings > 0 else 0

    print(f"  Compression effectiveness: {effectiveness * 100:.1f}%")

    if effectiveness >= 0.8:
        print("  ✅ PASS: Achieved ≥80% of target savings")
    elif effectiveness >= 0.5:
        print("  ⚠️ MARGINAL: Achieved 50-80% of target savings")
    else:
        print("  ❌ FAIL: Achieved <50% of target savings")

    # Check for assembly errors
    if compressed_context.count('<AREA_TO_COMPRESS>') > 0:
        print("  ❌ FAIL: Compression markers still present in output")
    else:
        print("  ✅ PASS: No compression markers in output")

    # Preview result
    print("\n=== FINAL CONTEXT PREVIEW (first 500 chars) ===")
    print(final_context[:500])
    print("...\n")

    print("=== SUMMARY ===")
    print(f"Original: {original_tokens} tokens")
    print(f"Compressed: {final_tokens} tokens")
    print(f"Savings: {original_tokens - final_tokens} tokens ({(original_tokens - final_tokens) / original_tokens * 100:.1f}%)")
    print(f"Blocks processed: {len(blocks_with_compression)}")
    print(f"Average block compression: {total_original / total_compressed:.2f}x")
    print(f"Overall status: {'✅ SUCCESS' if effectiveness >= 0.8 else '⚠️ NEEDS IMPROVEMENT'}")

if __name__ == "__main__":
    test_full_compression_cycle()
