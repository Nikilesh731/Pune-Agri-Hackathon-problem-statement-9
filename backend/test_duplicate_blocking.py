#!/usr/bin/env python3
"""
Realistic validation script for duplicate blocking functionality
Tests end-to-end duplicate prevention with proper farmer identity resolution
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
API_BASE = "http://localhost:3001"

def upload_file(filename: str, content: str, applicant_id: str = None, document_type: str = None) -> Dict[str, Any]:
    """Upload a test file to the API"""
    files = {
        'file': (filename, content.encode('utf-8'), 'text/plain')
    }
    
    data = {}
    if applicant_id:
        data['applicantId'] = applicant_id
    if document_type:
        data['documentType'] = document_type
    
    response = requests.post(f"{API_BASE}/api/applications/with-file", files=files, data=data)
    return response

def patch_requires_action(application_id: str) -> bool:
    """Patch an application to REQUIRES_ACTION status"""
    try:
        response = requests.patch(f"{API_BASE}/api/applications/{application_id}/request-clarification")
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error patching application {application_id}: {e}")
        return False

def assert_response(response: requests.Response, expected_status: int, expected_fields: Dict[str, Any] = None) -> bool:
    """Assert response has expected status and fields"""
    if response.status_code != expected_status:
        print(f"❌ Expected status {expected_status}, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    if expected_fields:
        try:
            data = response.json()
            for field, expected_value in expected_fields.items():
                if field not in data or data[field] != expected_value:
                    print(f"❌ Expected {field}={expected_value}, got {data.get(field)}")
                    return False
        except Exception as e:
            print(f"❌ Failed to parse response JSON: {e}")
            return False
    
    return True

def wait_for_application_existence(application_id: str, max_wait_seconds: int = 10) -> bool:
    """Wait for an application to exist in the system"""
    for _ in range(max_wait_seconds):
        try:
            response = requests.get(f"{API_BASE}/api/applications/{application_id}")
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_case_a_first_upload() -> bool:
    """CASE A: First upload - should be allowed"""
    print("\n=== CASE A: First Upload Test ===")
    
    # Unique timestamp to avoid collisions
    timestamp = int(time.time() * 1000)
    unique_aadhaar = f"{timestamp % 1000000000000:012d}"  # 12-digit unique Aadhaar
    unique_mobile = f"{timestamp % 10000000000:010d}"     # 10-digit unique mobile
    
    test_content = f"""
Farmer Name: Test Farmer A {timestamp}
Aadhaar: {unique_aadhaar}
Mobile: {unique_mobile}
Village: Test Village
District: Test District
State: Test State
Scheme: Agricultural Scheme
Document Type: Scheme Application
Timestamp: {timestamp}
"""
    
    response = upload_file(f'test_scheme_application_a_{timestamp}.txt', test_content, 
                          applicant_id=f'test-user-a-{timestamp}', 
                          document_type='scheme_application')
    
    success = assert_response(response, 201)
    if success:
        app_data = response.json()
        app_id = app_data.get('application', {}).get('id')
        print(f"✅ CASE A PASSED: First upload allowed, app_id: {app_id}")
        return True
    else:
        print("❌ CASE A FAILED: First upload should be allowed")
        return False

def test_case_b_duplicate_active() -> bool:
    """CASE B: Duplicate active upload - should be blocked"""
    print("\n=== CASE B: Duplicate Active Upload Test ===")
    
    # Unique timestamp to avoid collisions
    timestamp = int(time.time() * 1000)
    unique_aadhaar = f"{timestamp % 1000000000000:012d}"  # 12-digit unique Aadhaar
    unique_mobile = f"{timestamp % 10000000000:010d}"     # 10-digit unique mobile
    
    test_content = f"""
Farmer Name: Test Farmer B {timestamp}
Aadhaar: {unique_aadhaar}
Mobile: {unique_mobile}
Village: Test Village
District: Test District
State: Test State
Scheme: Agricultural Scheme
Document Type: Scheme Application
Timestamp: {timestamp}
"""
    
    # First upload - should succeed
    response1 = upload_file(f'test_scheme_application_b1_{timestamp}.txt', test_content,
                           applicant_id=f'test-user-b-{timestamp}',
                           document_type='scheme_application')
    
    if not assert_response(response1, 201):
        print("❌ CASE B FAILED: First upload should succeed")
        return False
    
    # Second upload with same farmer identity - should be blocked
    response2 = upload_file(f'test_scheme_application_b2_{timestamp}.txt', test_content,
                           applicant_id=f'test-user-b-diff-{timestamp}',  # Different applicantId but same farmer
                           document_type='scheme_application')
    
    success = assert_response(response2, 409, {
        'status': 'duplicate',
        'duplicateBlocked': True
    })
    
    if success:
        print("✅ CASE B PASSED: Duplicate upload blocked")
        return True
    else:
        print("❌ CASE B FAILED: Duplicate upload should be blocked with 409")
        return False

def test_case_c_resubmission_allowed() -> bool:
    """CASE C: Resubmission after REQUIRES_ACTION - should be allowed"""
    print("\n=== CASE C: Resubmission After REQUIRES_ACTION Test ===")
    
    # Unique timestamp to avoid collisions
    timestamp = int(time.time() * 1000)
    unique_aadhaar = f"{timestamp % 1000000000000:012d}"  # 12-digit unique Aadhaar
    unique_mobile = f"{timestamp % 10000000000:010d}"     # 10-digit unique mobile
    
    test_content = f"""
