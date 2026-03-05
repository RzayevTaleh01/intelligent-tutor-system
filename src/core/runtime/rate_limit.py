import time
from collections import defaultdict
from fastapi import Request, HTTPException
from src.config import get_settings

settings = get_settings()

class RateLimiter:
    def __init__(self):
        # Simple in-memory sliding window
        # Key: user_id or ip -> List[timestamp]
        self.requests = defaultdict(list)
        self.limit = 60 # requests per minute
        self.window = 60 # seconds

    async def check(self, key: str):
        now = time.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        
        if len(self.requests[key]) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
        self.requests[key].append(now)

rate_limiter = RateLimiter()
