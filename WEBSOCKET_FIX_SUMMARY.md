# WebSocket 403 Forbidden Error Fix

## Problem Description

The application was experiencing WebSocket connection errors with the following symptoms:

```
INFO:     connection rejected (403 Forbidden)
INFO:     connection closed
INFO:     ('127.0.0.1', 50963) - "WebSocket /ws/migration" 403
2025-09-15 12:34:06,677 - app.websocket.migration_ws - INFO - User connection 629f7951-980e-4117-a4af-db1c53881657 disconnected
```

## Root Cause Analysis

The issue was in the WebSocket authentication flow in `/app/websocket/routes.py`. The original code was:

1. **Attempting authentication before accepting the WebSocket connection**
2. **Closing the connection with error codes before the client could receive any feedback**
3. **FastAPI was translating WebSocket close codes to HTTP 403 Forbidden responses**

### Original Problematic Code Pattern:

```python
@router.websocket("/ws/migration")
async def migration_websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    try:
        # ❌ Authentication before accepting connection
        if token:
            user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication required")  # ❌ No feedback to client
            return
        # ... rest of the code
```

## Solution Implemented

### Key Changes:

1. **Accept WebSocket Connection First**: Always accept the WebSocket connection before attempting authentication
2. **Send Structured Error Messages**: Provide clear JSON error responses before closing connections
3. **Proper Connection Management**: Use a new `register_connection` method for already-accepted connections

### Fixed Code Pattern:

```python
@router.websocket("/ws/migration")
async def migration_websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    try:
        # ✅ Accept connection first
        await websocket.accept()
        
        # ✅ Then authenticate
        if token:
            try:
                user = await get_current_user_from_token(token, db)
            except Exception as e:
                # ✅ Send structured error before closing
                await websocket.send_json({
                    "type": "error",
                    "message": "Authentication failed",
                    "error_code": "AUTH_FAILED"
                })
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        if not user:
            # ✅ Send structured error before closing
            await websocket.send_json({
                "type": "error", 
                "message": "Authentication required",
                "error_code": "AUTH_REQUIRED"
            })
            await websocket.close(code=4001, reason="Authentication required")
            return
```

## Files Modified

### 1. `/app/websocket/routes.py`
- **Fixed all WebSocket endpoints**: `/ws`, `/ws/admin`, `/ws/migration`
- **Added proper error handling**: Accept connection first, then authenticate
- **Structured error responses**: JSON error messages with error codes

### 2. `/app/websocket/manager.py`
- **Added `register_connection` method**: For already-accepted WebSocket connections
- **Maintains backward compatibility**: Original `connect` method still works for new connections

### 3. `/app/websocket/migration_ws.py`
- **Updated to use `register_connection`**: Prevents double-acceptance of WebSocket connections
- **Improved error handling**: Better integration with the connection manager

## Benefits of the Fix

### 1. **Better User Experience**
- Clients receive clear error messages instead of generic HTTP 403 errors
- Structured JSON responses with error codes for programmatic handling

### 2. **Improved Debugging**
- Clear error messages help identify authentication issues
- Proper logging of connection attempts and failures

### 3. **Standards Compliance**
- Follows WebSocket protocol standards for connection establishment
- Proper handling of authentication in WebSocket context

### 4. **Backward Compatibility**
- Existing WebSocket clients continue to work
- No breaking changes to the API interface

## Error Response Format

Clients now receive structured error responses:

```json
{
  "type": "error",
  "message": "Authentication required",
  "error_code": "AUTH_REQUIRED"
}
```

### Error Codes:
- `AUTH_REQUIRED`: No authentication token provided
- `AUTH_FAILED`: Invalid or expired authentication token
- `ADMIN_REQUIRED`: Admin privileges required for admin endpoints

## Testing

A test script has been created at `/workspace/test_websocket_fix.py` to verify the fix:

```bash
python test_websocket_fix.py
```

This script tests:
1. Connection without token (should get AUTH_REQUIRED error)
2. Connection with invalid token (should get AUTH_FAILED error)
3. Proper error message structure and connection handling

## Prevention

To prevent similar issues in the future:

1. **Always accept WebSocket connections before authentication**
2. **Send structured error responses before closing connections**
3. **Use proper WebSocket error codes and messages**
4. **Test WebSocket endpoints with various authentication scenarios**

## Monitoring

The fix includes improved logging:
- Connection attempts are logged with user information
- Authentication failures are logged with specific error details
- Connection cleanup is properly tracked

This should eliminate the 403 Forbidden errors and provide a much better experience for WebSocket clients.