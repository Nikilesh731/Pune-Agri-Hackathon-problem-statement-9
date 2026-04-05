#!/usr/bin/env python3
"""
Test script to verify fraud detection fixes
"""
import requests
import json
import time

def test_fraud_detection_endpoint():
    """Test that fraud detection endpoint never crashes and always returns valid JSON"""
    print("Testing fraud detection endpoint...")
    
    # Test normal case
    normal_data = {
        "farmer_name": "Test Farmer",
        "aadhaar_number": "123456789012",
        "land_size": "5 acres"
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/api/fraud-detection/detect",
            json=normal_data,
            timeout=5
        )
        print(f"Normal case - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure valid: {data.get('success', False)}")
            print(f"Fraud score: {data.get('data', {}).get('fraud_score', 'N/A')}")
        else:
            print(f"ERROR: Unexpected status code {response.status_code}")
    except Exception as e:
        print(f"ERROR: Fraud detection endpoint failed: {e}")
    
    # Test malformed data that might cause internal errors
    malformed_data = {
        "farmer_name": None,
        "aadhaar_number": {"invalid": "structure"},
        "land_size": ["invalid", "type"]
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/api/fraud-detection/detect",
            json=malformed_data,
            timeout=5
        )
        print(f"Malformed case - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure valid: {data.get('success', False)}")
            print(f"Fraud score (safe default): {data.get('data', {}).get('fraud_score', 'N/A')}")
            print(f"Indicators: {data.get('data', {}).get('indicators', [])}")
        else:
            print(f"ERROR: Malformed data caused crash: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Fraud detection endpoint crashed on malformed data: {e}")

if __name__ == "__main__":
    test_fraud_detection_endpoint()
