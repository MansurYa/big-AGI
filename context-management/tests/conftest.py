"""
pytest configuration and fixtures.
"""
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture
def api_client():
    """Create Anthropic API client with proxy credentials"""
    from anthropic import Anthropic
    return Anthropic(
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

@pytest.fixture
def test_conversation_path():
    """Path to test conversation file"""
    return Path(__file__).parent.parent.parent / "references" / "conversation_-2--sensetivity_2026-03-12-1103.agi.json"

@pytest.fixture
def test_conversation(test_conversation_path):
    """Load test conversation data"""
    import json
    if not test_conversation_path.exists():
        pytest.skip(f"Test conversation file not found: {test_conversation_path}")
    with open(test_conversation_path) as f:
        return json.load(f)
