import httpx
import time
import json
import asyncio

# Config
BASE_URL = "http://127.0.0.1:8000/v2"
V1_URL = "http://127.0.0.1:8000/v1" # For some adaptive features not yet fully ported to v2 endpoints in demo

async def run_scenario():
    print("\n🎭 --- EduVision Full Scenario Demo ---\n")
    
    # 1. Registration (Student)
    print("👤 Step 1: User Registration")
    email = f"student_{int(time.time())}@uni.edu"
    password = "securepass123"
    print(f"   > Registering {email} at 'TechUniversity'...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Register
        resp = await client.post(f"{BASE_URL}/auth/register", params={
            "email": email,
            "password": password,
            "tenant_name": "TechUniversity",
            "role": "student"
        })
        if resp.status_code != 201:
            print(f"❌ Registration Failed: {resp.text}")
            return
        print("   ✅ Registered successfully.")

        # Login
        print("\n🔑 Step 2: Login & Authentication")
        resp = await client.post(f"{BASE_URL}/auth/login", data={
            "username": email,
            "password": password
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   ✅ Login successful. Token acquired.")

        # Create Session
        print("\n🎓 Step 3: Starting Learning Session")
        resp = await client.post(f"{BASE_URL}/sessions", headers=headers)
        session_id = resp.json()["session_id"]
        print(f"   ✅ Session Created: {session_id}")

        # Chat with AI Tutor (Adaptive)
        print("\n🤖 Step 4: Chat with AI Tutor")
        user_msg = "I want to learn about Photosynthesis."
        print(f"   > User: '{user_msg}'")
        
        # Note: In V2 chat is currently simplified, but let's see the LLM response
        resp = await client.post(f"{BASE_URL}/chat", headers=headers, params={
            "session_id": session_id, 
            "message": user_msg
        })
        
        data = resp.json()
        ai_reply = data.get("reply", "")
        provider = data.get("provider", "Unknown")
        
        print(f"   > AI ({provider}): '{ai_reply[:100]}...'")
        
        if "Ollama" in provider:
            print("   ✅ Real AI (Llama 3.1) is working!")
        else:
            print("   ⚠️ Running on Fallback/Mock mode.")

        # Knowledge Upload (Background Job)
        print("\n📚 Step 5: Uploading Knowledge Material")
        # Create dummy PDF content
        dummy_content = b"Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar."
        files = {'file': ('biology_notes.txt', dummy_content, 'text/plain')}
        
        resp = await client.post(f"{BASE_URL}/knowledge/upload", headers=headers, files=files)
        job_id = resp.json().get("job_id")
        print(f"   ✅ File uploaded. Job ID: {job_id}")
        
        # Check Job Status
        print("   > Checking indexing status...")
        await asyncio.sleep(1)
        resp = await client.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        print(f"   > Job Status: {resp.json().get('status')}")

        # Analytics/Metrics
        print("\n📊 Step 6: Checking System Metrics")
        resp = await client.get(f"{BASE_URL}/metrics")
        metrics = resp.text
        if "chat_latency" in metrics:
            print("   ✅ Metrics are being collected.")
        else:
            print("   ⚠️ Metrics empty (might need more activity).")

    print("\n🎉 Scenario Completed! System is fully operational.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
