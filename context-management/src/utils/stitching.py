"""
Context stitching module.
Assembles compressed blocks back into context.
"""
from typing import List, Dict

def stitch_compressed_blocks(original_context: str, blocks_with_compression: List[Dict]) -> str:
    """
    Assemble compressed blocks back into context.

    Algorithm: Process blocks from END to START (bottom-up) to avoid line shift issues.

    Args:
        original_context: Original context with line numbers
        blocks_with_compression: List of dicts with:
            - 'start_line': int
            - 'end_line': int
            - 'compressed_text': str

    Returns:
        Assembled context with compressed blocks

    Example:
        >>> blocks = [
        ...     {'start_line': 10, 'end_line': 20, 'compressed_text': 'compressed 1'},
        ...     {'start_line': 50, 'end_line': 60, 'compressed_text': 'compressed 2'}
        ... ]
        >>> result = stitch_compressed_blocks(original, blocks)
    """
    if not blocks_with_compression:
        return original_context

    # Sort blocks by start_line in reverse order (bottom-up)
    sorted_blocks = sorted(blocks_with_compression, key=lambda b: b['start_line'], reverse=True)

    # Split context into lines
    lines = original_context.split('\n')

    # Process each block from bottom to top
    for block in sorted_blocks:
        start_idx = block['start_line'] - 1  # Convert to 0-indexed
        end_idx = block['end_line']  # Exclusive end

        # Validate indices
        if start_idx < 0 or end_idx > len(lines):
            raise ValueError(
                f"Block indices out of range: start={block['start_line']}, "
                f"end={block['end_line']}, total_lines={len(lines)}"
            )

        if start_idx >= end_idx:
            raise ValueError(
                f"Invalid block range: start={block['start_line']} >= end={block['end_line']}"
            )

        # Extract before and after
        before = lines[:start_idx]
        after = lines[end_idx:]

        # Insert compressed block (split into lines)
        compressed_lines = block['compressed_text'].split('\n')

        # Reassemble
        lines = before + compressed_lines + after

    return '\n'.join(lines)


def validate_blocks(blocks: List[Dict], total_lines: int) -> None:
    """
    Validate that blocks don't overlap and are within bounds.

    Args:
        blocks: List of block dicts with 'start_line' and 'end_line'
        total_lines: Total number of lines in context

    Raises:
        ValueError: If blocks overlap or are out of bounds
    """
    if not blocks:
        return

    # Sort by start_line
    sorted_blocks = sorted(blocks, key=lambda b: b['start_line'])

    # Check each block
    for i, block in enumerate(sorted_blocks):
        # Check bounds
        if block['start_line'] < 1 or block['end_line'] > total_lines:
            raise ValueError(
                f"Block {i} out of bounds: lines {block['start_line']}-{block['end_line']}, "
                f"total={total_lines}"
            )

        # Check order
        if block['start_line'] >= block['end_line']:
            raise ValueError(
                f"Block {i} invalid range: start={block['start_line']} >= end={block['end_line']}"
            )

        # Check overlap with next block
        if i < len(sorted_blocks) - 1:
            next_block = sorted_blocks[i + 1]
            if block['end_line'] > next_block['start_line']:
                raise ValueError(
                    f"Blocks {i} and {i+1} overlap: "
                    f"block {i} ends at {block['end_line']}, "
                    f"block {i+1} starts at {next_block['start_line']}"
                )


def calculate_compression_stats(
    original_tokens: int,
    final_tokens: int,
    blocks: List[Dict]
) -> Dict:
    """
    Calculate compression statistics.

    Args:
        original_tokens: Original context token count
        final_tokens: Final context token count after compression
        blocks: List of compressed blocks with 'original_tokens' and 'compressed_tokens'

    Returns:
        Dict with compression statistics
    """
    total_original_blocks = sum(b.get('original_tokens', 0) for b in blocks)
    total_compressed_blocks = sum(b.get('compressed_tokens', 0) for b in blocks)

    tokens_saved = original_tokens - final_tokens
    savings_percent = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0

    avg_block_ratio = (
        total_original_blocks / total_compressed_blocks
        if total_compressed_blocks > 0 else 0
    )

    return {
        'original_tokens': original_tokens,
        'final_tokens': final_tokens,
        'tokens_saved': tokens_saved,
        'savings_percent': savings_percent,
        'blocks_processed': len(blocks),
        'total_original_blocks': total_original_blocks,
        'total_compressed_blocks': total_compressed_blocks,
        'avg_block_ratio': avg_block_ratio
    }
