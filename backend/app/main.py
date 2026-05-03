from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse
from .services.ai_engine import process_chat
from .core.config import settings
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="The Civic Navigator - Backend",
    version="1.0.0",
    description="Backend API for The Civic Navigator using Google Gemini and ADK."
)

# Allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Status"])
async def health_check() -> dict:
    """
    Checks the health of the API.
    
    Returns:
        dict: A status message indicating the API is healthy.
    """
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse, tags=["AI"])
async def chat_endpoint(request: ChatRequest, http_request: Request) -> ChatResponse:
    """
    Accepts chat context from the Next.js BFF and processes it via the AI engine.
    
    Args:
        request (ChatRequest): The chat request containing message history.
        http_request (Request): The raw HTTP request to extract headers.
        
    Returns:
        ChatResponse: The assistant's response.
        
    Raises:
        HTTPException: If the request is invalid or processing fails.
    """
    # Extract headers passed securely from Next.js BFF
    auth_header = http_request.headers.get("Authorization")

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
