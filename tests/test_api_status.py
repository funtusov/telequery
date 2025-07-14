import pytest
from fastapi.testclient import TestClient

from src.api.app import app


client = TestClient(app)


def test_health_check():
    """Test the /status endpoint returns correct response"""
    response = client.get("/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.1"