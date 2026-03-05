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

# Init Components
app = FastAPI(title="EduVision Pro API (v2)", version="2.0.0")
logger = logging.getLogger("eduvision.v2")

# LLM Factory (Fallback)
ollama = OllamaProvider()
mock_llm = MockProvider()
active_llm = ollama

@app.on_event("startup")
async def startup():
    global active_llm
    if await ollama.check_health():
        logger.info("Ollama is healthy. Using Primary LLM.")
        active_llm = ollama
    else:
        logger.warning("Ollama unavailable. Switching to Mock Provider.")
        active_llm = mock_llm

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
async def create_session_v2(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    session_id = str(uuid.uuid4())
    session = Session(id=session_id, user_id=current_user.id, tenant_id=current_user.tenant_id)
    db.add(session)
    await db.commit()
    metrics.inc("sessions_created", {"tenant": current_user.tenant_id})
    return {"session_id": session_id}

@app.post("/chat")
async def chat_v2(
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
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Session access denied")

    # Use LLM Provider
    try:
        reply = await active_llm.generate_chat([{"role": "user", "content": message}])
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        # Runtime fallback if primary failed during request
        if active_llm != mock_llm:
             reply = await mock_llm.generate_chat([{"role": "user", "content": message}])
        else:
             reply = "System Error: Unable to generate response."
    
    metrics.observe("chat_latency", (time.time() - start_time) * 1000, {"model": active_llm.__class__.__name__})
    
    return {"reply": reply, "provider": active_llm.__class__.__name__}

# --- Background Jobs ---

async def process_knowledge_upload(job_id: str, file_path: str, db: AsyncSession):
    # Simulate long running task
    logger.info(f"Starting job {job_id}")
    await asyncio.sleep(2) # Chunking...
    
    # Update progress
    # Note: separate DB session management needed for bg tasks usually
    # For simplicity here we just log
    logger.info(f"Job {job_id} completed processing {file_path}")

@app.post("/knowledge/upload")
async def upload_knowledge_v2(
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
    
    # Trigger BG Task (Mock)
    # background_tasks.add_task(process_knowledge_upload, job_id, path, db) 
    
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
