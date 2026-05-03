import pytest
from app.services.civic_api import fetch_civic_info
from app.services.translation_api import translate_civic_term, _cached_translate
from app.services.wallet_api import generate_voter_pass, create_wallet_class_sync
from app.services.calendar_api import add_calendar_event
from unittest.mock import MagicMock, patch, AsyncMock
import requests
import os

# --- Civic API Tests ---

@pytest.mark.asyncio
async def test_fetch_civic_info_success(mock_civic_api):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "pollingLocations": [{"address": {"line1": "123 Test St"}}],
        "state": [{"name": "Test State"}]
    }
    mock_civic_api.return_value = mock_response
    
    result = await fetch_civic_info("polling_location", "123 Main St")
    assert result["status"] == "success"
    assert len(result["polling_locations"]) == 1

@pytest.mark.asyncio
async def test_fetch_civic_info_representatives(mock_civic_api):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "officials": [{"name": "John Doe"}],
        "offices": [{"name": "Mayor"}]
    }
    mock_civic_api.return_value = mock_response
    
    result = await fetch_civic_info("representatives", "123 Main St")
    assert result["status"] == "success"
    assert len(result["officials"]) == 1

@pytest.mark.asyncio
async def test_fetch_civic_info_403_retry(mock_civic_api, monkeypatch):
    # Mock sleep to speed up test
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    
    mock_response_403 = MagicMock()
    mock_response_403.status_code = 403
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"officials": []}
    
    # Fail twice, succeed on third
    mock_civic_api.side_effect = [mock_response_403, mock_response_403, mock_response_200]
    
    result = await fetch_civic_info("representatives", "123 Main St")
    assert result["status"] == "success"
    assert mock_civic_api.call_count == 3

@pytest.mark.asyncio
async def test_fetch_civic_info_network_error(mock_civic_api, monkeypatch):
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock_civic_api.side_effect = requests.exceptions.RequestException("Conn error")
    
    result = await fetch_civic_info("polling_location", "123 Main St")
    assert "error" in result
    assert "Network error" in result["error"]

# --- Translation API Tests ---

@pytest.mark.asyncio
async def test_translate_civic_term_mock_fallback(monkeypatch):
    monkeypatch.setattr("app.services.translation_api.HAS_TRANSLATE_CREDS", False)
    # Clear cache to ensure we hit the logic
    _cached_translate.cache_clear()
    
    result = await translate_civic_term("ballot", "Spanish")
    assert "Mock Translation" in result["translated_text"]

def test_cached_translate_with_creds(monkeypatch):
    mock_client = MagicMock()
    mock_client.translate.return_value = {"translatedText": "Voto"}
    monkeypatch.setattr("app.services.translation_api.translate_client", mock_client)
    monkeypatch.setattr("app.services.translation_api.HAS_TRANSLATE_CREDS", True)
    _cached_translate.cache_clear()
    
    res = _cached_translate("vote", "Spanish")
    assert res == "Voto"
    mock_client.translate.assert_called_with("vote", target_language="es")

# --- Wallet API Tests ---

@pytest.mark.asyncio
async def test_generate_voter_pass_success(monkeypatch):
    # Mock credentials and jwt
    monkeypatch.setattr("app.services.wallet_api._get_service_account_credentials", lambda: {"client_email": "test@test.com", "private_key": "fake_key"})
    monkeypatch.setenv("WALLET_ISSUER_ID", "12345")
    
    with patch("jwt.encode") as mock_jwt:
        mock_jwt.return_value = "signed_token"
        result = await generate_voter_pass("California")
        assert "signed_token" in result["link"]
        assert result["message"] == "Successfully generated Digital Voter Pass."

def test_create_wallet_class_sync(monkeypatch):
    mock_auth = MagicMock()
    mock_creds = MagicMock()
    mock_creds.token = "fake_token"
    mock_auth.default.return_value = (mock_creds, "project_id")
    
    monkeypatch.setattr("google.auth.default", mock_auth.default)
    monkeypatch.setattr("app.services.wallet_api._get_service_account_credentials", lambda: {"email": "test"})
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"
        create_wallet_class_sync()
        mock_post.assert_called_once()

# --- Calendar API Tests ---

@pytest.mark.asyncio
async def test_add_calendar_event_token_variants(mock_calendar_service):
    mock_calendar_service.events().insert().execute.return_value = {"htmlLink": "link"}
    
    # Test Bearer prefix
    await add_calendar_event("Title", "2024-11-05", "Bearer secret_token")
    
    # Test missing token
    res = await add_calendar_event("Title", "2024-11-05", None)
    assert "error" in res
    assert "Missing Google Calendar access token" in res["error"]

@pytest.mark.asyncio
async def test_add_calendar_event_http_errors(mock_calendar_service):
    # Mock HttpError for 401
    from googleapiclient.errors import HttpError
    mock_resp = MagicMock()
    mock_resp.status = 401
    
    mock_calendar_service.events().insert().execute.side_effect = HttpError(resp=mock_resp, content=b"Unauthorized")
    res = await add_calendar_event("Title", "2024-11-05", "token")
    assert "expired or invalid" in res["error"]
    
    # Mock 403
    mock_resp.status = 403
    mock_calendar_service.events().insert().execute.side_effect = HttpError(resp=mock_resp, content=b"Forbidden")
    res = await add_calendar_event("Title", "2024-11-05", "token")
    assert "Insufficient permissions" in res["error"]
    
    # Mock 500
    mock_resp.status = 500
    mock_calendar_service.events().insert().execute.side_effect = HttpError(resp=mock_resp, content=b"Error")
    res = await add_calendar_event("Title", "2024-11-05", "token")
    assert "API error" in res["error"]

