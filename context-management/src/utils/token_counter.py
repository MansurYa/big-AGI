"""
Token counting utilities for context management.
Supports counting tokens by category and tracking quotas.
"""
import tiktoken
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CategoryQuota:
    """Quota configuration for a context category"""
    name: str
    quota: int  # Maximum tokens allowed
    current: int = 0  # Current token count

    @property
    def fill_percent(self) -> float:
        """Calculate fill percentage"""
        return (self.current / self.quota * 100) if self.quota > 0 else 0

    @property
    def needs_compression(self) -> bool:
        """Check if category needs compression (≥90% full)"""
        return self.fill_percent >= 90.0

    @property
    def target_after_compression(self) -> int:
        """Target token count after compression (70% of quota)"""
        return int(self.quota * 0.70)

    @property
    def tokens_to_free(self) -> int:
        """Calculate how many tokens need to be freed"""
        if not self.needs_compression:
            return 0
        return self.current - self.target_after_compression


class TokenCounter:
    """
    Token counter with category support.
    Tracks token usage across different context categories.
    """

    def __init__(self, encoding: str = "cl100k_base"):
        self.tokenizer = tiktoken.get_encoding(encoding)
        self.categories: Dict[str, CategoryQuota] = {}

    def set_quota(self, category: str, quota: int) -> None:
        """Set quota for a category"""
        if category not in self.categories:
            self.categories[category] = CategoryQuota(name=category, quota=quota)
        else:
            self.categories[category].quota = quota

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))

    def update_category(self, category: str, tokens: int) -> None:
        """Update token count for a category"""
        if category not in self.categories:
            raise ValueError(f"Category '{category}' not configured. Call set_quota() first.")
        self.categories[category].current = tokens

    def add_to_category(self, category: str, tokens: int) -> None:
        """Add tokens to a category"""
        if category not in self.categories:
            raise ValueError(f"Category '{category}' not configured. Call set_quota() first.")
        self.categories[category].current += tokens

    def get_category(self, category: str) -> Optional[CategoryQuota]:
        """Get category quota info"""
        return self.categories.get(category)

    def get_categories_needing_compression(self) -> List[CategoryQuota]:
        """Get list of categories that need compression"""
        return [cat for cat in self.categories.values() if cat.needs_compression]

    def get_total_tokens(self) -> int:
        """Get total tokens across all categories"""
        return sum(cat.current for cat in self.categories.values())

    def get_total_quota(self) -> int:
        """Get total quota across all categories"""
        return sum(cat.quota for cat in self.categories.values())

    def get_summary(self) -> Dict:
        """Get summary of all categories"""
        return {
            'categories': {
                name: {
                    'current': cat.current,
                    'quota': cat.quota,
                    'fill_percent': cat.fill_percent,
                    'needs_compression': cat.needs_compression,
                    'tokens_to_free': cat.tokens_to_free
                }
                for name, cat in self.categories.items()
            },
            'total_tokens': self.get_total_tokens(),
            'total_quota': self.get_total_quota(),
            'overall_fill_percent': (self.get_total_tokens() / self.get_total_quota() * 100)
                                   if self.get_total_quota() > 0 else 0
        }


def extract_category_from_message(message: Dict) -> str:
    """
    Extract category from message metadata.

    Args:
        message: Message dict with optional 'category' field

    Returns:
        Category name (default: 'Dialogue')
    """
    return message.get('category', 'Dialogue')


def count_tokens_by_category(messages: List[Dict], tokenizer: Optional[TokenCounter] = None) -> Dict[str, int]:
    """
    Count tokens for each category in message list.

    Args:
        messages: List of message dicts with 'content' and optional 'category'
        tokenizer: Optional TokenCounter instance (creates new if None)

    Returns:
        Dict mapping category name to token count
    """
    if tokenizer is None:
        tokenizer = TokenCounter()

    category_counts: Dict[str, int] = {}

    for message in messages:
        content = message.get('content', '')
        if isinstance(content, list):
            # Handle multi-part content (text + images)
            content = ' '.join([
                part.get('text', '') if isinstance(part, dict) else str(part)
                for part in content
            ])

        category = extract_category_from_message(message)
        tokens = tokenizer.count_tokens(str(content))

        category_counts[category] = category_counts.get(category, 0) + tokens

    return category_counts
