"""
Manual quality assessment for Agent 1 on large context (~180k tokens).
"""
from pathlib import Path
from src.agents.agent1_selector import Agent1Selector
from src.utils.data_loader import ConversationLoader, add_line_numbers

def extract_block_content(context: str, start_line: int, end_line: int) -> str:
    """Extract content of a specific block"""
    lines = context.split('\n')
    block_lines = lines[start_line-1:end_line]
    return '\n'.join(block_lines)

def manual_quality_check_large():
    """
    Run Agent 1 on full conversation (~180k tokens).
    """
    print("=== AGENT 1 QUALITY CHECK (LARGE: ~180k tokens) ===\n")

    # Load test data
    conv_path = Path(__file__).parent.parent.parent.parent / "references" / "conversation_-2--sensetivity_2026-03-12-1103.agi.json"
    loader = ConversationLoader(str(conv_path))

    # Get full conversation
    messages = loader.get_messages()
    context = "\n\n".join([loader._extract_content(msg) for msg in messages])
    actual_tokens = loader.count_tokens(context)
    numbered_context = add_line_numbers(context)

    print(f"Context: full conversation ({len(messages)} messages)")
    print(f"Total tokens: {actual_tokens}")
    print(f"Total lines: {len(context.split(chr(10)))}\n")

    # Run Agent 1
    agent1 = Agent1Selector()
    need_to_free = min(int(actual_tokens * 0.3), 50000)  # 30% or 50k, whichever is smaller

    print(f"Requesting to free: {need_to_free} tokens\n")

    try:
        result = agent1.select_blocks(
            context=numbered_context,
            need_to_free=need_to_free
        )

        print(f"Blocks selected: {len(result['blocks'])}")
        print(f"Total tokens to free: {result.get('total_tokens_to_free', 'N/A')}\n")

        # Display each block
        for i, block in enumerate(result['blocks'], 1):
            print(f"\n{'='*80}")
            print(f"BLOCK {i}")
            print(f"{'='*80}")
            print(f"Lines: {block['start_line']} - {block['end_line']}")
            print(f"Estimated tokens: {block['estimated_tokens']}")
            print(f"Reasoning: {block['reasoning']}")
            print(f"\n--- CONTENT PREVIEW ---")

            content = extract_block_content(
                numbered_context,
                block['start_line'],
                block['end_line']
            )

            # Show first and last 10 lines
            content_lines = content.split('\n')
            if len(content_lines) > 20:
                print('\n'.join(content_lines[:10]))
                print(f"\n... [{len(content_lines) - 20} lines omitted] ...\n")
                print('\n'.join(content_lines[-10:]))
            else:
                print(content)

            print(f"\n--- ASSESSMENT QUESTIONS ---")
            print("1. Does this block contain important formulas? [Y/N]")
            print("2. Does this block contain active code? [Y/N]")
            print("3. Does this block contain critical decisions? [Y/N]")
            print("4. Does this block contain current task context? [Y/N]")
            print("5. Is this block safe to compress? [Y/N]")
            print(f"{'='*80}\n")

        print("\n=== OVERALL ASSESSMENT ===")
        print(f"Total blocks: {len(result['blocks'])}")
        print(f"Estimated tokens to free: {result.get('total_tokens_to_free', 0)}")
        print(f"Target was: {need_to_free}")
        print(f"Coverage: {result.get('total_tokens_to_free', 0) / need_to_free * 100:.1f}%")
        print("\nQuality rating (1-10): ")
        print("Comments: ")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    manual_quality_check_large()
