# app/websocket/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..auth.security import verify_firebase_token_websocket  # ✅ firebase auth for websockets
from .manager import connection_manager
from .migration_ws import migration_progress_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = verify_firebase_token_websocket(token)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    connection_id = f"user:{user['uid']}"

    try:
        await connection_manager.connect(websocket, connection_id, user['uid'])
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket, token: str):
    user = verify_firebase_token_websocket(token)
    if not user or not user.get("is_admin"):  # you may need a custom claim for this
        await websocket.close(code=4003, reason="Unauthorized - admin access required")
        return

    connection_id = f"admin:{user['uid']}"

    try:
        await connection_manager.connect(websocket, connection_id, user['uid'])
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Admin message received: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/migration")
async def migration_websocket_endpoint(websocket: WebSocket, token: str):
    # Verify Firebase token using WebSocket-compatible function
    user = verify_firebase_token_websocket(token)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed - invalid or expired Firebase token")
        return

    connection_id = f"migration:{user['uid']}"

    try:
        await migration_progress_manager.connect_user(websocket, user['uid'], connection_id)
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages from client
            try:
                import json
                message = json.loads(data)
                await migration_progress_manager.handle_client_message(connection_id, message, user['uid'])
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
        await migration_progress_manager.disconnect_user(connection_id, user['uid'])