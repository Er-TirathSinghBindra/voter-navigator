import os
from google.adk.agents import Agent
from app.services.calendar_api import add_calendar_event
from app.services.wallet_api import generate_voter_pass
from app.services.translation_api import translate_civic_term

# Define the Utility & Logistics Assistant
utility_agent = Agent(
    name="utility_assistant",
    model="gemini-3.1-flash-lite-preview",
    instruction="""You are a Utility and Logistics Assistant.
    Your role is to:
    1. Add election deadlines to the user's Google Calendar.
    2. Generate Digital Voter Readiness Passes for Google Wallet.
    3. Translate complex civic terms into other languages.
    
    Use the provided tools for these tasks. 
    For calendar events, ensure you have a valid date.
    For translation, ensure you know the target language.""",
    tools=[add_calendar_event, generate_voter_pass, translate_civic_term]
)
