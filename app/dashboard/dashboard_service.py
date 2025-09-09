"""
Comprehensive dashboard service providing real-time metrics and insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import random

from ..database import User, Project, Job, DataProfile, MigrationLog
from ..monitoring.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)


class DashboardService:
    """Service providing comprehensive dashboard metrics and insights"""
    
    def __init__(self):
        self.monitoring_service = MonitoringService()
    
    async def get_dashboard_overview(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard overview for a user"""
        
        try:
            # Get user's projects
            user_projects = db.query(Project).filter(Project.owner_id == user_id).all()
            project_ids = [p.id for p in user_projects]
            
            # Basic statistics
            total_projects = len(user_projects)
            total_data_profiles = db.query(DataProfile).filter(
                DataProfile.project_id.in_(project_ids)
            ).count() if project_ids else 0
            
            # Recent activity (last 7 days)
            recent_date = datetime.utcnow() - timedelta(days=7)
            
            recent_jobs = db.query(Job).filter(
                Job.user_id == user_id,
                Job.created_at >= recent_date
            ).count()
            
            # Job statistics
            completed_jobs = db.query(Job).filter(
                Job.user_id == user_id,
                Job.status == "completed"
            ).count()
            
            failed_jobs = db.query(Job).filter(
                Job.user_id == user_id,
                Job.status == "failed"
            ).count()
            
            running_jobs = db.query(Job).filter(
                Job.user_id == user_id,
                Job.status == "running"
            ).count()
            
            # Calculate success rate
            total_finished_jobs = completed_jobs + failed_jobs
            success_rate = (completed_jobs / total_finished_jobs * 100) if total_finished_jobs > 0 else 100
            
            # Data quality metrics
            quality_scores = []
            if project_ids:
                profiles_with_scores = db.query(DataProfile).filter(
                    DataProfile.project_id.in_(project_ids),
                    DataProfile.overall_quality_score.isnot(None)
                ).all()
                quality_scores = [p.overall_quality_score for p in profiles_with_scores if p.overall_quality_score]
            
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Migration statistics
            migrations = db.query(MigrationLog).filter(
                MigrationLog.project_id.in_(project_ids)
            ).all() if project_ids else []
            
            active_migrations = len([m for m in migrations if m.status.value in ["running", "mapping", "translating", "executing"]])
            completed_migrations = len([m for m in migrations if m.status.value == "completed"])
            
            # Cost savings (mock calculation)
            cost_savings = sum([
                2340.0 if m.status.value == "completed" else 0 
                for m in migrations
            ])
            
            return {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_projects": total_projects,
                    "total_data_profiles": total_data_profiles,
                    "recent_activity_count": recent_jobs,
                    "success_rate": round(success_rate, 1),
                    "avg_quality_score": round(avg_quality_score, 1),
                    "cost_savings": cost_savings
                },
                "jobs": {
                    "running": running_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs,
                    "success_rate": round(success_rate, 1)
                },
                "migrations": {
                    "active": active_migrations,
                    "completed": completed_migrations,
                    "total": len(migrations)
                },
                "quality": {
                    "average_score": round(avg_quality_score, 1),
                    "profiles_analyzed": len(quality_scores),
                    "improvement_trend": "increasing" if avg_quality_score > 80 else "stable"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {str(e)}")
            raise
    
    async def get_recent_activity(self, user_id: int, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent user activity"""
        
        try:
            activities = []
            
            # Get recent jobs
            recent_jobs = db.query(Job).filter(
                Job.user_id == user_id
            ).order_by(desc(Job.created_at)).limit(limit * 2).all()
            
            for job in recent_jobs:
                activity_type = "data_analysis" if job.job_type == "data_upload" else job.job_type
                
                # Determine icon based on job type and status
                if job.status.value == "completed":
                    icon = "check-circle"
                    status_color = "success"
                elif job.status.value == "failed":
                    icon = "x-circle"
                    status_color = "danger"
                elif job.status.value == "running":
                    icon = "clock"
                    status_color = "primary"
                else:
                    icon = "circle"
                    status_color = "secondary"
                
                activities.append({
                    "id": job.job_id,
                    "type": activity_type,
                    "title": job.name or f"{job.job_type.replace('_', ' ').title()}",
                    "description": self._get_activity_description(job),
                    "timestamp": job.created_at.isoformat(),
                    "status": job.status.value,
                    "icon": icon,
                    "status_color": status_color,
                    "metadata": {
                        "job_type": job.job_type,
                        "progress": job.progress_percentage
                    }
                })
            
            # Get recent data profiles
            user_projects = db.query(Project).filter(Project.owner_id == user_id).all()
            project_ids = [p.id for p in user_projects]
            
            if project_ids:
                recent_profiles = db.query(DataProfile).filter(
                    DataProfile.project_id.in_(project_ids)
                ).order_by(desc(DataProfile.created_at)).limit(5).all()
                
                for profile in recent_profiles:
                    activities.append({
                        "id": f"profile_{profile.id}",
                        "type": "data_upload",
                        "title": f"Data uploaded: {profile.source_name}",
                        "description": f"Uploaded {profile.source_name} with {profile.row_count or 0} rows",
                        "timestamp": profile.created_at.isoformat(),
                        "status": "completed",
                        "icon": "upload",
                        "status_color": "success",
                        "metadata": {
                            "file_name": profile.source_name,
                            "rows": profile.row_count,
                            "columns": profile.column_count
                        }
                    })
            
            # Sort by timestamp and limit
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    def _get_activity_description(self, job: Job) -> str:
        """Generate activity description based on job details"""
        
        if job.job_type == "data_upload":
            return f"Analyzed data quality for uploaded file"
        elif job.job_type == "data_cleaning":
            return f"Cleaned data with {job.progress_percentage or 0}% completion"
        elif job.job_type == "sql_translation":
            return f"Translated SQL from {job.parameters.get('source_dialect', 'unknown')} to {job.parameters.get('target_dialect', 'unknown')}"
        elif job.job_type == "migration":
            return f"Database migration with {job.progress_percentage or 0}% completion"
        else:
            return f"Executed {job.job_type.replace('_', ' ')}"
    
    async def get_performance_metrics(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get performance metrics for dashboard"""
        
        try:
            # Get system metrics
            system_metrics = await self.monitoring_service.get_system_metrics()
            app_metrics = await self.monitoring_service.get_application_metrics(db)
            
            # Calculate user-specific metrics
            user_jobs_today = db.query(Job).filter(
                Job.user_id == user_id,
                Job.created_at >= datetime.utcnow() - timedelta(days=1)
            ).count()
            
            # Performance trends (mock data - would be real historical data)
            performance_trends = {
                "cpu_usage": [65, 72, 68, 71, 69, 74, system_metrics["cpu"]["usage_percent"]],
                "memory_usage": [78, 82, 79, 85, 81, 83, system_metrics["memory"]["usage_percent"]],
                "response_time": [850, 920, 780, 890, 820, 760, app_metrics["data_processing"]["avg_response_time_ms"]],
                "success_rate": [96.2, 97.1, 95.8, 98.2, 97.5, 96.8, app_metrics["jobs"]["success_rate"]]
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "current_metrics": {
                    "cpu_usage": system_metrics["cpu"]["usage_percent"],
                    "memory_usage": system_metrics["memory"]["usage_percent"],
                    "response_time": app_metrics["data_processing"]["avg_response_time_ms"],
                    "success_rate": app_metrics["jobs"]["success_rate"],
                    "active_jobs": app_metrics["jobs"]["active"],
                    "user_jobs_today": user_jobs_today
                },
                "trends": performance_trends,
                "status": {
                    "cpu": system_metrics["cpu"]["status"],
                    "memory": system_metrics["memory"]["status"],
                    "overall": app_metrics["overall_status"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "current_metrics": {},
                "trends": {},
                "status": {"overall": "unknown"}
            }
    
    async def get_data_quality_insights(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get data quality insights and trends"""
        
        try:
            # Get user's projects and data profiles
            user_projects = db.query(Project).filter(Project.owner_id == user_id).all()
            project_ids = [p.id for p in user_projects]
            
            if not project_ids:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": {"profiles_analyzed": 0, "average_quality": 0, "issues_found": 0},
                    "trends": {},
                    "top_issues": [],
                    "recommendations": []
                }
            
            # Get data profiles with quality scores
            profiles = db.query(DataProfile).filter(
                DataProfile.project_id.in_(project_ids),
                DataProfile.overall_quality_score.isnot(None)
            ).all()
            
            if not profiles:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": {"profiles_analyzed": 0, "average_quality": 0, "issues_found": 0},
                    "trends": {},
                    "top_issues": [],
                    "recommendations": []
                }
            
            # Calculate quality metrics
            quality_scores = [p.overall_quality_score for p in profiles if p.overall_quality_score]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Quality distribution
            excellent_count = len([s for s in quality_scores if s >= 90])
            good_count = len([s for s in quality_scores if 80 <= s < 90])
            fair_count = len([s for s in quality_scores if 70 <= s < 80])
            poor_count = len([s for s in quality_scores if s < 70])
            
            # Mock issue analysis (would be real data from analysis results)
            top_issues = [
                {"type": "Missing Values", "count": 892, "severity": "high", "trend": "increasing"},
                {"type": "Duplicates", "count": 1247, "severity": "medium", "trend": "stable"},
                {"type": "Format Issues", "count": 567, "severity": "medium", "trend": "decreasing"},
                {"type": "Outliers", "count": 234, "severity": "low", "trend": "stable"},
                {"type": "Invalid References", "count": 89, "severity": "high", "trend": "decreasing"}
            ]
            
            # Quality trends (mock data)
            quality_trends = {
                "weekly": [76.2, 78.5, 79.1, 82.3, 84.7, 86.2, avg_quality],
                "monthly": [74.1, 76.8, 79.2, 81.5, 83.8, avg_quality]
            }
            
            # Recommendations based on quality scores
            recommendations = []
            if avg_quality < 80:
                recommendations.append({
                    "type": "quality_improvement",
                    "priority": "high",
                    "title": "Implement comprehensive data cleaning",
                    "description": "Your average data quality score is below 80%. Consider implementing automated data cleaning processes."
                })
            
            if poor_count > 0:
                recommendations.append({
                    "type": "data_review",
                    "priority": "medium",
                    "title": "Review low-quality datasets",
                    "description": f"You have {poor_count} datasets with quality scores below 70%. These need immediate attention."
                })
            
            if not recommendations:
                recommendations.append({
                    "type": "maintenance",
                    "priority": "low",
                    "title": "Maintain current quality standards",
                    "description": "Your data quality is excellent. Continue monitoring and maintain current processes."
                })
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "profiles_analyzed": len(profiles),
                    "average_quality": round(avg_quality, 1),
                    "issues_found": sum(issue["count"] for issue in top_issues),
                    "quality_distribution": {
                        "excellent": excellent_count,
                        "good": good_count,
                        "fair": fair_count,
                        "poor": poor_count
                    }
                },
                "trends": quality_trends,
                "top_issues": top_issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality insights: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {"profiles_analyzed": 0, "average_quality": 0, "issues_found": 0},
                "trends": {},
                "top_issues": [],
                "recommendations": []
            }
    
    async def get_migration_dashboard(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get migration dashboard data"""
        
        try:
            # Get user's projects
            user_projects = db.query(Project).filter(Project.owner_id == user_id).all()
            project_ids = [p.id for p in user_projects]
            
            if not project_ids:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": {"total_migrations": 0, "active_migrations": 0, "success_rate": 0},
                    "recent_migrations": [],
                    "performance_analysis": {}
                }
            
            # Get migrations
            migrations = db.query(MigrationLog).filter(
                MigrationLog.project_id.in_(project_ids)
            ).order_by(desc(MigrationLog.created_at)).all()
            
            if not migrations:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": {"total_migrations": 0, "active_migrations": 0, "success_rate": 0},
                    "recent_migrations": [],
                    "performance_analysis": {}
                }
            
            # Calculate migration statistics
            total_migrations = len(migrations)
            active_migrations = len([m for m in migrations if m.status.value in ["running", "mapping", "translating", "executing"]])
            completed_migrations = len([m for m in migrations if m.status.value == "completed"])
            failed_migrations = len([m for m in migrations if m.status.value == "failed"])
            
            success_rate = (completed_migrations / (completed_migrations + failed_migrations) * 100) if (completed_migrations + failed_migrations) > 0 else 100
            
            # Recent migrations
            recent_migrations = []
            for migration in migrations[:10]:  # Last 10 migrations
                recent_migrations.append({
                    "migration_id": migration.migration_id,
                    "name": migration.name,
                    "source_dialect": migration.source_dialect,
                    "target_dialect": migration.target_dialect,
                    "status": migration.status.value,
                    "progress": migration.progress_percentage or 0,
                    "created_at": migration.created_at.isoformat(),
                    "started_at": migration.started_at.isoformat() if migration.started_at else None,
                    "completed_at": migration.completed_at.isoformat() if migration.completed_at else None
                })
            
            # Performance analysis (mock data for completed migrations)
            performance_analysis = {
                "total_cost_savings": completed_migrations * 2340.0,  # Mock calculation
                "average_improvement": 67.0,  # Mock percentage
                "query_performance_boost": 3.2,  # Mock multiplier
                "resource_reduction": 45.0  # Mock percentage
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_migrations": total_migrations,
                    "active_migrations": active_migrations,
                    "completed_migrations": completed_migrations,
                    "failed_migrations": failed_migrations,
                    "success_rate": round(success_rate, 1)
                },
                "recent_migrations": recent_migrations,
                "performance_analysis": performance_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting migration dashboard: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {"total_migrations": 0, "active_migrations": 0, "success_rate": 0},
                "recent_migrations": [],
                "performance_analysis": {}
            }