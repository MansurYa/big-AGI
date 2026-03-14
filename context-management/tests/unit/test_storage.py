"""
Unit tests for compression storage.
"""
import pytest
import tempfile
from pathlib import Path
from src.proxy.storage import (
    CompressionStorage,
    CompressionRecord,
    CompressionBlock,
    create_compression_record
)


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = CompressionStorage(storage_dir=Path(tmpdir))
        yield storage


def test_storage_initialization(temp_storage):
    """Test storage initializes correctly"""
    assert temp_storage.storage_dir.exists()
    assert temp_storage.storage_dir.is_dir()


def test_save_and_load_compression(temp_storage):
    """Test saving and loading compression records"""
    # Create test record
    block = CompressionBlock(
        start_line=10,
        end_line=20,
        original_text="Original text here",
        compressed_text="Compressed",
        original_tokens=100,
        compressed_tokens=25,
        tokens_saved=75,
        compression_ratio=4.0
    )

    record = CompressionRecord(
        id="test_001",
        timestamp=1234567890.0,
        chat_id="test_chat",
        category="Dialogue",
        blocks=[block],
        total_tokens_saved=75,
        original_context_tokens=1000,
        final_context_tokens=925
    )

    # Save
    temp_storage.save_compression(record)

    # Load
    loaded = temp_storage.load_all_compressions("test_chat")

    assert len(loaded) == 1
    assert loaded[0].id == "test_001"
    assert loaded[0].chat_id == "test_chat"
    assert loaded[0].category == "Dialogue"
    assert len(loaded[0].blocks) == 1
    assert loaded[0].blocks[0].tokens_saved == 75


def test_load_nonexistent_chat(temp_storage):
    """Test loading compressions for nonexistent chat"""
    records = temp_storage.load_all_compressions("nonexistent")
    assert records == []


def test_load_latest_compression(temp_storage):
    """Test loading latest compression"""
    # Create multiple records
    for i in range(3):
        block = CompressionBlock(
            start_line=10,
            end_line=20,
            original_text=f"Text {i}",
            compressed_text=f"Comp {i}",
            original_tokens=100,
            compressed_tokens=25,
            tokens_saved=75,
            compression_ratio=4.0
        )

        record = CompressionRecord(
            id=f"test_{i:03d}",
            timestamp=1234567890.0 + i,
            chat_id="test_chat",
            category="Dialogue",
            blocks=[block],
            total_tokens_saved=75,
            original_context_tokens=1000,
            final_context_tokens=925
        )

        temp_storage.save_compression(record)

    # Load latest
    latest = temp_storage.load_latest_compression("test_chat")

    assert latest is not None
    assert latest.id == "test_002"


def test_delete_latest_compression(temp_storage):
    """Test deleting latest compression"""
    # Create records
    for i in range(3):
        block = CompressionBlock(
            start_line=10,
            end_line=20,
            original_text=f"Text {i}",
            compressed_text=f"Comp {i}",
            original_tokens=100,
            compressed_tokens=25,
            tokens_saved=75,
            compression_ratio=4.0
        )

        record = CompressionRecord(
            id=f"test_{i:03d}",
            timestamp=1234567890.0 + i,
            chat_id="test_chat",
            category="Dialogue",
            blocks=[block],
            total_tokens_saved=75,
            original_context_tokens=1000,
            final_context_tokens=925
        )

        temp_storage.save_compression(record)

    # Delete latest
    deleted = temp_storage.delete_latest_compression("test_chat")

    assert deleted is not None
    assert deleted.id == "test_002"

    # Verify it's gone
    remaining = temp_storage.load_all_compressions("test_chat")
    assert len(remaining) == 2
    assert remaining[-1].id == "test_001"


def test_clear_all_compressions(temp_storage):
    """Test clearing all compressions"""
    # Create records
    for i in range(3):
        block = CompressionBlock(
            start_line=10,
            end_line=20,
            original_text=f"Text {i}",
            compressed_text=f"Comp {i}",
            original_tokens=100,
            compressed_tokens=25,
            tokens_saved=75,
            compression_ratio=4.0
        )

        record = CompressionRecord(
            id=f"test_{i:03d}",
            timestamp=1234567890.0 + i,
            chat_id="test_chat",
            category="Dialogue",
            blocks=[block],
            total_tokens_saved=75,
            original_context_tokens=1000,
            final_context_tokens=925
        )

        temp_storage.save_compression(record)

    # Clear all
    count = temp_storage.clear_all_compressions("test_chat")

    assert count == 3

    # Verify all gone
    remaining = temp_storage.load_all_compressions("test_chat")
    assert len(remaining) == 0


def test_get_compression_stats(temp_storage):
    """Test getting compression statistics"""
    # Create records
    for i in range(3):
        block = CompressionBlock(
            start_line=10,
            end_line=20,
            original_text=f"Text {i}",
            compressed_text=f"Comp {i}",
            original_tokens=100,
            compressed_tokens=25,
            tokens_saved=75,
            compression_ratio=4.0
        )

        record = CompressionRecord(
            id=f"test_{i:03d}",
            timestamp=1234567890.0 + i,
            chat_id="test_chat",
            category="Dialogue" if i < 2 else "Internet",
            blocks=[block],
            total_tokens_saved=75,
            original_context_tokens=1000,
            final_context_tokens=925
        )

        temp_storage.save_compression(record)

    # Get stats
    stats = temp_storage.get_compression_stats("test_chat")

    assert stats['total_compressions'] == 3
    assert stats['total_tokens_saved'] == 225  # 75 * 3
    assert stats['total_blocks_compressed'] == 3
    assert 'Dialogue' in stats['categories_compressed']
    assert 'Internet' in stats['categories_compressed']


def test_create_compression_record():
    """Test creating compression record from results"""
    blocks = [
        {
            'start_line': 10,
            'end_line': 20,
            'original_text': 'Original 1',
            'compressed_text': 'Comp 1',
            'original_tokens': 100,
            'compressed_tokens': 25,
            'ratio': 4.0
        },
        {
            'start_line': 30,
            'end_line': 40,
            'original_text': 'Original 2',
            'compressed_text': 'Comp 2',
            'original_tokens': 200,
            'compressed_tokens': 50,
            'ratio': 4.0
        }
    ]

    record = create_compression_record(
        chat_id="test_chat",
        category="Dialogue",
        blocks=blocks,
        original_context_tokens=1000,
        final_context_tokens=850
    )

    assert record.chat_id == "test_chat"
    assert record.category == "Dialogue"
    assert len(record.blocks) == 2
    assert record.total_tokens_saved == 225  # (100-25) + (200-50) = 75 + 150
    assert record.original_context_tokens == 1000
    assert record.final_context_tokens == 850
