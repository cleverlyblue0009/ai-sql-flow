from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and real-time updates"""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, client_info: Dict[str, Any] = None):
        """Accept WebSocket connection and add to active connections"""
        try:
            await websocket.accept()
            
            # Initialize user connections list if not exists
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            # Add connection
            self.active_connections[user_id].append(websocket)
            
            # Store metadata
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "client_info": client_info or {},
                "subscriptions": set()
            }
            
            logger.info(f"WebSocket connected for user {user_id}")
            
            # Send welcome message
            await self.send_personal_message({
                "type": "connection_established",
                "message": "WebSocket connection established",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id
            }, websocket)
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {str(e)}")
            await websocket.close()
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        try:
            # Get user ID from metadata
            metadata = self.connection_metadata.get(websocket)
            if not metadata:
                return
            
            user_id = metadata["user_id"]
            
            # Remove from active connections
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                
                # Clean up empty user connection lists
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            message_str = json.dumps(message, default=str)
            await websocket.send_text(message_str)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            await self.disconnect(websocket)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: int):
        """Send message to all connections of a specific user"""
        if user_id not in self.active_connections:
            return
        
        # Get all connections for the user
        connections = self.active_connections[user_id].copy()
        
        # Send to all user connections
        for connection in connections:
            try:
                await self.send_personal_message(message, connection)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                await self.disconnect(connection)
    
    async def broadcast(self, message: Dict[str, Any], exclude_user: Optional[int] = None):
        """Broadcast message to all connected users"""
        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            await self.send_to_user(message, user_id)
    
    async def send_to_subscribers(self, message: Dict[str, Any], topic: str):
        """Send message to all connections subscribed to a specific topic"""
        for websocket, metadata in self.connection_metadata.items():
            if topic in metadata.get("subscriptions", set()):
                await self.send_personal_message(message, websocket)
    
    async def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe connection to a specific topic"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].add(topic)
            logger.info(f"WebSocket subscribed to topic: {topic}")
    
    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe connection from a specific topic"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].discard(topic)
            logger.info(f"WebSocket unsubscribed from topic: {topic}")
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await self.subscribe(websocket, topic)
                    await self.send_personal_message({
                        "type": "subscription_confirmed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            
            elif message_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    await self.unsubscribe(websocket, topic)
                    await self.send_personal_message({
                        "type": "unsubscription_confirmed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            
            elif message_type == "ping":
                await self.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
            await self.send_personal_message({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.active_connections)
    
    def get_user_connections(self, user_id: int) -> List[WebSocket]:
        """Get all connections for a specific user"""
        return self.active_connections.get(user_id, [])
    
    async def send_job_update(self, job_id: str, user_id: int, status: str, progress: float, message: str):
        """Send job progress update to user"""
        update_message = {
            "type": "job_update",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(update_message, user_id)
    
    async def send_migration_update(self, migration_id: str, user_id: int, status: str, progress: float, phase: str):
        """Send migration progress update to user"""
        update_message = {
            "type": "migration_update",
            "migration_id": migration_id,
            "status": status,
            "progress": progress,
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(update_message, user_id)
    
    async def send_activity_update(self, user_id: int, activity: Dict[str, Any]):
        """Send new activity to user's activity feed"""
        update_message = {
            "type": "activity_update",
            "activity": activity,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(update_message, user_id)
    
    async def send_quality_analysis_progress(self, job_id: str, user_id: int, progress: float, stage: str):
        """Send data quality analysis progress update"""
        update_message = {
            "type": "quality_analysis_progress",
            "job_id": job_id,
            "progress": progress,
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(update_message, user_id)
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Send system-wide alert to all users"""
        alert_message = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(alert_message)
    
    async def send_dashboard_metrics_update(self, user_id: int, metrics: Dict[str, Any]):
        """Send dashboard metrics update to user"""
        update_message = {
            "type": "dashboard_metrics_update",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(update_message, user_id)


# Global connection manager instance
connection_manager = ConnectionManager()


# Background task to send periodic updates
async def periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            # Send heartbeat every 30 seconds
            await asyncio.sleep(30)
            
            if connection_manager.get_connection_count() > 0:
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_connections": connection_manager.get_connection_count(),
                    "active_users": connection_manager.get_user_count()
                }
                await connection_manager.broadcast(heartbeat_message)
                
        except Exception as e:
            logger.error(f"Error in periodic updates: {str(e)}")
            await asyncio.sleep(30)


# Start periodic updates task
async def start_periodic_updates():
    """Start the periodic updates background task"""
    asyncio.create_task(periodic_updates())