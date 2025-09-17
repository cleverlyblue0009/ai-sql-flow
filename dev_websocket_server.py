#!/usr/bin/env python3
"""
Development WebSocket server for testing migration progress
This is a simplified server that doesn't require Firebase authentication
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockMigrationServer:
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # migration_id -> set of connection_ids
        
    async def register_connection(self, websocket, connection_id: str):
        """Register a new WebSocket connection"""
        self.connections[connection_id] = websocket
        logger.info(f"Connection {connection_id} registered")
        
        # Send welcome message
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "message": "Connected to migration progress service",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def unregister_connection(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            
        # Remove from all subscriptions
        for migration_id, connections in list(self.subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.subscriptions[migration_id]
                
        logger.info(f"Connection {connection_id} unregistered")
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to a specific connection"""
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                await self.unregister_connection(connection_id)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
    
    async def handle_message(self, connection_id: str, message_data: dict):
        """Handle incoming WebSocket messages"""
        message_type = message_data.get("type")
        
        if message_type == "subscribe_migration":
            migration_id = message_data.get("migration_id")
            if migration_id:
                if migration_id not in self.subscriptions:
                    self.subscriptions[migration_id] = set()
                self.subscriptions[migration_id].add(connection_id)
                
                await self.send_to_connection(connection_id, {
                    "type": "subscription_confirmed",
                    "migration_id": migration_id
                })
                
                # Send mock initial status
                await self.send_to_connection(connection_id, {
                    "type": "migration_progress",
                    "migration_id": migration_id,
                    "data": {
                        "progress_percentage": 0,
                        "current_phase": "Initializing",
                        "status": "starting",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
                # Start mock progress updates
                asyncio.create_task(self.simulate_migration_progress(migration_id))
                
        elif message_type == "unsubscribe_migration":
            migration_id = message_data.get("migration_id")
            if migration_id and migration_id in self.subscriptions:
                self.subscriptions[migration_id].discard(connection_id)
                if not self.subscriptions[migration_id]:
                    del self.subscriptions[migration_id]
                
                await self.send_to_connection(connection_id, {
                    "type": "unsubscription_confirmed",
                    "migration_id": migration_id
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
    
    async def simulate_migration_progress(self, migration_id: str):
        """Simulate migration progress updates"""
        phases = [
            ("Initializing", 5),
            ("Source Connection", 15),
            ("Schema Analysis", 30),
            ("SQL Translation", 50),
            ("Validation", 70),
            ("Data Migration", 90),
            ("Performance Test", 100)
        ]
        
        for phase, progress in phases:
            if migration_id not in self.subscriptions:
                break
                
            # Send progress update to all subscribers
            for connection_id in list(self.subscriptions[migration_id]):
                await self.send_to_connection(connection_id, {
                    "type": "migration_progress",
                    "migration_id": migration_id,
                    "data": {
                        "progress_percentage": progress,
                        "current_phase": phase,
                        "status": "running" if progress < 100 else "completed",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            # Wait before next update
            await asyncio.sleep(3)
        
        # Send completion message
        if migration_id in self.subscriptions:
            for connection_id in list(self.subscriptions[migration_id]):
                await self.send_to_connection(connection_id, {
                    "type": "migration_completed",
                    "migration_id": migration_id,
                    "timestamp": datetime.utcnow().isoformat()
                })

# Global server instance
migration_server = MockMigrationServer()

async def handle_websocket(websocket, path):
    """Handle WebSocket connections"""
    connection_id = f"conn_{id(websocket)}"
    
    try:
        # Simple authentication check - accept any connection with a token parameter
        query_params = dict(param.split('=') for param in (path.split('?')[1] if '?' in path else '').split('&') if param)
        token = query_params.get('token')
        
        if not token or token == 'null' or token == 'undefined':
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Register connection
        await migration_server.register_connection(websocket, connection_id)
        
        # Listen for messages
        async for message in websocket:
            try:
                message_data = json.loads(message)
                await migration_server.handle_message(connection_id, message_data)
            except json.JSONDecodeError:
                await migration_server.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await migration_server.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Error processing message"
                })
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection {connection_id} closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await migration_server.unregister_connection(connection_id)

async def main():
    """Start the WebSocket server"""
    logger.info("Starting development WebSocket server on ws://localhost:8000/ws/migration")
    
    async with websockets.serve(handle_websocket, "localhost", 8000):
        logger.info("WebSocket server started. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")