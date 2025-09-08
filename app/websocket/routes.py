from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging
import json
from typing import Optional

from ..database import get_db, User
from ..auth import get_current_user_from_token
from .manager import connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time updates"""
    
    user = None
    
    try:
        # Authenticate user from token
        if token:
            try:
                user = await get_current_user_from_token(token, db)
            except Exception as e:
                logger.error(f"WebSocket authentication failed: {str(e)}")
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        if not user:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Connect to WebSocket manager
        await connection_manager.connect(websocket, user.id, {
            "user_agent": websocket.headers.get("user-agent"),
            "ip_address": websocket.client.host if websocket.client else None
        })
        
        # Send initial user data
        await connection_manager.send_personal_message({
            "type": "user_connected",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            },
            "message": f"Welcome back, {user.full_name}!"
        }, websocket)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                
                # Handle the message
                await connection_manager.handle_message(websocket, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user.id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": "An error occurred while processing your message",
                    "details": str(e)
                }, websocket)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Ensure cleanup
        await connection_manager.disconnect(websocket)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Admin WebSocket endpoint for system monitoring"""
    
    user = None
    
    try:
        # Authenticate admin user
        if token:
            try:
                user = await get_current_user_from_token(token, db)
                if user.role.value != "admin":
                    await websocket.close(code=4003, reason="Admin access required")
                    return
            except Exception as e:
                logger.error(f"Admin WebSocket authentication failed: {str(e)}")
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        if not user:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Connect to WebSocket manager
        await connection_manager.connect(websocket, user.id, {
            "user_agent": websocket.headers.get("user-agent"),
            "ip_address": websocket.client.host if websocket.client else None,
            "admin_connection": True
        })
        
        # Subscribe to admin topics
        await connection_manager.subscribe(websocket, "system_metrics")
        await connection_manager.subscribe(websocket, "system_alerts")
        await connection_manager.subscribe(websocket, "user_activity")
        
        # Send admin welcome message
        await connection_manager.send_personal_message({
            "type": "admin_connected",
            "message": "Admin WebSocket connected",
            "system_info": {
                "active_connections": connection_manager.get_connection_count(),
                "active_users": connection_manager.get_user_count()
            }
        }, websocket)
        
        # Listen for admin messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Handle admin-specific commands
                if data.get("type") == "get_system_status":
                    await connection_manager.send_personal_message({
                        "type": "system_status",
                        "data": {
                            "active_connections": connection_manager.get_connection_count(),
                            "active_users": connection_manager.get_user_count(),
                            "connection_details": [
                                {
                                    "user_id": metadata["user_id"],
                                    "connected_at": metadata["connected_at"].isoformat(),
                                    "subscriptions": list(metadata["subscriptions"])
                                }
                                for metadata in connection_manager.connection_metadata.values()
                            ]
                        }
                    }, websocket)
                
                elif data.get("type") == "broadcast_message":
                    message_content = data.get("message")
                    if message_content:
                        await connection_manager.broadcast({
                            "type": "admin_broadcast",
                            "message": message_content,
                            "from_admin": user.username
                        }, exclude_user=user.id)
                
                else:
                    # Handle regular message
                    await connection_manager.handle_message(websocket, message)
                
            except WebSocketDisconnect:
                logger.info(f"Admin WebSocket disconnected for user {user.id}")
                break
            except Exception as e:
                logger.error(f"Error handling admin WebSocket message: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"Admin WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"Admin WebSocket error: {str(e)}")
    finally:
        await connection_manager.disconnect(websocket)


# Helper function to send updates from background tasks
async def send_job_progress_update(job_id: str, user_id: int, progress_data: dict):
    """Send job progress update via WebSocket"""
    await connection_manager.send_job_update(
        job_id=job_id,
        user_id=user_id,
        status=progress_data.get("status", "running"),
        progress=progress_data.get("progress", 0),
        message=progress_data.get("message", "Processing...")
    )


async def send_migration_progress_update(migration_id: str, user_id: int, progress_data: dict):
    """Send migration progress update via WebSocket"""
    await connection_manager.send_migration_update(
        migration_id=migration_id,
        user_id=user_id,
        status=progress_data.get("status", "running"),
        progress=progress_data.get("progress", 0),
        phase=progress_data.get("phase", "Processing")
    )


async def send_new_activity(user_id: int, activity_data: dict):
    """Send new activity to user's activity feed"""
    await connection_manager.send_activity_update(user_id, activity_data)


async def send_system_notification(notification_type: str, message: str, severity: str = "info"):
    """Send system-wide notification"""
    await connection_manager.send_system_alert(notification_type, message, severity)