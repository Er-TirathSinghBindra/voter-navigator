import os
import logging
from functools import lru_cache
from google.cloud import translate_v2 as translate
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

# Try to initialize the translation client (requires GOOGLE_APPLICATION_CREDENTIALS)
try:
    translate_client = translate.Client()
    HAS_TRANSLATE_CREDS = True
except Exception as e:
    logger.warning(
        f"Translation client could not be initialized (using mock fallback): {e}"
    )
    HAS_TRANSLATE_CREDS = False


@lru_cache(maxsize=500)
def _cached_translate(term: str, target_language: str) -> str:
    """
    Synchronous cached translation function to prevent duplicate API hits.
    """
    if not HAS_TRANSLATE_CREDS:
        return f"[Mock Translation of '{term}' into {target_language}]"

    try:
        # We need a 2-letter language code. Usually target_language might be 'es', 'fr', etc.
        # But if Gemini passes "Spanish", we should Ideally map it to 'es'.
        # The translate API auto-detects English, but needs a valid target code.
        # For simplicity, if the target_language is longer than 2 chars, we try to use a simple mapping.
        lang_map = {
            "spanish": "es",
            "french": "fr",
            "german": "de",
            "mandarin": "zh",
            "chinese": "zh",
            "hindi": "hi",
            "arabic": "ar",
            "russian": "ru",
            "japanese": "ja",
            "korean": "ko",
            "vietnamese": "vi",
            "tagalog": "tl",
        }

        target_code = target_language.lower().strip()
        if len(target_code) > 2:
            target_code = lang_map.get(
                target_code, "en"
            )  # Fallback to English if unknown

        result = translate_client.translate(term, target_language=target_code)
        return result["translatedText"]

    except GoogleAPIError as e:
        logger.error(f"Google Translate API Error: {e}")
        return f"[Error translating term]"
    except Exception as e:
        logger.error(f"Unknown translation error: {e}")
        return f"[Error translating term]"


async def translate_civic_term(term: str, target_language: str) -> dict:
    """
    Translates a complex civic or election term into a target language.
    
    Args:
        term: The English civic term to translate (e.g., 'provisional ballot').
        target_language: The language to translate into (e.g., 'Spanish', 'Hindi').
    """
    # Use LRU cache to prevent rate limits for identical frequent queries like "provisional ballot"
    translated_text = _cached_translate(term, target_language)

    if "Error" in translated_text:
        return {"error": "Translation service is currently unavailable."}

    return {
        "status": "success",
        "original_term": term,
        "target_language": target_language,
        "translated_text": translated_text,
    }
