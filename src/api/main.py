import uuid
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.db.models import Session, Job
from src.db.models_prod import Tenant, User
from src.auth.utils import create_access_token, get_current_user, get_password_hash, verify_password, Token
from src.core.runtime.rate_limit import rate_limiter
from src.core.obs.metrics import metrics
from src.llm.providers.ollama import OllamaProvider
from src.llm.providers.mock import MockProvider
from fastapi.middleware.cors import CORSMiddleware

# Core Engines
from src.core.engines.learner import LearnerEngine
from src.core.engines.pedagogy import PedagogyEngine
from src.core.engines.assessment import AssessmentEngine
from src.core.engines.tutor import TutorEngine
from src.knowledge.engine import KnowledgeEngine
from src.core.adaptive.error_taxonomy import ErrorTracker
from src.core.runtime.cache import response_cache

# Plugin System
from src.core.plugin.registry import PluginRegistry
from src.plugins.default.plugin import DefaultPlugin
from src.core.plugin.generic_plugin import GenericPlugin
from src.api.routers import course
from src.db.models_course import Course

# Init Components
app = FastAPI(title="EduVision Pro API (Core)", version="2.0.0")

# Include Routers
app.include_router(course.router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("eduvision.core")

# LLM Factory (Fallback)
ollama = OllamaProvider()
mock_llm = MockProvider()
active_llm = ollama

# Engines
pedagogy_engine = PedagogyEngine()
# Assessment Engine needs a plugin instance, but we want it dynamic.
# We will instantiate it inside endpoints or make it plugin-aware.
# For now, we use a simple wrapper or instantiate on the fly.

@app.on_event("startup")
async def startup():
    global active_llm
    if await ollama.check_health():
        logger.info("Ollama is healthy. Using Primary LLM.")
        active_llm = ollama
    else:
        logger.warning("Ollama unavailable. Switching to Mock Provider.")
        active_llm = mock_llm
        
    # Register Default Plugin
    PluginRegistry.register("default", DefaultPlugin())
    
    # Load Courses from DB and register their plugins
    async for session in get_db():
        stmt = select(Course).where(Course.is_active == 1)
        res = await session.execute(stmt)
        courses = res.scalars().all()
        for c in courses:
            PluginRegistry.register(c.id, GenericPlugin(c.id))
            logger.info(f"Registered plugin for course: {c.title} ({c.id})")
        break # We only need one session from the generator
        
    logger.info("Startup complete. Plugins loaded.")

# --- Auth Endpoints ---

@app.post("/auth/register", status_code=201)
async def register(
    email: str, password: str, tenant_name: str, role: str = "student", 
    db: AsyncSession = Depends(get_db)
):
    # Simplified registration (auto-create tenant if needed)
    # In prod, tenant creation is separate superadmin step
    stmt = select(Tenant).where(Tenant.name == tenant_name)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    
    if not tenant:
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(id=tenant_id, name=tenant_name)
        db.add(tenant)
        await db.flush() # get id
    
    stmt_u = select(User).where(User.email == email, User.tenant_id == tenant.id)
    res_u = await db.execute(stmt_u)
    if res_u.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered in this tenant")
        
    hashed = get_password_hash(password)
    user = User(tenant_id=tenant.id, email=email, password_hash=hashed, role=role)
    db.add(user)
    await db.commit()
    return {"status": "created", "email": email, "tenant": tenant.name}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Username format expected: email@tenant_name (simple convention for multi-tenant login)
    # OR send tenant_id in header? simpler: username=email, we assume tenant from context or just find unique email
    # Let's simplify: login requires email and we find user. If duplicate emails across tenants, fail (demo limitation)
    
    stmt = select(User).where(User.email == form_data.username)
    res = await db.execute(stmt)
    users = res.scalars().all()
    
    if not users:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Just pick first for demo (assuming unique email globally for now or single tenant usage)
    user = users[0] 
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id, "role": user.role, "user_id": user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "role": current_user.role, "tenant_id": current_user.tenant_id}

# --- Core Features with Auth & Observability ---

