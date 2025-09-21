from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
import uuid

from .manager import connection_manager
from .migration_ws import migration_progress_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    
    try:
        await websocket.accept()
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Connect to WebSocket manager (no user authentication)
        await connection_manager.connect(websocket, connection_id, None, {
            "user_agent": websocket.headers.get("user-agent"),
            "ip_address": websocket.client.host if websocket.client else None
        })
        
        # Send initial connection confirmation
        await connection_manager.send_personal_message(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "message": "WebSocket connection established"
        }), connection_id)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                
                # Handle the message
                await connection_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for connection {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await connection_manager.send_personal_message(json.dumps({
                    "type": "error",
                    "message": "An error occurred while processing your message",
                    "details": str(e)
                }), connection_id)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for connection {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Ensure cleanup
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    """Admin WebSocket endpoint for system monitoring"""
    
    try:
        await websocket.accept()
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Connect to WebSocket manager (no authentication)
        await connection_manager.connect(websocket, connection_id, None, {
            "user_agent": websocket.headers.get("user-agent"),
            "ip_address": websocket.client.host if websocket.client else None,
            "admin_connection": True
        })
        
        # Subscribe to admin topics
        await connection_manager.subscribe(connection_id, "system_metrics")
        await connection_manager.subscribe(connection_id, "system_alerts")
        await connection_manager.subscribe(connection_id, "user_activity")
        
        # Send admin welcome message
        await connection_manager.send_personal_message(json.dumps({
            "type": "admin_connected",
            "message": "Admin WebSocket connected",
            "connection_id": connection_id,
            "system_info": {
                "active_connections": connection_manager.get_connection_count(),
                "active_users": connection_manager.get_user_count()
            }
        }), connection_id)
        
        # Listen for admin messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Handle admin-specific commands
                if data.get("type") == "get_system_status":
                    await connection_manager.send_personal_message(json.dumps({
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
                    }), connection_id)
                
                elif data.get("type") == "broadcast_message":
                    message_content = data.get("message")
                    if message_content:
                        await connection_manager.broadcast({
                            "type": "admin_broadcast",
                            "message": message_content,
                            "from_admin": "admin"
                        })
                
                else:
                    # Handle regular message
                    await connection_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Admin WebSocket disconnected for connection {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling admin WebSocket message: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"Admin WebSocket disconnected for connection {connection_id}")
    except Exception as e:
        logger.error(f"Admin WebSocket error: {str(e)}")
    finally:
        await connection_manager.disconnect(connection_id)


# Helper function to send updates from background tasks
async def send_job_progress_update(job_id: str, progress_data: dict):
    """Send job progress update via WebSocket to all connections"""
    await connection_manager.broadcast({
        "type": "job_progress",
        "job_id": job_id,
        "status": progress_data.get("status", "running"),
        "progress": progress_data.get("progress", 0),
        "message": progress_data.get("message", "Processing...")
    })


async def send_migration_progress_update(migration_id: str, progress_data: dict):
    """Send migration progress update via WebSocket to all connections"""
    await connection_manager.broadcast({
        "type": "migration_progress",
        "migration_id": migration_id,
        "status": progress_data.get("status", "running"),
        "progress": progress_data.get("progress", 0),
        "phase": progress_data.get("phase", "Processing")
    })


async def send_system_notification(notification_type: str, message: str, severity: str = "info"):
    """Send system-wide notification"""
    await connection_manager.broadcast({
        "type": "system_notification",
        "notification_type": notification_type,
        "message": message,
        "severity": severity
    })


@router.websocket("/ws/migration")
async def migration_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time migration progress tracking"""
    
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket.accept()
        
        # Connect to migration progress manager (no user authentication)
        await migration_progress_manager.connect_user(websocket, None, connection_id)
        
        logger.info(f"Migration WebSocket connected for connection {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                message_text = await websocket.receive_text()
                message_data = json.loads(message_text)
                
                # Handle the message through migration progress manager
                await migration_progress_manager.handle_client_message(
                    connection_id, message_data, None
                )
                
            except WebSocketDisconnect:
                logger.info(f"Migration WebSocket disconnected for connection {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from connection {connection_id}")
                await migration_progress_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error handling migration WebSocket message: {str(e)}")
                await migration_progress_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Error processing message"
                })
                
    except WebSocketDisconnect:
        logger.info(f"Migration WebSocket disconnected for connection {connection_id}")
    except Exception as e:
        logger.error(f"Migration WebSocket error: {str(e)}")
    finally:
        # Ensure cleanup
        await migration_progress_manager.disconnect_user(connection_id, None)