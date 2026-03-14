"""
Unit tests for stitching module.
"""
import pytest
from src.utils.stitching import (
    stitch_compressed_blocks,
    validate_blocks,
    calculate_compression_stats
)

def test_stitch_single_block():
    """Test stitching with a single block (end_line is inclusive)"""
    original = "\n".join([f"Line {i}" for i in range(1, 11)])

    blocks = [{
        'start_line': 3,
        'end_line': 7,  # Lines 3-7 inclusive will be replaced
        'compressed_text': 'COMPRESSED'
    }]

    result = stitch_compressed_blocks(original, blocks)
    lines = result.split('\n')

    assert lines[0] == "Line 1"
    assert lines[1] == "Line 2"
    assert lines[2] == "COMPRESSED"
    assert lines[3] == "Line 8"  # Line 8 comes after replaced block
    assert lines[4] == "Line 9"

def test_stitch_multiple_blocks():
    """Test stitching with multiple non-overlapping blocks"""
    original = "\n".join([f"Line {i}" for i in range(1, 21)])

    blocks = [
        {'start_line': 3, 'end_line': 5, 'compressed_text': 'COMP1'},
        {'start_line': 10, 'end_line': 12, 'compressed_text': 'COMP2'},
        {'start_line': 15, 'end_line': 18, 'compressed_text': 'COMP3'}
    ]

    result = stitch_compressed_blocks(original, blocks)
    lines = result.split('\n')

    # Check that compressed blocks are in place
    assert 'COMP1' in result
    assert 'COMP2' in result
    assert 'COMP3' in result

    # Check that uncompressed lines remain
    assert 'Line 1' in result
    assert 'Line 20' in result

def test_stitch_empty_blocks():
    """Test stitching with no blocks"""
    original = "Line 1\nLine 2\nLine 3"
    result = stitch_compressed_blocks(original, [])
    assert result == original

def test_stitch_multiline_compressed():
    """Test stitching with multi-line compressed text"""
    original = "\n".join([f"Line {i}" for i in range(1, 11)])

    blocks = [{
        'start_line': 3,
        'end_line': 7,
        'compressed_text': 'Compressed line 1\nCompressed line 2\nCompressed line 3'
    }]

    result = stitch_compressed_blocks(original, blocks)
    lines = result.split('\n')

    assert lines[2] == "Compressed line 1"
    assert lines[3] == "Compressed line 2"
    assert lines[4] == "Compressed line 3"

def test_validate_blocks_valid():
    """Test validation with valid blocks"""
    blocks = [
        {'start_line': 1, 'end_line': 5},
        {'start_line': 10, 'end_line': 15},
        {'start_line': 20, 'end_line': 25}
    ]

    # Should not raise
    validate_blocks(blocks, total_lines=30)

def test_validate_blocks_overlap():
    """Test validation detects overlapping blocks"""
    blocks = [
        {'start_line': 1, 'end_line': 10},
        {'start_line': 5, 'end_line': 15}  # Overlaps with first block
    ]

    with pytest.raises(ValueError, match="overlap"):
        validate_blocks(blocks, total_lines=20)

def test_validate_blocks_out_of_bounds():
    """Test validation detects out-of-bounds blocks"""
    blocks = [
        {'start_line': 1, 'end_line': 50}  # Exceeds total_lines
    ]

    with pytest.raises(ValueError, match="out of bounds"):
        validate_blocks(blocks, total_lines=30)

def test_validate_blocks_invalid_range():
    """Test validation detects invalid ranges"""
    blocks = [
        {'start_line': 10, 'end_line': 5}  # start >= end
    ]

    with pytest.raises(ValueError, match="invalid range"):
        validate_blocks(blocks, total_lines=30)

def test_calculate_compression_stats():
    """Test compression statistics calculation"""
    blocks = [
        {'original_tokens': 1000, 'compressed_tokens': 250},
        {'original_tokens': 2000, 'compressed_tokens': 500}
    ]

    stats = calculate_compression_stats(
        original_tokens=10000,
        final_tokens=7250,
        blocks=blocks
    )

    assert stats['original_tokens'] == 10000
    assert stats['final_tokens'] == 7250
    assert stats['tokens_saved'] == 2750
    assert abs(stats['savings_percent'] - 27.5) < 0.01  # Floating point tolerance
    assert stats['blocks_processed'] == 2
    assert stats['total_original_blocks'] == 3000
    assert stats['total_compressed_blocks'] == 750
    assert stats['avg_block_ratio'] == 4.0

def test_stitch_preserves_order():
    """Test that stitching processes blocks in correct order (bottom-up)"""
    original = "\n".join([f"Line {i}" for i in range(1, 11)])

    # Provide blocks in random order (end_line is inclusive)
    blocks = [
        {'start_line': 7, 'end_line': 9, 'compressed_text': 'COMPRESSED_3'},  # Replaces lines 7-9
        {'start_line': 1, 'end_line': 3, 'compressed_text': 'COMPRESSED_1'},  # Replaces lines 1-3
        {'start_line': 4, 'end_line': 6, 'compressed_text': 'COMPRESSED_2'}   # Replaces lines 4-6
    ]

    result = stitch_compressed_blocks(original, blocks)

    # All compressions should be present
    assert 'COMPRESSED_1' in result
    assert 'COMPRESSED_2' in result
    assert 'COMPRESSED_3' in result

    # Only line 10 should remain uncompressed
    assert 'Line 10' in result
    # Lines 1-9 were all replaced
    assert 'Line 1\n' not in result
    assert 'Line 9\n' not in result
