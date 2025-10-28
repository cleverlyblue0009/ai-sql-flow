from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..database.models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.ANALYST
    timezone: str = "UTC"


class FirebaseAuthRequest(BaseModel):
    token: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None


class FirebaseAuthResponse(BaseModel):
    user: UserResponse
    message: str