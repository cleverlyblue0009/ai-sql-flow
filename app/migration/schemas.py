from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ConnectionType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SNOWFLAKE = "snowflake"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MONGODB = "mongodb"


class MigrationStatus(str, Enum):
    CREATED = "created"
    MAPPING = "mapping"
    TRANSLATING = "translating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class DatabaseConfig(BaseModel):
    connection_type: ConnectionType
    host: str
    port: int
    database: str
    username: str
    password: str
    connection_params: Optional[Dict[str, Any]] = {}


class ConnectionTestRequest(BaseModel):
    connection_type: ConnectionType
    host: str
    port: int
    database: str
    username: str
    password: str
    connection_params: Optional[Dict[str, Any]] = {}


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    response_time_ms: Optional[float] = None
    database_version: Optional[str] = None
    schema_count: Optional[int] = None
    table_count: Optional[int] = None
    error_details: Optional[str] = None


class MigrationSetupRequest(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    source_config: DatabaseConfig
    target_config: DatabaseConfig
    migration_options: Optional[Dict[str, Any]] = {}


class MigrationResponse(BaseModel):
    migration_id: str
    status: str
    message: str
    created_at: datetime


class SQLTranslationRequest(BaseModel):
    source_sql: str
    source_dialect: str
    target_dialect: str
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD


class SQLTranslationResponse(BaseModel):
    job_id: str
    status: str
    message: str
    translated_sql: Optional[str] = None
    confidence_score: Optional[float] = None
    semantic_similarity: Optional[float] = None
    optimization_suggestions: Optional[List[str]] = None
    validation_result: Optional[Dict[str, Any]] = None


class MigrationConfigRequest(BaseModel):
    migrate_schema: bool = True
    migrate_data: bool = True
    preserve_constraints: bool = True
    optimize_for_target: bool = True
    batch_size: int = 1000
    parallel_jobs: int = 4


class MigrationStep(BaseModel):
    step_name: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    error_message: Optional[str] = None


class MigrationProgressResponse(BaseModel):
    migration_id: str
    status: MigrationStatus
    progress_percentage: float
    current_phase: str
    steps: List[MigrationStep]
    estimated_completion: Optional[datetime] = None
    started_at: Optional[datetime] = None
    tables_migrated: int = 0
    total_tables: int = 0
    records_migrated: int = 0
    total_records: int = 0
    current_table: Optional[str] = None


class PerformanceMetrics(BaseModel):
    before_migration: Dict[str, Any]
    after_migration: Dict[str, Any]
    improvement_percentage: Dict[str, float]


class ResourceUsage(BaseModel):
    cpu_usage_reduction: float
    memory_reduction: float
    io_operations_reduction: float


class CostAnalysis(BaseModel):
    monthly_cost_before: float
    monthly_cost_after: float
    monthly_savings: float
    annual_savings: float
    roi_percentage: float


class PerformanceAnalysisResponse(BaseModel):
    migration_id: str
    query_performance: PerformanceMetrics
    resource_usage: ResourceUsage
    cost_analysis: CostAnalysis
    optimization_recommendations: List[str]
    performance_score: float


class DatabaseInfo(BaseModel):
    type: str
    name: str
    version_support: List[str]
    features: List[str]
    connection_params: Dict[str, Any]


class DatabaseListResponse(BaseModel):
    databases: List[DatabaseInfo]


class MigrationStatusResponse(BaseModel):
    migration_id: str
    name: str
    description: Optional[str]
    status: MigrationStatus
    source_dialect: str
    target_dialect: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress_percentage: float
    current_phase: Optional[str]
    error_log: Optional[List[Dict[str, Any]]] = None
    performance_metrics: Optional[Dict[str, Any]] = None