from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from typing import List
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./app_data.db"
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str
    encryption_key: str
    
    # Firebase
    firebase_credentials_path: str = ""
    firebase_project_id: str = ""

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

# Initialize settings
settings = Settings()

# Create storage directory if it doesn't exist
os.makedirs(settings.local_storage_path, exist_ok=True)

# Database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Redis connection
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
    print("Redis connected successfully")
except Exception as e:
    print(f"Redis connection failed: {e}. Using in-memory fallback.")
    redis_client = None

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
