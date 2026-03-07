import uuid
import asyncio
import time
import logging
import aiofiles
from typing import Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware

from src.db.session import get_db
from src.db.models import Session, Job
from src.db.models_prod import Tenant, User
from src.auth.utils import create_access_token, get_current_user, get_password_hash, verify_password, Token
from src.core.runtime.rate_limit import rate_limiter
from src.core.obs.metrics import metrics
from src.llm.providers.together_ai import TogetherProvider
from src.config import get_settings

# Core Engines
from src.core.engines.learner import LearnerEngine
from src.core.engines.pedagogy import PedagogyEngine
from src.core.engines.tutor import TutorEngine
from src.core.adaptive.error_taxonomy import ErrorTracker

# Plugin System
from src.core.plugin.registry import PluginRegistry
from src.plugins.default.plugin import DefaultPlugin
from src.core.plugin.generic_plugin import GenericPlugin
from src.api.routers import course
from src.db.models_course import Course

# Configuration
settings = get_settings()
logger = logging.getLogger("eduvision.core")

# LLM Factory
together_ai = TogetherProvider()
active_llm = together_ai # Default

# Engines
pedagogy_engine = PedagogyEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global active_llm
    if await together_ai.check_health():
        logger.info("Together AI is healthy. Using Primary LLM.")
        active_llm = together_ai
    else:
        logger.error("Together AI unavailable! System cannot function without LLM.")
        # We might want to raise an exception here or just log critical error
        # raising error would prevent app startup which is safer for production
        raise RuntimeError("Critical: LLM Provider Unavailable")
        
    # Register Default Plugin
    PluginRegistry.register("default", DefaultPlugin())
    
    from src.db.session import AsyncSessionLocal, engine
    from src.db.base import Base

    # Create tables (auto-migration for dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load Courses from DB and register their plugins
    # Note: Using get_db() directly inside context manager is tricky because it yields.
    # We'll create a new session manually for startup.
    from src.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        stmt = select(Course).where(Course.is_active == 1)
        res = await session.execute(stmt)
        courses = res.scalars().all()
        for c in courses:
            PluginRegistry.register(str(c.id), GenericPlugin(str(c.id)))
            logger.info(f"Registered plugin for course: {c.title} ({c.id})")
            
    logger.info("Startup complete. Plugins loaded.")
    
    yield
    
    # Shutdown logic (if any)
    logger.info("Shutting down...")

# Init App
app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.VERSION, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Include Routers
app.include_router(course.router, prefix=settings.API_V1_STR)

# CORS Middleware (Driven by Config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Endpoints ---

@app.post(f"{settings.API_V1_STR}/auth/register", status_code=201)
async def register(
    email: str, password: str, tenant_name: str, role: str = "student", 
    db: AsyncSession = Depends(get_db)
):
    # Auto-create tenant logic (Simplified for demo)
    stmt = select(Tenant).where(Tenant.name == tenant_name)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    
    if not tenant:
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(id=tenant_id, name=tenant_name)
        db.add(tenant)
        await db.flush()
    
    stmt_u = select(User).where(User.email == email, User.tenant_id == tenant.id)
    res_u = await db.execute(stmt_u)
    if res_u.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered in this tenant")
        
    hashed = get_password_hash(password)
    user = User(tenant_id=tenant.id, email=email, password_hash=hashed, role=role)
    db.add(user)
    await db.commit()
    return {"status": "created", "email": email, "tenant": tenant.name}

@app.post(f"{settings.API_V1_STR}/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == form_data.username)
    res = await db.execute(stmt)
    users = res.scalars().all()
    
    if not users:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    user = users[0] 
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id, "role": user.role, "user_id": str(user.id)}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get(f"{settings.API_V1_STR}/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "role": current_user.role, "tenant_id": current_user.tenant_id}

# --- Core Features ---

@app.post(f"{settings.API_V1_STR}/sessions")
async def create_session(
    course_id: str = "default",
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
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
    
    metrics.inc("sessions_created", {"tenant": str(current_user.tenant_id)})
    return {"session_id": session_id}

@app.post(f"{settings.API_V1_STR}/chat")
async def chat(
    session_id: str, 
    message: str, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await rate_limiter.check(f"user:{current_user.id}")
    start_time = time.time()
    
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
    
    # 3. Content Retrieval
    plugin = PluginRegistry.get(course_id) or PluginRegistry.get("default")
    if not plugin:
         raise HTTPException(status_code=500, detail="No active plugin found")
         
    content_item = await plugin.get_content(plan["next_difficulty"], context={"db": db})
    
    # 4. Tutor Engine Response (Modernized)
    tutor_engine = TutorEngine(llm_client=active_llm)
    
    # Context data for Tutor Engine
    context_data = {
        "strategy": plan["chosen_action"],
        "mastery_score": state.mastery_score
    }
    
    # History Mock (Ideally fetch from DB)
    history = [] 
    
    try:
        reply = await tutor_engine.generate_reply(
            user_message=message,
            history=history,
            context_data=context_data,
            current_content=content_item
        )
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        reply = "I'm having trouble connecting to my brain. Let's try again."
    
    metrics.observe("chat_latency", (time.time() - start_time) * 1000, {"model": active_llm.__class__.__name__})
    
    return {
        "reply": reply, 
        "next_step": plan["chosen_action"],
        "content_id": content_item.content_id
    }

@app.post(f"{settings.API_V1_STR}/attempt")
async def submit_attempt(
    session_id: str,
    item_id: str,
    attempt_text: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=403, detail="Session access denied")

    course_id = session.course_id or "default"
    plugin = PluginRegistry.get(course_id)
    if not plugin:
         plugin = GenericPlugin(course_id)
         PluginRegistry.register(course_id, plugin)
         
    # 1. Assessment
    grade_result = await plugin.grade_attempt(item_id, attempt_text, context={"db": db})
    
    # 2. Learner Update
    learner_engine = LearnerEngine(db)
    state = await learner_engine.get_or_create_state(session_id)
    
    assessment_data = {
        "score": grade_result.score,
        "skill_tag": getattr(grade_result, "skill_tag", "general_topic"),
        "item_id": item_id
    }
    
    update_summary = await learner_engine.update_state(state, assessment_data)
    
    # 3. Error Tracking
    if grade_result.errors:
        error_tracker = ErrorTracker(db)
        error_codes = [e if isinstance(e, str) else str(e) for e in grade_result.errors]
        await error_tracker.record_errors(session_id, assessment_data["skill_tag"], error_codes)

    metrics.inc("attempts_submitted", {"tenant": str(current_user.tenant_id), "course": course_id})

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

@app.post(f"{settings.API_V1_STR}/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None, # kept for signature but unused in body to respect original logic
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    path = f"tmp_media/{file.filename}"
    
    # Async File Write using aiofiles
    async with aiofiles.open(path, "wb") as f:
        content = await file.read()
        await f.write(content)
        
    job = Job(id=job_id, tenant_id=current_user.tenant_id, user_id=current_user.id, type="BUILD_INDEX", status="pending")
    db.add(job)
    await db.commit()
    
    return {"job_id": job_id, "status": "queued"}

@app.get(f"{settings.API_V1_STR}/jobs/{{job_id}}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
