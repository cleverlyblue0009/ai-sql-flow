"""
Settings and configuration management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import logging

from ..database import get_db, User
from ..database.models import UserRole
from .settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])
logger = logging.getLogger(__name__)

# Initialize settings service
settings_service = SettingsService()


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


@router.get("/database-connections", response_model=Dict[str, Any])
async def get_database_connections(
    db: Session = Depends(get_db)
):
    """Get all database connections for the user"""
    current_user = _get_demo_user(db)
    
    try:
        connections = await settings_service.get_user_connections(current_user.id, db)
        return {
            "status": "success",
            "data": {
                "connections": connections,
                "total_count": len(connections)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve database connections"
        )


@router.post("/database-connections", response_model=Dict[str, Any])
async def create_database_connection(
    connection_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new database connection"""
    current_user = _get_demo_user(db)
    
    try:
        connection = await settings_service.create_connection(current_user.id, connection_data, db)
        return {
            "status": "success",
            "data": connection
        }
        
    except Exception as e:
        logger.error(f"Error creating database connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create database connection"
        )


@router.put("/database-connections/{connection_id}", response_model=Dict[str, Any])
async def update_database_connection(
    connection_id: int,
    connection_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update an existing database connection"""
    
    try:
        connection = await settings_service.update_connection(
            connection_id, current_user.id, connection_data, db
        )
        return {
            "status": "success",
            "data": connection
        }
        
    except Exception as e:
        logger.error(f"Error updating database connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database connection"
        )


@router.delete("/database-connections/{connection_id}", response_model=Dict[str, Any])
async def delete_database_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """Delete a database connection"""
    
    try:
        success = await settings_service.delete_connection(connection_id, current_user.id, db)
        if success:
            return {
                "status": "success",
                "message": "Database connection deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting database connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete database connection"
        )


@router.post("/database-connections/{connection_id}/test", response_model=Dict[str, Any])
async def test_database_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """Test a database connection"""
    
    try:
        result = await settings_service.test_connection(connection_id, current_user.id, db)
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test database connection"
        )


@router.get("/user-management", response_model=Dict[str, Any])
async def get_user_management_settings(
    db: Session = Depends(get_db)
):
    """Get user management settings (admin only)"""
    
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        users = await settings_service.get_all_users(db)
        return {
            "status": "success",
            "data": {
                "users": users,
                "total_count": len(users)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user management settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user management settings"
        )


@router.put("/users/{user_id}/role", response_model=Dict[str, Any])
async def update_user_role(
    user_id: int,
    role_data: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        success = await settings_service.update_user_role(
            user_id, role_data.get("role"), db
        )
        
        if success:
            return {
                "status": "success",
                "message": "User role updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )


@router.get("/ai-configuration", response_model=Dict[str, Any])
async def get_ai_configuration():
    """Get AI model configuration settings"""
    
    try:
        config = await settings_service.get_ai_configuration()
        return {
            "status": "success",
            "data": config
        }
        
    except Exception as e:
        logger.error(f"Error getting AI configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI configuration"
        )


@router.put("/ai-configuration", response_model=Dict[str, Any])
async def update_ai_configuration(
    config_data: Dict[str, Any]):
    """Update AI model configuration settings (admin only)"""
    
    current_user = _get_demo_user(db)
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        config = await settings_service.update_ai_configuration(config_data)
        return {
            "status": "success",
            "data": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update AI configuration"
        )


@router.get("/integrations", response_model=Dict[str, Any])
async def get_integrations():
    """Get external integrations configuration"""
    
    current_user = _get_demo_user(db)
    try:
        integrations = await settings_service.get_integrations()
        return {
            "status": "success",
            "data": integrations
        }
        
    except Exception as e:
        logger.error(f"Error getting integrations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integrations"
        )


@router.put("/integrations/{integration_name}", response_model=Dict[str, Any])
async def update_integration(
    integration_name: str,
    integration_data: Dict[str, Any]):
    """Update integration configuration (admin only)"""
    
    current_user = _get_demo_user(db)
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        success = await settings_service.update_integration(integration_name, integration_data)
        if success:
            return {
                "status": "success",
                "message": f"{integration_name} integration updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update integration"
        )


@router.get("/security", response_model=Dict[str, Any])
async def get_security_settings():
    """Get security and compliance settings"""
    
    current_user = _get_demo_user(db)
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        security_settings = await settings_service.get_security_settings()
        return {
            "status": "success",
            "data": security_settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security settings"
        )


@router.put("/security", response_model=Dict[str, Any])
async def update_security_settings(
    security_data: Dict[str, Any]):
    """Update security and compliance settings (admin only)"""
    
    current_user = _get_demo_user(db)
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        settings = await settings_service.update_security_settings(security_data)
        return {
            "status": "success",
            "data": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating security settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security settings"
        )