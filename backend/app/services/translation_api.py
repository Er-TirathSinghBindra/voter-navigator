import logging
from functools import lru_cache
from typing import Dict, Any
from google.cloud import translate_v2 as translate
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

# Try to initialize the translation client
try:
    translate_client = translate.Client()
    HAS_TRANSLATE_CREDS = True
except Exception as e:
    logger.warning(f"Translation client could not be initialized (using mock fallback): {e}")
    HAS_TRANSLATE_CREDS = False

@lru_cache(maxsize=500)
def _cached_translate(term: str, target_language: str) -> str:
    """
    Synchronous cached translation function to prevent duplicate API hits.
    
    Args:
        term (str): The English term to translate.
        target_language (str): The name or code of the target language.
        
    Returns:
        str: The translated text or a placeholder if unavailable.
    """
    if not HAS_TRANSLATE_CREDS:
        return f"[Mock Translation of '{term}' into {target_language}]"

    try:
        lang_map = {
            "spanish": "es", "french": "fr", "german": "de", "mandarin": "zh",
            "chinese": "zh", "hindi": "hi", "arabic": "ar", "russian": "ru",
            "japanese": "ja", "korean": "ko", "vietnamese": "vi", "tagalog": "tl",
        }

        target_code = target_language.lower().strip()
        if len(target_code) > 2:
            target_code = lang_map.get(target_code, "en")

        result = translate_client.translate(term, target_language=target_code)
        return result["translatedText"]

    except GoogleAPIError as e:
        logger.error(f"Google Translate API Error: {e}")
        return "[Error translating term]"
    except Exception as e:
        logger.error(f"Unknown translation error: {e}")
        return "[Error translating term]"

async def translate_civic_term(term: str, target_language: str) -> Dict[str, Any]:
    """
    Translates a complex civic or election term into a target language.
    
    Args:
        term (str): The English civic term to translate (e.g., 'provisional ballot').
        target_language (str): The language to translate into (e.g., 'Spanish', 'Hindi').
        
    Returns:
        Dict[str, Any]: A result dictionary with 'status' and 'translated_text'.
    """
    translated_text = _cached_translate(term, target_language)

    if "Error" in translated_text:
        return {"error": "Translation service is currently unavailable."}

    return {
        "status": "success",
        "original_term": term,
        "target_language": target_language,
        "translated_text": translated_text,
    }
