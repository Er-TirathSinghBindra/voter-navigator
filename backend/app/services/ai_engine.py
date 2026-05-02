import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    Content,
    Part,
    ChatSession
)

# Initialize Vertex AI - (Requires GOOGLE_APPLICATION_CREDENTIALS or Cloud Run metadata)
# vertexai.init(project="your-project-id", location="us-central1")

# Define tools (Function Calling)
get_civic_info_func = FunctionDeclaration(
    name="get_civic_info",
    description="Get polling locations, ballot information, or representative data based on the user's address.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {"type": "string", "description": "Type of info needed, e.g., 'polling_location', 'ballot', 'representatives'"},
            "address_context": {"type": "string", "description": "The user's current or provided address."}
        },
        "required": ["query_type"]
    }
)

add_calendar_deadline_func = FunctionDeclaration(
    name="add_calendar_deadline",
    description="Adds an election deadline to the user's Google Calendar.",
    parameters={
        "type": "object",
        "properties": {
            "event_title": {"type": "string", "description": "Title of the calendar event (e.g., 'Election Day', 'Voter Registration Deadline')"},
            "date": {"type": "string", "description": "ISO format date string of the deadline."}
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
        "required": []
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
"""

def get_model():
    # Use gemini-1.5-flash for fast reasoning and function calling
    return GenerativeModel(
        "gemini-1.5-flash-001",
        system_instruction=[SYSTEM_INSTRUCTION],
        tools=[civic_tools]
    )

async def process_chat(messages: list) -> str:
    """
    Processes the chat history, invokes Gemini, and handles any tool calls.
    """
    model = get_model()
    
    # Convert incoming messages to Vertex AI format
    history = []
    for msg in messages[:-1]: # All but the last one
        history.append(Content(role=msg.role, parts=[Part.from_text(msg.content)]))
        
    last_message = messages[-1].content
    
    # Start chat session
    chat = model.start_chat(history=history)
    
    # Send message to model
    response = chat.send_message(last_message)
    
    # Handle Tool Calls if any
    if response.function_call:
        func = response.function_call
        tool_name = func.name
        args = func.args
        
        print(f"Model called tool: {tool_name} with args: {args}")
        
        # MOCK IMPLEMENTATIONS
        tool_response_data = ""
        if tool_name == "get_civic_info":
            tool_response_data = f"Mock: Found polling location at 123 Main St for address query."
        elif tool_name == "add_calendar_deadline":
            tool_response_data = f"Mock: Successfully added '{args.get('event_title', 'Event')}' to your Google Calendar."
        elif tool_name == "generate_wallet_pass":
            tool_response_data = f"Mock: Generated Digital Voter Pass. Here is your mock link: https://pay.google.com/gp/v/save/mock-jwt-token"
        elif tool_name == "translate_civic_term":
            tool_response_data = f"Mock: The translation for '{args.get('term', '')}' in {args.get('target_language', '')} is 'Traducción simulada'."
        else:
            tool_response_data = "Mock: Action completed."
            
        # Send tool result back to Gemini to formulate final response
        final_response = chat.send_message(
            Part.from_function_response(
                name=tool_name,
                response={"result": tool_response_data}
            )
        )
        return final_response.text
    
    # If no tool was called, return the text directly
    return response.text
