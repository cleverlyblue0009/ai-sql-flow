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