from typing import Dict, Any, Optional
import time
import hashlib
import json

class LRUCache:
    def __init__(self, capacity: int = 100, ttl_seconds: int = 600):
        self.capacity = capacity
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []

    def _generate_key(self, lesson_id: str, difficulty: str, item_type: Optional[str] = None) -> str:
        raw = f"{lesson_id}:{difficulty}:{item_type}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, lesson_id: str, difficulty: str, item_type: Optional[str] = None) -> Optional[Any]:
        key = self._generate_key(lesson_id, difficulty, item_type)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                # Update access order
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                return entry["data"]
            else:
                # Expired
                self.delete(key)
        return None

    def set(self, lesson_id: str, difficulty: str, data: Any, item_type: Optional[str] = None):
        key = self._generate_key(lesson_id, difficulty, item_type)
        
        # Eviction
        if len(self.cache) >= self.capacity:
            oldest = self.access_order.pop(0)
            self.delete(oldest)
            
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        self.access_order.append(key)

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)

# Global instance
response_cache = LRUCache()
