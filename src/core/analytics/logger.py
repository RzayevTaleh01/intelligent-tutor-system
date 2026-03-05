from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models_adaptive import AnalyticsEvent
import json
import time

class AnalyticsLogger:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, session_id: str, event_type: str, payload: Dict[str, Any]):
        try:
            # Add timestamp if missing
            if "timestamp" not in payload:
                payload["timestamp"] = time.time()
                
            event = AnalyticsEvent(
                session_id=session_id,
                event_type=event_type,
                payload_json=payload
            )
            self.db.add(event)
            await self.db.commit()
        except Exception as e:
            print(f"Analytics Logging Error: {e}")
