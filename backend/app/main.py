from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse
from .services.ai_engine import process_chat
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="The Civic Navigator - Backend", version="1.0.0")

# Allow requests from the frontend (in production, strictly configure this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to frontend URL in prod
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
    user_email = http_request.headers.get("X-User-Email")
    
    # In a real implementation, we would validate the token if needed
    # logger.info(f"Received request from user: {user_email}")
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages payload cannot be empty")
        
    try:
        # Call the AI Engine service, passing the OAuth access token if available
        ai_response_text = await process_chat(
            messages=request.messages,
            access_token=auth_header
        )
        
        return ChatResponse(
            role="assistant",
            content=ai_response_text
        )
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
