import os
from google.adk.agents import Agent
from app.services.civic_api import fetch_civic_info

# Define the Civic Information Specialist
civic_agent = Agent(
    name="civic_specialist",
    model="gemini-3.1-flash-lite-preview",  # Using 3.1 as per user preference
    instruction="""You are a Civic Information Specialist. 
    Your role is to help users find their polling booths, ballot information, or representative data.
    Use the provided 'fetch_civic_info' tool to get accurate data.
    If an address is missing or incomplete, politely ask the user for it.""",
    tools=[fetch_civic_info]
)
