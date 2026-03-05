import httpx
import os

BASE_URL = "http://127.0.0.1:8000"

# Create dummy sample book
if not os.path.exists("tests/sample_book.txt"):
    if not os.path.exists("tests"):
        os.makedirs("tests")
    with open("tests/sample_book.txt", "w") as f:
        f.write("Habits are powerful. Small changes lead to big results. Atomic Habits focuses on 1% improvements. " * 50)

def run_test():
    print("--- Knowledge Smoke Test ---")
    
    # 1. Upload
    print("\n1. Uploading Book...")
    files = {'file': ('sample_book.txt', open('tests/sample_book.txt', 'rb'), 'text/plain')}
    resp = httpx.post(f"{BASE_URL}/knowledge/upload", files=files, timeout=60.0)
    if resp.status_code != 200:
        print(f"Upload Failed: {resp.text}")
        return
    data = resp.json()
    source_id = data["source_id"]
    print(f"Source ID: {source_id}")
    print(f"Chunks: {data['chunks_created']}")
    
    # 2. Search
    print("\n2. Searching 'habit'...")
    resp = httpx.get(f"{BASE_URL}/knowledge/search", params={"source_id": source_id, "q": "habit", "k": 2})
    results = resp.json()
    print(f"Found {len(results)} chunks.")
    if results:
        print(f"Top snippet: {results[0]['text_snippet']}")
        
    # 3. Graph
    print("\n3. Fetching Graph...")
    resp = httpx.get(f"{BASE_URL}/knowledge/graph", params={"source_id": source_id})
    graph = resp.json()
    print(f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
    
    # 4. Generate Lesson
    print("\n4. Generating Lesson...")
    payload = {"source_id": source_id, "level": "A2", "focus": "improvement"}
    resp = httpx.post(f"{BASE_URL}/knowledge/lesson", json=payload, timeout=60.0)
    if resp.status_code == 200:
        lesson_data = resp.json()
        print(f"Lesson Title: {lesson_data['lesson']['title']}")
        print(f"Generated Items: {len(lesson_data['items'])}")
    else:
        print(f"Lesson Gen Failed: {resp.text}")

if __name__ == "__main__":
    run_test()
