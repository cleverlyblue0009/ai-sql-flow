#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test():
    try:
        uri = "ws://localhost:8002/ws/migration?token=dev-mock-firebase-token-for-development"
        async with websockets.connect(uri) as ws:
            print("✅ CONNECTED!")
            
            # Send test message
            await ws.send(json.dumps({"type": "subscribe_migration", "migration_id": "test-123"}))
            
            # Get response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            print(f"✅ RECEIVED: {data['type']}")
            
            return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)