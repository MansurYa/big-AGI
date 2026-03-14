"""
Unit tests for Agent 1 (Selector).
"""
import pytest
from src.agents.agent1_selector import Agent1Selector
from src.utils.data_loader import ConversationLoader, add_line_numbers

@pytest.fixture
def agent1():
    return Agent1Selector()

@pytest.fixture
def small_context(test_conversation_path):
    """Create small test context"""
    loader = ConversationLoader(test_conversation_path)
    text = loader.create_slice(target_tokens=5000)
    return add_line_numbers(text)

def test_agent1_initialization(agent1):
    """Test Agent 1 initializes correctly"""
    assert agent1.model == "claude-sonnet-4.5"
    assert agent1.client is not None

def test_agent1_load_prompt(agent1):
    """Test prompt loading"""
    prompt = agent1.load_prompt()
    assert len(prompt) > 0
    assert "Agent 1 (Selector)" in prompt
    assert "COMPRESSIBLE_ZONE" in prompt

def test_agent1_select_blocks_structure(agent1, small_context):
    """Test that Agent 1 returns valid structure"""
    result = agent1.select_blocks(
        context=small_context,
        need_to_free=2000
    )

    # Validate structure
    assert 'blocks' in result
    assert isinstance(result['blocks'], list)
    assert len(result['blocks']) <= 5

    # Validate each block
    for block in result['blocks']:
        assert 'start_line' in block
        assert 'end_line' in block
        assert 'estimated_tokens' in block
        assert 'reasoning' in block

        # Validate types
        assert isinstance(block['start_line'], int)
        assert isinstance(block['end_line'], int)
        assert isinstance(block['estimated_tokens'], int)
        assert isinstance(block['reasoning'], str)

        # Validate ranges
        assert block['start_line'] < block['end_line']
        assert block['estimated_tokens'] <= 10000
        assert len(block['reasoning']) > 20  # Not empty

def test_agent1_no_overlaps(agent1, small_context):
    """Test that selected blocks don't overlap"""
    result = agent1.select_blocks(
        context=small_context,
        need_to_free=3000
    )

    blocks = result['blocks']
    if len(blocks) < 2:
        pytest.skip("Need at least 2 blocks to test overlaps")

    # Sort by start_line
    sorted_blocks = sorted(blocks, key=lambda b: b['start_line'])

    # Check no overlaps
    for i in range(len(sorted_blocks) - 1):
        current = sorted_blocks[i]
        next_block = sorted_blocks[i + 1]
        assert current['end_line'] < next_block['start_line'], \
            f"Overlap detected: {current['end_line']} >= {next_block['start_line']}"

def test_agent1_respects_token_target(agent1, small_context):
    """Test that Agent 1 selects approximately the right amount"""
    need_to_free = 2000
    result = agent1.select_blocks(
        context=small_context,
        need_to_free=need_to_free
    )

    total_selected = sum(b['estimated_tokens'] for b in result['blocks'])

    # Should be within 50% of target (conservative test)
    # Agent might select less if not enough low-value content
    assert total_selected >= need_to_free * 0.5 or total_selected == 0, \
        f"Selected {total_selected} tokens, needed {need_to_free}"
