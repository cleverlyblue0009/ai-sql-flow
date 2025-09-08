from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database import get_db, User, Project, DataProfile, Job, MigrationLog, AuditLog
from ..auth import get_current_verified_user
from .schemas import (
    DashboardMetrics, ActivityItem, QuickStats, SystemStatus,
    DashboardResponse, ActivityResponse
)
from .services import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)

# Initialize service
dashboard_service = DashboardService()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get key dashboard metrics"""
    
    try:
        metrics = await dashboard_service.get_dashboard_metrics(db, current_user.id)
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get recent platform activities"""
    
    try:
        activities = await dashboard_service.get_recent_activities(db, current_user.id, limit)
        return ActivityResponse(activities=activities, total=len(activities))
        
    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activities"
        )


@router.get("/quick-stats", response_model=QuickStats)
async def get_quick_stats(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get quick statistics for today"""
    
    try:
        stats = await dashboard_service.get_quick_stats(db, current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting quick stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quick stats"
        )


@router.get("/system-status", response_model=SystemStatus)
async def get_system_status(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get system health and status"""
    
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get complete dashboard overview"""
    
    try:
        # Get all dashboard data in one request
        metrics = await dashboard_service.get_dashboard_metrics(db, current_user.id)
        activities = await dashboard_service.get_recent_activities(db, current_user.id, 10)
        quick_stats = await dashboard_service.get_quick_stats(db, current_user.id)
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get performance trends over time"""
    
    try:
        trends = await dashboard_service.get_performance_trends(db, current_user.id, days)
        return trends
        
    except Exception as e:
        logger.error(f"Error getting performance trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance trends"
        )


@router.get("/cost-analysis")
async def get_cost_analysis(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get cost analysis and savings data"""
    
    try:
        cost_analysis = await dashboard_service.get_cost_analysis(db, current_user.id)
        return cost_analysis
        
    except Exception as e:
        logger.error(f"Error getting cost analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cost analysis"
        )