@app.post("/sessions")
async def create_session(
    course_id: str = "default",
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Verify course exists if not default
    if course_id != "default":
        stmt = select(Course).where(Course.id == course_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
             raise HTTPException(status_code=404, detail="Course not found")

    session_id = str(uuid.uuid4())
    session = Session(id=session_id, user_id=current_user.id, tenant_id=current_user.tenant_id, course_id=course_id)
    db.add(session)
    await db.commit()
    
    learner_engine = LearnerEngine(db)
    await learner_engine.get_or_create_state(session_id)
    
    metrics.inc("sessions_created", {"tenant": current_user.tenant_id})
    return {"session_id": session_id}

@app.post("/chat")
async def chat(
    session_id: str, 
    message: str, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Rate Limit
    await rate_limiter.check(f"user:{current_user.id}")
    
    start_time = time.time()
    
    # Verify ownership
    stmt = select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=403, detail="Session access denied")

    # 1. Learner State
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(session_id)
    
    # 2. Pedagogy Plan
    error_tracker = ErrorTracker(db)
    top_errors = await error_tracker.get_top_errors(session_id)
    
    course_id = session.course_id or "default"
    plan = await pedagogy_engine.determine_next_step_async(
        db, session_id, state, recent_errors=top_errors, course_id=course_id
    )
    
    # 3. Content from Plugin (Dynamic)
    course_id = session.course_id or "default"
    plugin = PluginRegistry.get(course_id)
    if not plugin:
         # Fallback to default if course plugin missing (e.g. after restart without DB sync)
         plugin = PluginRegistry.get("default")
         
    if not plugin:
         raise HTTPException(status_code=500, detail="No active plugin found")
         
    # Pass DB context for GenericPlugin
    content_item = await plugin.get_content(plan["next_difficulty"], context={"db": db})
    
    # 4. Generate AI Tutor Reply
    # We combine the content item with the LLM to generate a pedagogical response
    # This logic was partially in TutorEngine. Let's use TutorEngine if possible.
    tutor_engine = TutorEngine(llm_client=active_llm) # Use active_llm adapter
    
    # For now, simple direct generation
    system_prompt = f"""You are an AI Tutor. 
    Current Strategy: {plan['chosen_action']}
    Content: {content_item.text}
    User Mastery: {state.mastery_score}
    """
    
    try:
        reply = await active_llm.generate_chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ])
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        reply = "I'm having trouble connecting to my brain. Let's try again."
    
    metrics.observe("chat_latency", (time.time() - start_time) * 1000, {"model": active_llm.__class__.__name__})
    
    return {
        "reply": reply, 
        "next_step": plan["chosen_action"],
        "content_id": content_item.content_id
    }

@app.post("/attempt")
async def submit_attempt(
    session_id: str,
    item_id: str,
    attempt_text: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    stmt = select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=403, detail="Session access denied")

    # Get Plugin for Grading
    course_id = session.course_id or "default"
    plugin = PluginRegistry.get(course_id)
    if not plugin:
         # Try to register on fly if not found (e.g. after restart)
         plugin = GenericPlugin(course_id)
         PluginRegistry.register(course_id, plugin)
         
    # 1. Grade Attempt (Assessment Engine)
    grade_result = await plugin.grade_attempt(item_id, attempt_text, context={"db": db})
    
    # 2. Update Learner State (Learner Engine)
    # This now triggers BKT (Skill Mastery) and SRS (Forgetting Curve) updates
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(session_id)
    
    # Prepare assessment result for engine
    assessment_data = {
        "score": grade_result.score,
        "skill_tag": getattr(grade_result, "skill_tag", "general_topic"), # Plugin should ideally return skill tag
        "item_id": item_id
    }
    
    update_summary = await learner_engine.update_state(state, assessment_data)
    
    # 3. Record Errors (for Pedagogy)
    if grade_result.errors:
        error_tracker = ErrorTracker(db)
        # We assume grade_result.errors contains codes like ["WRONG_CHOICE"]
        # If it returns objects, we extract codes. 
        # For GenericPlugin currently it returns empty list or strings.
        # Let's handle list of strings.
        error_codes = [e if isinstance(e, str) else str(e) for e in grade_result.errors]
        await error_tracker.record_errors(session_id, assessment_data["skill_tag"], error_codes)

    metrics.inc("attempts_submitted", {"tenant": current_user.tenant_id, "course": course_id})

    return {
        "score": grade_result.score,
        "feedback": grade_result.feedback_short,
        "mastery_update": {
            "new_mastery": update_summary["mastery_score"],
            "skill_mastery": update_summary["skill_mastery"],
            "next_review": update_summary["next_review"]
        }
    }

# --- Background Jobs ---

async def process_knowledge_upload(job_id: str, file_path: str, db: AsyncSession):
    # Simulate long running task
    logger.info(f"Starting job {job_id}")
    await asyncio.sleep(2) # Chunking...
    
    # Update progress
    logger.info(f"Job {job_id} completed processing {file_path}")

@app.post("/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    # Save file temp
    path = f"tmp_media/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
        
    job = Job(id=job_id, tenant_id=current_user.tenant_id, user_id=current_user.id, type="BUILD_INDEX", status="pending")
    db.add(job)
    await db.commit()
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Job).where(Job.id == job_id, Job.tenant_id == current_user.tenant_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.id, "status": job.status, "progress": job.progress}

@app.get("/metrics")
async def get_metrics():
    return metrics.get_prometheus_text()
