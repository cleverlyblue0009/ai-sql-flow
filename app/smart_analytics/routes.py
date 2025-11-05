"""
Smart Analytics API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..database import get_db, User
from ..database.models import UserRole
from .analytics_service import SmartAnalyticsService

router = APIRouter(prefix="/smart-analytics", tags=["Smart Analytics"])
logger = logging.getLogger(__name__)

# Initialize service
analytics_service = SmartAnalyticsService()


def _get_demo_user(db: Session) -> User:
    """Get or create demo user - No auth required"""
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


@router.get("/query-optimizer", response_model=Dict[str, Any])
async def get_query_optimizer_insights(
    db: Session = Depends(get_db)
):
    """Get SQL query optimizer insights and recommendations"""
    current_user = _get_demo_user(db)
    
    try:
        insights = await analytics_service.get_query_optimizer_insights(current_user.id, db)
        return {
            "status": "success",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting query optimizer insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query optimizer insights"
        )


@router.get("/anomaly-detection", response_model=Dict[str, Any])
async def get_anomaly_detection_insights(
    db: Session = Depends(get_db)
):
    """Get data quality anomaly detection insights"""
    current_user = _get_demo_user(db)
    
    try:
        insights = await analytics_service.get_anomaly_detection_insights(current_user.id, db)
        return {
            "status": "success",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting anomaly detection insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anomaly detection insights"
        )


@router.get("/activity-intelligence", response_model=Dict[str, Any])
async def get_activity_intelligence(
    db: Session = Depends(get_db)
):
    """Get activity intelligence and pattern analysis"""
    current_user = _get_demo_user(db)
    
    try:
        intelligence = await analytics_service.get_activity_intelligence(current_user.id, db)
        return {
            "status": "success",
            "data": intelligence
        }
        
    except Exception as e:
        logger.error(f"Error getting activity intelligence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity intelligence"
        )


@router.get("/conversion-intelligence", response_model=Dict[str, Any])
async def get_conversion_intelligence(
    db: Session = Depends(get_db)
):
    """Get SQL conversion intelligence report"""
    current_user = _get_demo_user(db)
    
    try:
        intelligence = await analytics_service.get_conversion_intelligence(current_user.id, db)
        return {
            "status": "success",
            "data": intelligence
        }
        
    except Exception as e:
        logger.error(f"Error getting conversion intelligence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversion intelligence"
        )


@router.get("/performance-insights", response_model=Dict[str, Any])
async def get_performance_insights(
    db: Session = Depends(get_db)
):
    """Get performance insights across all platform features"""
    current_user = _get_demo_user(db)
    
    try:
        insights = await analytics_service.get_performance_insights(current_user.id, db)
        return {
            "status": "success",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting performance insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance insights"
        )


@router.get("/overview", response_model=Dict[str, Any])
async def get_analytics_overview(
    db: Session = Depends(get_db)
):
    """Get comprehensive smart analytics overview"""
    current_user = _get_demo_user(db)
    
    try:
        # Fetch all analytics data
        query_optimizer = await analytics_service.get_query_optimizer_insights(current_user.id, db)
        anomaly_detection = await analytics_service.get_anomaly_detection_insights(current_user.id, db)
        activity_intelligence = await analytics_service.get_activity_intelligence(current_user.id, db)
        conversion_intelligence = await analytics_service.get_conversion_intelligence(current_user.id, db)
        performance_insights = await analytics_service.get_performance_insights(current_user.id, db)
        
        return {
            "status": "success",
            "data": {
                "query_optimizer": query_optimizer,
                "anomaly_detection": anomaly_detection,
                "activity_intelligence": activity_intelligence,
                "conversion_intelligence": conversion_intelligence,
                "performance_insights": performance_insights
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics overview"
        )
