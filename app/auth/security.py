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
                import os
                credentials_path = settings.firebase_credentials_path
                
                # Check if credentials file exists
                if not os.path.exists(credentials_path):
                    print(f"Firebase credentials file not found at: {credentials_path}")
                    raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
                
                # Check if it's a mock file
                with open(credentials_path, 'r') as f:
                    content = f.read()
                    if "MOCK_PRIVATE_KEY_FOR_DEVELOPMENT_ONLY" in content:
                        print("Using mock Firebase credentials for development")
                        raise Exception("Mock credentials detected - using development mode")
                
                cred = credentials.Certificate(credentials_path)
            else:
                # Use default credentials (for Cloud Run or local development)
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred, {
                'projectId': settings.firebase_project_id,
            })
            print(f"Firebase initialized successfully for project: {settings.firebase_project_id}")
            
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            print("Running in development mode with mock Firebase authentication")
            # Initialize with mock credentials for development
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": settings.firebase_project_id or "dataflow-abb8a",
                "private_key_id": "mock-dev",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_DEV_KEY\n-----END PRIVATE KEY-----\n",
                "client_email": f"mock@{settings.firebase_project_id or 'dataflow-abb8a'}.iam.gserviceaccount.com",
                "client_id": "mock-dev-client",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            })
            firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token and return decoded token"""
    print(f"Verifying token: {token[:20]}..." if len(token) > 20 else f"Verifying token: {token}")
    
    # For development with mock tokens, allow specific development tokens
    if (token == "mock-firebase-token-for-dev" or 
        token.startswith("dev-") or 
        "mock" in token.lower() or
        token == "dev-mock-firebase-token-for-development"):
        print("✅ Using development token")
        return {
            "uid": "dev-user-1",
            "email": "dev@example.com",
            "name": "Development User",
            "email_verified": True
        }
    
    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(token)
        print("✅ Firebase token verified successfully")
        return decoded_token
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        
        # For development, allow mock tokens when Firebase is not properly configured
        if ("mock" in token.lower() or 
            token.startswith("dev-") or 
            len(token) < 50):  # Likely a development token
            print("🔧 Using fallback development authentication")
            return {
                "uid": "dev-user-1",
                "email": "dev@example.com",
                "name": "Development User",
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