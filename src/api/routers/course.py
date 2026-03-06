
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.db.models_course import Course
from src.db.models_prod import User
from src.auth.utils import get_current_user
from src.knowledge.engine import KnowledgeEngine
from src.core.plugin.registry import PluginRegistry
from src.core.plugin.generic_plugin import GenericPlugin

router = APIRouter(prefix="/courses", tags=["Courses"])
logger = logging.getLogger("eduvision.courses")

@router.post("/", status_code=201)
async def create_course(
    title: str, 
    description: str = None, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    course_id = str(uuid.uuid4())
    course = Course(
        id=course_id, 
        title=title, 
        description=description, 
        tenant_id=current_user.tenant_id,
        settings={"prompt_template": "default"}
    )
    db.add(course)
    await db.commit()
    
    # Register Plugin dynamically
    PluginRegistry.register(course_id, GenericPlugin(course_id))
    logger.info(f"Registered new plugin for course {course_id}")
    
    return {"course_id": course_id, "status": "created"}

@router.get("/")
async def list_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Filter by tenant
    stmt = select(Course).where(Course.tenant_id == current_user.tenant_id)
    res = await db.execute(stmt)
    courses = res.scalars().all()
    return [{"id": c.id, "title": c.title, "description": c.description} for c in courses]

async def process_upload_background(course_id: str, filename: str, content: bytes, db_session_factory):
    # We need a new session for background task
    async with db_session_factory() as db:
        engine = KnowledgeEngine(db)
        try:
            res = await engine.ingest_file(filename, content, course_id=course_id)
            logger.info(f"Ingested {filename} for course {course_id}: {res}")
        except Exception as e:
            logger.error(f"Failed to ingest {filename}: {e}")

@router.post("/{course_id}/upload")
async def upload_material(
    course_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    stmt = select(Course).where(Course.id == course_id, Course.tenant_id == current_user.tenant_id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    content = await file.read()
    
    # We need to pass a session factory to background task, or run it here (blocking for now for simplicity in MVP, or use small file)
    # Actually, for reliability in this demo, let's just await it. It's faster for small files.
    # In prod, use Celery/Redis.
    
    engine = KnowledgeEngine(db)
    result = await engine.ingest_file(file.filename, content, course_id=course_id)
    
    return {"status": "uploaded", "details": result}
