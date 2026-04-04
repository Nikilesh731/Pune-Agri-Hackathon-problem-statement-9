#!/usr/bin/env python3
"""
Enhanced cleanup script to remove all applications from database
Uses the new cleanup endpoint with mode=all for efficient bulk deletion
"""

import requests
import sys
import time

BACKEND_URL = "http://localhost:3001"
API_BASE = f"{BACKEND_URL}/api/applications"

def cleanup_all_applications():
    """Remove all applications using the new cleanup endpoint"""
    print("🧹 Using enhanced cleanup endpoint with mode=all...")
    
    try:
        # Use the new cleanup endpoint with mode=all for efficient bulk deletion
        response = requests.post(f"{API_BASE}/cleanup", json={"mode": "all"})
        
        if response.status_code == 200:
            result = response.json()
            deleted_count = result.get('count', 0)
            message = result.get('message', 'Unknown')
            mode = result.get('mode', 'unknown')
            
            print(f"✅ Cleanup successful!")
            print(f"   Mode: {mode}")
            print(f"   Message: {message}")
            print(f"   Deleted: {deleted_count} applications")
            
            # Verify cleanup worked
            time.sleep(1)
            verify_response = requests.get(f"{API_BASE}")
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                remaining = verify_data.get('total', 0)
                print(f"   Verified: {remaining} applications remaining")
                
                if remaining == 0:
                    print("   ✨ Database is completely clean!")
                else:
                    print(f"   ⚠️  Warning: {remaining} applications still remain")
            
            return deleted_count > 0
        else:
            print(f"❌ Cleanup failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    print("🧹 CLEANING ALL APPLICATIONS")
    print("=" * 40)
    
    success = cleanup_all_applications()
    
    if success:
        print("✅ Cleanup completed successfully")
    else:
        print("❌ Cleanup failed")
        sys.exit(1)
