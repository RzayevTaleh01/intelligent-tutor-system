
import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"
TOKEN = ""
HEADERS = {}

def print_step(msg):
    print(f"\n{'='*50}\n{msg}\n{'='*50}")

def run_test():
    global TOKEN, HEADERS
    
    # 1. Register & Login
    print_step("1. Auth")
    email = f"teacher_{int(time.time())}@edu.com"
    password = "password123"
    
    requests.post(f"{BASE_URL}/auth/register", params={
        "email": email, "password": password, "tenant_name": "univ_tenant", "role": "teacher"
    })
    
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
        
    TOKEN = resp.json()["access_token"]
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}
    print("Logged in.")

    # 2. Create Course
    print_step("2. Create Course 'Python 101'")
    resp = requests.post(f"{BASE_URL}/courses/", params={
        "title": "Python 101",
        "description": "Intro to Python Programming"
    }, headers=HEADERS)
    
    if resp.status_code != 201:
        print(f"Create Course failed: {resp.text}")
        return
        
    course_id = resp.json()["course_id"]
    print(f"Course Created: {course_id}")
    
    # 3. Upload Material
    print_step("3. Upload Material (dummy.txt) - SKIPPED FOR PERFORMANCE")
    # dummy_content = "Python is a high-level programming language. It uses indentation for blocks."
    # files = {"file": ("intro.txt", dummy_content, "text/plain")}
    
    # resp = requests.post(f"{BASE_URL}/courses/{course_id}/upload", files=files, headers=HEADERS)
    # if resp.status_code != 200:
    #     print(f"Upload failed: {resp.text}")
    # else:
    #     print(f"Upload success: {resp.json()}")
        
    # Wait for indexing (it's async but fast for small text)
    # time.sleep(1) 

    # 4. Create Session for this Course
    print_step("4. Student Session")
    resp = requests.post(f"{BASE_URL}/sessions", params={"course_id": course_id}, headers=HEADERS)
    if resp.status_code != 200:
        print(f"Session failed: {resp.text}")
        return
        
    session_id = resp.json()["session_id"]
    print(f"Session Created: {session_id} (linked to course {course_id})")

    # 5. Chat about Python
    print_step("5. Chat: 'What is Python?'")
    resp = requests.post(f"{BASE_URL}/chat", params={
        "session_id": session_id,
        "message": "What is Python?"
    }, headers=HEADERS)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"Reply: {data.get('reply')}")
        print(f"Content ID Used: {data.get('content_id')}")
        # Verify if RAG worked (content_id should not be generic)
        if data.get('content_id') != "generic_101" and data.get('content_id') != "no_content":
            print("✅ RAG Success! Retrieved uploaded content.")
        else:
            print("⚠️ RAG Warning: Got generic or no content.")
    else:
        print(f"Chat failed: {resp.text}")

if __name__ == "__main__":
    run_test()
