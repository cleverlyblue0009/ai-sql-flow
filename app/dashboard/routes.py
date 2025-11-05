from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database import get_db, User, Project, DataProfile, Job, MigrationLog, AuditLog
from ..database.models import UserRole
from .schemas import (
    DashboardMetrics, ActivityItem, QuickStats, SystemStatus,
    DashboardResponse, ActivityResponse
)
from .dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)

# Initialize service
dashboard_service = DashboardService()


def _get_demo_user(db: Session) -> User:
    """Get or create demo user for non-authenticated requests - No auth required"""
    demo_user = db.query(User).filter(User.email == "demo@example.com").first()
    if not demo_user:
        demo_user = User(
            email="demo@example.com",
            username="demo",
            firebase_uid="demo_uid",
            full_name="Demo User",
            role=UserRole.ADMIN
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    return demo_user


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: Session = Depends(get_db)
):
    """Get key dashboard metrics - No auth required - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        metrics = await dashboard_service.get_dashboard_metrics(db, demo_user.id)
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard metrics"
        )


@router.get("/activities", response_model=ActivityResponse)
async def get_recent_activities(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get recent platform activities - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        activities = await dashboard_service.get_recent_activities(db, demo_user.id, limit)
        return ActivityResponse(activities=activities, total=len(activities))
        
    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activities"
        )


@router.get("/quick-stats", response_model=QuickStats)
async def get_quick_stats(
    db: Session = Depends(get_db)
):
    """Get quick statistics for today - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        stats = await dashboard_service.get_quick_stats(db, demo_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting quick stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quick stats"
        )


@router.get("/system-status", response_model=SystemStatus)
async def get_system_status(
    db: Session = Depends(get_db)
):
    """Get system health and status - No auth required"""
    
    try:
        status_info = await dashboard_service.get_system_status(db)
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )


@router.get("/overview", response_model=DashboardResponse)
async def get_dashboard_overview(
    db: Session = Depends(get_db)
):
    """Get complete dashboard overview - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        # Get all dashboard data in one request
        metrics = await dashboard_service.get_dashboard_metrics(db, demo_user.id)
        activities = await dashboard_service.get_recent_activities(db, demo_user.id, 10)
        quick_stats = await dashboard_service.get_quick_stats(db, demo_user.id)
        system_status = await dashboard_service.get_system_status(db)
        
        return DashboardResponse(
            metrics=metrics,
            activities=activities,
            quick_stats=quick_stats,
            system_status=system_status
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard overview"
        )


@router.get("/performance-trends")
async def get_performance_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get performance trends over time - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        trends = await dashboard_service.get_performance_trends(db, demo_user.id, days)
        return trends
        
    except Exception as e:
        logger.error(f"Error getting performance trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance trends"
        )


@router.get("/cost-analysis")
async def get_cost_analysis(
    db: Session = Depends(get_db)
):
    """Get cost analysis and savings data - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        cost_analysis = await dashboard_service.get_cost_analysis(db, demo_user.id)
        return cost_analysis
        
    except Exception as e:
        logger.error(f"Error getting cost analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cost analysis"
        )


