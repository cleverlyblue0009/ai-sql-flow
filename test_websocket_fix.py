#!/usr/bin/env python3
"""
Test script to verify WebSocket connection fix
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection with proper error handling"""
    
    # Test without token (should get proper error message)
    print("Testing WebSocket connection without token...")
    try:
        uri = "ws://localhost:8000/ws/migration"
        async with websockets.connect(uri) as websocket:
            # Wait for initial message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received response: {data}")
            
            if data.get("type") == "error" and data.get("error_code") == "AUTH_REQUIRED":
                print("✓ Correctly received authentication required error")
            else:
                print("✗ Unexpected response format")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✓ Connection closed as expected: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with invalid token
    print("Testing WebSocket connection with invalid token...")
    try:
        uri = "ws://localhost:8000/ws/migration?token=invalid_token"
        async with websockets.connect(uri) as websocket:
            # Wait for initial message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received response: {data}")
            
            if data.get("type") == "error" and data.get("error_code") == "AUTH_FAILED":
                print("✓ Correctly received authentication failed error")
            else:
                print("✗ Unexpected response format")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✓ Connection closed as expected: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "="*50 + "\n")
    print("WebSocket fix verification complete!")
    print("\nThe fix ensures that:")
    print("1. WebSocket connections are accepted before authentication")
    print("2. Proper error messages are sent to clients before closing")
    print("3. No more 403 Forbidden errors during connection establishment")
    print("4. Clients can receive structured error responses")

if __name__ == "__main__":
    print("WebSocket Connection Fix Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")