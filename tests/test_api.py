import pytest
import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.api.main import app

# Mock Ollama response to avoid dependency on running Ollama service during tests
from unittest.mock import AsyncMock, patch

@pytest.fixture(scope="module")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(loop_scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio(loop_scope="module")
async def test_create_session(client):
    response = await client.post("/sessions")
    assert response.status_code == 200
    assert "session_id" in response.json()

@pytest.mark.asyncio(loop_scope="module")
async def test_chat_flow(client):
    # 1. Create Session
    response = await client.post("/sessions")
    session_id = response.json()["session_id"]
    
    # 2. Mock Ollama
    with patch("src.llm.ollama_client.OllamaClient.generate_chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "This is a mock response from Tutor."
        
        # 3. Send Chat
        chat_payload = {
            "session_id": session_id,
            "message": "Hello"
        }
        response = await client.post("/chat", json=chat_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "This is a mock response from Tutor."
        assert "next_step_plan" in data
        assert "mastery_score" in data
        assert "items" in data # New field check
        
        # 4. Test Attempt Submission (if items generated)
        if data["items"]:
            target_item = data["items"][0]
            attempt_payload = {
                "session_id": session_id,
                "item_id": target_item["id"],
                "attempt_text": "test attempt"
            }
            
            attempt_resp = await client.post("/attempt", json=attempt_payload)
            assert attempt_resp.status_code == 200
            attempt_data = attempt_resp.json()
            
            assert "score" in attempt_data
            assert "feedback" in attempt_data
            assert "mastery_score" in attempt_data
            # Mastery should change (or stay same if score matches expectation)
            # Just verify structure for now
