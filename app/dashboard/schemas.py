from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MetricTrend(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class ActivityStatus(str, Enum):
    SUCCESS = "success"
    RUNNING = "running"
    WARNING = "warning"
    PENDING = "pending"
    FAILED = "failed"


class ActivityType(str, Enum):
    MIGRATION = "migration"
    QUALITY = "quality"
    ALERT = "alert"
    UPLOAD = "upload"
    CLEANING = "cleaning"


class MetricValue(BaseModel):
    title: str
    value: str
    change: str
    trend: MetricTrend
    icon: str
    color: str
    description: Optional[str] = None


class DashboardMetrics(BaseModel):
    data_quality_score: MetricValue
    active_migrations: MetricValue
    success_rate: MetricValue
    cost_savings: MetricValue
    tables_processed_today: int
    updated_at: datetime


class ActivityItem(BaseModel):
    id: str
    type: ActivityType
    title: str
    description: Optional[str] = None
    timestamp: datetime
    status: ActivityStatus
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None


class ActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total: int


class QuickStats(BaseModel):
    tables_processed_today: int
    data_uploaded_mb: float
    migrations_completed: int
    quality_checks_run: int
    active_users: int
    avg_processing_time: float
    updated_at: datetime


class SystemHealthCheck(BaseModel):
    service: str
    status: str
    response_time_ms: Optional[float] = None
    uptime_percentage: float
    last_check: datetime


class SystemStatus(BaseModel):
    overall_health: str
    data_processing: SystemHealthCheck
    migration_engine: SystemHealthCheck
    ai_processing: SystemHealthCheck
    database: SystemHealthCheck
    redis: SystemHealthCheck
    storage: SystemHealthCheck
    active_users: int
    system_load: float
    memory_usage: float
    cpu_usage: float


class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    activities: List[ActivityItem]
    quick_stats: QuickStats
    system_status: SystemStatus


class PerformanceTrend(BaseModel):
    date: datetime
    quality_score: float
    processing_time: float
    success_rate: float
    migrations_count: int


class CostAnalysis(BaseModel):
    monthly_savings: float
    annual_savings: float
    roi_percentage: float
    cost_breakdown: Dict[str, float]
    savings_trend: List[Dict[str, Any]]
    projected_savings: Dict[str, float]