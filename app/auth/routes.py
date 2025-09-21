from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, User
from .security import verify_password, hash_password, verify_firebase_token

router = APIRouter()

# Example: Firebase login endpoint (verifies token)
@router.post("/firebase-auth")
async def firebase_authenticate(token: str, db: Session = Depends(get_db)):
    """Authenticate with Firebase ID token and ensure user exists in DB"""
    try:
        payload = verify_firebase_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    uid = payload.get("uid")
    email = payload.get("email")
    name = payload.get("name", "Unknown")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user:
        user = User(
            firebase_uid=uid,
            email=email,
            username=email.split("@")[0] if email else uid,
            full_name=name,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"message": "Authenticated via Firebase", "user": user.to_dict()}


# Example: Get current user (using Firebase token)
@router.get("/me")
async def get_me(token: str, db: Session = Depends(get_db)):
    payload = verify_firebase_token(token)
    uid = payload.get("uid")
    user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()
