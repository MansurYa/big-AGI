"""
Tests for compression instructions reading.
"""
import pytest
from pathlib import Path
from src.proxy.compression import CompressionOrchestrator, INSTRUCTIONS_FILE


def test_instructions_file_exists():
    """Test that compression instructions file exists"""
    assert INSTRUCTIONS_FILE.exists(), f"Instructions file not found at {INSTRUCTIONS_FILE}"


def test_instructions_file_readable():
    """Test that instructions file can be read"""
    with open(INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    assert len(content) > 0, "Instructions file is empty"
    assert "READ THIS FILE BEFORE EVERY COMPRESSION" in content


def test_orchestrator_reads_instructions():
    """Test that orchestrator reads instructions before compression"""
    orchestrator = CompressionOrchestrator()

    # Read instructions
    instructions = orchestrator._read_compression_instructions()

    assert len(instructions) > 0, "Instructions should not be empty"
    assert "Agent 1" in instructions
    assert "Agent 2" in instructions


def test_instructions_contain_critical_rules():
    """Test that instructions contain all critical rules"""
    with open(INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for critical sections
    assert "DO NOT MODIFY" in content
    assert "Compression Workflow" in content
    assert "Key Constraints" in content
    assert "Categories" in content
    assert "Error Handling" in content

    # Check for specific values
    assert "90%" in content  # Trigger threshold
    assert "70%" in content  # Target threshold
    assert "4.0x" in content  # Compression ratio
