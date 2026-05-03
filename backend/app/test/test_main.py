import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
import os
import sys

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_chat_endpoint_success():
    with patch("app.main.process_chat", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "Mocked Response"
        
        payload = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        response = client.post("/api/chat", json=payload)
        
        assert response.status_code == 200
        assert response.json() == {"role": "assistant", "content": "Mocked Response"}
        mock_process.assert_called_once()

def test_chat_endpoint_empty_messages():
    payload = {"messages": []}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]

@pytest.mark.asyncio
async def test_chat_endpoint_error():
    with patch("app.main.process_chat", new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("Internal Crash")
        
        payload = {
            "messages": [{"role": "user", "content": "Crash me"}]
        }
        response = client.post("/api/chat", json=payload)
        
        assert response.status_code == 500
        assert "Internal Server Error" in response.json()["detail"]

