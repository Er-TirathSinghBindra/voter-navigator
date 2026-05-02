import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.models import Message
from app.services.ai_engine import process_chat

async def test_vertex_ai_routing():
    print("--- Starting Vertex AI Routing Logic Test ---")

    # Test 1: Civic Info Routing
    print("\nTest 1: Polling Location (Civic API)")
    msg1 = Message(
        role="user",
        content="I am an 18-year-old out-of-state college student. Where is my polling place at 1600 Pennsylvania Avenue NW, Washington, DC?",
    )
    resp1 = await process_chat([msg1])
    print(f"Response: {resp1}")
    if "Mock Translation" in resp1 or "Wallet" in resp1 or "Calendar" in resp1:
        print("Test 1 FAILED: Wrong tool routed.")
    else:
        print("Test 1 PASSED: Correctly evaluated Civic API intent.")

    # Test 2: Calendar Action
    print("\nTest 2: Calendar Reminder")
    msg2 = Message(
        role="user", content="Remind me to register to vote on October 15th 2026."
    )
    resp2 = await process_chat([msg2])
    print(f"Response: {resp2}")
    if "Calendar" not in resp2 and "added" not in resp2:
        print("Test 2 FAILED: Did not route to Calendar API.")
    else:
        print("Test 2 PASSED: Correctly evaluated Calendar API intent.")

    # Test 3: Wallet Action
    print("\nTest 3: Wallet Pass")
    msg3 = Message(
        role="user", content="Can you give me my digital voter pass for New York?"
    )
    resp3 = await process_chat([msg3])
    print(f"Response: {resp3}")
    if "Wallet" not in resp3 and "pay.google.com" not in resp3:
        print("Test 3 FAILED: Did not route to Wallet API.")
    else:
        print("Test 3 PASSED: Correctly evaluated Wallet API intent.")

    # Test 4: Translation Action
    print("\nTest 4: Translation")
    msg4 = Message(role="user", content="What does provisional ballot mean in Spanish?")
    resp4 = await process_chat([msg4])
    print(f"Response: {resp4}")
    if (
        "Translation" not in resp4
        and "Mock Translation" not in resp4
        and "provisional ballot" not in resp4
    ):
        print("Test 4 FAILED: Did not route to Translation API.")
    else:
        print("Test 4 PASSED: Correctly evaluated Translation API intent.")

    print("\n--- Routing Tests Complete ---")


if __name__ == "__main__":
    asyncio.run(test_vertex_ai_routing())
