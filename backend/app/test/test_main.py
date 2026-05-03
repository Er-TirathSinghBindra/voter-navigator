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

@pytest.mark.asyncio
async def test_startup_event_success():
    # Mocking os.environ to have required secrets
    with patch.dict(os.environ, {"GEMINI_API_KEY": "key1", "CIVIC_INFO_API_KEY": "key2"}):
        from app.main import startup_event
        # This should run without error
        await startup_event()

@pytest.mark.asyncio
async def test_startup_event_missing_secrets():
    # Mocking os.environ to MISS secrets
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "CIVIC_INFO_API_KEY": ""}, clear=True):
        # We need to mock sys.exit to prevent the test from exiting
        with patch("sys.exit") as mock_exit:
            from app.main import startup_event
            await startup_event()
            mock_exit.assert_called_once_with(1)
