"""
Integration test for proxy server.
Tests the full proxy workflow with compression.
"""
import pytest
from fastapi.testclient import TestClient
from src.proxy.server import app


client = TestClient(app)


def test_proxy_health_check():
    """Test proxy health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'version' in data


def test_proxy_status():
    """Test proxy status endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'categories' in data
    assert 'total_tokens' in data


def test_set_quotas():
    """Test setting category quotas"""
    response = client.post("/api/quotas/set", json={
        'quotas': {
            'System': 5000,
            'Internet': 60000,
            'Dialogue': 100000
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'quotas' in data


def test_compression_stats_empty():
    """Test getting compression stats for nonexistent chat"""
    response = client.get("/api/compression/stats/nonexistent_chat")
    assert response.status_code == 200
    data = response.json()
    assert data['total_compressions'] == 0


def test_rollback_nonexistent():
    """Test rollback for nonexistent chat"""
    response = client.post("/api/compression/rollback", json={
        'chat_id': 'nonexistent_chat'
    })
    assert response.status_code == 404


def test_rollback_all_empty():
    """Test rollback all for chat with no compressions"""
    response = client.post("/api/compression/rollback-all", json={
        'chat_id': 'empty_chat'
    })
    assert response.status_code == 200
    data = response.json()
    assert data['compressions_removed'] == 0
