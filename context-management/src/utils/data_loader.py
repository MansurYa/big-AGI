"""
Data loader for test conversation.
Provides utilities to load and slice test data.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import tiktoken

class ConversationLoader:
    """Load and manipulate test conversation data"""

    def __init__(self, conversation_path: str):
        self.path = Path(conversation_path)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self._conversation = None

    def load(self) -> Dict:
        """Load full conversation"""
        if self._conversation is None:
            with open(self.path) as f:
                self._conversation = json.load(f)
        return self._conversation

    def get_messages(self) -> List[Dict]:
        """Extract messages array"""
        conv = self.load()
        return conv.get('messages', [])

    def create_slice(self, target_tokens: int, tolerance: float = 0.1) -> str:
        """
        Create a slice of conversation with approximately target_tokens.

        Args:
            target_tokens: Target number of tokens
            tolerance: Acceptable deviation (0.1 = ±10%)

        Returns:
            String with conversation slice
        """
        messages = self.get_messages()
        result = []
        current_tokens = 0

        for msg in messages:
            content = self._extract_content(msg)
            msg_tokens = len(self.tokenizer.encode(content))

            if current_tokens + msg_tokens > target_tokens * (1 + tolerance):
                break

            result.append(content)
            current_tokens += msg_tokens

            if current_tokens >= target_tokens * (1 - tolerance):
                break

        return "\n\n".join(result)

    def _extract_content(self, message: Dict) -> str:
        """Extract text content from message"""
        fragments = message.get('fragments', [])
        texts = []

        for frag in fragments:
            if frag.get('ft') == 'content':
                part = frag.get('part', {})
                if part.get('pt') == 'text':
                    texts.append(part.get('text', ''))

        return "\n".join(texts)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))

def add_line_numbers(text: str) -> str:
    """Add line numbers to text"""
    lines = text.split('\n')
    numbered = [f"[LINE_{i:04d}] {line}" for i, line in enumerate(lines, 1)]
    return "\n".join(numbered)

def remove_line_numbers(text: str) -> str:
    """Remove line numbers from text"""
    import re
    return re.sub(r'^\[LINE_\d+\]\s*', '', text, flags=re.MULTILINE)
