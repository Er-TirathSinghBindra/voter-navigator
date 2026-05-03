from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    Attributes:
        app_name (str): The name of the application.
        gemini_api_key (str): Google Gemini API key for AI engine.
        civic_info_api_key (str): Google Civic Information API key.
        wallet_issuer_id (str): Google Wallet issuer ID.
        wallet_class_id (str): Google Wallet class ID.
        frontend_url (str): The URL of the frontend application.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "The Civic Navigator"
    gemini_api_key: str = Field(...)
    civic_info_api_key: str = Field(...)
    
    # Wallet configuration
    wallet_issuer_id: str = Field("PLACEHOLDER_ISSUER")
    wallet_class_id: str = Field("")
    
    # Frontend configuration
    frontend_url: str = Field("*")
    google_application_credentials: str = Field("./service-account.json")
    
    # Default model
    default_model: str = "gemini-3.1-flash-lite-preview"

settings = Settings()

# Ensure GOOGLE_API_KEY is set for ADK/GenAI SDKs
import os
if settings.gemini_api_key:
    os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
