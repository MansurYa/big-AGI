"""
Test Agent 2 on technical content (code, formulas, architecture).
"""
from pathlib import Path
from src.agents.agent1_selector import Agent1Selector
from src.agents.agent2_compressor import Agent2Compressor
from src.utils.data_loader import ConversationLoader, add_line_numbers

def test_agent2_on_technical_content():
    """
    Test Agent 2 on technical blocks with code, formulas, and architecture.
    """
    print("=== AGENT 2 TECHNICAL CONTENT TEST ===\n")

    # Load test data
    conv_path = Path(__file__).parent.parent.parent.parent / "references" / "conversation_-2--sensetivity_2026-03-12-1103.agi.json"
    loader = ConversationLoader(str(conv_path))

    # Build a deterministic slice to keep runtime predictable
    import os
    target_tokens = int(os.getenv("AGENT2_CONTEXT_TOKENS", "30000"))
    context = loader.create_slice(target_tokens=target_tokens)
    numbered_context = add_line_numbers(context)

    print(f"Context: {loader.count_tokens(context)} tokens\n", flush=True)

    # Run Agent 1 to select technical blocks
    agent1 = Agent1Selector()
    need_to_free = 9000

    print("Running Agent 1 to select technical blocks...\n")
    result = agent1.select_blocks(
        context=numbered_context,
        need_to_free=need_to_free
    )

    if not result['blocks']:
        print("ERROR: Agent 1 didn't select any blocks")
        return

    # Test on multiple blocks
    import os
    strategy = os.getenv("AGENT2_STRATEGY", "minimal")
    agent2 = Agent2Compressor(strategy=strategy)
    print(f"Agent2 strategy: {strategy}\n", flush=True)

    for idx, block in enumerate(result['blocks'][:3], 1):  # Test first 3 blocks
        print(f"\n{'='*80}")
        print(f"TESTING BLOCK {idx}/{min(3, len(result['blocks']))}")
        print(f"{'='*80}")
        print(f"Lines: {block['start_line']} - {block['end_line']}")
        print(f"Estimated tokens: {block['estimated_tokens']}")
        print(f"Reasoning: {block['reasoning'][:100]}...\n")

        # Extract block preview
        lines = numbered_context.split('\n')
        block_lines = lines[block['start_line']-1:block['end_line']]
        block_text = '\n'.join(block_lines)

        print("=== ORIGINAL (first 300 chars) ===")
        print(block_text[:300])
        print("...\n")

        # Compress
        print("Compressing...")
        compression_result = agent2.compress_block(
            context=numbered_context,
            start_line=block['start_line'],
            end_line=block['end_line'],
            estimated_tokens=block['estimated_tokens']
        )

        print(f"\n=== RESULTS ===")
        print(f"Original tokens: {compression_result['original_tokens']}")
        print(f"Compressed tokens: {compression_result['compressed_tokens']}")
        print(f"Ratio: {compression_result['ratio']:.2f}x")
        print(f"Status: {'✅ PASS' if 3.0 <= compression_result['ratio'] <= 5.0 else '⚠️ MARGINAL' if 2.5 <= compression_result['ratio'] < 3.0 else '❌ FAIL'}")

        print(f"\n=== COMPRESSED (first 300 chars) ===")
        print(compression_result['compressed_text'][:300])
        print("...\n")

        # Check for common technical entities
        original_lower = block_text.lower()
        compressed_lower = compression_result['compressed_text'].lower()

        # Look for formulas, code patterns
        has_formulas = any(marker in original_lower for marker in ['=', '∑', '∫', 'formula', 'equation'])
        has_code = any(marker in original_lower for marker in ['def ', 'class ', 'function', 'return', 'import'])
        has_tables = '|' in block_text and '---' in block_text

        print(f"Content type: ", end="")
        if has_formulas:
            print("Formulas ", end="")
        if has_code:
            print("Code ", end="")
        if has_tables:
            print("Tables ", end="")
        print()

        # Entity preservation check
        if has_formulas or has_code:
            # Extract some technical terms
            import re
            # Find variable-like patterns (word_word, CamelCase, etc.)
            tech_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b|\b\w+_\w+\b|\b[A-Z]{2,}\b', block_text)
            if tech_terms:
                sample_terms = list(set(tech_terms))[:10]
                preserved = sum(1 for term in sample_terms if term in compression_result['compressed_text'])
                print(f"Technical term preservation: {preserved}/{len(sample_terms)} terms")

        print(f"{'='*80}\n")

    print("\n=== OVERALL ASSESSMENT ===")
    print("Skipped: would re-run compressions (extra API calls) and may trigger proxy timeouts.")
    print("Use the per-block ratios above for evaluation.")

if __name__ == "__main__":
    test_agent2_on_technical_content()
