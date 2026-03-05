from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.session import get_db
from src.db.models_prod import User
from src.config import get_settings

settings = get_settings()

# Config
SECRET_KEY = getattr(settings, "SECRET_KEY", "insecure_dev_secret_key_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# Fix for bcrypt > 4.0.0 and passlib
import bcrypt
# Add this monkeypatch for passlib compatibility with newer bcrypt
if not hasattr(bcrypt, '__about__'):
    class About:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = About()

# Use 'django_pbkdf2_sha256' or similar if bcrypt issues persist, but sticking to bcrypt with workaround
# Or just handle the 72 byte limit if that's the only issue remaining
# The error "password cannot be longer than 72 bytes" is specific to bcrypt limitation.
# We can pre-hash or just truncate if acceptable (not ideal for prod but ok for smoke test)
# Better: Use 'pbkdf2_sha256' which is standard in passlib and has no length limit

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v2/auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        if username is None or tenant_id is None:
            raise credentials_exception
        token_data = TokenData(username=username, tenant_id=tenant_id, role=payload.get("role"), user_id=payload.get("user_id"))
    except JWTError:
        raise credentials_exception
        
    stmt = select(User).where(User.email == token_data.username, User.tenant_id == token_data.tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return current_user
