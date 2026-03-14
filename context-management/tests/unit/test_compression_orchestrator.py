"""
Unit tests for compression orchestrator.
"""
import pytest
from src.proxy.compression import CompressionOrchestrator
from src.utils.token_counter import TokenCounter


def test_orchestrator_initialization():
    """Test orchestrator initializes correctly"""
    orchestrator = CompressionOrchestrator()

    assert orchestrator.agent1 is not None
    assert orchestrator.agent2 is not None
    assert orchestrator.token_counter is not None


def test_should_compress_category():
    """Test compression trigger logic"""
    orchestrator = CompressionOrchestrator()

    # 80% - should not compress
    assert not orchestrator.should_compress_category("Test", 800, 1000)

    # 90% - should compress
    assert orchestrator.should_compress_category("Test", 900, 1000)

    # 95% - should compress
    assert orchestrator.should_compress_category("Test", 950, 1000)


def test_calculate_tokens_to_free():
    """Test tokens to free calculation"""
    orchestrator = CompressionOrchestrator()

    # Current: 950, Quota: 1000
    # Target: 70% of 1000 = 700
    # Need to free: 950 - 700 = 250
    tokens_to_free = orchestrator.calculate_tokens_to_free(950, 1000)
    assert tokens_to_free == 250

    # Current: 900, Quota: 1000
    # Target: 700
    # Need to free: 900 - 700 = 200
    tokens_to_free = orchestrator.calculate_tokens_to_free(900, 1000)
    assert tokens_to_free == 200

    # Current: 600, Quota: 1000
    # Target: 700
    # Need to free: 0 (already below target)
    tokens_to_free = orchestrator.calculate_tokens_to_free(600, 1000)
    assert tokens_to_free == 0


def test_compress_context_empty_blocks():
    """Test compression when no blocks are selected"""
    orchestrator = CompressionOrchestrator()

    # Very small context - Agent 1 likely won't select anything
    context = "This is a very short test context."

    result = orchestrator.compress_context(
        context=context,
        category="Test",
        need_to_free=100  # Request more than available
    )

    # Should return original context unchanged
    assert result['compressed_context'] == context
    assert len(result['blocks']) == 0
    assert result['tokens_saved'] == 0
