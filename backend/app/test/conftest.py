import pytest
import os
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure environment variables are set for tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("CIVIC_INFO_API_KEY", "test_civic_key")
    monkeypatch.setenv("WALLET_ISSUER_ID", "test_issuer")
    monkeypatch.setenv("WALLET_CLASS_ID", "test_class")
    monkeypatch.setenv("FRONTEND_URL", "http://test-frontend.com")


@pytest.fixture
def mock_civic_api(monkeypatch):
    """Mock the Civic API requests."""
    mock_get = MagicMock()
    monkeypatch.setattr("requests.get", mock_get)
    return mock_get

@pytest.fixture
def mock_calendar_service(monkeypatch):
    """Mock the Google Calendar API service."""
    mock_service = MagicMock()
    monkeypatch.setattr("app.services.calendar_api.build", lambda *args, **kwargs: mock_service)
    return mock_service
