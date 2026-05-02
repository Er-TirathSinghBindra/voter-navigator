import os
import json
import jwt
import time
import requests
import logging

logger = logging.getLogger(__name__)

# Note: In a real environment, GOOGLE_APPLICATION_CREDENTIALS points to the service account
# which gives us the private key. For JWT generation, we explicitly need the client_email and private_key.


def _get_service_account_credentials():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./service-account.json")
    try:
        with open(creds_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


async def generate_voter_pass(voter_state: str) -> dict:
    """
    Generates a Google Wallet Add-to-Wallet URL for a Voter Readiness Pass.
    If credentials are not found, returns a placeholder mock URL.
    """
    issuer_id = os.getenv("WALLET_ISSUER_ID", "PLACEHOLDER_ISSUER")
    class_id = os.getenv("WALLET_CLASS_ID", f"{issuer_id}.voter_readiness_pass")

    creds = _get_service_account_credentials()

    if not creds or issuer_id == "PLACEHOLDER_ISSUER":
        logger.warning(
            "Wallet Service Account not found or Issuer ID is placeholder. Returning mock link."
        )
        return {
            "link": "https://pay.google.com/gp/v/save/mock-jwt-token",
            "message": f"Generated Mock Pass for state: {voter_state}",
        }

    client_email = creds.get("client_email")
    private_key = creds.get("private_key")

    # Generate unique object ID
    object_id = f"{issuer_id}.voter_pass_{int(time.time())}"

    # Define the Generic Object
    generic_object = {
        "id": object_id,
        "classId": class_id,
        "genericType": "GENERIC_TYPE_UNSPECIFIED",
        "hexBackgroundColor": "#2563eb",
        "logo": {
            "sourceUri": {
                "uri": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Checkmark_green.svg/120px-Checkmark_green.svg.png"
            }
        },
        "cardTitle": {
            "defaultValue": {"language": "en", "value": "Voter Readiness Pass"}
        },
        "header": {
            "defaultValue": {"language": "en", "value": "State of " + voter_state}
        },
        "textModulesData": [
            {"header": "Status", "body": "Ready to Vote", "id": "status"}
        ],
    }

    # Create the JWT payload
    claims = {
        "iss": client_email,
        "aud": "google",
        "origins": [
            "http://localhost:3000",
            "https://your-frontend-url.com",
        ],  # Ensure CORS compatibility
        "typ": "savetowallet",
        "payload": {"genericObjects": [generic_object]},
    }

    try:
        # Sign the JWT with the RSA private key
        signed_jwt = jwt.encode(claims, private_key, algorithm="RS256")
        save_url = f"https://pay.google.com/gp/v/save/{signed_jwt}"
        return {
            "link": save_url,
            "message": "Successfully generated Digital Voter Pass.",
        }
    except Exception as e:
        logger.error(f"Error signing Wallet JWT: {str(e)}")
        return {"error": "Failed to generate Wallet Pass due to internal error."}


def create_wallet_class_sync():
    """
    Helper function to create the GenericClass via REST API.
    Run this once to provision the class in the Wallet Console.
    Requires google-auth.
    """
    import google.auth
    from google.auth.transport.requests import Request as AuthRequest

    creds = _get_service_account_credentials()
    if not creds:
        print("Need Service Account to create Wallet Class.")
        return

    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/wallet_object.issuer"]
    )
    credentials.refresh(AuthRequest())

    issuer_id = os.getenv("WALLET_ISSUER_ID")
    class_id = os.getenv("WALLET_CLASS_ID", f"{issuer_id}.voter_readiness_pass")

    payload = {
        "id": class_id,
        "issuerName": "The Civic Navigator",
        "reviewStatus": "UNDER_REVIEW",  # Or DRAFT
    }

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        "https://walletobjects.googleapis.com/walletobjects/v1/genericClass",
        json=payload,
        headers=headers,
    )
    print("Class creation response:", resp.status_code, resp.text)
