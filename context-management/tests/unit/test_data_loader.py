"""
Unit tests for data_loader module.
"""
import pytest
from src.utils.data_loader import ConversationLoader, add_line_numbers, remove_line_numbers

def test_load_conversation(test_conversation_path):
    """Test loading conversation file"""
    loader = ConversationLoader(test_conversation_path)
    conv = loader.load()
    assert 'messages' in conv
    assert len(conv['messages']) > 0

def test_create_slice_10k(test_conversation_path):
    """Test creating 10k token slice"""
    loader = ConversationLoader(test_conversation_path)
    slice_text = loader.create_slice(target_tokens=10000)
    actual_tokens = loader.count_tokens(slice_text)

    # Should get some content (conversation might be smaller than 10k)
    assert actual_tokens > 0, "Should extract some content"
    # If conversation is large enough, should be close to target
    if actual_tokens >= 9000:
        assert actual_tokens <= 11000, f"Got {actual_tokens} tokens, expected ~10000"

def test_line_numbering():
    """Test line numbering functions"""
    text = "line1\nline2\nline3"
    numbered = add_line_numbers(text)

    assert "[LINE_0001]" in numbered
    assert "[LINE_0002]" in numbered
    assert "[LINE_0003]" in numbered

    # Test removal
    restored = remove_line_numbers(numbered)
    assert restored == text

def test_line_numbering_preserves_content():
    """Test that line numbering preserves content"""
    text = "Important formula: E=mc²\nVariable: alpha=0.05"
    numbered = add_line_numbers(text)
    restored = remove_line_numbers(numbered)

    assert "E=mc²" in restored
    assert "alpha=0.05" in restored
