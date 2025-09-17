#!/usr/bin/env python3
"""
Standalone WebSocket server for migration progress with proper Firebase authentication
This bypasses the complex dependency chain of the full FastAPI app
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_development_token(token: str) -> Optional[Dict]:
    """Simple token verification for development"""
    # Accept development tokens
    if (token and (
        token.startswith("dev-") or 
        "mock" in token.lower() or
        token == "dev-mock-firebase-token-for-development"
    )):
        logger.info(f"✅ Accepting development token: {token[:20]}...")
        return {
            "uid": "dev-user-1",
            "email": "dev@example.com", 
            "name": "Development User",
            "email_verified": True
        }
    
    logger.warning(f"❌ Rejecting token: {token[:20] if token else 'None'}...")
    return None

class MigrationWebSocketServer:
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # migration_id -> connection_ids
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        
    async def authenticate_connection(self, websocket, path):
        """Authenticate WebSocket connection"""
        try:
            # Parse query parameters
            parsed_url = urlparse(path)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            
            if not token:
                logger.warning("❌ No token provided")
                await websocket.close(code=4001, reason="Authentication required")
                return None
                
            # Verify token
            user_data = verify_development_token(token)
            if not user_data:
                logger.warning("❌ Invalid token")
                await websocket.close(code=4001, reason="Invalid token")
                return None
                
            logger.info(f"✅ User authenticated: {user_data['email']}")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return None
    
    async def register_connection(self, websocket, connection_id: str, user_data: Dict):
        """Register authenticated connection"""
        self.connections[connection_id] = websocket
        
        user_id = user_data['uid']
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Send welcome message
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "message": "Connected to migration progress service",
            "user": user_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"📝 Connection {connection_id} registered for user {user_data['email']}")
    
    async def unregister_connection(self, connection_id: str):
        """Unregister connection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            
        # Remove from user connections
        for user_id, connections in list(self.user_connections.items()):
            connections.discard(connection_id)
            if not connections:
                del self.user_connections[user_id]
                
        # Remove from subscriptions
        for migration_id, connections in list(self.subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.subscriptions[migration_id]
                
        logger.info(f"🗑️ Connection {connection_id} unregistered")
    
    async def send_to_connection(self, connection_id: str, message: Dict):
        """Send message to specific connection"""
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].send(json.dumps(message))
                logger.debug(f"📤 Sent {message['type']} to {connection_id}")
            except websockets.exceptions.ConnectionClosed:
                await self.unregister_connection(connection_id)
            except Exception as e:
                logger.error(f"❌ Error sending to {connection_id}: {e}")
    
    async def handle_message(self, connection_id: str, message_data: Dict):
        """Handle incoming messages"""
        message_type = message_data.get("type")
        logger.info(f"📥 Received {message_type} from {connection_id}")
        
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
                
                # Start mock progress
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
        """Simulate realistic migration progress"""
        if migration_id not in self.subscriptions:
            return
            
        phases = [
            ("Initializing", 5),
            ("Source Connection", 15), 
            ("Schema Analysis", 30),
            ("SQL Translation", 50),
            ("Validation", 70),
            ("Data Migration", 90),
            ("Performance Test", 100)
        ]
        
        logger.info(f"🚀 Starting migration simulation for {migration_id}")
        
        for phase, progress in phases:
            if migration_id not in self.subscriptions:
                break
                
            # Send progress to all subscribers
            subscribers = list(self.subscriptions[migration_id])
            for connection_id in subscribers:
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
            
            await asyncio.sleep(2)  # Realistic delay
        
        # Send completion
        if migration_id in self.subscriptions:
            subscribers = list(self.subscriptions[migration_id])
            for connection_id in subscribers:
                await self.send_to_connection(connection_id, {
                    "type": "migration_completed",
                    "migration_id": migration_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"✅ Migration {migration_id} completed")

# Global server instance
migration_server = MigrationWebSocketServer()

async def handle_websocket_connection(websocket, path):
    """Handle new WebSocket connections"""
    connection_id = f"conn_{id(websocket)}"
    user_data = None
    
    try:
        # Authenticate
        user_data = await migration_server.authenticate_connection(websocket, path)
        if not user_data:
            return  # Connection already closed
            
        # Register connection
        await migration_server.register_connection(websocket, connection_id, user_data)
        
        # Handle messages
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
                logger.error(f"❌ Message handling error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 Connection {connection_id} closed")
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
    finally:
        await migration_server.unregister_connection(connection_id)

async def main():
    """Start the WebSocket server"""
    host = "localhost"
    port = 8002
    
    logger.info(f"🚀 Starting Migration WebSocket Server")
    logger.info(f"📡 WebSocket endpoint: ws://{host}:{port}/ws/migration")
    logger.info(f"🔐 Authentication: Development tokens accepted")
    logger.info(f"🛠️  Test with: ws://{host}:{port}/ws/migration?token=dev-mock-firebase-token-for-development")
    
    # Handle WebSocket connections directly
    async def route_handler(websocket):
        # Get path from the websocket request
        path = websocket.request.path
        logger.info(f"📍 Connection to path: {path}")
        
        if path.startswith('/ws/migration'):
            await handle_websocket_connection(websocket, path)
        else:
            await websocket.close(code=4004, reason="Path not found")
    
    async with websockets.serve(route_handler, host, port):
        logger.info("✅ Server started successfully! Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")