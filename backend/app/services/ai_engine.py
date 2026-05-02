import os
import json
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

from .civic_api import fetch_civic_info
from .wallet_api import generate_voter_pass
from .calendar_api import add_calendar_event
from .translation_api import translate_civic_term

# Initialize new Gemini SDK (google.genai)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

# Create the GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

# Define Tools via Function Schemas
def get_civic_info(query_type: str, address_context: str):
    """
    Get polling locations, ballot information, or representative data based on the user's address. Use this whenever the user asks where to vote or who their representative is.
    Args:
        query_type: Type of info needed, exactly one of: 'polling_location', 'ballot', 'representatives'
        address_context: The user's current or provided address. MUST include street and ZIP code if possible.
    """
    pass

def add_calendar_deadline(event_title: str, date: str):
    """
    Adds an election deadline to the user's Google Calendar.
    Args:
        event_title: Title of the calendar event (e.g., 'Election Day', 'Voter Registration Deadline')
        date: ISO format date string of the deadline (YYYY-MM-DD).
    """
    pass

def generate_wallet_pass(voter_state: str):
    """
    Generates a Digital Voter Readiness Pass for Google Wallet.
    Args:
        voter_state: The state the voter is registered in.
    """
    pass

def translate_civic_term(term: str, target_language: str):
    """
    Translates a complex civic or election term into another language.
    Args:
        term: The English term to translate (e.g., 'provisional ballot')
        target_language: The language to translate to (e.g., 'Spanish', 'Mandarin')
    """
    pass

civic_tools = [get_civic_info, add_calendar_deadline, generate_wallet_pass, translate_civic_term]

# Persona configuration
SYSTEM_INSTRUCTION = """
You are "The Civic Navigator", a helpful, neutral, and highly knowledgeable election assistant. 
Your goal is to help users navigate the voting process, find polling locations, track deadlines, 
generate their readiness passes, and translate complex civic terminology.

Rules:
1. Remain strictly non-partisan and neutral. Do not endorse any candidate or party.
2. Use the provided tools when the user's intent matches them.
3. Be concise and friendly.
4. If an API tool returns an error (like missing address), politely ask the user for the missing information.
5. Do NOT make up polling locations or dates. Only use data returned by the tools.
"""

async def process_chat(messages: list, access_token: str = None) -> str:
    """
    Processes the chat history, invokes Gemini, and handles real API tool calls.
    """
    # Convert incoming messages to google.genai Content format
    history = []
    for msg in messages[:-1]: # All but the last one
        role = "model" if msg.role == "assistant" else "user"
        history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
    last_message = messages[-1].content
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=civic_tools
    )
    
    chat = client.chats.create(
        model="gemini-3.1-flash-lite-preview",
        config=config,
        history=history if history else None
    )
    
    response = chat.send_message(last_message)
    
    # Handle Tool Calls
    if response.function_calls:
        for function_call in response.function_calls:
            tool_name = function_call.name
            args = function_call.args
            
            tool_response_data = {}
            
            if tool_name == "get_civic_info":
                tool_response_data = await fetch_civic_info(
                    query_type=args.get("query_type", "polling_location"),
                    address_context=args.get("address_context", "")
                )
            elif tool_name == "add_calendar_deadline":
                tool_response_data = await add_calendar_event(
                    event_title=args.get("event_title", "Election Event"),
                    date_iso=args.get("date", ""),
                    access_token=access_token
                )
            elif tool_name == "generate_wallet_pass":
                tool_response_data = await generate_voter_pass(
                    voter_state=args.get("voter_state", "Unknown")
                )
            elif tool_name == "translate_civic_term":
                tool_response_data = await translate_civic_term(
                    term=args.get("term", ""),
                    target_language=args.get("target_language", "es")
                )
            else:
                tool_response_data = {"error": f"Unknown tool called: {tool_name}"}
                
            # Send tool result back to Gemini to formulate final response
            tool_part = types.Part.from_function_response(
                name=tool_name,
                response=tool_response_data
            )
            final_response = chat.send_message(tool_part)
            return final_response.text
    
    return response.text
