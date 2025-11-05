from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, User
from ..database.models import UserRole
from .schemas import FirebaseAuthRequest, FirebaseAuthResponse, UserResponse, FirebaseSignUpRequest
from .dependencies import get_current_verified_user
from .security import verify_firebase_token

router = APIRouter()


# ------------------------------
# Firebase Sign Up
# ------------------------------
@router.post("/signup", response_model=FirebaseAuthResponse)
async def signup(
    request: FirebaseSignUpRequest,
    db: Session = Depends(get_db)
):
    """Sign up a new user with Firebase token and additional details"""
    try:
        payload = verify_firebase_token(request.token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}",
        )

    uid = payload.get("uid")
    email = payload.get("email")

    if not uid or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.firebase_uid == uid).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists. Please login instead.",
        )

    # Check if email is already used
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user with provided details
    user = User(
        firebase_uid=uid,
        email=email,
        username=request.username or email.split("@")[0],
        full_name=request.full_name,
        role=UserRole.ANALYST,  # Default role for new users
        timezone=request.timezone or "UTC",
        is_verified=True  # Assume verified if using Firebase
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)

    return FirebaseAuthResponse(message="User registered successfully", user=user)


# ------------------------------
# Firebase Login
# ------------------------------
@router.post("/login", response_model=FirebaseAuthResponse)
async def login(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """Login existing user with Firebase ID token"""
    try:
        payload = verify_firebase_token(request.token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}",
        )

    uid = payload.get("uid")
    email = payload.get("email")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    # Find user by Firebase UID
    user = db.query(User).filter(User.firebase_uid == uid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sign up first.",
        )

    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return FirebaseAuthResponse(message="Login successful", user=user)


# ------------------------------
# Firebase Auto-Login/Register (Legacy endpoint)
# ------------------------------
@router.post("/firebase-auth", response_model=FirebaseAuthResponse)
async def firebase_authenticate(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """Authenticate with Firebase ID token and auto-create user if not exists (Legacy)"""
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
            role=UserRole.ANALYST,
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
