"""
Unit tests for MCP server.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from src.mcp.server import (
    get_project_path,
    validate_path,
    BASE_DIR
)

# Use a temporary directory for tests
TEST_BASE_DIR = Path(tempfile.mkdtemp())

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment with temporary directory"""
    monkeypatch.setattr('src.mcp.server.BASE_DIR', TEST_BASE_DIR)
    yield
    # Cleanup
    if TEST_BASE_DIR.exists():
        shutil.rmtree(TEST_BASE_DIR)

@pytest.fixture
def test_chat_id():
    return "test_chat_123"

def test_get_project_path(test_chat_id):
    """Test project path generation"""
    path = get_project_path(test_chat_id)
    assert path == TEST_BASE_DIR / test_chat_id
    assert path.name == test_chat_id

def test_validate_path_valid(test_chat_id):
    """Test path validation with valid path"""
    project_path = get_project_path(test_chat_id)
    project_path.mkdir(parents=True, exist_ok=True)

    test_file = project_path / "test.txt"
    test_file.touch()

    # Should not raise
    validate_path(test_file, test_chat_id)

def test_validate_path_outside_project(test_chat_id):
    """Test path validation rejects paths outside project"""
    outside_path = Path("/tmp/outside.txt")

    with pytest.raises(ValueError, match="outside project directory"):
        validate_path(outside_path, test_chat_id)

def test_validate_path_traversal_attack(test_chat_id):
    """Test path validation prevents directory traversal"""
    project_path = get_project_path(test_chat_id)
    project_path.mkdir(parents=True, exist_ok=True)

    # Try to escape with ../
    malicious_path = project_path / ".." / ".." / "etc" / "passwd"

    with pytest.raises(ValueError, match="outside project directory"):
        validate_path(malicious_path, test_chat_id)
