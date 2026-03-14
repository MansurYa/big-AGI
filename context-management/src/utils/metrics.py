"""
Metrics collection and reporting system.
Tracks compression performance, costs, and quality.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class CompressionMetrics:
    """Metrics for a single compression operation"""
    timestamp: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    time_seconds: float
    cost_usd: float
    agent1_time: float
    agent2_time: float
    stitching_time: float
    entities_preserved: Optional[int] = None
    entities_total: Optional[int] = None

    @property
    def entity_preservation_rate(self) -> Optional[float]:
        if self.entities_total and self.entities_total > 0:
            return self.entities_preserved / self.entities_total
        return None

@dataclass
class MetricsCollector:
    """Collects and aggregates metrics"""
    metrics: List[CompressionMetrics] = field(default_factory=list)

    def record_compression(
        self,
        original_tokens: int,
        compressed_tokens: int,
        time_seconds: float,
        cost_usd: float,
        agent1_time: float = 0,
        agent2_time: float = 0,
        stitching_time: float = 0,
        entities_preserved: Optional[int] = None,
        entities_total: Optional[int] = None
    ):
        """Record a compression operation"""
        ratio = original_tokens / compressed_tokens if compressed_tokens > 0 else 0

        metric = CompressionMetrics(
            timestamp=datetime.now().isoformat(),
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=ratio,
            time_seconds=time_seconds,
            cost_usd=cost_usd,
            agent1_time=agent1_time,
            agent2_time=agent2_time,
            stitching_time=stitching_time,
            entities_preserved=entities_preserved,
            entities_total=entities_total
        )

        self.metrics.append(metric)

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.metrics:
            return {}

        return {
            'total_compressions': len(self.metrics),
            'avg_compression_ratio': sum(m.compression_ratio for m in self.metrics) / len(self.metrics),
            'avg_time_seconds': sum(m.time_seconds for m in self.metrics) / len(self.metrics),
            'total_cost_usd': sum(m.cost_usd for m in self.metrics),
            'avg_entity_preservation': self._avg_entity_preservation(),
            'min_compression_ratio': min(m.compression_ratio for m in self.metrics),
            'max_compression_ratio': max(m.compression_ratio for m in self.metrics),
        }

    def _avg_entity_preservation(self) -> Optional[float]:
        rates = [m.entity_preservation_rate for m in self.metrics if m.entity_preservation_rate is not None]
        if rates:
            return sum(rates) / len(rates)
        return None

    def export_json(self, path: str):
        """Export metrics to JSON file"""
        data = {
            'summary': self.get_summary(),
            'metrics': [
                {
                    'timestamp': m.timestamp,
                    'original_tokens': m.original_tokens,
                    'compressed_tokens': m.compressed_tokens,
                    'compression_ratio': m.compression_ratio,
                    'time_seconds': m.time_seconds,
                    'cost_usd': m.cost_usd,
                    'entity_preservation_rate': m.entity_preservation_rate
                }
                for m in self.metrics
            ]
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def print_summary(self):
        """Print summary to console"""
        summary = self.get_summary()
        print("\n=== METRICS SUMMARY ===")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"{key}: {value:.3f}")
            else:
                print(f"{key}: {value}")
        print("=" * 25 + "\n")
