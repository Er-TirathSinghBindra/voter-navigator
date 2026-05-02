import os
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

# Google Civic Information API base URL
CIVIC_API_BASE_URL = "https://www.googleapis.com/civicinfo/v2"

async def fetch_civic_info(query_type: str, address_context: str) -> dict:
    """
    Fetches polling locations or representatives using Google Civic Information API.
    query_type can be 'polling_location', 'representatives'.
    """
    api_key = os.getenv("CIVIC_INFO_API_KEY", "PLACEHOLDER_KEY")
    if api_key == "PLACEHOLDER_KEY":
        logger.warning("Using placeholder Civic Info API key.")
        return {"error": "API Key is missing. Using placeholder mode. (Mock: Found polling location at 123 Main St for address query.)"}

    # Determine endpoint based on query_type
    endpoint = "voterinfo" if query_type in ["polling_location", "ballot"] else "representatives"
    
    url = f"{CIVIC_API_BASE_URL}/{endpoint}"
    params = {
        "key": api_key,
        "address": address_context
    }
    
    # Simple exponential backoff for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format response lightly to reduce token usage when returning to Gemini
                if endpoint == "voterinfo":
                    polling_locations = data.get("pollingLocations", [])
                    state_info = data.get("state", [])
                    return {
                        "status": "success",
                        "polling_locations": polling_locations,
                        "state_elections": state_info
                    }
                else:
                    return {
                        "status": "success",
                        "officials": data.get("officials", []),
                        "offices": data.get("offices", [])
                    }
            
            elif response.status_code == 400:
                return {"error": "Invalid address provided. Ask the user for a more specific address including zip code."}
            elif response.status_code == 403:
                # Quota exceeded or rate limited
                logger.warning(f"Civic API Rate Limit hit. Attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt) # 1s, 2s
                    continue
                return {"error": "Quota exceeded. Try again later."}
            else:
                return {"error": f"API returned status {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling Civic API: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"error": "Network error reaching Google APIs."}
            
    return {"error": "Max retries exceeded while calling Civic Information API."}
