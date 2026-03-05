import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("--- Adaptive Smoke Test ---")
    
    # 1. Create Session
    resp = httpx.post(f"{BASE_URL}/sessions")
    if resp.status_code != 200:
        print("Failed to create session")
        return
    session_id = resp.json()["session_id"]
    print(f"Session: {session_id}")
    
    # 2. Chat to generate items
    print("\n2. Chatting to generate items...")
    chat_payload = {"session_id": session_id, "message": "I want to practice present tense."}
    resp = httpx.post(f"{BASE_URL}/chat", json=chat_payload, timeout=60.0)
    data = resp.json()
    items = data.get("items", [])
    print(f"Generated {len(items)} items.")
    
    if not items:
        print("No items generated, skipping attempts.")
        return

    # 3. Submit Attempts (Simulate Learning)
    print("\n3. Submitting Attempts...")
    item_id = items[0]["id"]
    
    # Attempt 1: Wrong (Grammar Error)
    print("  - Attempt 1: Wrong")
    resp = httpx.post(f"{BASE_URL}/attempt", json={
        "session_id": session_id,
        "item_id": item_id,
        "attempt_text": "I goed to school" # Intentional error
    })
    print(f"    Feedback: {resp.json().get('feedback')}")
    print(f"    Error Codes: {resp.json().get('error_codes')}")
    
    # Attempt 2: Correct
    print("  - Attempt 2: Correct")
    # Need correct answer? Usually plugin knows. Let's guess or assume we know for test.
    # Actually for smoke test we can just send the correct answer field from item if available,
    # or just another wrong one to see error tracking.
    # Let's send a generic wrong one again to boost error count.
    resp = httpx.post(f"{BASE_URL}/attempt", json={
        "session_id": session_id,
        "item_id": item_id,
        "attempt_text": "I wented to school"
    })
    
    # 4. Check Learner State (Adaptive Model)
    print("\n4. Checking Learner State...")
    resp = httpx.get(f"{BASE_URL}/learner/state", params={"session_id": session_id})
    state = resp.json()
    print(f"  Mastery: {state['mastery_overall']}")
    print(f"  Recent Errors: {state['recent_errors']}")
    
    # 5. Check Analytics
    print("\n5. Checking Analytics...")
    resp = httpx.get(f"{BASE_URL}/analytics/summary", params={"session_id": session_id})
    print(f"  Summary: {resp.json()}")

if __name__ == "__main__":
    run_test()
