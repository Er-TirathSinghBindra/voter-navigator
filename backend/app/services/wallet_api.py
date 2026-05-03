import logging
import json
import time
from typing import Optional, Dict, Any
import jwt
import requests
import anyio

from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_service_account_credentials() -> Optional[Dict[str, Any]]:
    """
    Loads service account credentials from the configured path.
    
    Returns:
        Optional[Dict[str, Any]]: The credentials dictionary or None if not found.
    """
    # In production, this path should be managed securely
    creds_path = settings.google_application_credentials
    try:
        with open(creds_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

async def generate_voter_pass(voter_state: str) -> Dict[str, Any]:
    """
    Generates a Google Wallet 'Add-to-Wallet' URL for a Voter Readiness Pass.
    
    Args:
        voter_state (str): The state or region name to display on the digital pass.
        
    Returns:
        Dict[str, Any]: A result dictionary with the wallet link or error.
    """
    issuer_id = settings.wallet_issuer_id
    class_id = settings.wallet_class_id or f"{issuer_id}.voter_readiness_pass"

    creds = _get_service_account_credentials()

    if not creds or issuer_id == "PLACEHOLDER_ISSUER":
        logger.warning("Wallet Service Account not found or Issuer ID is placeholder. Returning mock link.")
        return {
            "link": "https://pay.google.com/gp/v/save/mock-jwt-token",
            "message": f"Generated Mock Pass for state: {voter_state}",
        }

    client_email = creds.get("client_email")
    private_key = creds.get("private_key")
    object_id = f"{issuer_id}.voter_pass_{int(time.time())}"

    generic_object = {
        "id": object_id,
        "classId": class_id,
        "genericType": "GENERIC_TYPE_UNSPECIFIED",
        "hexBackgroundColor": "#2563eb",
        "logo": {
            "sourceUri": {"uri": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Checkmark_green.svg/120px-Checkmark_green.svg.png"}
        },
        "cardTitle": {"defaultValue": {"language": "en", "value": "Voter Readiness Pass"}},
        "header": {"defaultValue": {"language": "en", "value": f"State of {voter_state}"}},
        "textModulesData": [{"header": "Status", "body": "Ready to Vote", "id": "status"}],
    }

    claims = {
        "iss": client_email,
        "aud": "google",
        "origins": ["http://localhost:3000", settings.frontend_url],
        "typ": "savetowallet",
        "payload": {"genericObjects": [generic_object]},
    }

    try:
        # Wrap blocking JWT encoding in a thread
        signed_jwt = await anyio.to_thread.run_sync(
            lambda: jwt.encode(claims, private_key, algorithm="RS256")
        )
        save_url = f"https://pay.google.com/gp/v/save/{signed_jwt}"
        return {
            "link": save_url,
            "message": "Successfully generated Digital Voter Pass.",
        }
    except Exception as e:
        logger.error(f"Error signing Wallet JWT: {str(e)}")
        return {"error": "Failed to generate Wallet Pass due to internal error."}

async def create_wallet_class_async() -> None:
    """
    Helper function to create the GenericClass via REST API asynchronously.
    """
    import google.auth
    from google.auth.transport.requests import Request as AuthRequest

    creds = _get_service_account_credentials()
    if not creds:
        logger.error("Need Service Account to create Wallet Class.")
        return

    # Wrap blocking google-auth calls in threads
    credentials, _ = await anyio.to_thread.run_sync(
        lambda: google.auth.default(scopes=["https://www.googleapis.com/auth/wallet_object.issuer"])
    )
    await anyio.to_thread.run_sync(lambda: credentials.refresh(AuthRequest()))

    issuer_id = settings.wallet_issuer_id
    class_id = settings.wallet_class_id or f"{issuer_id}.voter_readiness_pass"

    payload = {
        "id": class_id,
        "issuerName": settings.app_name,
        "reviewStatus": "UNDER_REVIEW",
    }

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    # Wrap blocking requests.post in a thread
    resp = await anyio.to_thread.run_sync(
        lambda: requests.post(
            "https://walletobjects.googleapis.com/walletobjects/v1/genericClass",
            json=payload,
            headers=headers,
        )
    )
    logger.info(f"Class creation response: {resp.status_code} {resp.text}")
