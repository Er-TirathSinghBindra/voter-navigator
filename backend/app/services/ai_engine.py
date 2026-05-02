import vertexai
import json
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    Content,
    Part,
    ChatSession
)

from .civic_api import fetch_civic_info
from .wallet_api import generate_voter_pass
from .calendar_api import add_calendar_event
from .translation_api import translate_civic_term

# Initialize Vertex AI - (Requires GOOGLE_APPLICATION_CREDENTIALS)
# try:
#     vertexai.init(project="your-project-id", location="us-central1")
# except Exception as e:
#     print("Warning: Vertex AI not initialized correctly.", e)

# Define tools (Function Calling)
get_civic_info_func = FunctionDeclaration(
    name="get_civic_info",
    description="Get polling locations, ballot information, or representative data based on the user's address. Use this whenever the user asks where to vote or who their representative is.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {"type": "string", "description": "Type of info needed, exactly one of: 'polling_location', 'ballot', 'representatives'"},
            "address_context": {"type": "string", "description": "The user's current or provided address. MUST include street and ZIP code if possible."}
        },
        "required": ["query_type", "address_context"]
    }
)

add_calendar_deadline_func = FunctionDeclaration(
    name="add_calendar_deadline",
    description="Adds an election deadline to the user's Google Calendar.",
    parameters={
        "type": "object",
        "properties": {
            "event_title": {"type": "string", "description": "Title of the calendar event (e.g., 'Election Day', 'Voter Registration Deadline')"},
            "date": {"type": "string", "description": "ISO format date string of the deadline (YYYY-MM-DD)."}
        },
        "required": ["event_title", "date"]
    }
)

generate_wallet_pass_func = FunctionDeclaration(
    name="generate_wallet_pass",
    description="Generates a Digital Voter Readiness Pass for Google Wallet.",
    parameters={
        "type": "object",
        "properties": {
            "voter_state": {"type": "string", "description": "The state the voter is registered in."}
        },
        "required": ["voter_state"]
    }
)

translate_civic_term_func = FunctionDeclaration(
    name="translate_civic_term",
    description="Translates a complex civic or election term into another language.",
    parameters={
        "type": "object",
        "properties": {
            "term": {"type": "string", "description": "The English term to translate (e.g., 'provisional ballot')"},
            "target_language": {"type": "string", "description": "The language to translate to (e.g., 'Spanish', 'Mandarin')"}
        },
        "required": ["term", "target_language"]
    }
)

civic_tools = Tool(
    function_declarations=[
        get_civic_info_func,
        add_calendar_deadline_func,
        generate_wallet_pass_func,
        translate_civic_term_func
    ]
)

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

def get_model():
    return GenerativeModel(
        "gemini-3.1-flash-lite-preview",
        system_instruction=[SYSTEM_INSTRUCTION],
        tools=[civic_tools]
    )

async def process_chat(messages: list, access_token: str = None) -> str:
    """
    Processes the chat history, invokes Gemini, and handles real API tool calls.
    """
    model = get_model()
    
    # Convert incoming messages to Vertex AI format
    history = []
    for msg in messages[:-1]: # All but the last one
        history.append(Content(role=msg.role, parts=[Part.from_text(msg.content)]))
        
    last_message = messages[-1].content
    
    chat = model.start_chat(history=history)
    response = chat.send_message(last_message)
    
    # Handle Tool Calls
    if response.function_call:
        func = response.function_call
        tool_name = func.name
        args = {key: value for key, value in func.args.items()}
        
        print(f"Model called tool: {tool_name} with args: {args}")
        
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
        final_response = chat.send_message(
            Part.from_function_response(
                name=tool_name,
                response=tool_response_data
            )
        )
        return final_response.text
    
    return response.text
