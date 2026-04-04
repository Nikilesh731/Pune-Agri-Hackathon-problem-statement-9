#!/usr/bin/env python3
"""Test backend AI processing directly"""

import requests
import json

def test_backend_ai_processing():
    # First, let's create a test application or trigger AI processing on existing one
    backend_url = "http://localhost:3001"
    
    # Test 1: Check if we can reach backend
    try:
        response = requests.get(f"{backend_url}/api/applications", timeout=10)
        print(f"Backend health check: {response.status_code}")
        if response.status_code == 200:
            apps = response.json()
            print(f"Found {len(apps)} applications")
            if apps:
                app_id = apps[0].get('id')
                print(f"Testing with application ID: {app_id}")
                
                # Test 2: Trigger AI processing
                try:
                    process_response = requests.post(
                        f"{backend_url}/api/applications/{app_id}/process-ai",
                        timeout=30
                    )
                    print(f"AI processing trigger: {process_response.status_code}")
                    print(f"Response: {process_response.text}")
                    
                except Exception as e:
                    print(f"AI processing failed: {e}")
        else:
            print(f"Backend error: {response.text}")
            
    except Exception as e:
        print(f"Backend connection failed: {e}")

    # Test 3: Direct AI orchestrator test
    try:
        ai_payload = {
            "processing_type": "extract_structured",
            "options": {
                "fileName": "test.pdf",
                "fileType": "application/pdf",
                "ocr_text": """Applicant Details
Farmer Name: Ravi Kumar
Scheme Name: Pradhan Mantri Kisan Samman Nidhi
Requested Amount: Rs. 6,000"""
            },
            "extract_metadata": True
        }
        
        print(f"\nTesting AI orchestrator directly...")
        print(f"Payload: {json.dumps(ai_payload, indent=2)}")
        
        # This would be the exact call backend makes
        ai_response = requests.post(
            "http://localhost:8000/api/document-processing/process-from-metadata",
            json=ai_payload,
            timeout=30
        )
        
        print(f"AI Service Response: {ai_response.status_code}")
        if ai_response.status_code == 200:
            result = ai_response.json()
            print(f"✅ AI Service working!")
            print(f"Document type: {result.get('data', {}).get('document_type')}")
            print(f"Summary: {result.get('data', {}).get('summary')}")
        else:
            print(f"❌ AI Service error: {ai_response.text}")
            
    except Exception as e:
        print(f"AI Service connection failed: {e}")

if __name__ == "__main__":
    test_backend_ai_processing()
