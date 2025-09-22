from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, User
from .schemas import FirebaseAuthRequest, FirebaseAuthResponse, UserResponse
from .dependencies import get_current_verified_user
from .security import verify_firebase_token

router = APIRouter()


# ------------------------------
# Firebase login / registration
# ------------------------------
@router.post("/firebase-auth", response_model=FirebaseAuthResponse)
async def firebase_authenticate(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """Authenticate with Firebase ID token and ensure user exists in DB"""
    try:
        payload = verify_firebase_token(request.token)
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

    return FirebaseAuthResponse(message="Authenticated via Firebase", user=user)


# ------------------------------
# Get current logged-in user
# ------------------------------
@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_verified_user)):
    """Get currently authenticated user"""
    return user


# ------------------------------
# Example of a protected route
# ------------------------------
@router.get("/protected", response_model=UserResponse)
async def protected_route(user: User = Depends(get_current_verified_user)):
    """This route requires Firebase auth"""
    return user
