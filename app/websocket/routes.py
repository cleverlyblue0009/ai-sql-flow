# app/websocket/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .manager import connection_manager
from .migration_ws import migration_progress_manager
import uuid

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Generate a unique connection ID without requiring authentication
    connection_id = f"user:{uuid.uuid4()}"

    try:
        await connection_manager.connect(websocket, connection_id, None)
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    # Generate a unique connection ID without requiring authentication
    connection_id = f"admin:{uuid.uuid4()}"

    try:
        await connection_manager.connect(websocket, connection_id, None)
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Admin message received: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/migration")
async def migration_websocket_endpoint(websocket: WebSocket):
    # Generate a unique connection ID without requiring authentication
    connection_id = f"migration:{uuid.uuid4()}"
    session_id = str(uuid.uuid4())

    try:
        await migration_progress_manager.connect_user(websocket, session_id, connection_id)
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages from client
            try:
                import json
                message = json.loads(data)
                await migration_progress_manager.handle_client_message(connection_id, message, session_id)
            except json.JSONDecodeError:
                # Send error response for invalid JSON
                await migration_progress_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                print(f"Error handling client message: {e}")
                await migration_progress_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Error processing message"
                })
    except WebSocketDisconnect:
        await migration_progress_manager.disconnect_user(connection_id, session_id)