import asyncio
import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create Session
        print("Creating Session...")
        try:
            resp = await client.post(f"{BASE_URL}/sessions")
            resp.raise_for_status()
            session_id = resp.json()["session_id"]
            print(f"Session Created: {session_id}")
        except Exception as e:
            print(f"Failed to create session: {e}")
            return

        # 2. Chat to get items
        print("\nSending Chat Message: 'I want to practice.'")
        chat_payload = {
            "session_id": session_id,
            "message": "I want to practice."
        }
        resp = await client.post(f"{BASE_URL}/chat", json=chat_payload)
        chat_data = resp.json()
        print(f"Reply: {chat_data['reply'][:100]}...")
        
        items = chat_data.get("items", [])
        print(f"Generated {len(items)} items.")
        
        if not items:
            print("No items generated. Exiting.")
            return

        # 3. Submit Attempt for first item
        target_item = items[0]
        print(f"\nAttempting Item: {target_item['type']} - {target_item['prompt']}")
        
        # Mock attempt logic
        attempt_text = "test"
        if target_item['type'] == 'vocab_fill':
            attempt_text = target_item.get('expected_answer', 'wrong')
        elif target_item['type'] == 'grammar_mcq':
            attempt_text = target_item.get('expected_answer', 'wrong')
            
        print(f"Submitting attempt: '{attempt_text}'")
        
        attempt_payload = {
            "session_id": session_id,
            "item_id": target_item['id'],
            "attempt_text": attempt_text
        }
        
        resp = await client.post(f"{BASE_URL}/attempt", json=attempt_payload)
        result = resp.json()
        
        print("\nAttempt Result:")
        print(f"Score: {result['score']}")
        print(f"Feedback: {result['feedback']}")
        print(f"New Mastery: {result['mastery_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
