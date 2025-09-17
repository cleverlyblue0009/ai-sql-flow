from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db, User, UserRole
from .security import verify_firebase_token


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from Firebase token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify Firebase token
        decoded_token = verify_firebase_token(credentials.credentials)
        if decoded_token is None:
            raise credentials_exception
        
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        
        if not firebase_uid or not email:
            raise credentials_exception
        
        # Get user from database by email or create if doesn't exist
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            # Create user from Firebase token info
            user = User(
                email=email,
                username=decoded_token.get("name", email.split("@")[0]),
                full_name=decoded_token.get("name", ""),
                hashed_password="firebase_auth",  # Placeholder since Firebase handles auth
                firebase_uid=firebase_uid,
                is_active=True,
                is_verified=decoded_token.get("email_verified", False)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update Firebase UID if not set
            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
                db.commit()
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    except Exception as e:
        print(f"Authentication error: {e}")
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    async def role_checker(current_user: User = Depends(get_current_verified_user)) -> User:
        # Role hierarchy: admin > engineer > analyst
        role_hierarchy = {
            UserRole.ANALYST: 0,
            UserRole.ENGINEER: 1,
            UserRole.ADMIN: 2
        }
        
        user_level = role_hierarchy.get(current_user.role, -1)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        
        return current_user
    
    return role_checker


# Specific role dependencies
require_admin = require_role(UserRole.ADMIN)
require_engineer = require_role(UserRole.ENGINEER)
require_analyst = require_role(UserRole.ANALYST)


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    try:
        # Try to get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        decoded_token = verify_firebase_token(token)
        if decoded_token is None:
            return None
        
        email = decoded_token.get("email")
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        return user
    
    except Exception:
        return None


async def get_current_user_from_token(token: str, db: Session) -> User:
    """Get current user from Firebase token (for WebSocket authentication)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    try:
        # Verify Firebase token
        decoded_token = verify_firebase_token(token)
        if decoded_token is None:
            raise credentials_exception
        
        email = decoded_token.get("email")
        if email is None:
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
    
    except Exception:
        raise credentials_exception


class RateLimiter:
    """Rate limiting dependency"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def __call__(self, request: Request, current_user: Optional[User] = Depends(get_optional_user)):
        # Implementation would use Redis for distributed rate limiting
        # For now, this is a placeholder
        return True