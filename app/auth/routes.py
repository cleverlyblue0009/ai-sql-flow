from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any

from ..database import get_db, User, AuditLog, redis_client
from .schemas import (
    UserCreate, UserLogin, UserResponse, UserUpdate, FirebaseAuthRequest, FirebaseAuthResponse,
    PasswordReset, PasswordResetConfirm, PasswordChange, EmailVerification,
    OAuth2AuthRequest
)
from .security import (
    verify_password, get_password_hash, verify_firebase_token, create_custom_token,
    generate_reset_token, generate_verification_token
)
from .dependencies import (
    get_current_user, get_current_active_user, get_current_verified_user,
    require_admin, RateLimiter
)
from ..utils.email import send_verification_email, send_password_reset_email
from ..utils.audit import log_user_action


router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiters
login_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
register_limiter = RateLimiter(max_requests=3, window_seconds=3600)  # 3 registrations per hour


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: Any = Depends(register_limiter)
):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        timezone=user_data.timezone
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate verification token
    verification_token = generate_verification_token()
    redis_client.setex(
        f"verification:{verification_token}",
        timedelta(hours=24),
        str(db_user.id)
    )
    
    # Send verification email
    await send_verification_email(db_user.email, verification_token)
    
    # Log action
    await log_user_action(
        db=db,
        user_id=db_user.id,
        action="user_register",
        resource_type="user",
        resource_id=str(db_user.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        success=True
    )
    
    return db_user


@router.post("/firebase-auth")
async def firebase_auth(
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user with Firebase token"""
    try:
        body = await request.json()
        firebase_token = body.get("token")
        
        if not firebase_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Firebase token is required"
            )
        
        # Verify Firebase token
        decoded_token = verify_firebase_token(firebase_token)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )
        
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        name = decoded_token.get("name", "")
        email_verified = decoded_token.get("email_verified", False)
        
        if not firebase_uid or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token data"
            )
        
        # Get or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Create new user
            user = User(
                email=email,
                username=name or email.split("@")[0],
                full_name=name,
                hashed_password="firebase_auth",
                firebase_uid=firebase_uid,
                is_active=True,
                is_verified=email_verified,
                role=UserRole.ANALYST
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update Firebase UID if not set
            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
                user.is_verified = email_verified
                db.commit()
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Log successful authentication
        await log_user_action(
            db=db,
            user_id=user.id,
            action="firebase_auth",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return {
            "user": user,
            "message": "Authentication successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user - Firebase tokens are handled client-side"""
    
    # Log logout action
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="logout",
        resource_type="user",
        resource_id=str(current_user.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        success=True
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user




@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    db: Session = Depends(get_db)
):
    """Verify user email address"""
    
    # Get user ID from Redis
    user_id = redis_client.get(f"verification:{verification_data.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get and update user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    db.commit()
    
    # Remove verification token
    redis_client.delete(f"verification:{verification_data.token}")
    
    return {"message": "Email verified successfully"}


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_reset_token()
    redis_client.setex(
        f"password_reset:{reset_token}",
        timedelta(hours=1),
        str(user.id)
    )
    
    # Send reset email
    await send_password_reset_email(user.email, reset_token)
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset"""
    
    # Get user ID from Redis
    user_id = redis_client.get(f"password_reset:{reset_data.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get and update user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    db.commit()
    
    # Remove reset token and all refresh tokens
    redis_client.delete(f"password_reset:{reset_data.token}")
    redis_client.delete(f"refresh_token:{user.id}")
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Invalidate all refresh tokens
    redis_client.delete(f"refresh_token:{current_user.id}")
    
    return {"message": "Password changed successfully"}