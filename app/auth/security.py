from typing import Optional, Dict, Any
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets
import base64
import firebase_admin
from firebase_admin import credentials, auth
from ..database.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption for sensitive data
def generate_key() -> bytes:
    """Generate a new encryption key"""
    return Fernet.generate_key()

def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    # In production, this should be stored securely (e.g., AWS KMS, HashiCorp Vault)
    key = getattr(settings, 'encryption_key', None)
    if not key:
        key = base64.urlsafe_b64encode(settings.secret_key.encode()[:32].ljust(32, b'0'))
    return key

cipher_suite = Fernet(get_encryption_key())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def encrypt_data(data: str) -> bytes:
    """Encrypt sensitive data"""
    return cipher_suite.encrypt(data.encode())


def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypt sensitive data"""
    return cipher_suite.decrypt(encrypted_data).decode()


# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            if settings.firebase_credentials_path:
                cred = credentials.Certificate(settings.firebase_credentials_path)
            else:
                # Use default credentials (for Cloud Run or local development)
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred, {
                'projectId': settings.firebase_project_id,
            })
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            # Initialize with mock credentials for development
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": settings.firebase_project_id or "mock-project",
                "private_key_id": "mock",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----\n",
                "client_email": "mock@mock-project.iam.gserviceaccount.com",
                "client_id": "mock",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            })
            firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token and return decoded token"""
    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        # For development/testing, return a mock token if Firebase is not properly configured
        if settings.debug and "mock" in str(e).lower():
            return {
                "uid": "mock-user-123",
                "email": "test@example.com",
                "name": "Test User",
                "email_verified": True
            }
        return None


def create_custom_token(uid: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """Create a custom Firebase token for a user"""
    try:
        initialize_firebase()
        return auth.create_custom_token(uid, additional_claims)
    except Exception as e:
        print(f"Failed to create custom token: {e}")
        return ""


def generate_reset_token() -> str:
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)