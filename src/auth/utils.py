from datetime import datetime, timedelta, timezone
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
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, "SECRET_KEY") else "insecure_dev_secret_key_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# Password Hashing
# Fix for bcrypt > 4.0.0 and passlib compatibility
import bcrypt
# Add this monkeypatch for passlib compatibility with newer bcrypt
if not hasattr(bcrypt, '__about__'):
    class About:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = About()

# Use pbkdf2_sha256 which is more robust and has no 72-byte limit like bcrypt
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
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
        # In a real JWT, custom claims might be at root or under a namespace
        # Adjust based on how we create token. We pass `data` to create_access_token.
        # Assuming we put username in 'sub' and others as direct keys
        tenant_id: str = payload.get("tenant_id")
        
        if username is None:
             raise credentials_exception
             
        token_data = TokenData(
            username=username, 
            tenant_id=tenant_id, 
            role=payload.get("role"), 
            user_id=payload.get("user_id")
        )
    except JWTError:
        raise credentials_exception
        
    # If we have user_id, use that for faster lookup
    if token_data.user_id:
        stmt = select(User).where(User.id == token_data.user_id)
    else:
        # Fallback to email/tenant
        stmt = select(User).where(User.email == token_data.username)
        if token_data.tenant_id:
            stmt = stmt.where(User.tenant_id == token_data.tenant_id)
            
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return current_user
