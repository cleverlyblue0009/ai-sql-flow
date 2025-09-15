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
        # Store active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # Store user connections
        self.user_connections: Dict[int, List[str]] = {}
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[int] = None, client_info: Dict[str, Any] = None):
        """Accept WebSocket connection and add to active connections"""
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[connection_id] = websocket
            
            # Store metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "client_info": client_info or {},
                "subscriptions": set()
            }
            
            # Track user connections
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = []
                self.user_connections[user_id].append(connection_id)
            
            logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
            
            # Send welcome message
            await self.send_personal_message(json.dumps({
                "type": "connection_established",
                "message": "WebSocket connection established",
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": connection_id
            }), connection_id)
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {str(e)}")
            await websocket.close()
    
    async def register_connection(self, websocket: WebSocket, connection_id: str, user_id: Optional[int] = None, client_info: Dict[str, Any] = None):
        """Register an already accepted WebSocket connection"""
        try:
            # Store connection (WebSocket is already accepted)
            self.active_connections[connection_id] = websocket
            
            # Store metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "client_info": client_info or {},
                "subscriptions": set()
            }
            
            # Track user connections
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = []
                self.user_connections[user_id].append(connection_id)
            
            logger.info(f"WebSocket registered: {connection_id} for user {user_id}")
            
            # Send welcome message
            await self.send_personal_message(json.dumps({
                "type": "connection_established",
                "message": "WebSocket connection established",
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": connection_id
            }), connection_id)
            
        except Exception as e:
            logger.error(f"Error registering WebSocket: {str(e)}")
            await websocket.close()
    
    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        try:
            # Get metadata
            metadata = self.connection_metadata.get(connection_id)
            if not metadata:
                return
            
            user_id = metadata.get("user_id")
            
            # Remove from active connections
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                if connection_id in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(connection_id)
                
                # Clean up empty user connection lists
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
    
    async def send_personal_message(self, message: str, connection_id: str):
        """Send message to specific WebSocket connection"""
        try:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message to {connection_id}: {str(e)}")
            await self.disconnect(connection_id)

    async def broadcast_to_connections(self, message: Dict[str, Any], connection_ids: List[str]):
        """Send message to specific connections"""
        message_str = json.dumps(message, default=str)
        for connection_id in connection_ids:
            await self.send_personal_message(message_str, connection_id)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: int):
        """Send message to all connections of a specific user"""
        if user_id not in self.user_connections:
            return
        
        # Get all connection IDs for the user
        connection_ids = self.user_connections[user_id].copy()
        await self.broadcast_to_connections(message, connection_ids)
    
    async def broadcast(self, message: Dict[str, Any], exclude_user: Optional[int] = None):
        """Broadcast message to all connected users"""
        for user_id in self.user_connections:
            if exclude_user and user_id == exclude_user:
                continue
            
            await self.send_to_user(message, user_id)
    
    async def send_to_subscribers(self, message: Dict[str, Any], topic: str):
        """Send message to all connections subscribed to a specific topic"""
        subscriber_connections = []
        for connection_id, metadata in self.connection_metadata.items():
            if topic in metadata.get("subscriptions", set()):
                subscriber_connections.append(connection_id)
        
        await self.broadcast_to_connections(message, subscriber_connections)
    
    async def subscribe(self, connection_id: str, topic: str):
        """Subscribe connection to a specific topic"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].add(topic)
            logger.info(f"Connection {connection_id} subscribed to topic: {topic}")
    
    async def unsubscribe(self, connection_id: str, topic: str):
        """Unsubscribe connection from a specific topic"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].discard(topic)
            logger.info(f"Connection {connection_id} unsubscribed from topic: {topic}")
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await self.subscribe(connection_id, topic)
                    await self.send_personal_message(json.dumps({
                        "type": "subscription_confirmed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }), connection_id)
            
            elif message_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    await self.unsubscribe(connection_id, topic)
                    await self.send_personal_message(json.dumps({
                        "type": "unsubscription_confirmed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }), connection_id)
            
            elif message_type == "ping":
                await self.send_personal_message(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }), connection_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
            await self.send_personal_message(json.dumps({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.utcnow().isoformat()
            }), connection_id)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.user_connections)
    
    def get_user_connections(self, user_id: int) -> List[str]:
        """Get all connection IDs for a specific user"""
        return self.user_connections.get(user_id, [])
    
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