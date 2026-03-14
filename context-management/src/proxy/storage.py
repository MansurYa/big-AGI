"""
Storage for compression metadata and rollback support.
Stores compression history to enable full rollback functionality.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CompressionBlock:
    """Metadata for a single compressed block"""
    start_line: int
    end_line: int
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float


@dataclass
class CompressionRecord:
    """Record of a single compression operation"""
    id: str
    timestamp: float
    chat_id: str
    category: str
    blocks: List[CompressionBlock]
    total_tokens_saved: int
    original_context_tokens: int
    final_context_tokens: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'chat_id': self.chat_id,
            'category': self.category,
            'blocks': [asdict(block) for block in self.blocks],
            'total_tokens_saved': self.total_tokens_saved,
            'original_context_tokens': self.original_context_tokens,
            'final_context_tokens': self.final_context_tokens
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CompressionRecord':
        """Create from dictionary"""
        blocks = [CompressionBlock(**block) for block in data['blocks']]
        return cls(
            id=data['id'],
            timestamp=data['timestamp'],
            chat_id=data['chat_id'],
            category=data['category'],
            blocks=blocks,
            total_tokens_saved=data['total_tokens_saved'],
            original_context_tokens=data['original_context_tokens'],
            final_context_tokens=data['final_context_tokens']
        )


class CompressionStorage:
    """
    Storage for compression metadata.
    Stores compression history to enable rollback functionality.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize storage.

        Args:
            storage_dir: Directory for storage files (default: ./compression_storage)
        """
        if storage_dir is None:
            storage_dir = Path.cwd() / "compression_storage"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_chat_file(self, chat_id: str) -> Path:
        """Get path to chat's compression history file"""
        return self.storage_dir / f"{chat_id}.json"

    def save_compression(self, record: CompressionRecord) -> None:
        """
        Save a compression record.

        Args:
            record: CompressionRecord to save
        """
        chat_file = self._get_chat_file(record.chat_id)

        # Load existing records
        records = self.load_all_compressions(record.chat_id)

        # Add new record
        records.append(record)

        # Save to file
        with open(chat_file, 'w') as f:
            json.dump([r.to_dict() for r in records], f, indent=2)

    def load_all_compressions(self, chat_id: str) -> List[CompressionRecord]:
        """
        Load all compression records for a chat.

        Args:
            chat_id: Chat identifier

        Returns:
            List of CompressionRecord objects (empty if none exist)
        """
        chat_file = self._get_chat_file(chat_id)

        if not chat_file.exists():
            return []

        with open(chat_file) as f:
            data = json.load(f)

        return [CompressionRecord.from_dict(record) for record in data]

    def load_latest_compression(self, chat_id: str) -> Optional[CompressionRecord]:
        """
        Load the most recent compression record for a chat.

        Args:
            chat_id: Chat identifier

        Returns:
            Latest CompressionRecord or None if no compressions exist
        """
        records = self.load_all_compressions(chat_id)
        return records[-1] if records else None

    def delete_latest_compression(self, chat_id: str) -> Optional[CompressionRecord]:
        """
        Delete the most recent compression record (for undo).

        Args:
            chat_id: Chat identifier

        Returns:
            Deleted CompressionRecord or None if no compressions exist
        """
        records = self.load_all_compressions(chat_id)

        if not records:
            return None

        deleted = records.pop()

        # Save updated list
        chat_file = self._get_chat_file(chat_id)
        with open(chat_file, 'w') as f:
            json.dump([r.to_dict() for r in records], f, indent=2)

        return deleted

    def clear_all_compressions(self, chat_id: str) -> int:
        """
        Clear all compression records for a chat.

        Args:
            chat_id: Chat identifier

        Returns:
            Number of records deleted
        """
        records = self.load_all_compressions(chat_id)
        count = len(records)

        chat_file = self._get_chat_file(chat_id)
        if chat_file.exists():
            chat_file.unlink()

        return count

    def get_compression_stats(self, chat_id: str) -> Dict:
        """
        Get compression statistics for a chat.

        Args:
            chat_id: Chat identifier

        Returns:
            Dict with compression statistics
        """
        records = self.load_all_compressions(chat_id)

        if not records:
            return {
                'total_compressions': 0,
                'total_tokens_saved': 0,
                'total_blocks_compressed': 0
            }

        total_tokens_saved = sum(r.total_tokens_saved for r in records)
        total_blocks = sum(len(r.blocks) for r in records)

        return {
            'total_compressions': len(records),
            'total_tokens_saved': total_tokens_saved,
            'total_blocks_compressed': total_blocks,
            'first_compression': records[0].timestamp,
            'latest_compression': records[-1].timestamp,
            'categories_compressed': list(set(r.category for r in records))
        }


def create_compression_record(
    chat_id: str,
    category: str,
    blocks: List[Dict],
    original_context_tokens: int,
    final_context_tokens: int
) -> CompressionRecord:
    """
    Create a compression record from compression results.

    Args:
        chat_id: Chat identifier
        category: Category that was compressed
        blocks: List of block dicts with compression results
        original_context_tokens: Original context size
        final_context_tokens: Final context size after compression

    Returns:
        CompressionRecord object
    """
    compression_blocks = []
    total_tokens_saved = 0

    for block in blocks:
        tokens_saved = block['original_tokens'] - block['compressed_tokens']
        total_tokens_saved += tokens_saved

        compression_blocks.append(CompressionBlock(
            start_line=block['start_line'],
            end_line=block['end_line'],
            original_text=block.get('original_text', ''),
            compressed_text=block['compressed_text'],
            original_tokens=block['original_tokens'],
            compressed_tokens=block['compressed_tokens'],
            tokens_saved=tokens_saved,
            compression_ratio=block.get('ratio', 0.0)
        ))

    return CompressionRecord(
        id=f"compression_{int(time.time() * 1000)}",
        timestamp=time.time(),
        chat_id=chat_id,
        category=category,
        blocks=compression_blocks,
        total_tokens_saved=total_tokens_saved,
        original_context_tokens=original_context_tokens,
        final_context_tokens=final_context_tokens
    )
