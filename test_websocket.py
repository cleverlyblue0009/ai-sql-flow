#!/usr/bin/env python3
"""
Simple WebSocket test to verify the migration WebSocket endpoint works
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8002/ws/migration?token=dev-mock-firebase-token-for-development"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket!")
            
            # Send a test message
            test_message = {
                "type": "subscribe_migration",
                "migration_id": "test-migration-123"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Sent subscription message")
            
            # Wait for responses
            for i in range(3):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"📥 Received: {data['type']}")
                    if data.get('migration_id'):
                        print(f"   Migration ID: {data['migration_id']}")
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print("🔌 Closing connection")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket connection to ws://localhost:8002/ws/migration")
    asyncio.run(test_websocket())