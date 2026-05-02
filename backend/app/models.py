from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    # In a real scenario, frontend would pass ephemeral context
    # user_location: Optional[str] = None 

class ChatResponse(BaseModel):
    role: str
    content: str
