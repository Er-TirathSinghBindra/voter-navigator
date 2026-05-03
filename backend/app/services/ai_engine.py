import os
import logging
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.civic import civic_agent
from app.agents.utility import utility_agent

logger = logging.getLogger(__name__)

# Application Configuration
APP_NAME = "civic_navigator"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 1. Define the Primary Coordinator Agent
# This agent acts as the router and orchestrator
root_agent = Agent(
    name="primary_coordinator",
    model="gemini-3.1-flash-lite-preview",  # Keeping the user's preferred model for the coordinator
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

# 3. Setup the ADK Runner
coordinator_runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

async def process_chat(messages: list, access_token: str = None) -> str:
    """
    Processes the chat history using the Google ADK Runner.
    This replaces the manual tool-calling loop.
    """
    # For ADK, we typically use session-based state. 
    # For this simple implementation, we'll create a unique session ID per request
    # or use a placeholder if we want to maintain history across requests.
    session_id = "default_session" # In production, this would be tied to the user
    user_id = "user_123"

    # Ensure session exists
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

    # The last message from the user
    last_msg = messages[-1].content
    new_message = types.Content(role='user', parts=[types.Part.from_text(text=last_msg)])

    # Add the OAuth token to the session context if available
    # The ADK Runner can pass context to tools
    context = {"access_token": access_token} if access_token else {}

    try:
        final_answer = ""
        # The ADK Runner handles history and tool calls internally
        async for event in coordinator_runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=new_message,
            # context=context # Assuming Runner/Agent can pass context to tool functions
        ):
            if event.is_final_response() and event.content:
                final_answer = event.content.parts[0].text.strip()
        
        return final_answer
    except Exception as e:
        logger.error(f"ADK Runner Error: {e}")
        return "I encountered an error while processing your request. Please try again."
