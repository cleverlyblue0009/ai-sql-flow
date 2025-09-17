#!/usr/bin/env python3
"""
Direct test of Firebase authentication without complex imports
"""

import sys
import os
sys.path.append('/workspace')

# Test the authentication directly
def test_firebase_auth():
    try:
        # Import just the auth security module
        from app.auth.security import verify_firebase_token
        
        # Test development tokens
        test_tokens = [
            "dev-mock-firebase-token-for-development",
            "mock-firebase-token-for-dev",
            "dev-test-token",
            "mock-token-123"
        ]
        
        print("🧪 Testing Firebase token verification...")
        
        for token in test_tokens:
            print(f"\n🔍 Testing token: {token}")
            result = verify_firebase_token(token)
            if result:
                print(f"✅ Token accepted! User: {result.get('email', 'unknown')}")
                return True
            else:
                print("❌ Token rejected")
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")
        return False

if __name__ == "__main__":
    success = test_firebase_auth()
    if success:
        print("\n🎉 Authentication is working!")
    else:
        print("\n💥 Authentication failed")
    
    sys.exit(0 if success else 1)