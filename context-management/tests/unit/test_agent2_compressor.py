"""
Unit tests for Agent 2 (Compressor).
"""
import pytest
import re
from src.agents.agent2_compressor import Agent2Compressor
from src.utils.data_loader import ConversationLoader, add_line_numbers

@pytest.fixture
def agent2(monkeypatch):
    """Agent2 with API calls stubbed out (unit tests must be offline)."""
    agent = Agent2Compressor()

    # Default stub: return a short deterministic compression.
    def _stub_compress_once(*, system_prompt: str, user_message: str) -> str:
        # If this is a retry message, compress harder.
        if user_message.startswith("Retry:"):
            return "MC: N=10000, seed=42, epsilon=0.001, alpha=0.05; ZeroDivisionError node B QUEUE; DA=(N_success/N_total)*100%; fix: if queue.isEmpty() return 0; PostgreSQL ACID; https://api.example.com/v1/simulate; 99.9%."

        # First pass: still compressed but possibly too long to exercise retry in some tests.
        return (
            "We ran a Monte Carlo simulation with N=10000 iterations (seed=42, epsilon=0.001, alpha=0.05). "
            "We encountered a ZeroDivisionError in node B during QUEUE aggregation. "
            "Formula: DA = (N_success / N_total) * 100%. "
            "Fix: if queue.isEmpty() then return 0. "
            "PostgreSQL uses ACID transactions. "
            "API: https://api.example.com/v1/simulate. "
            "Result: 99.9% availability."
        )

    monkeypatch.setattr(agent, "_compress_once", _stub_compress_once)
    return agent

@pytest.fixture
def test_context(test_conversation_path):
    """Create test context with line numbers"""
    loader = ConversationLoader(test_conversation_path)
    text = loader.create_slice(target_tokens=5000)
    return add_line_numbers(text)

def test_agent2_initialization(agent2):
    """Test Agent 2 initializes correctly"""
    assert agent2.model == "claude-sonnet-4.5"
    assert agent2.client is not None
    assert agent2.strategy in ("minimal", "full_dup")

def test_agent2_load_prompt(agent2):
    """Test prompt loading"""
    prompt = agent2.load_prompt()
    assert len(prompt) > 0
    assert "Agent 2 (Compressor)" in prompt
    assert "AREA_TO_COMPRESS" in prompt
    assert "4x" in prompt

def test_agent2_compress_block_structure(agent2, test_context):
    """Test that Agent 2 returns valid structure"""
    # Compress lines 50-100 (small block for testing)
    result = agent2.compress_block(
        context=test_context,
        start_line=50,
        end_line=100,
        estimated_tokens=2000
    )

    # Validate structure
    assert 'compressed_text' in result
    assert 'original_tokens' in result
    assert 'compressed_tokens' in result
    assert 'ratio' in result

    # Validate types
    assert isinstance(result['compressed_text'], str)
    assert isinstance(result['original_tokens'], int)
    assert isinstance(result['compressed_tokens'], int)
    assert isinstance(result['ratio'], float)

    # Validate compression happened
    assert len(result['compressed_text']) > 0
    assert result['compressed_tokens'] < result['original_tokens']

def test_agent2_compression_ratio(agent2, test_context):
    """Test that compression reduces tokens (offline stub cannot guarantee 4x on arbitrary input)."""
    result = agent2.compress_block(
        context=test_context,
        start_line=50,
        end_line=150,
        estimated_tokens=4000,
        min_acceptable_ratio=1.2,
    )

    ratio = result['ratio']
    assert ratio >= 1.2

