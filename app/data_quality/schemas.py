from pydantic import BaseModel, validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum


class DataSourceType(str, Enum):
    FILE = "file"
    DATABASE = "database"
    API = "api"


class FileFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"
    TSV = "tsv"


class DataQualityJobType(str, Enum):
    UPLOAD = "upload"
    ANALYZE = "analyze"
    CLEAN = "clean"
    PROFILE = "profile"


# Request schemas
class DataUploadRequest(BaseModel):
    project_id: int
    file_name: str
    file_format: FileFormat
    delimiter: Optional[str] = ","
    encoding: Optional[str] = "utf-8"
    has_header: bool = True
    sample_rows: Optional[int] = 1000
    
    @validator('file_name')
    def validate_file_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('File name cannot be empty')
        return v.strip()


class DataAnalysisRequest(BaseModel):
    project_id: Optional[int] = None
    data_profile_id: int
    analysis_types: List[str] = ["completeness", "accuracy", "consistency", "validity", "uniqueness"]
    ai_enabled: bool = True
    sample_size: Optional[int] = None
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        valid_types = {"completeness", "accuracy", "consistency", "validity", "uniqueness", "outliers", "duplicates", "patterns"}
        invalid_types = set(v) - valid_types
        if invalid_types:
            raise ValueError(f'Invalid analysis types: {invalid_types}')
        return v


class DataCleaningRequest(BaseModel):
    project_id: Optional[int] = None
    data_profile_id: int
    cleaning_operations: List[Dict[str, Any]]
    preview_only: bool = False
    
    @validator('cleaning_operations')
    def validate_operations(cls, v):
        if not v:
            raise ValueError('At least one cleaning operation is required')
        
        valid_ops = {
            "remove_duplicates", "fill_missing", "remove_outliers", 
            "standardize_format", "correct_types", "normalize_values"
        }
        
        for op in v:
            if 'operation' not in op:
                raise ValueError('Each operation must have an "operation" field')
            if op['operation'] not in valid_ops:
                raise ValueError(f'Invalid operation: {op["operation"]}')
        
        return v


# Response schemas
class ColumnProfile(BaseModel):
    name: str
    data_type: str
    inferred_type: Optional[str] = None
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    min_value: Optional[Union[str, int, float]] = None
    max_value: Optional[Union[str, int, float]] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    mode_value: Optional[Union[str, int, float]] = None
    std_deviation: Optional[float] = None
    pattern_matches: Optional[Dict[str, int]] = None
    sample_values: Optional[List[str]] = None


class DataQualityMetrics(BaseModel):
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    validity_score: float
    uniqueness_score: float
    overall_quality_score: float
    
    @validator('*', pre=True)
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Scores must be between 0 and 100')
        return v


class DuplicateAnalysis(BaseModel):
    total_duplicates: int
    duplicate_percentage: float
    duplicate_groups: List[Dict[str, Any]]
    similarity_threshold: float
    ai_confidence: Optional[float] = None


class OutlierAnalysis(BaseModel):
    total_outliers: int
    outlier_percentage: float
    outliers_by_column: Dict[str, List[Dict[str, Any]]]
    detection_methods: List[str]
    ai_confidence: Optional[float] = None


class MissingValueAnalysis(BaseModel):
    total_missing: int
    missing_percentage: float
    missing_by_column: Dict[str, Dict[str, Any]]
    missing_patterns: List[Dict[str, Any]]
    imputation_suggestions: Dict[str, str]


class PatternAnalysis(BaseModel):
    detected_patterns: Dict[str, List[Dict[str, Any]]]
    format_consistency: Dict[str, float]
    regex_patterns: Dict[str, str]
    ai_suggestions: Optional[Dict[str, Any]] = None


class AIRecommendations(BaseModel):
    data_type_corrections: Dict[str, str]
    cleaning_priority: List[Dict[str, Any]]
    quality_improvements: List[Dict[str, Any]]
    automation_suggestions: List[str]
    confidence_scores: Dict[str, float]


class DataProfileResponse(BaseModel):
    id: int
    project_id: int
    source_name: str
    source_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    column_count: int
    row_count: int
    created_at: datetime
    updated_at: datetime
    
    # Quality metrics
    quality_metrics: Optional[DataQualityMetrics] = None
    
    # Column profiles
    column_profiles: List[ColumnProfile]
    
    # Analysis results
    duplicate_analysis: Optional[DuplicateAnalysis] = None
    outlier_analysis: Optional[OutlierAnalysis] = None
    missing_value_analysis: Optional[MissingValueAnalysis] = None
    pattern_analysis: Optional[PatternAnalysis] = None
    
    # AI recommendations
    ai_recommendations: Optional[AIRecommendations] = None
    
    class Config:
        from_attributes = True


class DataCleaningResult(BaseModel):
    original_rows: int
    cleaned_rows: int
    removed_rows: int
    modifications: Dict[str, int]
    cleaning_summary: Dict[str, Any]
    quality_improvement: Dict[str, float]
    preview_data: Optional[List[Dict[str, Any]]] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percentage: float
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DataQualityReport(BaseModel):
    job_id: str
    project_id: int
    data_profile_id: int
    generated_at: datetime
    
    # Summary
    summary: Dict[str, Any]
    
    # Detailed analysis
    quality_metrics: DataQualityMetrics
    column_analysis: List[ColumnProfile]
    issues_found: List[Dict[str, Any]]
    
    # AI insights
    ai_insights: Optional[Dict[str, Any]] = None
    recommendations: Optional[AIRecommendations] = None
    
    # Visualizations (base64 encoded images or chart data)
    charts: Optional[Dict[str, str]] = None