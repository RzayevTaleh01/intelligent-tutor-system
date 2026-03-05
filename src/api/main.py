import uuid
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.db.session import get_db
from src.db.init_db import init_models
from src.db.models import Session, Message, Event
from src.core.engines.learner import LearnerEngine
from src.core.engines.pedagogy import PedagogyEngine
from src.core.engines.assessment import AssessmentEngine
from src.core.engines.tutor import TutorEngine
from src.plugins.english.plugin import EnglishPlugin
from src.llm.ollama_client import OllamaClient

# Initialize Components
app = FastAPI(title="Adaptive Learning Core API")
ollama_client = OllamaClient()
english_plugin = EnglishPlugin()

# Engines
assessment_engine = AssessmentEngine(plugin=english_plugin)
pedagogy_engine = PedagogyEngine()
tutor_engine = TutorEngine(llm_client=ollama_client)

# Pydantic Models
class CreateSessionResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    next_step_plan: Dict[str, Any]
    mastery_score: float
    items: List[Dict[str, Any]] = []

class AttemptRequest(BaseModel):
    session_id: str
    item_id: str
    attempt_text: str

class AttemptResponse(BaseModel):
    score: float
    feedback: str
    mastery_score: float
    readiness_score: float

@app.on_event("startup")
async def on_startup():
    await init_models()

@app.post("/sessions", response_model=CreateSessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    new_session = Session(id=session_id)
    db.add(new_session)
    await db.commit()
    
    # Initialize learner state
    learner_engine = LearnerEngine(db)
    await learner_engine.get_or_create_state(session_id)
    
    return {"session_id": session_id}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 1. Load Session and State
    result = await db.execute(select(Session).where(Session.id == request.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(request.session_id)
    
    # 2. Determine Next Step (Pedagogy)
    # We do this first to know WHAT content to talk about
    plan = pedagogy_engine.determine_next_step(state)
    
    # 3. Get Content from Plugin
    content_item = english_plugin.get_content(plan["next_difficulty"])
    
    # 4. Generate Learning Items (Exercises)
    # Context for generator
    gen_context = {"content_id": content_item.content_id}
    generated_items = english_plugin.generate_items(gen_context)
    
    # 5. Generate Tutor Response
    # Fetch history
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == request.session_id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_objs = history_result.scalars().all()
    history = [{"role": msg.role, "content": msg.content} for msg in reversed(history_objs)]
    
    context_data = {
        "mastery_score": state.mastery_score,
        "strategy": plan["strategy"]
    }
    
    reply = await tutor_engine.generate_reply(
        user_message=request.message,
        history=history,
        context_data=context_data,
        current_content=content_item
    )
    
    # 6. Save Messages
    user_msg = Message(session_id=request.session_id, role="user", content=request.message)
    bot_msg = Message(session_id=request.session_id, role="assistant", content=reply)
    db.add(user_msg)
    db.add(bot_msg)
    await db.commit()
    
    return {
        "reply": reply,
        "next_step_plan": plan,
        "mastery_score": state.mastery_score,
        "items": generated_items
    }

@app.post("/attempt", response_model=AttemptResponse)
async def submit_attempt(request: AttemptRequest, db: AsyncSession = Depends(get_db)):
    # 1. Load Session
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(request.session_id)
    
    # 2. Grade Attempt via Plugin
    grade_result = english_plugin.grade_attempt(request.item_id, request.attempt_text)
    
    # 3. Update Learner State
    # Logic: mastery = clamp(mastery*0.7 + score*0.3)
    # readiness = clamp(readiness*0.8 + (score - 0.5)*0.2)
    
    current_mastery = state.mastery_score
    current_readiness = state.readiness_score
    score = grade_result.score
    
    new_mastery = (current_mastery * 0.7) + (score * 0.3)
    new_mastery = max(0.0, min(1.0, new_mastery))
    
    new_readiness = (current_readiness * 0.8) + ((score - 0.5) * 0.2)
    new_readiness = max(0.0, min(1.0, new_readiness))
    
    state.mastery_score = new_mastery
    state.readiness_score = new_readiness
    
    # 4. Log Event
    attempt_event = Event(
        session_id=request.session_id,
        event_type="attempt",
        details={
            "item_id": request.item_id,
            "attempt": request.attempt_text,
            "score": score,
            "feedback": grade_result.feedback_short
        }
    )
    db.add(attempt_event)
    await db.commit()
    await db.refresh(state)
    
    return {
        "score": score,
        "feedback": grade_result.feedback_short,
        "mastery_score": state.mastery_score,
        "readiness_score": state.readiness_score
    }
