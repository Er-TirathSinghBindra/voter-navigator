import logging
import asyncio
from typing import Dict, Any
import requests
import anyio

from app.core.config import settings

logger = logging.getLogger(__name__)

# Google Civic Information API base URL
CIVIC_API_BASE_URL = "https://www.googleapis.com/civicinfo/v2"

async def fetch_civic_info(query_type: str, address_context: str) -> Dict[str, Any]:
    """
    Fetches polling locations, ballot info, or representative data using the Google Civic Information API.
    
    Args:
        query_type (str): The type of info to fetch ('polling_location', 'ballot', or 'representatives').
        address_context (str): The user's street address, city, and state/zip code.
        
    Returns:
        Dict[str, Any]: A result dictionary with 'status', 'polling_locations', 'officials', etc.
    """
    api_key = settings.civic_info_api_key
    if api_key == "PLACEHOLDER_KEY":
        logger.warning("Using placeholder Civic Info API key.")
        return {
            "error": "API Key is missing. Using placeholder mode. (Mock: Found polling location at 123 Main St for address query.)"
        }

    # Determine endpoint based on query_type
    endpoint = "voterinfo" if query_type in ["polling_location", "ballot"] else "representatives"
    url = f"{CIVIC_API_BASE_URL}/{endpoint}"
    params = {"key": api_key, "address": address_context}

    # Simple exponential backoff for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Wrap blocking requests.get in a thread
            response = await anyio.to_thread.run_sync(
                lambda: requests.get(url, params=params, timeout=10)
            )

            if response.status_code == 200:
                data = response.json()
                if endpoint == "voterinfo":
                    return {
                        "status": "success",
                        "polling_locations": data.get("pollingLocations", []),
                        "state_elections": data.get("state", []),
                    }
                else:
                    return {
                        "status": "success",
                        "officials": data.get("officials", []),
                        "offices": data.get("offices", []),
                    }

            elif response.status_code == 400:
                return {"error": "Invalid address provided. Ask the user for a more specific address including zip code."}
            elif response.status_code == 403:
                logger.warning(f"Civic API Rate Limit hit. Attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return {"error": "Quota exceeded. Try again later."}
            else:
                return {"error": f"API returned status {response.status_code}: {response.text}"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling Civic API: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
                continue
            return {"error": "Network error reaching Google APIs."}

