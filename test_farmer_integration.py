#!/usr/bin/env python3
"""
End-to-End Farmer Profile Integration Test
Tests the complete flow: AI Processing → Backend Service → Farmer Creation/Linking
"""

import asyncio
import json
import sys
import os
import requests
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:3001"
AI_SERVICE_URL = "http://localhost:8001"

async def test_backend_farmer_integration():
    """Test farmer creation through the complete backend flow"""
    
    print("🧪 Testing End-to-End Farmer Profile Integration")
    print("=" * 60)
    
    # Test 1: Upload farmer record document
    print("\n📄 Test 1: Upload Farmer Record (Should Create New Farmer)")
    
    farmer_record_content = """FARMER RECORD
    
Name: Rajesh Kumar
Father's Name: Suresh Kumar
Aadhaar Number: 234567890123
Mobile Number: 9876543210
Address: 123 Village Street, Rampur
Village: Rampur
District: Bareilly
State: Uttar Pradesh
Land Size: 5 acres
Survey Number: 456/789
"""
    
    try:
        # Create a temporary file
        with open("test_farmer_record.txt", "w") as f:
            f.write(farmer_record_content)
        
        # Upload through backend API
        with open("test_farmer_record.txt", "rb") as f:
            files = {"file": ("farmer_record.txt", f, "text/plain")}
            response = requests.post(f"{BACKEND_URL}/api/applications/upload", files=files)
        
        if response.status_code == 200:
            app1 = response.json()
            print(f"✅ Upload successful: {app1.get('id', 'N/A')}")
            print(f"📋 Status: {app1.get('status', 'N/A')}")
            print(f"🆔 Farmer ID: {app1.get('farmerId', 'None')}")
            
            # Wait for AI processing
            print("⏳ Waiting for AI processing...")
            await asyncio.sleep(10)
            
            # Check updated application
            app_response = requests.get(f"{BACKEND_URL}/api/applications/{app1['id']}")
            if app_response.status_code == 200:
                updated_app = app_response.json()
                print(f"🔄 Updated Status: {updated_app.get('status', 'N/A')}")
                print(f"🆔 Farmer ID: {updated_app.get('farmerId', 'None')}")
                print(f"👤 Farmer Info: {updated_app.get('farmer', 'None')}")
                
                # Check extracted data
                extracted_data = updated_app.get('extractedData', {})
                structured_data = extracted_data.get('structured_data', {})
                print(f"📊 Extracted Name: {structured_data.get('farmer_name', 'N/A')}")
                print(f"📊 Extracted Aadhaar: {structured_data.get('aadhaar_number', 'N/A')}")
                print(f"📊 Extracted Mobile: {structured_data.get('phone_number', 'N/A')}")
            else:
                print(f"❌ Failed to get updated app: {app_response.status_code}")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Upload scheme application with same Aadhaar
    print("\n📄 Test 2: Upload Scheme Application (Should Link to Existing Farmer)")
    
    scheme_application_content = """SCHEME APPLICATION
    
Applicant Name: Rajesh Kumar
Father's Name: Suresh Kumar
Aadhaar Number: 234567890123
Mobile Number: 9876543210
Address: 123 Village Street, Rampur
Village: Rampur
District: Bareilly
State: Uttar Pradesh
Scheme Name: PM Kisan Samman Nidhi
Request Type: New Application
Requested Amount: 6000
Land Size: 5 acres
Survey Number: 456/789
"""
    
    try:
        with open("test_scheme_application.txt", "w") as f:
            f.write(scheme_application_content)
        
        with open("test_scheme_application.txt", "rb") as f:
            files = {"file": ("scheme_application.txt", f, "text/plain")}
            response = requests.post(f"{BACKEND_URL}/api/applications/upload", files=files)
        
        if response.status_code == 200:
            app2 = response.json()
            print(f"✅ Upload successful: {app2.get('id', 'N/A')}")
            print(f"📋 Status: {app2.get('status', 'N/A')}")
            print(f"🆔 Farmer ID: {app2.get('farmerId', 'None')}")
            
            # Wait for AI processing
            print("⏳ Waiting for AI processing...")
            await asyncio.sleep(10)
            
            # Check updated application
            app_response = requests.get(f"{BACKEND_URL}/api/applications/{app2['id']}")
            if app_response.status_code == 200:
                updated_app = app_response.json()
                print(f"🔄 Updated Status: {updated_app.get('status', 'N/A')}")
                print(f"🆔 Farmer ID: {updated_app.get('farmerId', 'None')}")
                print(f"👤 Farmer Info: {updated_app.get('farmer', 'None')}")
                
                # Check if same farmer as Test 1
                if app1 and updated_app.get('farmerId') == app1.get('farmerId'):
                    print("✅ Successfully linked to existing farmer!")
                else:
                    print("⚠️  Different farmer ID - may have created new farmer")
                    
                # Check extracted data
                extracted_data = updated_app.get('extractedData', {})
                structured_data = extracted_data.get('structured_data', {})
                print(f"📊 Extracted Name: {structured_data.get('farmer_name', 'N/A')}")
                print(f"📊 Extracted Aadhaar: {structured_data.get('aadhaar_number', 'N/A')}")
                print(f"📊 Extracted Mobile: {structured_data.get('phone_number', 'N/A')}")
            else:
                print(f"❌ Failed to get updated app: {app_response.status_code}")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Upload document with mobile only
    print("\n📄 Test 3: Upload Document with Mobile Only (Should Create New Farmer)")
    
    mobile_only_content = """GRIEVANCE LETTER
    
Name: Anita Devi
Mobile Number: 9876543211
Address: 456 Colony, New Town
Village: New Town
District: Azamgarh
State: Uttar Pradesh
Issue Summary: Crop insurance claim not processed
"""
    
    try:
        with open("test_mobile_only.txt", "w") as f:
            f.write(mobile_only_content)
        
        with open("test_mobile_only.txt", "rb") as f:
            files = {"file": ("grievance.txt", f, "text/plain")}
            response = requests.post(f"{BACKEND_URL}/api/applications/upload", files=files)
        
        if response.status_code == 200:
            app3 = response.json()
            print(f"✅ Upload successful: {app3.get('id', 'N/A')}")
            print(f"📋 Status: {app3.get('status', 'N/A')}")
            print(f"🆔 Farmer ID: {app3.get('farmerId', 'None')}")
            
            # Wait for AI processing
            print("⏳ Waiting for AI processing...")
            await asyncio.sleep(10)
            
            # Check updated application
            app_response = requests.get(f"{BACKEND_URL}/api/applications/{app3['id']}")
            if app_response.status_code == 200:
                updated_app = app_response.json()
                print(f"🔄 Updated Status: {updated_app.get('status', 'N/A')}")
                print(f"🆔 Farmer ID: {updated_app.get('farmerId', 'None')}")
                print(f"👤 Farmer Info: {updated_app.get('farmer', 'None')}")
                
                # Check extracted data
                extracted_data = updated_app.get('extractedData', {})
                structured_data = extracted_data.get('structured_data', {})
                print(f"📊 Extracted Name: {structured_data.get('farmer_name', 'N/A')}")
                print(f"📊 Extracted Aadhaar: {structured_data.get('aadhaar_number', 'N/A')}")
                print(f"📊 Extracted Mobile: {structured_data.get('phone_number', 'N/A')}")
            else:
                print(f"❌ Failed to get updated app: {app_response.status_code}")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    # Cleanup
    print("\n🧹 Cleaning up test files...")
    for file in ["test_farmer_record.txt", "test_scheme_application.txt", "test_mobile_only.txt"]:
        try:
            os.remove(file)
        except:
            pass
    
    print("\n" + "=" * 60)
    print("📊 END-TO-END FARMER INTEGRATION TEST COMPLETE")
    print("=" * 60)
    print("🎯 Check the results above to verify:")
    print("  1. Farmers are created during AI processing")
    print("  2. Same Aadhaar links to existing farmer")
    print("  3. Mobile-only creates new farmer")
    print("  4. Applications store farmerId correctly")

if __name__ == "__main__":
    asyncio.run(test_backend_farmer_integration())
