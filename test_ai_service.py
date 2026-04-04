#!/usr/bin/env python3
"""Test AI service directly"""

import requests
import json

def test_ai_service():
    url = "http://localhost:8000/api/document-processing/process-from-metadata"
    
    payload = {
        "processing_type": "extract_structured",
        "options": {
            "fileName": "test.pdf",
            "fileType": "application/pdf",
            "ocr_text": """Applicant Details
Farmer Name: Ravi Kumar
Father / Guardian Name: Mohan Lal
Aadhaar Number: 123456789012
Mobile Number: 9876543210
Village: Karari
District: Kaushambi
State: Uttar Pradesh
Address: House No. 12, Ward 4, Karari, Kaushambi, Uttar Pradesh - 212206

Agriculture Details
Land Size: 2.5 acres
Survey Number: KH-45/12
Crop Name: Paddy
Season: Kharif 2026
Location: Karari block agricultural land parcel

Request Details
Scheme Name: Pradhan Mantri Kisan Samman Nidhi
Request Type: Fresh application
Requested Amount: Rs. 6,000"""
        },
        "extract_metadata": True
    }
    
    try:
        print("Testing AI service...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse Body: {json.dumps(result, indent=2)}")
            
            # Check if we have the expected fields
            if result.get("success") and result.get("data"):
                data = result["data"]
                print(f"\n✅ SUCCESS!")
                print(f"Document Type: {data.get('document_type')}")
                print(f"Confidence: {data.get('confidence')}")
                print(f"Structured Data: {data.get('structured_data', {})}")
                print(f"Missing Fields: {data.get('missing_fields', [])}")
                print(f"Summary: {data.get('summary', 'No summary')}")
                print(f"Case Insight: {data.get('case_insight', [])}")
                print(f"Decision Support: {data.get('decision_support', {})}")
            else:
                print(f"❌ FAILED: {result}")
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            print(f"Error Body: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_ai_service()
