"""
Unit tests for token counter.
"""
import pytest
from src.utils.token_counter import (
    TokenCounter,
    CategoryQuota,
    extract_category_from_message,
    count_tokens_by_category
)


def test_category_quota_fill_percent():
    """Test fill percentage calculation"""
    quota = CategoryQuota(name="Test", quota=1000, current=500)
    assert quota.fill_percent == 50.0

    quota.current = 900
    assert quota.fill_percent == 90.0


def test_category_quota_needs_compression():
    """Test compression trigger at 90%"""
    quota = CategoryQuota(name="Test", quota=1000, current=800)
    assert not quota.needs_compression

    quota.current = 900
    assert quota.needs_compression

    quota.current = 950
    assert quota.needs_compression


def test_category_quota_tokens_to_free():
    """Test tokens to free calculation"""
    quota = CategoryQuota(name="Test", quota=1000, current=950)
    # Target: 70% of 1000 = 700
    # Need to free: 950 - 700 = 250
    assert quota.tokens_to_free == 250


def test_token_counter_basic():
    """Test basic token counting"""
    counter = TokenCounter()

    text = "Hello world, this is a test."
    tokens = counter.count_tokens(text)

    assert tokens > 0
    assert isinstance(tokens, int)


def test_token_counter_set_quota():
    """Test setting category quotas"""
    counter = TokenCounter()

    counter.set_quota("System", 5000)
    counter.set_quota("Dialogue", 100000)

    assert "System" in counter.categories
    assert "Dialogue" in counter.categories
    assert counter.categories["System"].quota == 5000
    assert counter.categories["Dialogue"].quota == 100000


def test_token_counter_update_category():
    """Test updating category token counts"""
    counter = TokenCounter()
    counter.set_quota("Test", 1000)

    counter.update_category("Test", 500)
    assert counter.categories["Test"].current == 500

    counter.update_category("Test", 800)
    assert counter.categories["Test"].current == 800


def test_token_counter_add_to_category():
    """Test adding tokens to category"""
    counter = TokenCounter()
    counter.set_quota("Test", 1000)

    counter.update_category("Test", 100)
    counter.add_to_category("Test", 50)

    assert counter.categories["Test"].current == 150


def test_token_counter_get_categories_needing_compression():
    """Test finding categories that need compression"""
    counter = TokenCounter()

    counter.set_quota("Cat1", 1000)
    counter.set_quota("Cat2", 1000)
    counter.set_quota("Cat3", 1000)

    counter.update_category("Cat1", 800)  # 80% - no compression
    counter.update_category("Cat2", 900)  # 90% - needs compression
    counter.update_category("Cat3", 950)  # 95% - needs compression

    needing = counter.get_categories_needing_compression()

    assert len(needing) == 2
    assert all(cat.name in ["Cat2", "Cat3"] for cat in needing)


def test_token_counter_get_summary():
    """Test summary generation"""
    counter = TokenCounter()

    counter.set_quota("System", 5000)
    counter.set_quota("Dialogue", 100000)

    counter.update_category("System", 2000)
    counter.update_category("Dialogue", 50000)

    summary = counter.get_summary()

    assert summary['total_tokens'] == 52000
    assert summary['total_quota'] == 105000
    assert 'categories' in summary
    assert 'System' in summary['categories']
    assert 'Dialogue' in summary['categories']


def test_extract_category_from_message():
    """Test category extraction from message"""
    msg1 = {'content': 'test', 'category': 'System'}
    assert extract_category_from_message(msg1) == 'System'

    msg2 = {'content': 'test'}
    assert extract_category_from_message(msg2) == 'Dialogue'


def test_count_tokens_by_category():
    """Test counting tokens by category"""
    messages = [
        {'content': 'System message', 'category': 'System'},
        {'content': 'User message 1', 'category': 'Dialogue'},
        {'content': 'User message 2', 'category': 'Dialogue'},
        {'content': 'Internet content', 'category': 'Internet'}
    ]

    counts = count_tokens_by_category(messages)

    assert 'System' in counts
    assert 'Dialogue' in counts
    assert 'Internet' in counts
    assert counts['System'] > 0
    assert counts['Dialogue'] > counts['System']  # Two messages vs one


def test_count_tokens_multipart_content():
    """Test counting tokens with multi-part content"""
    messages = [
        {
            'content': [
                {'type': 'text', 'text': 'Hello'},
                {'type': 'text', 'text': 'World'}
            ],
            'category': 'Dialogue'
        }
    ]

    counts = count_tokens_by_category(messages)

    assert 'Dialogue' in counts
    assert counts['Dialogue'] > 0
