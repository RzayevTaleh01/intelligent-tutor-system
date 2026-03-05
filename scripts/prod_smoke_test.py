import httpx
import time

BASE_URL = "http://127.0.0.1:8000/v2"

def run_prod_test():
    print("--- Production Smoke Test (V2) ---")
    
    # 1. Register
    print("\n1. Registering User...")
    email = f"student_{int(time.time())}@uni.edu"
    payload = {
        "email": email,
        "password": "securepass123",
        "tenant_name": "TechUniversity",
        "role": "student"
    }
    try:
        resp = httpx.post(f"{BASE_URL}/auth/register", params=payload)
        print(f"Register: {resp.status_code}")
    except Exception as e:
        print(f"Register Error: {e}")
        return

    # 2. Login
    print("\n2. Logging In...")
    login_data = {
        "username": email,
        "password": "securepass123"
    }
    try:
        resp = httpx.post(f"{BASE_URL}/auth/login", data=login_data)
        if resp.status_code != 200:
            print(f"Login Failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login Success (Token obtained)")
    except Exception as e:
        print(f"Login Error: {e}")
        return

    # 3. Create Session (Auth required)
    print("\n3. Creating Session...")
    try:
        resp = httpx.post(f"{BASE_URL}/sessions", headers=headers)
        session_id = resp.json()["session_id"]
        print(f"Session: {session_id}")
    except Exception as e:
        print(f"Session Error: {e}")
        return

    # 4. Chat (Rate limited & Auth)
    print("\n4. Chatting...")
    try:
        chat_payload = {"session_id": session_id, "message": "Hello from prod"}
        resp = httpx.post(f"{BASE_URL}/chat", params=chat_payload, headers=headers)
        print(f"Chat Response: {resp.json()}")
    except Exception as e:
        print(f"Chat Error: {e}")

    # 5. Metrics
    print("\n5. Checking Observability...")
    try:
        resp = httpx.get("http://127.0.0.1:8000/v2/metrics")
        print(f"Metrics Endpoint: {resp.status_code}")
        # print(resp.text)
    except:
        pass

if __name__ == "__main__":
    run_prod_test()
