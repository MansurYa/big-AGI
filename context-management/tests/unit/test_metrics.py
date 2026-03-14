"""
Unit tests for metrics module.
"""
import pytest
from src.utils.metrics import MetricsCollector

def test_record_compression():
    """Test recording a compression operation"""
    collector = MetricsCollector()

    collector.record_compression(
        original_tokens=10000,
        compressed_tokens=2500,
        time_seconds=5.2,
        cost_usd=0.85
    )

    assert len(collector.metrics) == 1
    metric = collector.metrics[0]
    assert metric.compression_ratio == 4.0
    assert metric.time_seconds == 5.2

def test_summary_statistics():
    """Test summary statistics calculation"""
    collector = MetricsCollector()

    # Record multiple compressions
    collector.record_compression(10000, 2500, 5.0, 0.80)
    collector.record_compression(20000, 5000, 10.0, 1.60)
    collector.record_compression(15000, 3750, 7.5, 1.20)

    summary = collector.get_summary()

    assert summary['total_compressions'] == 3
    assert summary['avg_compression_ratio'] == 4.0
    assert abs(summary['total_cost_usd'] - 3.60) < 0.01  # Use approximate comparison for floats

def test_entity_preservation_tracking():
    """Test entity preservation tracking"""
    collector = MetricsCollector()

    collector.record_compression(
        original_tokens=10000,
        compressed_tokens=2500,
        time_seconds=5.0,
        cost_usd=0.80,
        entities_preserved=98,
        entities_total=100
    )

    summary = collector.get_summary()
    assert summary['avg_entity_preservation'] == 0.98
