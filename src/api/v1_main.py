# Renaming current main.py to v1_main.py (Legacy Dev)
import uuid
import os
import json
import asyncio
import time
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
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
from src.plugins.english.lesson_builder import LessonBuilder
from src.llm.ollama_client import OllamaClient

# Voice & Runtime
from src.voice.asr import ASRService
from src.voice.tts import TTSService
from src.voice.utils import save_upload_file, get_media_url
from src.voice.models import ASRResponse, TTSRequest
from src.core.runtime.cache import response_cache

# Knowledge
from src.knowledge.engine import KnowledgeEngine
from src.knowledge.models import SourceResponse, SearchResult, GraphResponse, LessonFromBookRequest

# Adaptive
from src.core.adaptive.bkt import BKTModel
from src.core.adaptive.srs import SRSScheduler
from src.core.adaptive.error_taxonomy import ErrorTracker
from src.core.analytics.logger import AnalyticsLogger

# Diagnostics
from src.core.diagnostics.engine import CognitiveDiagnosticsEngine
from src.core.diagnostics.concept_graph import ConceptGraph
from src.core.optimizer.bandit import BanditOptimizer

# Initialize Components
app = FastAPI(title="Adaptive Learning Core API (v1 Dev)")
ollama_client = OllamaClient()
english_plugin = EnglishPlugin()
lesson_builder = LessonBuilder()

# Engines
assessment_engine = AssessmentEngine(plugin=english_plugin)
pedagogy_engine = PedagogyEngine()
tutor_engine = TutorEngine(llm_client=ollama_client)

# Voice Services
asr_service = ASRService()
tts_service = TTSService()

# Mount static media
if not os.path.exists("tmp_media"):
    os.makedirs("tmp_media")
app.mount("/media", StaticFiles(directory="tmp_media"), name="media")

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
    error_codes: List[str] = []

class ConceptEdgeRequest(BaseModel):
    from_skill_tag: str
    to_skill_tag: str
    weight: float

@app.on_event("startup")
async def on_startup():
    await init_models()
    # Check LLM connection in background
    asyncio.create_task(ollama_client.check_connection())

@app.post("/sessions", response_model=CreateSessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    new_session = Session(id=session_id)
    db.add(new_session)
    await db.commit()
    
    learner_engine = LearnerEngine(db)
    await learner_engine.get_or_create_state(session_id)
    
    # Log Session Start
    analytics = AnalyticsLogger(db)
    await analytics.log_event(session_id, "SESSION_START", {"timestamp": time.time()})
    
    return {"session_id": session_id}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    return await _process_chat(request.session_id, request.message, db)

async def _process_chat(session_id: str, message: str, db: AsyncSession):
    # 1. Load Session and State
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(session_id)
    
    # Adaptive: Fetch Skills & Errors for Planning
    error_tracker = ErrorTracker(db)
    top_errors = await error_tracker.get_top_errors(session_id)
    
    # 2. Determine Next Step (Pedagogy)
    # Using new async method
    plan = await pedagogy_engine.determine_next_step_async(
        db, session_id, state, recent_errors=top_errors
    )
    
    # 3. Get Content from Plugin
    content_item = english_plugin.get_content(plan["next_difficulty"])
    
    # 4. Generate Learning Items (Exercises) - with Cache
    cache_key = f"{content_item.content_id}:{plan['next_difficulty']}"
    generated_items = response_cache.get(content_item.content_id, plan["next_difficulty"])
    
    if not generated_items:
        gen_context = {
            "content_id": content_item.content_id,
            "remediation_plan": plan["remediation_plan"],
            "chosen_action": plan["chosen_action"] # For bandit/diagnostics influence
        }
        generated_items = english_plugin.generate_items(gen_context)
        response_cache.set(content_item.content_id, plan["next_difficulty"], generated_items)
    
    # 5. Generate Tutor Response
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_objs = history_result.scalars().all()
    history = [{"role": msg.role, "content": msg.content} for msg in reversed(history_objs)]
    
    # Apply Cost Control
    optimized_ctx = pedagogy_engine.prepare_context(content_item.text, history)
    
    context_data = {
        "mastery_score": state.mastery_score,
        "strategy": plan["strategy"],
        "remediation": plan["remediation_plan"],
        "why": plan["why_this_plan"]
    }
    
    reply = await tutor_engine.generate_reply(
        user_message=message,
        history=optimized_ctx["history"],
        context_data=context_data,
        current_content=content_item
    )
    
    # 6. Save Messages & Log
    user_msg = Message(session_id=session_id, role="user", content=message)
    bot_msg = Message(session_id=session_id, role="assistant", content=reply)
    db.add(user_msg)
    db.add(bot_msg)
    await db.commit()
    
    analytics = AnalyticsLogger(db)
    await analytics.log_event(session_id, "CHAT", {
        "length": len(message), 
        "variant": plan.get("variant"),
        "chosen_action": plan.get("chosen_action")
    })
    
    return {
        "reply": reply,
        "next_step_plan": plan,
        "mastery_score": state.mastery_score,
        "items": generated_items
    }

@app.get("/chat/stream")
async def stream_chat(session_id: str, message: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(session_id)
    
    # Adaptive Context
    error_tracker = ErrorTracker(db)
    top_errors = await error_tracker.get_top_errors(session_id)
    plan = await pedagogy_engine.determine_next_step_async(db, session_id, state, recent_errors=top_errors)
    
    content_item = english_plugin.get_content(plan["next_difficulty"])
    
    history_result = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(10))
    history = [{"role": m.role, "content": m.content} for m in reversed(history_result.scalars().all())]
    optimized_ctx = pedagogy_engine.prepare_context(content_item.text, history)
    
    system_prompt = tutor_engine._construct_system_prompt(
        {"mastery_score": state.mastery_score, "strategy": plan["strategy"]}, 
        content_item
    )
    
    messages = [{"role": "system", "content": system_prompt}] + optimized_ctx["history"] + [{"role": "user", "content": message}]

    async def event_generator():
        full_reply = ""
        async for chunk in ollama_client.stream_chat_completion(messages):
            full_reply += chunk
            yield f"event: token\ndata: {chunk}\n\n"
            
        gen_context = {"content_id": content_item.content_id, "remediation_plan": plan["remediation_plan"], "chosen_action": plan["chosen_action"]}
        items = english_plugin.generate_items(gen_context)
        
        final_data = {
            "reply_text": full_reply,
            "items": items,
            "next_step_plan": plan
        }
        yield f"event: done\ndata: {json.dumps(final_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/voice/chat")
