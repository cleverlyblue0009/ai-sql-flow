from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from .security import verify_firebase_token
from ..database import get_db, User

async def get_current_user_from_token(token: str, db: Session = Depends(get_db)):
    """Extract user from Firebase token and ensure they exist in DB"""
    try:
        payload = verify_firebase_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase credentials",
        )

    uid = payload.get("uid")
    email = payload.get("email")
    name = payload.get("name", "Unknown")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    # Check if user exists in DB
    user = db.query(User).filter(User.firebase_uid == uid).first()

    # If not, create one
    if not user:
        user = User(
            firebase_uid=uid,
            email=email,
            username=email.split("@")[0] if email else uid,
            full_name=name,
            role="user",  # default role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

async def get_current_verified_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from Authorization header with Firebase token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    
    # Extract token from Bearer authorization header
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    
    return await get_current_user_from_token(token, db)
