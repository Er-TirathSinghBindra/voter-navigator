import logging
from typing import List, Optional

from app.core.config import settings
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.civic import civic_agent
from app.agents.utility import utility_agent
from app.models import Message

logger = logging.getLogger(__name__)

# 1. Define the Primary Coordinator Agent
root_agent = Agent(
    name="primary_coordinator",
    model=settings.default_model,
    instruction="""You are "The Civic Navigator" Primary Coordinator.
    Your goal is to help users navigate the election process.
    
    Delegation Strategy:
    - For polling locations, representatives, or ballot info: Use the 'civic_specialist' sub-agent.
    - For calendar syncing, wallet passes, or translations: Use the 'utility_assistant' sub-agent.
    
    Remain neutral, concise, and friendly. Synthesize the sub-agent responses into a helpful final answer.""",
    sub_agents=[civic_agent, utility_agent]
)

# 2. Setup Session Service (In-memory for development)
session_service = InMemorySessionService()

# 3. Setup the ADK Runner (Relies on GOOGLE_API_KEY set in config.py)
coordinator_runner = Runner(
    agent=root_agent,
    app_name=settings.app_name,
    session_service=session_service,
)

async def process_chat(
    messages: List[Message], 
    access_token: Optional[str] = None,
    user_id: str = "user_123",
    session_id: str = "default_session"
) -> str:
    """
    Processes the chat history using the Google ADK Runner.
    
    Args:
        messages (List[Message]): The list of chat messages.
        access_token (Optional[str]): The OAuth access token for tools.
        user_id (str): The unique ID of the user.
        session_id (str): The unique ID for the chat session.
        
    Returns:
        str: The final answer from the AI coordinator.
    """
    # Ensure session exists
    await session_service.create_session(
        app_name=settings.app_name, 
        user_id=user_id, 
        session_id=session_id
    )

    # The last message from the user
    last_msg = messages[-1].content
    new_message = types.Content(role='user', parts=[types.Part.from_text(text=last_msg)])

    try:
        final_answer = ""
        # The ADK Runner handles history and tool calls internally
        async for event in coordinator_runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=new_message,
        ):
            if event.is_final_response() and event.content:
                final_answer = event.content.parts[0].text.strip()
        
        return final_answer
    except Exception as e:
        logger.error(f"ADK Runner Error: {e}")
        return "I encountered an error while processing your request. Please try again."
