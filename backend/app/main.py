from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse
from .services.ai_engine import process_chat
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import sys

app = FastAPI(title="The Civic Navigator - Backend", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    required_secrets = ["GEMINI_API_KEY", "CIVIC_INFO_API_KEY"]
    missing = [secret for secret in required_secrets if not os.environ.get(secret)]
    
    if missing:
        logger.error(f"CRITICAL STARTUP ERROR: Missing required secrets: {', '.join(missing)}")
        logger.error("Ensure these are injected via GCP Secret Manager or .env file.")
        sys.exit(1)
    
    logger.info("Startup validation passed. All required secrets are present.")

# Allow requests from the frontend (in production, strictly configure this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, http_request: Request):
    """
    Accepts chat context from the Next.js BFF and processes it via Vertex AI.
    """
    # Extract headers passed securely from Next.js BFF
    auth_header = http_request.headers.get("Authorization")

    # Security: Do not extract or log PII like user email here.

    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages payload cannot be empty")

    try:
        # Call the AI Engine service, passing the OAuth access token if available
        ai_response_text = await process_chat(
            messages=request.messages, access_token=auth_header
        )

        return ChatResponse(role="assistant", content=ai_response_text)
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
