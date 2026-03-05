import httpx
import asyncio

BASE_URL = "http://127.0.0.1:8000"

# Mock seed
EDGES = [
    ("vocab_travel", "reading_travel", 0.8),
    ("grammar_past_simple", "rewrite_past", 0.9),
    ("vocab_business", "email_writing", 0.7)
]

async def seed():
    print("--- Seeding English Concept Graph ---")
    async with httpx.AsyncClient() as client:
        for u, v, w in EDGES:
            payload = {"from_skill_tag": u, "to_skill_tag": v, "weight": w}
            resp = await client.post(f"{BASE_URL}/concept-graph/edge", json=payload)
            print(f"Edge {u}->{v}: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(seed())
