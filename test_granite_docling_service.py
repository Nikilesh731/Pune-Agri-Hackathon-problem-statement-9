"""
Test script for Granite-Docling Service
Run this script to test the new document parsing functionality
"""
import requests
import json
import os

# Base URL for the AI service
BASE_URL = "http://localhost:8000"

def test_service_info():
    """Test getting service information"""
    print("=== Testing Service Info ===")
    try:
        response = requests.get(f"{BASE_URL}/api/document-processing/parse-info")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_document_parsing(file_path):
    """Test document parsing with a file"""
    print(f"\n=== Testing Document Parsing: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            response = requests.post(f"{BASE_URL}/api/document-processing/parse", files=files)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Parser: {result.get('parser')}")
            print(f"Source Type: {result.get('source_type')}")
            print(f"Text Length: {len(result.get('raw_text', ''))}")
            print(f"Pages: {len(result.get('pages', []))}")
            print(f"Blocks: {len(result.get('blocks', []))}")
            print(f"Tables: {len(result.get('tables', []))}")
            print(f"OCR Used: {result.get('ocr_used')}")
            print(f"Fallback Used: {result.get('fallback_used')}")
            
            if result.get('errors'):
                print(f"Errors: {result['errors']}")
            
            # Show first 200 characters of extracted text
            raw_text = result.get('raw_text', '')
            if raw_text:
                print(f"Text Preview: {raw_text[:200]}...")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Granite-Docling Service Test Suite")
    print("=" * 50)
    
    # Test service info
    service_ok = test_service_info()
    
    # Test with available documents in the project
    test_files = [
        "01_scheme_application_pm_kisan.pdf",
        "02_subsidy_claim_drip_irrigation.pdf", 
        "03_insurance_claim_crop_loss.pdf",
        "04_grievance_delayed_subsidy_payment.pdf",
        "05_farmer_record_profile.pdf",
        "06_supporting_document_land_receipt.pdf"
    ]
    
    results = []
    for filename in test_files:
        if os.path.exists(filename):
            result = test_document_parsing(filename)
            results.append((filename, result))
        else:
            print(f"\n=== File Not Found: {filename} ===")
            results.append((filename, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Service Info: {'✓' if service_ok else '✗'}")
    
    for filename, success in results:
        status = '✓' if success else '✗'
        print(f"{filename}: {status}")
    
    total_tests = 1 + len(results)
    passed_tests = sum([service_ok] + [success for _, success in results])
    print(f"\nPassed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    main()
