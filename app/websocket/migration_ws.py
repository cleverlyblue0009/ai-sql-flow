"""
WebSocket service for real-time migration progress tracking
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket
from sqlalchemy.orm import Session

from .manager import ConnectionManager
from ..database import get_db, MigrationLog, Job, User

logger = logging.getLogger(__name__)


class MigrationProgressManager:
    """Manages WebSocket connections for migration progress tracking"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.migration_subscriptions: Dict[str, Set[str]] = {}  # migration_id -> set of connection_ids
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> set of connection_ids
        self.active_migrations: Dict[str, Dict[str, Any]] = {}  # migration_id -> progress data
        
    async def connect_user(self, websocket: WebSocket, user_id: int, connection_id: str):
        """Connect a user to the migration progress service"""
        try:
            # Register the already accepted WebSocket connection
            await self.connection_manager.register_connection(websocket, connection_id, user_id)
            
            # Track user connection
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Send initial connection confirmation
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "message": "Connected to migration progress service",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"User {user_id} connected to migration progress service")
            
        except Exception as e:
            logger.error(f"Error connecting user {user_id}: {str(e)}")
            raise
    
    async def disconnect_user(self, connection_id: str, user_id: Optional[int] = None):
        """Disconnect a user from the migration progress service"""
        try:
            await self.connection_manager.disconnect(connection_id)
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from migration subscriptions
            for migration_id, connections in list(self.migration_subscriptions.items()):
                connections.discard(connection_id)
                if not connections:
                    del self.migration_subscriptions[migration_id]
            
            logger.info(f"User connection {connection_id} disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting user {connection_id}: {str(e)}")
    
    async def subscribe_to_migration(self, connection_id: str, migration_id: str, user_id: int):
        """Subscribe a connection to migration progress updates"""
        try:
            # Verify user has access to this migration (basic check)
            # In production, you'd verify project ownership/permissions
            
            if migration_id not in self.migration_subscriptions:
                self.migration_subscriptions[migration_id] = set()
            
            self.migration_subscriptions[migration_id].add(connection_id)
            
            # Send current migration status if available
            if migration_id in self.active_migrations:
                await self.send_to_connection(connection_id, {
                    "type": "migration_status",
                    "migration_id": migration_id,
                    "data": self.active_migrations[migration_id]
                })
            
            logger.info(f"Connection {connection_id} subscribed to migration {migration_id}")
            
        except Exception as e:
            logger.error(f"Error subscribing to migration {migration_id}: {str(e)}")
    
    async def unsubscribe_from_migration(self, connection_id: str, migration_id: str):
        """Unsubscribe a connection from migration progress updates"""
        try:
            if migration_id in self.migration_subscriptions:
                self.migration_subscriptions[migration_id].discard(connection_id)
                if not self.migration_subscriptions[migration_id]:
                    del self.migration_subscriptions[migration_id]
            
            logger.info(f"Connection {connection_id} unsubscribed from migration {migration_id}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing from migration {migration_id}: {str(e)}")
    
    async def broadcast_migration_progress(self, migration_id: str, progress_data: Dict[str, Any]):
        """Broadcast migration progress to all subscribed connections"""
        try:
            # Update active migrations cache
            self.active_migrations[migration_id] = {
                **progress_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Get subscribed connections
            if migration_id in self.migration_subscriptions:
                connections = self.migration_subscriptions[migration_id]
                
                message = {
                    "type": "migration_progress",
                    "migration_id": migration_id,
                    "data": self.active_migrations[migration_id]
                }
                
                # Send to all subscribed connections
                await self.connection_manager.broadcast_to_connections(
                    message, list(connections)
                )
                
                logger.info(f"Broadcasted progress for migration {migration_id} to {len(connections)} connections")
            
        except Exception as e:
            logger.error(f"Error broadcasting migration progress: {str(e)}")
    
    async def broadcast_migration_status(self, migration_id: str, status: str, message: str, additional_data: Optional[Dict] = None):
        """Broadcast migration status change to subscribed connections"""
        try:
            status_data = {
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if additional_data:
                status_data.update(additional_data)
            
            # Update active migrations cache
            if migration_id in self.active_migrations:
                self.active_migrations[migration_id].update(status_data)
            else:
                self.active_migrations[migration_id] = status_data
            
            # Broadcast to subscribed connections
            if migration_id in self.migration_subscriptions:
                connections = self.migration_subscriptions[migration_id]
                
                ws_message = {
                    "type": "migration_status_change",
                    "migration_id": migration_id,
                    "data": status_data
                }
                
                await self.connection_manager.broadcast_to_connections(
                    ws_message, list(connections)
                )
                
                logger.info(f"Broadcasted status change for migration {migration_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error broadcasting migration status: {str(e)}")
    
    async def send_migration_error(self, migration_id: str, error_message: str, error_details: Optional[Dict] = None):
        """Send migration error to subscribed connections"""
        try:
            error_data = {
                "error": error_message,
                "details": error_details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if migration_id in self.migration_subscriptions:
                connections = self.migration_subscriptions[migration_id]
                
                message = {
                    "type": "migration_error",
                    "migration_id": migration_id,
                    "data": error_data
                }
                
                await self.connection_manager.broadcast_to_connections(
                    message, list(connections)
                )
                
                logger.info(f"Sent error notification for migration {migration_id}")
            
        except Exception as e:
            logger.error(f"Error sending migration error: {str(e)}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection"""
        try:
            await self.connection_manager.send_personal_message(json.dumps(message), connection_id)
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {str(e)}")
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """Send message to all connections for a specific user"""
        try:
            if user_id in self.user_connections:
                connections = list(self.user_connections[user_id])
                await self.connection_manager.broadcast_to_connections(message, connections)
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
    
    async def handle_client_message(self, connection_id: str, message: Dict[str, Any], user_id: int):
        """Handle incoming WebSocket messages from clients"""
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe_migration":
                migration_id = message.get("migration_id")
                if migration_id:
                    await self.subscribe_to_migration(connection_id, migration_id, user_id)
                    await self.send_to_connection(connection_id, {
                        "type": "subscription_confirmed",
                        "migration_id": migration_id
                    })
            
            elif message_type == "unsubscribe_migration":
                migration_id = message.get("migration_id")
                if migration_id:
                    await self.unsubscribe_from_migration(connection_id, migration_id)
                    await self.send_to_connection(connection_id, {
                        "type": "unsubscription_confirmed",
                        "migration_id": migration_id
                    })
            
            elif message_type == "get_migration_status":
                migration_id = message.get("migration_id")
                if migration_id and migration_id in self.active_migrations:
                    await self.send_to_connection(connection_id, {
                        "type": "migration_status",
                        "migration_id": migration_id,
                        "data": self.active_migrations[migration_id]
                    })
            
            elif message_type == "ping":
                await self.send_to_connection(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                await self.send_to_connection(connection_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
            
        except Exception as e:
            logger.error(f"Error handling client message: {str(e)}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "message": "Error processing message"
            })
    
    async def cleanup_completed_migration(self, migration_id: str):
        """Clean up resources for completed migration"""
        try:
            # Keep the migration data for a while for clients to fetch final status
            # In production, you might want to implement a TTL-based cleanup
            
            # Optionally notify subscribers that migration is complete
            if migration_id in self.migration_subscriptions:
                connections = self.migration_subscriptions[migration_id]
                
                message = {
                    "type": "migration_completed",
                    "migration_id": migration_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.connection_manager.broadcast_to_connections(
                    message, list(connections)
                )
            
            logger.info(f"Cleaned up resources for completed migration {migration_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up migration {migration_id}: {str(e)}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        return {
            "total_connections": len(self.connection_manager.active_connections),
            "total_users": len(self.user_connections),
            "active_migrations": len(self.active_migrations),
            "migration_subscriptions": len(self.migration_subscriptions),
            "connections_per_migration": {
                migration_id: len(connections) 
                for migration_id, connections in self.migration_subscriptions.items()
            }
        }


# Global instance
migration_progress_manager = MigrationProgressManager()


# Helper functions for background tasks
async def update_migration_progress(
    migration_id: str,
    progress_percentage: float,
    current_phase: str,
    current_step: Optional[str] = None,
    additional_data: Optional[Dict] = None
):
    """Update migration progress and broadcast to subscribers"""
    progress_data = {
        "progress_percentage": progress_percentage,
        "current_phase": current_phase,
        "current_step": current_step,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if additional_data:
        progress_data.update(additional_data)
    
    await migration_progress_manager.broadcast_migration_progress(migration_id, progress_data)


async def notify_migration_status_change(
    migration_id: str,
    status: str,
    message: str,
    additional_data: Optional[Dict] = None
):
    """Notify migration status change"""
    await migration_progress_manager.broadcast_migration_status(
        migration_id, status, message, additional_data
    )


async def notify_migration_error(
    migration_id: str,
    error_message: str,
    error_details: Optional[Dict] = None
):
    """Notify migration error"""
    await migration_progress_manager.send_migration_error(
        migration_id, error_message, error_details
    )