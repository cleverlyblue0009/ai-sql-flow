from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, JSON,
    ForeignKey, Enum as SQLEnum, LargeBinary, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .config import Base


class UserRole(enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    ANALYST = "analyst"


class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConnectionType(enum.Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"


class MigrationStatus(enum.Enum):
    CREATED = "created"
    MAPPING = "mapping"
    TRANSLATING = "translating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # OAuth fields
    google_id = Column(String(100), unique=True)
    github_id = Column(String(100), unique=True)
    
    # Profile fields
    avatar_url = Column(String(500))
    timezone = Column(String(50), default="UTC")
    preferences = Column(JSON)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    connections = relationship("Connection", back_populates="user")
    jobs = relationship("Job", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Project settings
    settings = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    data_profiles = relationship("DataProfile", back_populates="project")
    migration_logs = relationship("MigrationLog", back_populates="project")
    jobs = relationship("Job", back_populates="project")


class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    connection_type = Column(SQLEnum(ConnectionType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Connection details (encrypted)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    encrypted_password = Column(LargeBinary, nullable=False)
    
    # Additional connection parameters
    connection_params = Column(JSON)
    
    # Health monitoring
    is_active = Column(Boolean, default=True, nullable=False)
    last_tested = Column(DateTime(timezone=True))
    test_result = Column(JSON)
    
    # Relationships - FIXED: Properly specify foreign_keys to avoid ambiguity
    user = relationship("User", back_populates="connections")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    job_type = Column(String(100), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Job details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parameters = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(255))
    total_steps = Column(Integer)
    
    # Resource usage
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    execution_time = Column(Float)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    project = relationship("Project", back_populates="jobs")


class DataProfile(Base):
    __tablename__ = "data_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Data source info
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(100), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # Schema information
    column_count = Column(Integer)
    row_count = Column(Integer)
    schema_info = Column(JSON)
    
    # Data quality metrics
    completeness_score = Column(Float)
    accuracy_score = Column(Float)
    consistency_score = Column(Float)
    validity_score = Column(Float)
    uniqueness_score = Column(Float)
    overall_quality_score = Column(Float)
    
    # Detailed analysis results
    column_profiles = Column(JSON)
    duplicate_analysis = Column(JSON)
    outlier_analysis = Column(JSON)
    missing_value_analysis = Column(JSON)
    data_type_analysis = Column(JSON)
    pattern_analysis = Column(JSON)
    
    # AI model results
    ai_recommendations = Column(JSON)
    cleaning_suggestions = Column(JSON)
    
    # Cleaning history
    cleaning_history = Column(JSON)
    
    # Relationships
    project = relationship("Project", back_populates="data_profiles")


class MigrationLog(Base):
    __tablename__ = "migration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    migration_id = Column(String(255), unique=True, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False)
    target_connection_id = Column(Integer, ForeignKey("connections.id"))
    status = Column(SQLEnum(MigrationStatus), default=MigrationStatus.CREATED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Migration details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_dialect = Column(String(50), nullable=False)
    target_dialect = Column(String(50), nullable=False)
    
    # Schema mapping
    schema_mapping = Column(JSON)
    table_mappings = Column(JSON)
    
    # SQL translation
    original_sql = Column(Text)
    translated_sql = Column(Text)
    translation_confidence = Column(Float)
    semantic_similarity = Column(Float)
    
    # Execution results
    execution_log = Column(JSON)
    performance_metrics = Column(JSON)
    error_log = Column(JSON)
    
    # AI model results
    ai_optimizations = Column(JSON)
    performance_predictions = Column(JSON)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    current_phase = Column(String(100))
    
    # Relationships - FIXED: Properly specify foreign_keys to resolve ambiguity
    project = relationship("Project", back_populates="migration_logs")
    source_connection = relationship(
        "Connection", 
        foreign_keys=[source_connection_id],
        backref="source_migrations"
    )
    target_connection = relationship(
        "Connection", 
        foreign_keys=[target_connection_id],
        backref="target_migrations"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255))
    
    # Request details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_method = Column(String(10))
    request_path = Column(String(500))
    
    # Additional context
    details = Column(JSON)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


# Indexes for better performance
Index('idx_jobs_status_user', Job.status, Job.user_id)
Index('idx_jobs_type_created', Job.job_type, Job.created_at)
Index('idx_audit_logs_user_timestamp', AuditLog.user_id, AuditLog.timestamp)
Index('idx_data_profiles_project_created', DataProfile.project_id, DataProfile.created_at)
Index('idx_migration_logs_status_project', MigrationLog.status, MigrationLog.project_id)