# app/websocket/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..auth.security import verify_firebase_token  # ✅ firebase auth
from .manager import connection_manager
from .migration_ws import migration_progress_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = verify_firebase_token(token)
    if not user:
        await websocket.close(code=1008, reason="Authentication failed")
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
    user = verify_firebase_token(token)
    if not user or not user.get("is_admin"):  # you may need a custom claim for this
        await websocket.close(code=1008, reason="Unauthorized")
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
    try:
        # Verify Firebase token
        user = verify_firebase_token(token)
        if not user:
            await websocket.close(code=1008, reason="Authentication failed")
            return
    except Exception as e:
        # Log the error
        print(f"Firebase token verification failed: {e}")
        await websocket.close(code=1008, reason="Invalid Firebase token")
        return

    connection_id = f"migration:{user['uid']}"

    try:
        await migration_progress_manager.connect_user(websocket, user['uid'], connection_id)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await migration_progress_manager.disconnect_user(connection_id, user['uid'])