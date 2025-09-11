from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from typing import List
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/mydb"
    redis_url: str

    # Security
    secret_key: str
    encryption_key: str
    jwt_secret_key: str = "your_secret_key_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth2
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # Storage
    storage_type: str = "local"
    local_storage_path: str = "./storage"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = ""

    # Celery
    celery_broker_url: str="redis://localhost:6379/0"
    celery_result_backend: str="redis://localhost:6379/0"

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
    allowed_origins: List[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

# Initialize settings with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"Settings initialization failed: {e}. Using defaults.")
    # Create minimal settings for testing
    class MinimalSettings:
        database_url = "sqlite:///./test.db"
        redis_url = "redis://localhost:6379/0"
        local_storage_path = "./storage"
        debug = True
        log_level = "INFO"
        max_file_size_mb = 100
        allowed_origins = []
    settings = MinimalSettings()

# Create storage directory if it doesn't exist
os.makedirs(settings.local_storage_path, exist_ok=True)

# Database engine with error handling
try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )
except Exception as e:
    print(f"Database engine creation failed: {e}")
    # Create a fallback SQLite engine
    engine = create_engine(
        "sqlite:///./fallback.db",
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Redis connection - lazy initialization to avoid blocking during import
redis_client = None

def get_redis_client():
    """Get Redis client with lazy initialization"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2, socket_connect_timeout=2)
            redis_client.ping()
            print("Redis connected successfully")
        except Exception as e:
            print(f"Redis connection failed: {e}. Running without Redis.")
            redis_client = False  # Use False to indicate failed connection
    return redis_client if redis_client is not False else None

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database tables
def create_tables():
    Base.metadata.create_all(bind=engine)
