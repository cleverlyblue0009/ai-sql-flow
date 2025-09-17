#!/usr/bin/env python3
"""
Test real Firebase credentials
"""

import sys
import os
import json

def test_firebase_credentials():
    """Test if Firebase credentials are real or mock"""
    
    credentials_path = "firebase/service-account.json"
    
    try:
        # Check if file exists
        if not os.path.exists(credentials_path):
            print("❌ Firebase credentials file not found!")
            return False
        
        # Read the file
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        # Check if it's still the mock file
        if "MOCK_PRIVATE_KEY_FOR_DEVELOPMENT_ONLY" in creds.get("private_key", ""):
            print("⚠️  Still using MOCK credentials")
            print("📋 To fix:")
            print("1. Go to https://console.firebase.google.com/")
            print("2. Select project 'dataflow-abb8a'")
            print("3. Go to Project Settings → Service Accounts")
            print("4. Click 'Generate new private key'")
            print("5. Download the JSON file")
            print(f"6. Replace {credentials_path} with the downloaded file")
            return False
        
        # Check if it has the right project ID
        if creds.get("project_id") != "dataflow-abb8a":
            print(f"❌ Wrong project ID: {creds.get('project_id')}")
            print("Expected: dataflow-abb8a")
            return False
        
        # Check if it looks like a real Firebase service account
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if not creds.get(field)]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ Firebase credentials look valid!")
        print(f"📧 Service account: {creds.get('client_email')}")
        print(f"🏷️  Project ID: {creds.get('project_id')}")
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in credentials file")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking Firebase credentials...")
    success = test_firebase_credentials()
    sys.exit(0 if success else 1)