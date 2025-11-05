"""
Monitoring and alerting API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import logging

from ..database import get_db, User
from .monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])
logger = logging.getLogger(__name__)

# Initialize monitoring service
monitoring_service = MonitoringService()

def _get_demo_user(db: Session) -> User:
    """Get or create demo user - No auth required"""
    from ..database.models import UserRole
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




@router.get("/system", response_model=Dict[str, Any])
async def get_system_metrics():
    """Get system performance metrics"""
    
    try:
        metrics = await monitoring_service.get_system_metrics()
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )


@router.get("/application", response_model=Dict[str, Any])
async def get_application_metrics(
    db: Session = Depends(get_db)
):
    """Get application performance metrics"""
    
    try:
        metrics = await monitoring_service.get_application_metrics(db)
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting application metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application metrics"
        )


@router.get("/services", response_model=Dict[str, Any])
async def get_service_status():
    """Get status of all platform services"""
    
    try:
        status_info = await monitoring_service.get_service_status()
        return {
            "status": "success",
            "data": status_info
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service status"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_active_alerts(
    db: Session = Depends(get_db)
):
    """Get all active alerts"""
    
    try:
        alerts = await monitoring_service.get_active_alerts(db)
        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "total_count": len(alerts),
                "critical_count": len([a for a in alerts if a["severity"] == "high"]),
                "warning_count": len([a for a in alerts if a["severity"] == "medium"]),
                "info_count": len([a for a in alerts if a["severity"] == "low"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.post("/alerts", response_model=Dict[str, Any])
async def create_alert(
    alert_data: Dict[str, Any]):
    """Create a new alert"""
    
    try:
        required_fields = ["type", "severity", "title", "message"]
        for field in required_fields:
            if field not in alert_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        alert = await monitoring_service.create_alert(
            alert_type=alert_data["type"],
            severity=alert_data["severity"],
            title=alert_data["title"],
            message=alert_data["message"],
            user_id=current_user.id
        )
        
        return {
            "status": "success",
            "data": alert
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


@router.post("/alerts/{alert_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(
    alert_id: str):
    """Acknowledge an alert"""
    
    try:
        success = await monitoring_service.acknowledge_alert(alert_id, current_user.id)
        
        if success:
            return {
                "status": "success",
                "message": "Alert acknowledged successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_health_summary():
    """Get overall platform health summary"""
    
    try:
        # Get all metrics
        system_metrics = await monitoring_service.get_system_metrics()
        service_status = await monitoring_service.get_service_status()
        
        # Calculate overall health
        system_health = "healthy"
        if any(component["status"] == "warning" for component in [
            system_metrics["cpu"], system_metrics["memory"], 
            system_metrics["disk"], system_metrics["processes"]
        ]):
            system_health = "warning"
        
        service_health = service_status["overall_health"]
        
        # Overall platform health
        if system_health == "warning" or service_health in ["degraded", "critical"]:
            overall_health = "warning"
        elif service_health == "critical":
            overall_health = "critical"
        else:
            overall_health = "healthy"
        
        return {
            "status": "success",
            "data": {
                "overall_health": overall_health,
                "system_health": system_health,
                "service_health": service_health,
                "timestamp": system_metrics["timestamp"],
                "uptime_percentage": 99.2,  # Would be calculated from actual uptime
                "last_incident": "2024-01-15T10:30:00Z",  # Mock data
                "next_maintenance": "2024-02-01T02:00:00Z"  # Mock data
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting health summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health summary"
        )


@router.get("/metrics/realtime", response_model=Dict[str, Any])
async def get_realtime_metrics(
    db: Session = Depends(get_db)
):
    """Get real-time metrics for dashboard"""
    
    try:
        # Collect all metrics
        system_metrics = await monitoring_service.get_system_metrics()
        app_metrics = await monitoring_service.get_application_metrics(db)
        service_status = await monitoring_service.get_service_status()
        alerts = await monitoring_service.get_active_alerts(db)
        
        # Format for real-time dashboard
        realtime_data = {
            "timestamp": system_metrics["timestamp"],
            "summary": {
                "active_processes": app_metrics["jobs"]["active"],
                "success_rate": app_metrics["jobs"]["success_rate"],
                "avg_response_time": app_metrics["data_processing"]["avg_response_time_ms"],
                "error_rate": app_metrics["jobs"]["error_rate"],
                "cpu_usage": system_metrics["cpu"]["usage_percent"],
                "memory_usage": system_metrics["memory"]["usage_percent"],
                "active_alerts": len([a for a in alerts if a["severity"] == "high"])
            },
            "trends": {
                "cpu_trend": "stable",  # Would be calculated from historical data
                "memory_trend": "increasing",
                "response_time_trend": "improving",
                "error_rate_trend": "stable"
            },
            "service_count": {
                "operational": len([s for s in service_status["services"].values() if s["status"] == "operational"]),
                "degraded": len([s for s in service_status["services"].values() if s["status"] == "degraded"]),
                "error": len([s for s in service_status["services"].values() if s["status"] == "error"])
            }
        }
        
        return {
            "status": "success",
            "data": realtime_data
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve realtime metrics"
        )