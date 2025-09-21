#!/usr/bin/env python3
"""
Simplified backend for testing WebSocket connections
This bypasses complex Firebase authentication for debugging
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="WebSocket Test Server")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple connection manager
class SimpleConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # connection_id -> user_id
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = "test-user"):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.user_connections[connection_id] = user_id
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message(connection_id, {
            "type": "connection_established",
            "message": "Connected to test WebSocket server",
            "user_id": user_id,
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.user_connections:
            del self.user_connections[connection_id]
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)

# Global connection manager
connection_manager = SimpleConnectionManager()

@app.get("/")
async def root():
    return {"message": "WebSocket Test Server", "endpoints": ["/ws", "/ws/migration"]}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "active_connections": len(connection_manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """Main WebSocket endpoint"""
    connection_id = f"conn_{datetime.utcnow().timestamp()}"
    
    try:
        # Simple token validation (for testing)
        if not token:
            await websocket.close(code=4001, reason="Token required for testing")
            return
        
        # Accept any token for testing
        user_id = f"user_{token[-8:]}" if len(token) > 8 else "test-user"
        
        await connection_manager.connect(websocket, connection_id, user_id)
        
        # Message handling loop
        while True:
            try:
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                logger.info(f"Received message from {connection_id}: {message}")
                
                # Handle different message types
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                        "original_message": message
                    })
                
                elif message_type == "subscribe_migration":
                    migration_id = message.get("migration_id", "test-migration")
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "subscription_confirmed",
                        "migration_id": migration_id,
                        "message": f"Subscribed to migration {migration_id}"
                    })
                
                else:
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await connection_manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await connection_manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": f"Server error: {str(e)}"
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(connection_id)

@app.websocket("/ws/migration")
async def migration_websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """Migration-specific WebSocket endpoint"""
    connection_id = f"migration_conn_{datetime.utcnow().timestamp()}"
    
    try:
        # Simple token validation
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        user_id = f"user_{token[-8:]}" if len(token) > 8 else "test-user"
        
        await connection_manager.connect(websocket, connection_id, user_id)
        
        # Send initial migration status
        await connection_manager.send_personal_message(connection_id, {
            "type": "migration_status",
            "migration_id": "test-migration",
            "status": "ready",
            "message": "Migration WebSocket connected successfully"
        })
        
        # Message handling loop
        while True:
            try:
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                logger.info(f"Migration message from {connection_id}: {message}")
                
                message_type = message.get("type", "unknown")
                
                if message_type == "subscribe_migration":
                    migration_id = message.get("migration_id", "default-migration")
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "subscription_confirmed",
                        "migration_id": migration_id
                    })
                    
                    # Simulate migration progress
                    for progress in [25, 50, 75, 100]:
                        await asyncio.sleep(1)
                        await connection_manager.send_personal_message(connection_id, {
                            "type": "migration_progress",
                            "migration_id": migration_id,
                            "data": {
                                "progress_percentage": progress,
                                "current_phase": f"Processing step {progress//25}",
                                "status": "completed" if progress == 100 else "running"
                            }
                        })
                
                elif message_type == "ping":
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                else:
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await connection_manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error in migration WebSocket: {e}")
                
    except Exception as e:
        logger.error(f"Migration WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(connection_id)

if __name__ == "__main__":
    print("🚀 Starting simplified WebSocket test server...")
    print("📡 WebSocket endpoints:")
    print("   ws://localhost:8000/ws?token=your-token")
    print("   ws://localhost:8000/ws/migration?token=your-token")
    print("🌐 HTTP endpoints:")
    print("   http://localhost:8000/")
    print("   http://localhost:8000/health")
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )