"""
Compression orchestration logic.
Coordinates Agent 1 (Selector) + Agent 2 (Compressor) + Stitching.
"""
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from src.agents.agent1_selector import Agent1Selector
from src.agents.agent2_compressor import Agent2Compressor
from src.utils.stitching import stitch_compressed_blocks
from src.utils.token_counter import TokenCounter
from src.utils.data_loader import add_line_numbers, remove_line_numbers

# Path to compression instructions file
INSTRUCTIONS_FILE = Path(__file__).parent.parent.parent / "COMPRESSION_INSTRUCTIONS.md"


class CompressionOrchestrator:
    """
    Orchestrates the compression workflow:
    1. Agent 1 selects blocks to compress
    2. Agent 2 compresses each block (parallel)
    3. Stitching reassembles the context
    """

    def __init__(
        self,
        agent1: Optional[Agent1Selector] = None,
        agent2: Optional[Agent2Compressor] = None,
        token_counter: Optional[TokenCounter] = None
    ):
        """
        Initialize orchestrator.

        Args:
            agent1: Agent 1 instance (creates new if None)
            agent2: Agent 2 instance (creates new if None)
            token_counter: TokenCounter instance (creates new if None)
        """
        self.agent1 = agent1 or Agent1Selector()
        self.agent2 = agent2 or Agent2Compressor()
        self.token_counter = token_counter or TokenCounter()

    def _read_compression_instructions(self) -> str:
        """
        Read compression instructions file before each compression.

        Returns:
            Instructions text or empty string if file not found
        """
        try:
            if INSTRUCTIONS_FILE.exists():
                with open(INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
                    instructions = f.read()
                print(f"[Orchestrator] Read compression instructions ({len(instructions)} chars)")
                return instructions
            else:
                print(f"[Orchestrator] Warning: Instructions file not found at {INSTRUCTIONS_FILE}")
                return ""
        except Exception as e:
            print(f"[Orchestrator] Error reading instructions: {e}")
            return ""

    def compress_context(
        self,
        context: str,
        category: str,
        need_to_free: int
    ) -> Dict:
        """
        Compress context by freeing specified number of tokens.

        Args:
            context: Full context text (without line numbers)
            category: Category being compressed
            need_to_free: Number of tokens to free

        Returns:
            Dict with:
                - compressed_context: str
                - blocks: List[Dict] with compression details
                - original_tokens: int
                - final_tokens: int
                - tokens_saved: int
                - time_seconds: float
        """
        start_time = time.time()

        # ALWAYS read compression instructions before starting
        instructions = self._read_compression_instructions()

        # Add line numbers for Agent 1
        numbered_context = add_line_numbers(context)

        # Step 1: Agent 1 selects blocks
        selection_result = self.agent1.select_blocks(
            context=numbered_context,
            need_to_free=need_to_free,
            category=category
        )

        if not selection_result['blocks']:
            # No blocks selected - return original context
            return {
                'compressed_context': context,
                'blocks': [],
                'original_tokens': self.token_counter.count_tokens(context),
                'final_tokens': self.token_counter.count_tokens(context),
                'tokens_saved': 0,
                'time_seconds': time.time() - start_time
            }

        # Step 2: Agent 2 compresses each block
        blocks_with_compression = []
        total_original = 0
        total_compressed = 0

        for block in selection_result['blocks']:
            compression_result = self.agent2.compress_block(
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

        # Step 3: Stitch compressed blocks back
        compressed_context_numbered = stitch_compressed_blocks(
            numbered_context,
            blocks_with_compression
        )

        # Remove line numbers for final result
        compressed_context = remove_line_numbers(compressed_context_numbered)

        # Calculate final metrics
        original_tokens = self.token_counter.count_tokens(context)
        final_tokens = self.token_counter.count_tokens(compressed_context)
        tokens_saved = original_tokens - final_tokens

        return {
            'compressed_context': compressed_context,
            'blocks': blocks_with_compression,
            'original_tokens': original_tokens,
            'final_tokens': final_tokens,
            'tokens_saved': tokens_saved,
            'time_seconds': time.time() - start_time
        }

    def should_compress_category(
        self,
        category: str,
        current_tokens: int,
        quota: int
    ) -> bool:
        """
        Check if category needs compression.

        Args:
            category: Category name
            current_tokens: Current token count
            quota: Token quota for category

        Returns:
            True if compression needed (≥90% full)
        """
        fill_percent = (current_tokens / quota * 100) if quota > 0 else 0
        return fill_percent >= 90.0

    def calculate_tokens_to_free(
        self,
        current_tokens: int,
        quota: int
    ) -> int:
        """
        Calculate how many tokens need to be freed.

        Args:
            current_tokens: Current token count
            quota: Token quota

        Returns:
            Number of tokens to free (to reach 70% of quota)
        """
        target = int(quota * 0.70)
        return max(0, current_tokens - target)
