import httpx
import sys
import os

# Create dummy wav if not exists
if not os.path.exists("tests/sample.wav"):
    if not os.path.exists("tests"):
        os.makedirs("tests")
    import soundfile as sf
    import numpy as np
    sf.write("tests/sample.wav", np.random.uniform(-0.1, 0.1, 16000), 16000)

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("--- Voice Smoke Test ---")
    
    # 1. Create Session
    try:
        resp = httpx.post(f"{BASE_URL}/sessions")
        if resp.status_code != 200:
            print(f"Failed to create session: {resp.status_code} {resp.text}")
            return
        session_id = resp.json()["session_id"]
        print(f"Session: {session_id}")
    except Exception as e:
        print(f"Session Creation Error: {e}")
        return
    
    # 2. Voice Chat
    print("\nSending Voice Chat (sample.wav - noise)...")
    files = {'file': ('sample.wav', open('tests/sample.wav', 'rb'), 'audio/wav')}
    try:
        resp = httpx.post(f"{BASE_URL}/voice/chat", params={"session_id": session_id}, files=files, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            print(f"ASR Text: {data['asr_text']}")
            print(f"Reply: {data['reply_text'][:50]}...")
            print(f"Audio URL: {data['audio_url']}")
        elif resp.status_code == 400:
            print("Voice Chat: Received 400 (Expected for noise input)")
        else:
            print(f"Voice Chat Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    # 2.1 Standalone ASR
    print("\nTesting /voice/asr...")
    files_asr = {'file': ('sample.wav', open('tests/sample.wav', 'rb'), 'audio/wav')}
    try:
        resp = httpx.post(f"{BASE_URL}/voice/asr", files=files_asr)
        if resp.status_code == 200:
            print(f"ASR Result: {resp.json()}")
        elif resp.status_code == 400:
            print("ASR: Received 400 (Expected for noise input)")
        else:
            print(f"ASR Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"ASR Error: {e}")

    # 2.2 Standalone TTS
    print("\nTesting /voice/tts...")
    try:
        resp = httpx.post(f"{BASE_URL}/voice/tts", json={"text": "Hello world"})
        if resp.status_code == 200:
            print(f"TTS Result: Got {len(resp.content)} bytes audio")
        else:
            print(f"TTS Failed: {resp.text}")
    except Exception as e:
        print(f"TTS Error: {e}")

    # 3. Stream Chat
    print("\nTesting Chat Stream...")
    try:
        with httpx.stream("GET", f"{BASE_URL}/chat/stream", params={"session_id": session_id, "message": "Hello stream"}) as r:
            print("Receiving stream:", end=" ")
            for chunk in r.iter_text():
                if "token" in chunk:
                    print(".", end="", flush=True)
            print("\nStream finished.")
    except Exception as e:
        print(f"Stream Error: {e}")

if __name__ == "__main__":
    run_test()