async def voice_chat(
    session_id: str, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    file_path = save_upload_file(file)
    text = asr_service.transcribe(file_path)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
    chat_response = await _process_chat(session_id, text, db)
    wav_filename = tts_service.generate_audio(chat_response["reply"])
    audio_url = get_media_url(wav_filename, request)
    
    return {
        "asr_text": text,
        "reply_text": chat_response["reply"],
        "next_step_plan": chat_response["next_step_plan"],
        "items": chat_response["items"],
        "audio_url": audio_url
    }

@app.post("/voice/asr", response_model=ASRResponse)
async def voice_asr(file: UploadFile = File(...)):
    file_path = save_upload_file(file)
    text = asr_service.transcribe(file_path)
    if not text:
        raise HTTPException(status_code=400, detail="ASR failed")
    return {"text": text, "duration": 0.0}

@app.post("/voice/tts")
async def voice_tts(request: TTSRequest, req: Request):
    wav_filename = tts_service.generate_audio(request.text)
    audio_url = get_media_url(wav_filename, req)
    
    file_path = os.path.join("tmp_media", wav_filename)
    
    def iterfile():
        with open(file_path, "rb") as f:
            yield from f
            
    return StreamingResponse(iterfile(), media_type="audio/wav")

@app.post("/attempt", response_model=AttemptResponse)
async def submit_attempt(request: AttemptRequest, db: AsyncSession = Depends(get_db)):
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(request.session_id)
    grade_result = english_plugin.grade_attempt(request.item_id, request.attempt_text)
    
    score = grade_result.score
    
    # Get active item to know skill_tag and item_type
    # Ideally should be passed or stored better, but using cache for now
    active_item = english_plugin.active_items.get(request.item_id)
    skill_tag = "general_english" # Default
    item_type = "mixed" # Default
    difficulty = 1 # Default
    
    if active_item:
        # Assuming metadata has skill info or we infer
        # For now mock inference
        skill_tag = "general_english" 
        item_type = active_item.type
        difficulty = int(active_item.difficulty * 5)
    
    # 1. Update BKT (Skill State)
    bkt = BKTModel(db)
    new_mastery = await bkt.update_skill_state(request.session_id, skill_tag, score > 0.7)
    
    # 2. Update SRS (Schedule)
    srs = SRSScheduler(db)
    await srs.schedule_update(request.session_id, skill_tag, score)
    
    # 3. Track Errors
    error_tracker = ErrorTracker(db)
    if grade_result.error_codes:
        await error_tracker.record_errors(request.session_id, skill_tag, grade_result.error_codes)
    
    # 4. Cognitive Diagnostics (IRT + Propagation)
    diag_engine = CognitiveDiagnosticsEngine(db)
    await diag_engine.update_diagnostics(request.session_id, skill_tag, item_type, score)
    
    # 5. Bandit Update (Reward)
    bandit = BanditOptimizer(db)
    # Reward: score - penalty
    reward = score
    if grade_result.error_codes:
        reward -= 0.2 # Penalty for errors
    await bandit.update_reward(skill_tag, item_type, difficulty, reward)
    
    # 6. Update Overall State
    current_readiness = state.readiness_score
    new_readiness = (current_readiness * 0.8) + ((score - 0.5) * 0.2)
    new_readiness = max(0.0, min(1.0, new_readiness))
    
    state.mastery_score = new_mastery 
    state.readiness_score = new_readiness
    
    # 7. Log Event
    analytics = AnalyticsLogger(db)
    await analytics.log_event(request.session_id, "ATTEMPT", {
        "item_id": request.item_id,
        "score": score,
        "errors": grade_result.error_codes,
        "diagnostics_updated": True
    })
    
    attempt_event = Event(
        session_id=request.session_id,
        event_type="attempt",
        details={
            "item_id": request.item_id,
            "attempt": request.attempt_text,
            "score": score,
            "feedback": grade_result.feedback_short,
            "errors": grade_result.error_codes
        }
    )
    db.add(attempt_event)
    await db.commit()
    await db.refresh(state)
    
    return {
        "score": score,
        "feedback": grade_result.feedback_short,
        "mastery_score": state.mastery_score,
        "readiness_score": state.readiness_score,
        "error_codes": grade_result.error_codes
    }

# --- Knowledge Engine Endpoints ---

@app.post("/knowledge/upload", response_model=SourceResponse)
async def upload_knowledge(
    file: UploadFile = File(...),
    source_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    engine = KnowledgeEngine(db)
    content = await file.read()
    result = await engine.ingest_file(file.filename, content, source_id)
    return result

@app.get("/knowledge/search", response_model=List[SearchResult])
async def search_knowledge(
    source_id: str,
    q: str,
    k: int = 5,
    db: AsyncSession = Depends(get_db)
):
    engine = KnowledgeEngine(db)
    results = await engine.search(source_id, q, k)
    return results

@app.get("/knowledge/graph", response_model=GraphResponse)
async def get_knowledge_graph(
    source_id: str,
    db: AsyncSession = Depends(get_db)
):
    engine = KnowledgeEngine(db)
    return await engine.get_graph(source_id)

@app.post("/knowledge/lesson")
async def generate_lesson_from_knowledge(
    request: LessonFromBookRequest,
    db: AsyncSession = Depends(get_db)
):
    engine = KnowledgeEngine(db)
    chunks = await engine.search(request.source_id, request.focus if request.focus else "main concepts", k=6)
    lesson_model = lesson_builder.build_lesson_from_chunks(chunks, request.level)
    gen_items = english_plugin.generator.generate_items(lesson_model, count=3)
    for item in gen_items:
        english_plugin.active_items[item.id] = item
    return {
        "lesson": lesson_model.model_dump(),
        "items": [item.model_dump() for item in gen_items]
    }

# --- Adaptive, Analytics & Diagnostics Endpoints ---

@app.get("/learner/state")
async def get_learner_state_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(session_id)
    
    bkt = BKTModel(db)
    srs = SRSScheduler(db)
    error_tracker = ErrorTracker(db)
    
    skill_state = await bkt.get_skill_state(session_id, "general_english")
    due_skills = await srs.get_due_skills(session_id)
    top_errors = await error_tracker.get_top_errors(session_id)
    
    return {
        "mastery_overall": state.mastery_score,
        "readiness": state.readiness_score,
        "skills": [{
            "skill_tag": "general_english",
            "p_mastery": skill_state["p_mastery"] if skill_state else 0.1,
            "due": "general_english" in due_skills
        }],
        "recent_errors": top_errors
    }

@app.get("/analytics/summary")
async def get_analytics_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Event).where(Event.session_id == session_id)
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    attempts = [e for e in events if e.event_type == "attempt"]
    avg_score = sum([e.details.get("score", 0) for e in attempts]) / len(attempts) if attempts else 0.0
    
    return {
        "attempts_count": len(attempts),
        "avg_score": avg_score,
        "last_active_at": events[-1].created_at if events else None
    }

@app.get("/diagnostics/report")
async def get_diagnostics_report(session_id: str, db: AsyncSession = Depends(get_db)):
    engine = CognitiveDiagnosticsEngine(db)
    return await engine.get_report(session_id)

@app.post("/concept-graph/edge")
async def add_concept_edge(request: ConceptEdgeRequest, db: AsyncSession = Depends(get_db)):
    graph = ConceptGraph(db)
    await graph.upsert_edge(request.from_skill_tag, request.to_skill_tag, request.weight)
    return {"status": "ok"}

@app.get("/concept-graph")
async def get_concept_graph(db: AsyncSession = Depends(get_db)):
    graph = ConceptGraph(db)
    nodes = await graph.get_all_nodes()
    # Edges not fully exposed in list for simplicity, but nodes help
    return {"nodes": nodes, "edge_count": "Use specific queries"}
