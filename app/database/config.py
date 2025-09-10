from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from typing import List
import os


class Settings(BaseSettings):
    # Database - Updated with working defaults
    database_url: str = "sqlite:///./ai_data_platform.db"  # Changed to SQLite for easier setup
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    encryption_key: str = "your-encryption-key-32-chars-long!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # OAuth2
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    
    # Storage - Fixed paths
    storage_type: str = "local"
    local_storage_path: str = "./storage"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "ai-data-platform-storage"
    
    # Celery - Fixed to use Redis
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # AI Models
    huggingface_api_key: str = ""
    openai_api_key: str = ""
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    
    # Application
    debug: bool = True
    log_level: str = "INFO"
    max_file_size_mb: int = 100
    allowed_origins: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8000", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env


# Initialize settings
settings = Settings()

# Create storage directory if it doesn't exist
os.makedirs(settings.local_storage_path, exist_ok=True)

# Database engines
engine = create_engine(
    settings.database_url, 
    pool_pre_ping=True,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Redis connection (with error handling)
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
except Exception as e:
    print(f"Redis connection failed: {e}. Some features may not work.")
    redis_client = None


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)