@router.get("/comprehensive-overview", response_model=Dict[str, Any])
async def get_comprehensive_overview(
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard overview with all metrics - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        overview = await dashboard_service.get_dashboard_overview(demo_user.id, db)
        return {
            "status": "success",
            "data": overview
        }
        
    except Exception as e:
        logger.error(f"Error getting comprehensive overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comprehensive overview"
        )


@router.get("/activity-feed", response_model=Dict[str, Any])
async def get_activity_feed(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's activity feed - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        activities = await dashboard_service.get_recent_activity(demo_user.id, db, limit)
        return {
            "status": "success",
            "data": {
                "activities": activities,
                "total_count": len(activities)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting activity feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity feed"
        )


@router.get("/performance-dashboard", response_model=Dict[str, Any])
async def get_performance_dashboard(
    db: Session = Depends(get_db)
):
    """Get performance metrics dashboard - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        metrics = await dashboard_service.get_performance_metrics(demo_user.id, db)
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance dashboard"
        )


@router.get("/data-quality-insights", response_model=Dict[str, Any])
async def get_data_quality_insights(
    db: Session = Depends(get_db)
):
    """Get data quality insights and analytics - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        insights = await dashboard_service.get_data_quality_insights(demo_user.id, db)
        return {
            "status": "success",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting data quality insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data quality insights"
        )


@router.get("/migration-dashboard", response_model=Dict[str, Any])
async def get_migration_dashboard(
    db: Session = Depends(get_db)
):
    """Get migration dashboard with statistics and progress - No auth required"""
    
    try:
        demo_user = _get_demo_user(db)
        dashboard_data = await dashboard_service.get_migration_dashboard(demo_user.id, db)
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting migration dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get migration dashboard"
        )


@router.get("/real-stats")
async def get_real_dashboard_stats(
    db: Session = Depends(get_db)
):
    """Get real dashboard statistics - No mock data"""
    
    try:
        demo_user = _get_demo_user(db)
        
        # Get real data quality metrics
        data_profiles = db.query(DataProfile).all()
        
        if not data_profiles:
            return {
                "status": "success",
                "data": {
                    "data_quality_score": 0,
                    "active_migrations": 0,
                    "success_rate": 0,
                    "total_files": 0,
                    "trends": {
                        "quality": 0,
                        "migrations": 0
                    }
                }
            }
        
        # Calculate average quality score
        avg_quality = sum(p.quality_score for p in data_profiles) / len(data_profiles)
        
        # Count cleaned files (simulating migrations)
        cleaned_count = sum(1 for p in data_profiles if p.cleaning_history)
        
        # Calculate success rate (files with quality > 80%)
        successful = sum(1 for p in data_profiles if p.quality_score >= 80)
        success_rate = (successful / len(data_profiles)) * 100 if data_profiles else 0
        
        # Get recent profiles for trend
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_profiles = [p for p in data_profiles if p.created_at >= recent_cutoff]
        
        return {
            "status": "success",
            "data": {
                "data_quality_score": round(avg_quality, 1),
                "active_migrations": cleaned_count,
                "success_rate": round(success_rate, 1),
                "total_files": len(data_profiles),
                "trends": {
                    "quality": round(avg_quality - 90, 1),  # Simplified trend
                    "migrations": len(recent_profiles)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting real dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard stats"
        )


@router.get("/real-activity")
async def get_real_activity_feed(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get real activity feed from all platform features"""
    
    try:
        demo_user = _get_demo_user(db)
        activities = []
        
        # Get data quality activities
        recent_profiles = db.query(DataProfile).order_by(
            desc(DataProfile.created_at)
        ).limit(limit).all()
        
        for profile in recent_profiles:
            # File upload activity
            activities.append({
                "id": f"upload_{profile.id}",
                "type": "clean_data",
                "action": f"Uploaded {profile.file_name} for cleaning",
                "timestamp": profile.created_at.isoformat(),
                "icon": "file-up",
                "metadata": {
                    "file_id": profile.id,
                    "quality_score": profile.quality_score,
                    "rows": profile.row_count
                }
            })
            
            # Cleaning activity if cleaned
            if profile.cleaning_history:
                activities.append({
                    "id": f"clean_{profile.id}",
                    "type": "clean_data",
                    "action": f"Data quality improved for {profile.file_name}",
                    "timestamp": profile.created_at.isoformat(),
                    "icon": "check-circle",
                    "metadata": {
                        "file_id": profile.id,
                        "quality_score": profile.quality_score
                    }
                })
        
        # Get audit log activities (for SQL conversions)
        audit_logs = db.query(AuditLog).order_by(
            desc(AuditLog.created_at)
        ).limit(limit // 2).all()
        
        for log in audit_logs:
            if "migration" in log.action.lower() or "convert" in log.action.lower():
                activities.append({
                    "id": f"migration_{log.id}",
                    "type": "convert_sql",
                    "action": log.action,
                    "timestamp": log.created_at.isoformat(),
                    "icon": "database-transfer",
                    "metadata": log.metadata or {}
                })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "status": "success",
            "data": activities[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error getting real activity feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity feed"
        )


@router.get("/platform-insights")
async def get_platform_insights(
    db: Session = Depends(get_db)
):
    """Get platform insights from Smart Analytics"""
    
    try:
        demo_user = _get_demo_user(db)
        
        # Get data profiles for analysis
        profiles = db.query(DataProfile).all()
        
        if not profiles:
            return {
                "status": "success",
                "data": []
            }
        
        insights = []
        
        # Most active data type
        avg_quality = sum(p.quality_score for p in profiles) / len(profiles)
        insights.append({
            "title": "Average Data Quality",
            "value": f"{round(avg_quality, 1)}%",
            "metric": "quality",
            "source": "clean_data"
        })
        
        # Quality improvement
        cleaned = [p for p in profiles if p.cleaning_history]
        if cleaned:
            insights.append({
                "title": "Files Cleaned",
                "value": f"{len(cleaned)} files",
                "metric": "cleaning",
                "source": "clean_data"
            })
        
        # Total processed
        insights.append({
            "title": "Total Files Processed",
            "value": f"{len(profiles)} files",
            "metric": "volume",
            "source": "clean_data"
        })
        
        return {
            "status": "success",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting platform insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform insights"
        )