"""
Authentication and Security Module
JWT-based authentication with role-based access control
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
from dotenv import load_dotenv
import bcrypt
import secrets
import hashlib
from enum import Enum

# auth is imported before main.py calls load_dotenv(), so load the .env here
# too (idempotent) to ensure SECRET_KEY is available at import time.
load_dotenv()

logger = logging.getLogger(__name__)


# Security Configuration
# Load the JWT signing key from the environment so it stays stable across
# restarts (a regenerated key would invalidate every issued token/session).
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Fail fast in production: signing with an ephemeral key silently breaks
    # all existing sessions on every restart. Allow a generated dev-only
    # fallback so local development still works without configuration.
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError(
            "SECRET_KEY environment variable is required in production. "
            "Set it to a stable, secret value, e.g. `python -c \"import secrets; "
            "print(secrets.token_urlsafe(32))\"`."
        )
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning(
        "SECRET_KEY is not set; using an ephemeral development key. "
        "Tokens will be invalidated on restart. Set SECRET_KEY in your .env."
    )

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# bcrypt operates on at most 72 bytes of input; longer passwords are truncated
# to keep hashing and verification consistent (standard bcrypt behavior).
BCRYPT_MAX_BYTES = 72

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


class User(BaseModel):
    """User model"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    disabled: bool = False
    created_at: datetime = datetime.utcnow()
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ or -)')
        if len(v) < 3 or len(v) > 30:
            raise ValueError('Username must be between 3 and 30 characters')
        return v.lower()


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str
    api_keys: List[str] = []
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


class UserCreate(BaseModel):
    """User registration model"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None


class APIKey(BaseModel):
    """API Key model"""
    key: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class PasswordHash:
    """Password hashing utilities (bcrypt, used directly)"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        pwd_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
        return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        pwd_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
        try:
            return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
        except (ValueError, TypeError):
            return False


class TokenManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            username: str = payload.get("sub")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            
            if username is None:
                return None
            
            return TokenData(
                username=username,
                role=UserRole(role) if role else None,
                exp=datetime.fromtimestamp(exp) if exp else None
            )
        except JWTError:
            return None


class APIKeyManager:
    """API Key management"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        # Format: tbk_<random_32_chars>
        random_part = secrets.token_urlsafe(32)
        return f"tbk_{random_part}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key


class UserDatabase:
    """In-memory user database (replace with real database in production)"""
    
    def __init__(self):
        self.users: Dict[str, UserInDB] = {}
        self.api_keys: Dict[str, str] = {}  # hashed_key -> username
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_user = UserInDB(
            username="admin",
            email="admin@tradebotcascade.com",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            hashed_password=PasswordHash.hash_password("Admin123!"),
            created_at=datetime.utcnow()
        )
        self.users["admin"] = admin_user
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        return self.users.get(username.lower())
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def create_user(self, user_create: UserCreate, role: UserRole = UserRole.VIEWER) -> UserInDB:
        """Create new user"""
        # Check if username exists
        if self.get_user(user_create.username):
            raise ValueError("Username already exists")
        
        # Check if email exists
        if self.get_user_by_email(user_create.email):
            raise ValueError("Email already exists")
        
        # Create user
        user = UserInDB(
            username=user_create.username.lower(),
            email=user_create.email,
            full_name=user_create.full_name,
            role=role,
            hashed_password=PasswordHash.hash_password(user_create.password),
            created_at=datetime.utcnow()
        )
        
        self.users[user.username] = user
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until.isoformat()}"
            )
        
        # Verify password
        if not PasswordHash.verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account locked due to too many failed login attempts"
                )
            
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        
        return user
    
    def create_api_key(self, username: str, key_name: str) -> str:
        """Create API key for user"""
        user = self.get_user(username)
        if not user:
            raise ValueError("User not found")
        
        # Generate API key
        api_key = APIKeyManager.generate_api_key()
        hashed_key = APIKeyManager.hash_api_key(api_key)
        
        # Store hashed key
        self.api_keys[hashed_key] = username
        user.api_keys.append(hashed_key)
        
        return api_key  # Return plain key only once
    
    def verify_api_key(self, api_key: str) -> Optional[UserInDB]:
        """Verify API key and return user"""
        hashed_key = APIKeyManager.hash_api_key(api_key)
        username = self.api_keys.get(hashed_key)
        
        if username:
            return self.get_user(username)
        
        return None


# Global user database instance
user_db = UserDatabase()


# Dependency functions
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserInDB:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = TokenManager.verify_token(token, token_type="access")
    
    if token_data is None or token_data.username is None:
        raise credentials_exception
    
    user = user_db.get_user(token_data.username)
    
    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[UserInDB]:
    """Get current user (optional, for public endpoints with optional auth)"""
    # Try JWT token first
    if credentials:
        try:
            return await get_current_user(credentials)
        except HTTPException:
            pass
    
    # Try API key
    if api_key:
        user = user_db.verify_api_key(api_key)
        if user and not user.disabled:
            return user
    
    return None


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


# Role hierarchy for permission checking
ROLE_HIERARCHY = {
    UserRole.VIEWER: 0,
    UserRole.TRADER: 1,
    UserRole.ADMIN: 2
}


# Role-specific dependencies
async def require_admin(current_user: UserInDB = Depends(get_current_active_user)):
    """Require ADMIN role"""
    if ROLE_HIERARCHY[current_user.role] < ROLE_HIERARCHY[UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: admin"
        )
    return current_user


async def require_trader(current_user: UserInDB = Depends(get_current_active_user)):
    """Require TRADER role or higher"""
    if ROLE_HIERARCHY[current_user.role] < ROLE_HIERARCHY[UserRole.TRADER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: trader"
        )
    return current_user


async def require_viewer(current_user: UserInDB = Depends(get_current_active_user)):
    """Require VIEWER role or higher (any authenticated user)"""
    return current_user
