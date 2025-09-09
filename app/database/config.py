from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import redis
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./ai_data_platform.db"
    async_database_url: str = "sqlite+aiosqlite:///./ai_data_platform.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-secret-key-here"
    encryption_key: str = "your-encryption-key-32-chars-long!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # OAuth2
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    
    # AWS/MinIO
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "ai-data-platform-storage"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # AI Models
    huggingface_api_key: str = ""
    openai_api_key: str = ""
    
    # Monitoring
    sentry_dsn: str = ""
    prometheus_port: int = 8001
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Application
    debug: bool = True
    log_level: str = "INFO"
    max_file_size_mb: int = 100
    allowed_origins: List[str] = ["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"


# Initialize settings
settings = Settings()

# Database engines
engine = create_engine(settings.database_url, pool_pre_ping=True)
# async_engine = create_async_engine(settings.async_database_url, echo=settings.debug)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# AsyncSessionLocal = sessionmaker(
#     async_engine, class_=AsyncSession, expire_on_commit=False
# )

# Base class for models
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# async def get_async_db():
#     async with AsyncSessionLocal() as session:
#         yield session


# Initialize database
def create_tables():
    Base.metadata.create_all(bind=engine)