@pytest.mark.asyncio
async def test_add_calendar_event_error(mock_calendar_service):
    mock_calendar_service.events().insert().execute.side_effect = Exception("API Error")
    
    result = await add_calendar_event("Election", "2024-11-05", "token")
    assert "error" in result
    assert "Failed to access Google Calendar" in result["error"]

# --- Additional Coverage ---

@pytest.mark.asyncio
async def test_fetch_civic_info_missing_key(monkeypatch):
    monkeypatch.setenv("CIVIC_INFO_API_KEY", "PLACEHOLDER_KEY")
    result = await fetch_civic_info("polling_location", "addr")
    assert "API Key is missing" in result["error"]

@pytest.mark.asyncio
async def test_generate_voter_pass_missing_creds(monkeypatch):
    monkeypatch.setattr("app.services.wallet_api._get_service_account_credentials", lambda: None)
    result = await generate_voter_pass("Delhi")
    assert "mock-jwt-token" in result["link"]

@pytest.mark.asyncio
async def test_wallet_jwt_signing_error(monkeypatch):
    monkeypatch.setattr("app.services.wallet_api._get_service_account_credentials", lambda: {"client_email": "t", "private_key": "p"})
    with patch("jwt.encode", side_effect=Exception("Sign error")):
        result = await generate_voter_pass("Delhi")
        assert "Failed to generate Wallet Pass" in result["error"]

def test_get_service_account_credentials_not_found(monkeypatch):
    from app.services.wallet_api import _get_service_account_credentials
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "non_existent.json")
    assert _get_service_account_credentials() is None

@pytest.mark.asyncio
async def test_translate_civic_term_api_error(monkeypatch):
    from google.api_core.exceptions import GoogleAPIError
    mock_client = MagicMock()
    mock_client.translate.side_effect = GoogleAPIError("API Fail")
    monkeypatch.setattr("app.services.translation_api.translate_client", mock_client)
    monkeypatch.setattr("app.services.translation_api.HAS_TRANSLATE_CREDS", True)
    _cached_translate.cache_clear()
    
    result = await translate_civic_term("ballot", "Spanish")
    assert "error" in result
    assert "service is currently unavailable" in result["error"]

@pytest.mark.asyncio
async def test_translate_civic_term_unknown_error(monkeypatch):
    mock_client = MagicMock()
    mock_client.translate.side_effect = Exception("Unknown")
    monkeypatch.setattr("app.services.translation_api.translate_client", mock_client)
    monkeypatch.setattr("app.services.translation_api.HAS_TRANSLATE_CREDS", True)
    _cached_translate.cache_clear()
    
    result = await translate_civic_term("ballot", "Spanish")
    assert "error" in result

def test_create_wallet_class_no_creds(monkeypatch):
    monkeypatch.setattr("app.services.wallet_api._get_service_account_credentials", lambda: None)
    # Should just return/print
    create_wallet_class_sync()

def test_get_service_account_credentials_success(monkeypatch, tmp_path):
    from app.services.wallet_api import _get_service_account_credentials
    d = tmp_path / "creds"
    d.mkdir()
    f = d / "service-account.json"
    f.write_text('{"client_email": "test@test.com"}')
    
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(f))
    creds = _get_service_account_credentials()
    assert creds["client_email"] == "test@test.com"

@pytest.mark.asyncio
async def test_fetch_civic_info_quota_exceeded(mock_civic_api, monkeypatch):
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock_response_403 = MagicMock()
    mock_response_403.status_code = 403
    mock_civic_api.return_value = mock_response_403
    
    result = await fetch_civic_info("polling_location", "addr")
    assert "Quota exceeded" in result["error"]

@pytest.mark.asyncio
async def test_fetch_civic_info_invalid_address(mock_civic_api):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_civic_api.return_value = mock_response
    result = await fetch_civic_info("polling_location", "invalid")
    assert "Invalid address" in result["error"]

@pytest.mark.asyncio
async def test_fetch_civic_info_other_error(mock_civic_api):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_civic_api.return_value = mock_response
    result = await fetch_civic_info("polling_location", "addr")
    assert "API returned status 500" in result["error"]

@pytest.mark.asyncio
async def test_fetch_civic_info_max_retries(mock_civic_api, monkeypatch):
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock_civic_api.side_effect = requests.exceptions.RequestException("Conn error")
    
    result = await fetch_civic_info("polling_location", "addr")
    assert "Network error reaching Google APIs" in result["error"]

def test_translation_client_init_failure(monkeypatch):
    import importlib
    import app.services.translation_api
    
    with patch("google.cloud.translate_v2.Client", side_effect=Exception("No Creds")):
        # Reloading the module will trigger the try-except block
        importlib.reload(app.services.translation_api)
        assert app.services.translation_api.HAS_TRANSLATE_CREDS is False
