#!/usr/bin/env python3
"""
Simple script to test WebSocket connection and identify issues
"""
import asyncio
import json
import websockets
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_websocket_connection():
    """Test WebSocket connection with mock authentication"""
    
    # Test URLs
    websocket_urls = [
        "ws://localhost:8000/ws/migration?token=mock-token-for-testing",
        "ws://localhost:8000/ws?token=mock-token-for-testing"
    ]
    
    for url in websocket_urls:
        print(f"\n🔍 Testing WebSocket connection: {url}")
        
        try:
            async with websockets.connect(url, timeout=10) as websocket:
                print("✅ WebSocket connected successfully!")
                
                # Send a test message
                test_message = {
                    "type": "ping",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                
                await websocket.send(json.dumps(test_message))
                print("📤 Sent ping message")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📥 Received response: {response}")
                except asyncio.TimeoutError:
                    print("⚠️  No response received within 5 seconds")
                
        except websockets.exceptions.ConnectionClosed as e:
            print(f"❌ Connection closed: {e}")
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"❌ Invalid status code: {e}")
        except ConnectionRefusedError:
            print("❌ Connection refused - server may not be running")
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")

def check_server_status():
    """Check if the FastAPI server is running"""
    import requests
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI server is running")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI server is not running")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 WebSocket Connection Test")
    print("=" * 50)
    
    # Check if server is running
    if not check_server_status():
        print("\n💡 To start the server, run:")
        print("   cd /workspace && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # Test WebSocket connections
    await test_websocket_connection()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")