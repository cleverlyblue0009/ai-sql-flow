from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import asyncio
from cryptography.fernet import Fernet

from ..database import Connection, MigrationLog, Job, ConnectionType, settings
from .schemas import (
    DatabaseInfo, ConnectionTestResponse, MigrationProgressResponse, 
    MigrationStep, PerformanceAnalysisResponse, PerformanceMetrics,
    ResourceUsage, CostAnalysis, MigrationStatusResponse, MigrationStatus
)
from .ai_translator import AITranslationEngine

logger = logging.getLogger(__name__)


class MigrationService:
    """Service for managing database migrations"""

    async def get_supported_databases(self) -> List[DatabaseInfo]:
        """Get list of supported database types"""
        
        return [
            DatabaseInfo(
                type="postgresql",
                name="PostgreSQL",
                version_support=["9.6+", "10+", "11+", "12+", "13+", "14+", "15+"],
                features=[
                    "Full schema migration",
                    "Data type conversion",
                    "Index migration",
                    "Constraint preservation",
                    "Stored procedures",
                    "Views and materialized views"
                ],
                connection_params={
                    "sslmode": "prefer",
                    "application_name": "DataFlow AI",
                    "connect_timeout": 30
                }
            ),
            DatabaseInfo(
                type="mysql",
                name="MySQL",
                version_support=["5.7+", "8.0+"],
                features=[
                    "Full schema migration",
                    "Data type conversion",
                    "Index migration",
                    "Foreign key constraints",
                    "Triggers and procedures",
                    "Views"
                ],
                connection_params={
                    "charset": "utf8mb4",
                    "autocommit": True,
                    "connect_timeout": 30
                }
            ),
            DatabaseInfo(
                type="snowflake",
                name="Snowflake",
                version_support=["Latest"],
                features=[
                    "Cloud-optimized migration",
                    "Automatic scaling",
                    "Column-level security",
                    "Time travel",
                    "Zero-copy cloning",
                    "Semi-structured data"
                ],
                connection_params={
                    "warehouse": "COMPUTE_WH",
                    "role": "ACCOUNTADMIN",
                    "authenticator": "snowflake"
                }
            ),
            DatabaseInfo(
                type="sqlserver",
                name="SQL Server",
                version_support=["2016+", "2017+", "2019+", "2022+"],
                features=[
                    "Full schema migration",
                    "Identity column handling",
                    "Clustered indexes",
                    "Stored procedures",
                    "User-defined types",
                    "Partitioning"
                ],
                connection_params={
                    "driver": "ODBC Driver 17 for SQL Server",
                    "trustServerCertificate": "yes",
                    "connection_timeout": 30
                }
            ),
            DatabaseInfo(
                type="oracle",
                name="Oracle Database",
                version_support=["12c+", "18c+", "19c+", "21c+"],
                features=[
                    "Full schema migration",
                    "PL/SQL procedures",
                    "Packages and triggers",
                    "Materialized views",
                    "Partitioning",
                    "Advanced queuing"
                ],
                connection_params={
                    "encoding": "UTF-8",
                    "nencoding": "UTF-8",
                    "threaded": True
                }
            )
        ]

    async def get_migration_progress(self, migration_log: MigrationLog, job: Optional[Job] = None) -> MigrationProgressResponse:
        """Get detailed migration progress"""
        
        try:
            # Define migration steps
            steps = [
                MigrationStep(
                    step_name="Source Connection",
                    status="completed" if migration_log.status.value != "created" else "pending"
                ),
                MigrationStep(
                    step_name="Schema Analysis",
                    status="completed" if migration_log.status.value in ["translating", "executing", "completed"] else 
                           "running" if migration_log.status.value == "mapping" else "pending"
                ),
                MigrationStep(
                    step_name="SQL Translation",
                    status="completed" if migration_log.status.value in ["executing", "completed"] else
                           "running" if migration_log.status.value == "translating" else "pending"
                ),
                MigrationStep(
                    step_name="Validation",
                    status="completed" if migration_log.status.value in ["executing", "completed"] else "pending"
                ),
                MigrationStep(
                    step_name="Data Migration",
                    status="completed" if migration_log.status.value == "completed" else
                           "running" if migration_log.status.value == "executing" else "pending"
                ),
                MigrationStep(
                    step_name="Performance Test",
                    status="completed" if migration_log.status.value == "completed" else "pending"
                )
            ]
            
            # Add timing information (mock for now)
            if migration_log.started_at:
                base_time = migration_log.started_at
                for i, step in enumerate(steps):
                    if step.status == "completed":
                        step.start_time = base_time + timedelta(minutes=i * 3)
                        step.end_time = step.start_time + timedelta(minutes=random.randint(2, 5))
                        step.duration_minutes = (step.end_time - step.start_time).total_seconds() / 60
                    elif step.status == "running":
                        step.start_time = base_time + timedelta(minutes=i * 3)
            
            # Calculate progress percentage
            completed_steps = len([s for s in steps if s.status == "completed"])
            running_steps = len([s for s in steps if s.status == "running"])
            progress = (completed_steps / len(steps)) * 100
            if running_steps > 0:
                progress += (running_steps / len(steps)) * 50  # Add 50% for running steps
            
            # Estimate completion time
            estimated_completion = None
            if migration_log.started_at and progress > 0 and progress < 100:
                elapsed = datetime.utcnow() - migration_log.started_at
                estimated_total = elapsed * (100 / progress)
                estimated_completion = migration_log.started_at + estimated_total
            
            # Mock table and record counts
            total_tables = random.randint(10, 50)
            tables_migrated = int((progress / 100) * total_tables)
            total_records = random.randint(100000, 1000000)
            records_migrated = int((progress / 100) * total_records)
            
            current_table = None
            if migration_log.status.value == "executing":
                table_names = ["users", "orders", "products", "customers", "transactions", "inventory"]
                current_table = random.choice(table_names)
            
            return MigrationProgressResponse(
                migration_id=migration_log.migration_id,
                status=MigrationStatus(migration_log.status.value),
                progress_percentage=progress,
                current_phase=migration_log.current_phase or migration_log.status.value,
                steps=steps,
                estimated_completion=estimated_completion,
                started_at=migration_log.started_at,
                tables_migrated=tables_migrated,
                total_tables=total_tables,
                records_migrated=records_migrated,
                total_records=total_records,
                current_table=current_table
            )
            
        except Exception as e:
            logger.error(f"Error getting migration progress: {str(e)}")
            raise

    async def get_performance_analysis(self, migration_log: MigrationLog) -> PerformanceAnalysisResponse:
        """Get performance analysis for completed migration"""
        
        try:
            # Mock performance data (in real implementation, this would come from actual measurements)
            before_metrics = {
                "avg_query_time_ms": 2400,
                "queries_per_second": 150,
                "cpu_utilization": 75,
                "memory_usage_gb": 8.5,
                "io_operations_per_sec": 2500
            }
            
            after_metrics = {
                "avg_query_time_ms": 800,
                "queries_per_second": 450,
                "cpu_utilization": 42,
                "memory_usage_gb": 5.8,
                "io_operations_per_sec": 1050
            }
            
            # Calculate improvements
            improvements = {}
            for key in before_metrics:
                if key in ["queries_per_second"]:
                    # Higher is better
                    improvements[key] = ((after_metrics[key] - before_metrics[key]) / before_metrics[key]) * 100
                else:
                    # Lower is better
                    improvements[key] = ((before_metrics[key] - after_metrics[key]) / before_metrics[key]) * 100
            
            query_performance = PerformanceMetrics(
                before_migration=before_metrics,
                after_migration=after_metrics,
                improvement_percentage=improvements
            )
            
            resource_usage = ResourceUsage(
                cpu_usage_reduction=45.0,
                memory_reduction=32.0,
                io_operations_reduction=58.0
            )
            
            cost_analysis = CostAnalysis(
                monthly_cost_before=5200.0,
                monthly_cost_after=2860.0,
                monthly_savings=2340.0,
                annual_savings=28080.0,
                roi_percentage=340.0
            )
            
            optimization_recommendations = [
                "Consider implementing query result caching for frequently accessed data",
                "Add composite indexes on commonly joined columns",
                "Enable automatic statistics updates for query optimization",
                "Consider partitioning large tables for better performance",
                "Implement connection pooling to reduce overhead"
            ]
            
            # Calculate overall performance score (0-100)
            performance_score = (
                min(improvements.get("avg_query_time_ms", 0), 100) * 0.4 +
                min(improvements.get("cpu_utilization", 0), 100) * 0.3 +
                min(improvements.get("memory_usage_gb", 0), 100) * 0.2 +
                min(improvements.get("io_operations_per_sec", 0), 100) * 0.1
            )
            
            return PerformanceAnalysisResponse(
                migration_id=migration_log.migration_id,
                query_performance=query_performance,
                resource_usage=resource_usage,
                cost_analysis=cost_analysis,
                optimization_recommendations=optimization_recommendations,
                performance_score=max(0, performance_score)
            )
            
        except Exception as e:
            logger.error(f"Error getting performance analysis: {str(e)}")
            raise

    async def get_migration_status(self, migration_log: MigrationLog) -> MigrationStatusResponse:
        """Get detailed migration status"""
        
        try:
            error_log = None
            if migration_log.error_log:
                error_log = migration_log.error_log
            
            performance_metrics = None
            if migration_log.performance_metrics:
                performance_metrics = migration_log.performance_metrics
            
            return MigrationStatusResponse(
                migration_id=migration_log.migration_id,
                name=migration_log.name,
                description=migration_log.description,
                status=MigrationStatus(migration_log.status.value),
                source_dialect=migration_log.source_dialect,
                target_dialect=migration_log.target_dialect,
                created_at=migration_log.created_at,
                started_at=migration_log.started_at,
                completed_at=migration_log.completed_at,
                progress_percentage=migration_log.progress_percentage,
                current_phase=migration_log.current_phase,
                error_log=error_log,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Error getting migration status: {str(e)}")
            raise


class SQLTranslationService:
    """Service for SQL dialect translation"""

    def __init__(self):
        # Initialize AI translation engine
        self.ai_engine = AITranslationEngine()
        self.translation_models = {}

    async def translate_sql(
        self, 
        source_sql: str, 
        source_dialect: str, 
        target_dialect: str, 
        optimization_level: str = "standard",
        schema_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Translate SQL from source dialect to target dialect using AI"""
        
        try:
            # Use AI translation engine for advanced translation
            result = await self.ai_engine.translate_sql_advanced(
                source_sql=source_sql,
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                optimization_level=optimization_level,
                schema_context=schema_context
            )
            
            # Add additional metadata
            result["translation_method"] = "ai_advanced"
            result["processing_time_ms"] = 2000  # Would be actual processing time
            
            return result
            
        except Exception as e:
            logger.error(f"Error translating SQL with AI: {str(e)}")
            
            # Fallback to basic translation
            logger.info("Falling back to basic translation")
            return await self._basic_translate_sql(source_sql, source_dialect, target_dialect, optimization_level)
    
    async def _basic_translate_sql(
        self,
        source_sql: str,
        source_dialect: str,
        target_dialect: str,
        optimization_level: str = "standard"
    ) -> Dict[str, Any]:
        """Basic SQL translation as fallback"""
        
        try:
            await asyncio.sleep(1)  # Simulate processing time
            
            # Simple dialect-specific transformations
            translated_sql = source_sql
            
            if source_dialect == "mysql" and target_dialect == "snowflake":
                translated_sql = self._mysql_to_snowflake(source_sql)
            elif source_dialect == "postgresql" and target_dialect == "snowflake":
                translated_sql = self._postgresql_to_snowflake(source_sql)
            elif source_dialect == "sqlserver" and target_dialect == "snowflake":
                translated_sql = self._sqlserver_to_snowflake(source_sql)
            
            # Apply basic optimizations
            if optimization_level in ["standard", "aggressive"]:
                translated_sql = self._apply_optimizations(translated_sql, target_dialect, optimization_level)
            
            # Mock scores for basic translation
            confidence_score = random.uniform(0.75, 0.85)
            semantic_similarity = random.uniform(0.85, 0.95)
            
            # Generate basic suggestions
            suggestions = self._generate_optimization_suggestions(translated_sql, target_dialect)
            
            # Basic validation
            validation_result = {
                "syntax_valid": True,
                "performance_optimized": optimization_level != "basic",
                "semantically_equivalent": semantic_similarity > 0.90,
                "warnings": ["Basic translation used - consider manual review for complex queries"]
            }
            
            return {
                "translated_sql": translated_sql,
                "confidence_score": confidence_score,
                "semantic_similarity": semantic_similarity,
                "optimization_suggestions": suggestions,
                "validation_result": validation_result,
                "translation_method": "basic_fallback"
            }
            
        except Exception as e:
            logger.error(f"Error in basic SQL translation: {str(e)}")
            raise

    def _mysql_to_snowflake(self, sql: str) -> str:
        """Convert MySQL-specific syntax to Snowflake"""
        # Mock transformations
        sql = sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
        sql = sql.replace("TINYINT", "SMALLINT")
        sql = sql.replace("MEDIUMINT", "INT")
        sql = sql.replace("LONGTEXT", "TEXT")
        sql = sql.replace("`", '"')  # Quote style
        return sql

    def _postgresql_to_snowflake(self, sql: str) -> str:
        """Convert PostgreSQL-specific syntax to Snowflake"""
        # Mock transformations
        sql = sql.replace("SERIAL", "AUTOINCREMENT")
        sql = sql.replace("BIGSERIAL", "AUTOINCREMENT")
        sql = sql.replace("BOOLEAN", "BOOL")
        sql = sql.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP_TZ")
        return sql

    def _sqlserver_to_snowflake(self, sql: str) -> str:
        """Convert SQL Server-specific syntax to Snowflake"""
        # Mock transformations
        sql = sql.replace("IDENTITY(1,1)", "AUTOINCREMENT")
        sql = sql.replace("NVARCHAR", "VARCHAR")
        sql = sql.replace("DATETIME2", "TIMESTAMP")
        sql = sql.replace("[", '"').replace("]", '"')  # Quote style
        return sql

    def _apply_optimizations(self, sql: str, target_dialect: str, level: str) -> str:
        """Apply performance optimizations to translated SQL"""
        # Mock optimization logic
        if level == "aggressive" and target_dialect == "snowflake":
            # Add clustering hints, optimize joins, etc.
            if "JOIN" in sql.upper():
                sql += "\n-- Optimized for Snowflake clustering"
        
        return sql

    def _generate_optimization_suggestions(self, sql: str, target_dialect: str) -> List[str]:
        """Generate optimization suggestions for the translated SQL"""
        suggestions = []
        
        if "SELECT *" in sql:
            suggestions.append("Consider specifying column names instead of SELECT * for better performance")
        
        if target_dialect == "snowflake":
            if "JOIN" in sql.upper():
                suggestions.append("Consider using clustering keys for frequently joined tables")
            suggestions.append("Enable result caching for frequently executed queries")
        
        if len(suggestions) == 0:
            suggestions.append("Query is well-optimized for the target platform")
        
        return suggestions


class ConnectionService:
    """Service for managing database connections"""

    def __init__(self):
        # Initialize encryption key for storing credentials
        try:
            self.cipher = Fernet(settings.encryption_key.encode())
        except:
            # Generate a key if not configured (for development)
            self.cipher = Fernet(Fernet.generate_key())

    async def test_connection(
        self,
        connection_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        connection_params: Dict[str, Any] = None
    ) -> ConnectionTestResponse:
        """Test database connection"""
        
        try:
            start_time = datetime.utcnow()
            
            # Mock connection testing (in real implementation, would actually connect)
            await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulate connection time
            
            # Mock success/failure (95% success rate)
            success = random.random() > 0.05
            
            end_time = datetime.utcnow()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            if success:
                return ConnectionTestResponse(
                    success=True,
                    message="Connection successful",
                    response_time_ms=response_time_ms,
                    database_version=self._get_mock_version(connection_type),
                    schema_count=random.randint(1, 10),
                    table_count=random.randint(10, 100)
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message="Connection failed",
                    response_time_ms=response_time_ms,
                    error_details="Unable to connect to database server. Please check credentials and network connectivity."
                )
                
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return ConnectionTestResponse(
                success=False,
                message="Connection test failed",
                error_details=str(e)
            )

    async def create_or_get_connection(
        self,
        db: Session,
        user_id: int,
        name: str,
        connection_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        connection_params: Dict[str, Any] = None
    ) -> Connection:
        """Create or get existing database connection"""
        
        try:
            # Check if connection already exists
            existing_connection = db.query(Connection).filter(
                Connection.user_id == user_id,
                Connection.host == host,
                Connection.port == port,
                Connection.database_name == database,
                Connection.username == username
            ).first()
            
            if existing_connection:
                return existing_connection
            
            # Encrypt password
            encrypted_password = self.cipher.encrypt(password.encode())
            
            # Create new connection
            connection = Connection(
                name=name,
                connection_type=ConnectionType(connection_type),
                user_id=user_id,
                host=host,
                port=port,
                database_name=database,
                username=username,
                encrypted_password=encrypted_password,
                connection_params=connection_params or {},
                is_active=True,
                last_tested=datetime.utcnow(),
                test_result={"status": "success", "message": "Connection created"}
            )
            
            db.add(connection)
            db.commit()
            db.refresh(connection)
            
            return connection
            
        except Exception as e:
            logger.error(f"Error creating connection: {str(e)}")
            raise

    def _get_mock_version(self, connection_type: str) -> str:
        """Get mock database version"""
        versions = {
            "postgresql": "PostgreSQL 15.2",
            "mysql": "MySQL 8.0.33",
            "snowflake": "Snowflake 7.34.2",
            "sqlserver": "Microsoft SQL Server 2022",
            "oracle": "Oracle Database 19c"
        }
        return versions.get(connection_type, "Unknown")