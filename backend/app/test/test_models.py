from app.models import Message, ChatRequest, ChatResponse

def test_message_model():
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

def test_chat_request_model():
    req = ChatRequest(messages=[Message(role="user", content="Hello")])
    assert len(req.messages) == 1
    assert req.messages[0].role == "user"

def test_chat_response_model():
    res = ChatResponse(role="assistant", content="Hi")
    assert res.role == "assistant"
    assert res.content == "Hi"
