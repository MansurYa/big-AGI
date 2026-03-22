"""
Parallel Agent 1 orchestration for large contexts.
Splits context into chunks and processes them in parallel.
"""
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from src.agents.agent1_selector import Agent1Selector
from src.utils.context_chunker import ContextChunker, ContextChunk


class ParallelAgent1Orchestrator:
    """
    Orchestrates parallel Agent 1 processing for large contexts.

    Features:
    - Splits contexts >170k tokens into chunks
    - Processes up to 6 chunks in parallel
    - Merges results with proper line number adjustment
    """

    def __init__(
        self,
        agent1: Agent1Selector = None,
        max_parallel: int = 6,
        chunk_size: int = 170000
    ):
        """
        Initialize orchestrator.

        Args:
            agent1: Agent1Selector instance (creates new if None)
            max_parallel: Maximum parallel Agent 1 instances (default 6)
            chunk_size: Target chunk size in tokens (default 170k)
        """
        self.agent1 = agent1 or Agent1Selector()
        self.max_parallel = max_parallel
        self.chunker = ContextChunker(chunk_size=chunk_size, max_chunks=max_parallel)

    def select_blocks_parallel(
        self,
        context: str,
        need_to_free: int,
        category: str = "Dialogue"
    ) -> Dict:
        """
        Select blocks using parallel Agent 1 processing if needed.

        Args:
            context: Full context with line numbering
            need_to_free: Number of tokens to free
            category: Category being compressed

        Returns:
            Dict with 'blocks' array and 'total_tokens_to_free'
        """
        # Check if chunking is needed
        if not self.chunker.should_chunk(context):
            # Context small enough, use single Agent 1
            print(f"[ParallelAgent1] Context small enough, using single Agent 1")
            return self.agent1.select_blocks(
                context=context,
                need_to_free=need_to_free,
                category=category
            )

        # Split into chunks
        chunks = self.chunker.chunk_context(context, category)

        if len(chunks) == 1:
            # Only one chunk, use single Agent 1
            print(f"[ParallelAgent1] Only one chunk, using single Agent 1")
            return self.agent1.select_blocks(
                context=context,
                need_to_free=need_to_free,
                category=category
            )

        print(f"[ParallelAgent1] Processing {len(chunks)} chunks in parallel")

        # Calculate need_to_free per chunk (proportional to chunk size)
        total_tokens = sum(chunk.tokens for chunk in chunks)
        chunk_needs = [
            int(need_to_free * (chunk.tokens / total_tokens))
            for chunk in chunks
        ]

        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=min(len(chunks), self.max_parallel)) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                future = executor.submit(
                    self._process_chunk,
                    chunk,
                    chunk_needs[i],
                    category
                )
                futures.append(future)

            # Wait for all to complete
            chunk_selections = [future.result() for future in futures]

        # Merge results
        merged = self.chunker.merge_selections(chunk_selections, chunks)

        print(f"[ParallelAgent1] Merged {len(merged['blocks'])} blocks from {len(chunks)} chunks")

        return merged

    def _process_chunk(
        self,
        chunk: ContextChunk,
        need_to_free: int,
        category: str
    ) -> Dict:
        """
        Process a single chunk with Agent 1.

        Args:
            chunk: ContextChunk to process
            need_to_free: Tokens to free from this chunk
            category: Category being compressed

        Returns:
            Selection result from Agent 1
        """
        print(f"[ParallelAgent1] Processing chunk {chunk.chunk_id} ({chunk.tokens} tokens)")

        try:
            result = self.agent1.select_blocks(
                context=chunk.content,
                need_to_free=need_to_free,
                category=category
            )

            print(f"[ParallelAgent1] Chunk {chunk.chunk_id} selected {len(result.get('blocks', []))} blocks")
            return result

        except Exception as e:
            print(f"[ParallelAgent1] Error processing chunk {chunk.chunk_id}: {e}")
            # Return empty selection on error
            return {'blocks': [], 'total_tokens_to_free': 0}
