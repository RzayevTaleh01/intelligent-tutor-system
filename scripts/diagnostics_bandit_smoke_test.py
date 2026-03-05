import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("--- Diagnostics & Bandit Smoke Test ---")
    
    # 1. Seed Graph
    # Assumes server is running and seed script is available or we just call endpoint here manually
    # We'll skip manual seed call if script exists, but let's just do one edge here
    print("\n1. Seeding Edge...")
    httpx.post(f"{BASE_URL}/concept-graph/edge", json={"from_skill_tag": "A", "to_skill_tag": "B", "weight": 0.5})
    
    # 2. Create Session
    resp = httpx.post(f"{BASE_URL}/sessions")
    if resp.status_code != 200:
        print("Failed to create session")
        return
    session_id = resp.json()["session_id"]
    print(f"Session: {session_id}")
    
    # 3. Chat -> Plan (Diagnostics Check)
    print("\n3. Chatting...")
    chat_payload = {"session_id": session_id, "message": "I want to learn english"}
    try:
        resp = httpx.post(f"{BASE_URL}/chat", json=chat_payload, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            plan = data.get("next_step_plan", {})
            print(f"Reply: {data.get('reply')[:50]}...")
            print(f"Variant: {plan.get('variant')}")
            print(f"Why: {plan.get('why_this_plan')}")
            print(f"Chosen Action: {plan.get('chosen_action')}")
            
            items = data.get("items", [])
            if items:
                item_id = items[0]["id"]
                # 4. Attempt -> Update IRT/Bandit
                print("\n4. Attempting...")
                resp = httpx.post(f"{BASE_URL}/attempt", json={
                    "session_id": session_id,
                    "item_id": item_id,
                    "attempt_text": "correct answer" # Mock correctness
                })
                print(f"Attempt Status: {resp.status_code}")
                if resp.status_code == 200:
                    att_data = resp.json()
                    print(f"Feedback: {att_data.get('feedback')}")
                    print(f"Mastery: {att_data.get('mastery_score')}")
        else:
            print(f"Chat Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Chat Error: {e}")
    
    # 5. Diagnostics Report
    print("\n5. Diagnostics Report...")
    try:
        resp = httpx.get(f"{BASE_URL}/diagnostics/report", params={"session_id": session_id})
        if resp.status_code == 200:
            print(resp.json())
        else:
            print(f"Report Failed: {resp.status_code}")
    except Exception as e:
        print(f"Report Error: {e}")

if __name__ == "__main__":
    run_test()