Farmer Name: Test Farmer C {timestamp}
Aadhaar: {unique_aadhaar}
Mobile: {unique_mobile}
Village: Test Village
District: Test District
State: Test State
Scheme: Agricultural Scheme
Document Type: Scheme Application
Timestamp: {timestamp}
"""
    
    # Step 1: Upload first document
    response1 = upload_file(f'test_scheme_application_c1_{timestamp}.txt', test_content,
                           applicant_id=f'test-user-c-{timestamp}',
                           document_type='scheme_application')
    
    if not assert_response(response1, 201):
        print("❌ CASE C FAILED: First upload should succeed")
        return False
    
    app_id = response1.json().get('application', {}).get('id')
    if not app_id:
        print("❌ CASE C FAILED: No application ID returned")
        return False
    
    # Step 2: Wait for application to exist and patch to REQUIRES_ACTION
    if not wait_for_application_existence(app_id):
        print(f"❌ CASE C FAILED: Application {app_id} never became available")
        return False
    
    if not patch_requires_action(app_id):
        print(f"❌ CASE C FAILED: Could not patch application {app_id} to REQUIRES_ACTION")
        return False
    
    # Step 3: Upload same farmer + same doc type again - should be allowed
    response2 = upload_file(f'test_scheme_application_c2_{timestamp}.txt', test_content,
                           applicant_id=f'test-user-c-resubmit-{timestamp}',  # Different applicantId but same farmer
                           document_type='scheme_application')
    
    success = assert_response(response2, 201)  # Should be allowed
    if success:
        print("✅ CASE C PASSED: Resubmission after REQUIRES_ACTION allowed")
        return True
    else:
        print("❌ CASE C FAILED: Resubmission should be allowed")
        return False

def test_case_d_different_doc_type() -> bool:
    """CASE D: Different document type same farmer - should be allowed"""
    print("\n=== CASE D: Different Document Type Test ===")
    
    # Unique timestamp to avoid collisions
    timestamp = int(time.time() * 1000)
    unique_aadhaar = f"{timestamp % 1000000000000:012d}"  # 12-digit unique Aadhaar
    unique_mobile = f"{timestamp % 10000000000:010d}"     # 10-digit unique mobile
    
    # First upload - scheme application
    scheme_content = f"""
Farmer Name: Test Farmer D {timestamp}
Aadhaar: {unique_aadhaar}
Mobile: {unique_mobile}
Village: Test Village
District: Test District
State: Test State
Scheme: Agricultural Scheme
Document Type: Scheme Application
Timestamp: {timestamp}
"""
    
    response1 = upload_file(f'test_scheme_application_d_{timestamp}.txt', scheme_content,
                           applicant_id=f'test-user-d-{timestamp}',
                           document_type='scheme_application')
    
    if not assert_response(response1, 201):
        print("❌ CASE D FAILED: First upload should succeed")
        return False
    
    # Second upload - insurance claim with same farmer
    insurance_content = f"""
Farmer Name: Test Farmer D {timestamp}
Aadhaar: {unique_aadhaar}
Mobile: {unique_mobile}
Village: Test Village
District: Test District
State: Test State
Claim Type: Crop Insurance
Document Type: Insurance Claim
Timestamp: {timestamp}
"""
    
    response2 = upload_file(f'test_insurance_claim_d_{timestamp}.txt', insurance_content,
                           applicant_id=f'test-user-d-insurance-{timestamp}',
                           document_type='insurance_claim')
    
    success = assert_response(response2, 201)  # Should be allowed
    if success:
        print("✅ CASE D PASSED: Different document type allowed")
        return True
    else:
        print("❌ CASE D FAILED: Different document type should be allowed")
        return False

def test_case_e_supporting_document() -> bool:
    """CASE E: Supporting document same farmer - should be allowed"""
    print("\n=== CASE E: Supporting Document Test ===")
    
    # Unique timestamp to avoid collisions
    timestamp = int(time.time() * 1000)
    unique_aadhaar = f"{timestamp % 1000000000000:012d}"  # 12-digit unique Aadhaar
    unique_mobile = f"{timestamp % 10000000000:010d}"     # 10-digit unique mobile
    
    test_content = f"""
Farmer Name: Test Farmer E {timestamp}
Aadhaar: {unique_aadhaar}
Mobile: {unique_mobile}
Village: Test Village
District: Test District
State: Test State
Document Type: Supporting Document
Purpose: Land Record Supporting
Timestamp: {timestamp}
"""
    
    response = upload_file(f'test_supporting_document_e_{timestamp}.txt', test_content,
                          applicant_id=f'test-user-e-{timestamp}',
                          document_type='supporting_document')
    
    success = assert_response(response, 201)  # Should be allowed
    if success:
        print("✅ CASE E PASSED: Supporting document allowed")
        return True
    else:
        print("❌ CASE E FAILED: Supporting document should be allowed")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Starting Realistic Duplicate Blocking Validation Tests")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE}/api/applications/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend health check failed")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Make sure the backend is running on http://localhost:3001")
        return 1
    
    print("✅ Backend is running")
    
    # Run test cases
    results = []
    
    # Case A: First upload
    results.append(test_case_a_first_upload())
    time.sleep(1)
    
    # Case B: Duplicate active
    results.append(test_case_b_duplicate_active())
    time.sleep(1)
    
    # Case C: Resubmission allowed
    results.append(test_case_c_resubmission_allowed())
    time.sleep(1)
    
    # Case D: Different document type
    results.append(test_case_d_different_doc_type())
    time.sleep(1)
    
    # Case E: Supporting document
    results.append(test_case_e_supporting_document())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    test_names = [
        "CASE A: First Upload",
        "CASE B: Duplicate Active Upload",
        "CASE C: Resubmission After REQUIRES_ACTION",
        "CASE D: Different Document Type",
        "CASE E: Supporting Document"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! Duplicate blocking is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
