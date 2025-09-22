import bcrypt
import logging
import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-creds.json")
    firebase_admin.initialize_app(cred)


# ------------------------------
# Password Hashing Helpers
# ------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


# ------------------------------
# Firebase Token Verification
# ------------------------------
def verify_firebase_token(token: str):
    """Verify Firebase ID token and return decoded claims"""
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Invalid Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )


def verify_firebase_token_websocket(token: str):
    """Verify Firebase ID token for WebSocket connections - returns None on failure instead of raising exception"""
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        logger.info(f"WebSocket token verified for user: {decoded_token.get('uid', 'unknown')}")
        return decoded_token
    except Exception as e:
        logger.error(f"WebSocket Firebase token verification failed: {e}")
        return None