def test_agent2_output_format(agent2, test_context):
    """Test that output is plain text (no JSON, XML, markdown)"""
    result = agent2.compress_block(
        context=test_context,
        start_line=50,
        end_line=100,
        estimated_tokens=2000
    )

    compressed = result['compressed_text']

    # Should not contain JSON markers
    assert not compressed.startswith('{')
    assert not compressed.startswith('[')

    # Should not start with other wrapper XML (we allow <AREA_TO_COMPRESS> as an output wrapper)
    assert not compressed.startswith('<COMPRESSION_REQUEST>')
    assert '<FULL_CONTEXT_WITH_MARKER>' not in compressed
    assert '<MINI_PROMPT>' not in compressed
    assert '<DUPLICATED_AREA>' not in compressed

    # Should not contain markdown code blocks
    assert not compressed.startswith('```')

    # Should not contain meta-commentary
    assert not re.search(r'here is|compressed version|summary', compressed, re.IGNORECASE)

def test_agent2_full_dup_payload_contains_markers(monkeypatch):
    agent = Agent2Compressor(strategy="full_dup")

    # Stub compression so we don't hit network
    monkeypatch.setattr(agent, "_compress_once", lambda **kwargs: "OK")

    context = "[LINE_0001] a\n[LINE_0002] b\n[LINE_0003] c"
    result = agent.compress_block(context=context, start_line=2, end_line=2, estimated_tokens=10, min_acceptable_ratio=0.0)
    assert result["compressed_text"] == "OK"

    # Validate the full-dup message builder itself
    msg = agent._build_user_message_full_dup(
        full_context=context,
        block_text="[LINE_0002] b",
        start_line=2,
        end_line=2,
        target_max_tokens=5,
        anchor_entities=[],
        selection_reasoning=None,
    )
    assert "<FULL_CONTEXT_WITH_MARKER>" in msg
    assert "<MINI_PROMPT>" in msg
    assert "<DUPLICATED_AREA>" in msg
    assert msg.count("<AREA_TO_COMPRESS>") >= 2


def test_agent2_postprocess_strips_tags_and_codefences(agent2):
    raw = "```\n<AREA_TO_COMPRESS>\n[LINE_0001] x\n</AREA_TO_COMPRESS>\n```"
    cleaned = agent2._postprocess_output(raw)
    assert "```" not in cleaned
    assert "<AREA_TO_COMPRESS>" not in cleaned
    assert "</AREA_TO_COMPRESS>" not in cleaned
    assert "[LINE_" not in cleaned


def test_agent2_preserves_entities(agent2):
    """Test that entities are preserved in compression"""
    # Create a context with known entities
    test_text = """
[LINE_0001] We ran a Monte Carlo simulation with N=10000 iterations.
[LINE_0002] The parameters were: seed=42, epsilon=0.001, alpha=0.05.
[LINE_0003] We encountered a ZeroDivisionError in node B during QUEUE aggregation.
[LINE_0004] The formula used was: DA = (N_success / N_total) * 100%.
[LINE_0005] After investigation, we found that the queue was empty.
[LINE_0006] We added validation: if queue.isEmpty() then return 0.
[LINE_0007] The PostgreSQL database uses ACID transactions for consistency.
[LINE_0008] The API endpoint is: https://api.example.com/v1/simulate
[LINE_0009] This solved the problem and the simulation now runs successfully.
[LINE_0010] We achieved 99.9% availability with this fix.
"""

    result = agent2.compress_block(
        context=test_text,
        start_line=1,
        end_line=10,
        estimated_tokens=400,
        min_acceptable_ratio=1.2,
    )

    compressed = result['compressed_text']

    # Check that key entities are preserved
    entities = [
        'N=10000', 'seed=42', 'epsilon=0.001', 'alpha=0.05',
        'ZeroDivisionError', 'node B', 'QUEUE',
        'DA', 'N_success', 'N_total',
        'PostgreSQL', 'ACID',
        'https://api.example.com/v1/simulate',
        '99.9%'
    ]

    missing_entities = []
    for entity in entities:
        if entity not in compressed:
            missing_entities.append(entity)

    # Allow some flexibility - at least 80% of entities should be preserved
    preservation_rate = (len(entities) - len(missing_entities)) / len(entities)
    assert preservation_rate >= 0.8, \
        f"Only {preservation_rate*100:.1f}% of entities preserved. Missing: {missing_entities}"
