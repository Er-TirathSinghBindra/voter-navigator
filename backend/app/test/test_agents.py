import pytest
from app.services.ai_engine import process_chat
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_process_chat_basic_flow(monkeypatch):
    # Mock the Runner
    mock_runner = MagicMock()
    
    # Create a mock event
    mock_event = MagicMock()
    # is_final_response should be a callable returning True
    mock_event.is_final_response.return_value = True
    
    # Create the nested content.parts structure
    mock_part = MagicMock()
    mock_part.text = "Test Response"
    mock_event.content.parts = [mock_part]
    
    # Define an async generator for the runner
    async def async_generator(*args, **kwargs):
        yield mock_event
        
    mock_runner.run_async.side_effect = async_generator
    monkeypatch.setattr("app.services.ai_engine.coordinator_runner", mock_runner)
    
    # Mock session service with AsyncMock for create_session
    mock_session = MagicMock()
    mock_session.create_session = AsyncMock()
    monkeypatch.setattr("app.services.ai_engine.session_service", mock_session)
    
    messages = [MagicMock(role="user", content="Hello")]
    response = await process_chat(messages, "fake_token")
    assert response == "Test Response"

@pytest.mark.asyncio
async def test_process_chat_error_handling(monkeypatch):
    mock_runner = MagicMock()
    # When using 'async for', run_async needs to return something iterable or an async generator
    # Setting side_effect to an exception will raise it immediately when called
    mock_runner.run_async.side_effect = Exception("Runner Crash")
    monkeypatch.setattr("app.services.ai_engine.coordinator_runner", mock_runner)
    
    # Mock session service with AsyncMock
    mock_session = MagicMock()
    mock_session.create_session = AsyncMock()
    monkeypatch.setattr("app.services.ai_engine.session_service", mock_session)
    
    messages = [MagicMock(role="user", content="Crash me")]
    response = await process_chat(messages)
    assert "encountered an error" in response
