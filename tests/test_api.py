"""Tests for the FastAPI endpoints."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def client():
    """Create a test client with a mocked agent."""
    # Mock the agent before importing the app
    with patch("backend.main.agent") as mock_agent:
        mock_agent.process.return_value = {
            "answer": "Alice Chen has 3 orders.",
            "data": [{"name": "Alice Chen", "order_count": 3}],
            "sql_used": "SELECT COUNT(*) FROM orders WHERE customer_id = 1",
            "conversation_id": "test-conv-123",
        }

        from backend.main import app
        yield TestClient(app)


class TestChatEndpoint:
    """Test POST /api/chat."""

    def test_chat_success(self, client):
        response = client.post("/api/chat", json={
            "message": "How many orders does Alice have?",
        })
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "conversation_id" in data

    def test_chat_empty_message(self, client):
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422  # Validation error

    def test_chat_with_conversation_id(self, client):
        response = client.post("/api/chat", json={
            "message": "Show me their tickets too",
            "conversation_id": "test-conv-123",
        })
        assert response.status_code == 200

    def test_chat_returns_sql(self, client):
        response = client.post("/api/chat", json={
            "message": "List all customers",
        })
        data = response.json()
        assert "sql_used" in data


class TestHealthEndpoint:
    """Test GET /api/health."""

    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        # May return 200 or 503 depending on DB state
        assert response.status_code in [200, 503]
