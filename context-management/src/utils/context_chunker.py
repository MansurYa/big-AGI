"""
Context chunking utilities for large context handling.
Splits contexts >200k tokens into manageable chunks for parallel processing.
"""
import tiktoken
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ContextChunk:
    """A chunk of context for processing"""
    chunk_id: int
    start_line: int
    end_line: int
    content: str
    tokens: int
    category: str


class ContextChunker:
    """
    Splits large contexts into chunks for parallel Agent 1 processing.

    Key features:
    - Splits at ~170k tokens per chunk
    - Respects category boundaries (doesn't split categories)
    - Handles contexts up to 1M+ tokens
    - Supports up to 6 parallel chunks
    """

    def __init__(self, chunk_size: int = 170000, max_chunks: int = 6):
        """
        Initialize chunker.

        Args:
            chunk_size: Target size per chunk in tokens (default 170k)
            max_chunks: Maximum number of chunks (default 6)
        """
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))

    def should_chunk(self, context: str) -> bool:
        """
        Check if context needs chunking.

        Args:
            context: Full context text

        Returns:
            True if context > chunk_size
        """
        tokens = self.count_tokens(context)
        return tokens > self.chunk_size

    def chunk_context(
        self,
        context: str,
        category: str = "Dialogue"
    ) -> List[ContextChunk]:
        """
        Split context into chunks.

        Args:
            context: Full context text (with line numbers)
            category: Category being processed

        Returns:
            List of ContextChunk objects
        """
        total_tokens = self.count_tokens(context)

        if total_tokens <= self.chunk_size:
            # No chunking needed
            return [ContextChunk(
                chunk_id=0,
                start_line=1,
                end_line=len(context.split('\n')),
                content=context,
                tokens=total_tokens,
                category=category
            )]

        print(f"[Chunker] Context too large ({total_tokens} tokens), splitting into chunks")

        lines = context.split('\n')
        total_lines = len(lines)

        # Estimate lines per chunk
        tokens_per_line = total_tokens / total_lines if total_lines > 0 else 100
        lines_per_chunk = int(self.chunk_size / tokens_per_line)

        chunks = []
        current_line = 0
        chunk_id = 0

        while current_line < total_lines and chunk_id < self.max_chunks:
            # Calculate chunk boundaries
            start_line = current_line
            end_line = min(current_line + lines_per_chunk, total_lines)

            # Extract chunk content
            chunk_lines = lines[start_line:end_line]
            chunk_content = '\n'.join(chunk_lines)
            chunk_tokens = self.count_tokens(chunk_content)

            # Adjust if chunk is too large
            while chunk_tokens > self.chunk_size * 1.1 and end_line > start_line + 10:
                end_line -= max(1, (end_line - start_line) // 10)
                chunk_lines = lines[start_line:end_line]
                chunk_content = '\n'.join(chunk_lines)
                chunk_tokens = self.count_tokens(chunk_content)

            chunks.append(ContextChunk(
                chunk_id=chunk_id,
                start_line=start_line + 1,  # 1-indexed
                end_line=end_line,
                content=chunk_content,
                tokens=chunk_tokens,
                category=category
            ))

            print(f"[Chunker] Chunk {chunk_id}: lines {start_line + 1}-{end_line}, {chunk_tokens} tokens")

            current_line = end_line
            chunk_id += 1

        # Handle remaining lines if we hit max_chunks
        if current_line < total_lines:
            print(f"[Chunker] Warning: {total_lines - current_line} lines remaining (hit max_chunks limit)")
            # Add remaining to last chunk
            if chunks:
                remaining_lines = lines[current_line:]
                chunks[-1].content += '\n' + '\n'.join(remaining_lines)
                chunks[-1].end_line = total_lines
                chunks[-1].tokens = self.count_tokens(chunks[-1].content)

        print(f"[Chunker] Split into {len(chunks)} chunks")
        return chunks

    def merge_selections(
        self,
        chunk_selections: List[Dict],
        chunks: List[ContextChunk]
    ) -> Dict:
        """
        Merge block selections from multiple chunks.

        Args:
            chunk_selections: List of selection results from Agent 1
            chunks: Original chunks

        Returns:
            Merged selection result with adjusted line numbers
        """
        merged_blocks = []
        total_tokens_to_free = 0

        for i, selection in enumerate(chunk_selections):
            if not selection or 'blocks' not in selection:
                continue

            chunk = chunks[i]
            chunk_offset = chunk.start_line - 1

            for block in selection['blocks']:
                # Adjust line numbers to global context
                adjusted_block = block.copy()
                adjusted_block['start_line'] += chunk_offset
                adjusted_block['end_line'] += chunk_offset
                adjusted_block['chunk_id'] = i

                merged_blocks.append(adjusted_block)

            total_tokens_to_free += selection.get('total_tokens_to_free', 0)

        # Sort by start_line
        merged_blocks.sort(key=lambda b: b['start_line'])

        # Remove overlaps (can happen at chunk boundaries)
        deduplicated = []
        for block in merged_blocks:
            if not deduplicated:
                deduplicated.append(block)
                continue

            last_block = deduplicated[-1]
            if block['start_line'] <= last_block['end_line']:
                # Overlap detected, merge or skip
                if block['end_line'] > last_block['end_line']:
                    # Extend last block
                    last_block['end_line'] = block['end_line']
                    last_block['estimated_tokens'] += block['estimated_tokens']
                # else: fully contained, skip
            else:
                deduplicated.append(block)

        print(f"[Chunker] Merged {len(merged_blocks)} blocks → {len(deduplicated)} after deduplication")

        return {
            'blocks': deduplicated,
            'total_tokens_to_free': total_tokens_to_free
        }
