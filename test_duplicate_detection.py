#!/usr/bin/env python3
"""
Test script for strict pre-save duplicate detection
Tests the 3 scenarios:
1. BLOCK DUPLICATE - Same file with active status
2. ALLOW RE-UPLOAD - Same file with completed status  
3. DIFFERENT DOCUMENT - Normal processing
"""

import requests
import hashlib
import json
import time
from pathlib import Path
import random
import string

# Configuration
BACKEND_URL = "http://localhost:3001"
API_BASE = f"{BACKEND_URL}/api/applications"

def generate_unique_content():
    """Generate unique content for each test run"""
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    timestamp = int(time.time())
    return f"Test content {random_str} at {timestamp}"

def generate_file_hash(file_content: bytes) -> str:
    """Generate SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def create_test_file(filename: str, content: str) -> bytes:
    """Create test file content"""
    return content.encode('utf-8')

def upload_document(file_content: bytes, filename: str, applicant_id: str = "test-farmer-001") -> dict:
    """Upload document and return response"""
    url = f"{API_BASE}/with-file"
    
    files = {
        'file': (filename, file_content, 'application/pdf')
    }
    
    data = {
        'applicantId': applicant_id,
        'documentType': 'scheme_application'
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        response_data = response.json() if response.content else None
        
        result = {
            'status_code': response.status_code,
            'response': response_data,
            'success': response.status_code in [200, 201]
        }
        
        # Add error details for debugging
        if response.status_code >= 400:
            result['error_details'] = {
                'text': response.text,
                'headers': dict(response.headers),
                'status_code': response.status_code
            }
        
        return result
        
    except Exception as e:
        return {
            'status_code': 0,
            'response': {'error': str(e)},
            'success': False,
            'error_details': {'exception': str(e)}
        }

def test_scenario_1_block_duplicate():
    """Test SCENARIO 1: BLOCK DUPLICATE - Same file with active status"""
    print("\n" + "="*60)
    print("SCENARIO 1: BLOCK DUPLICATE - Same file with active status")
    print("="*60)
    
    # Create test file with unique content
    unique_content = generate_unique_content()
    file_content = create_test_file("scheme_application.pdf", f"Test scheme application content: {unique_content}")
    file_hash = generate_file_hash(file_content)
    print(f"File hash: {file_hash[:16]}...")
    
    # First upload - should succeed
    print("\n1. First upload (should succeed):")
    result1 = upload_document(file_content, "scheme_application.pdf")
    print(f"   Status: {result1['status_code']}")
    print(f"   Success: {result1['success']}")
    if result1['response']:
        print(f"   Message: {result1['response'].get('message', 'N/A')}")
        app_id = result1['response'].get('application', {}).get('id')
        print(f"   Application ID: {app_id}")
    
    # Second upload of same file - should be blocked
    print("\n2. Second upload of same file (should be blocked):")
    result2 = upload_document(file_content, "scheme_application.pdf")
    print(f"   Status: {result2['status_code']}")
    print(f"   Success: {result2['success']}")
    if result2['response']:
        print(f"   Message: {result2['response'].get('message', 'N/A')}")
        print(f"   Status: {result2['response'].get('status', 'N/A')}")
        print(f"   Duplicate Blocked: {result2['response'].get('duplicateBlocked', False)}")
        print(f"   Existing Application ID: {result2['response'].get('existingApplicationId', 'N/A')}")
    
    # Verify expectations
    success = (
        result1['success'] and 
        result1['status_code'] == 201 and
        result2['status_code'] == 409 and
        result2['response'].get('duplicateBlocked') == True
    )
    
    print(f"\n✅ SCENARIO 1 {'PASSED' if success else 'FAILED'}")
    return success

def test_scenario_2_allow_reupload():
    """Test SCENARIO 2: ALLOW RE-UPLOAD - Same file with completed status"""
    print("\n" + "="*60)
    print("SCENARIO 2: ALLOW RE-UPLOAD - Same file with completed status")
    print("="*60)
    
    # Create different test file with unique content
    unique_content = generate_unique_content()
    file_content = create_test_file("subsidy_claim.pdf", f"Test subsidy claim content: {unique_content}")
    file_hash = generate_file_hash(file_content)
    print(f"File hash: {file_hash[:16]}...")
    
    # First upload
    print("\n1. First upload:")
    result1 = upload_document(file_content, "subsidy_claim.pdf", "test-farmer-002")
    print(f"   Status: {result1['status_code']}")
    print(f"   Success: {result1['success']}")
    
    if not result1['success'] and 'error_details' in result1:
        print(f"   Error Details: {result1['error_details']}")
    
    original_app_id = None
    original_version = None
    
    if result1['success']:
        original_app_id = result1['response'].get('application', {}).get('id')
        original_version = result1['response'].get('application', {}).get('versionNumber', 1)
        print(f"   Application ID: {original_app_id}")
        print(f"   Version Number: {original_version}")
        
        # Wait for AI processing to complete
        time.sleep(3)
        
        # Use the correct approve endpoint
        update_response = requests.patch(f"{API_BASE}/{original_app_id}/approve")
        print(f"   Updated status to APPROVED: {update_response.status_code == 200}")
        
        # Verify the status was actually updated
        check_response = requests.get(f"{API_BASE}/{original_app_id}")
        if check_response.status_code == 200:
            actual_status = check_response.json()['status']
            print(f"   Actual status: {actual_status}")
    
    # Second upload of same file - should allow re-upload
    print("\n2. Second upload of same file (should allow re-upload):")
    result2 = upload_document(file_content, "subsidy_claim.pdf", "test-farmer-002")
    print(f"   Status: {result2['status_code']}")
    print(f"   Success: {result2['success']}")
    
    if not result2['success'] and 'error_details' in result2:
        print(f"   Error Details: {result2['error_details']}")
    
    new_app_id = None
    new_version = None
    
    if result2['response']:
        print(f"   Message: {result2['response'].get('message', 'N/A')}")
        print(f"   Status: {result2['response'].get('status', 'N/A')}")
        print(f"   Is Re-upload: {result2['response'].get('isReupload', False)}")
        print(f"   Parent Application ID: {result2['response'].get('parentApplicationId', 'N/A')}")
        new_app = result2['response'].get('application', {})
        if new_app:
            new_app_id = new_app.get('id')
            new_version = new_app.get('versionNumber', 1)
            print(f"   New Application ID: {new_app_id}")
            print(f"   Version Number: {new_version}")
    
    # Verify expectations - ALL must be true
    success = (
        result1['success'] and 
        result2['success'] and
        result2['response'].get('status') == 'reupload_allowed' and
        result2['response'].get('isReupload') == True and
        result2['response'].get('parentApplicationId') == original_app_id and
        new_app_id != original_app_id and
        new_version > original_version
    )
    
    # Print detailed verification results
    print(f"\n   Verification Details:")
    print(f"   ✓ First upload success: {result1['success']}")
    print(f"   ✓ Second upload success: {result2['success']}")
    print(f"   ✓ Status is 'reupload_allowed': {result2['response'].get('status') == 'reupload_allowed'}")
    print(f"   ✓ Is re-upload flag: {result2['response'].get('isReupload') == True}")
    print(f"   ✓ Parent ID matches original: {result2['response'].get('parentApplicationId') == original_app_id}")
    print(f"   ✓ New app ID is different: {new_app_id != original_app_id}")
    print(f"   ✓ Version incremented: {new_version > original_version}")
    print(f"   Original: ID={original_app_id}, Version={original_version}")
    print(f"   New: ID={new_app_id}, Version={new_version}")
    
    print(f"\n✅ SCENARIO 2 {'PASSED' if success else 'FAILED'}")
    return success

def test_scenario_3_different_document():
    """Test SCENARIO 3: DIFFERENT DOCUMENT - Normal processing"""
    print("\n" + "="*60)
    print("SCENARIO 3: DIFFERENT DOCUMENT - Normal processing")
    print("="*60)
    
    # Create two different files with unique content
    unique_content1 = generate_unique_content()
    unique_content2 = generate_unique_content()
    file1_content = create_test_file("insurance_claim.pdf", f"Test insurance claim content: {unique_content1}")
    file2_content = create_test_file("grievance.pdf", f"Test grievance content: {unique_content2}")
    
    file1_hash = generate_file_hash(file1_content)
    file2_hash = generate_file_hash(file2_content)
    
    print(f"File 1 hash: {file1_hash[:16]}...")
    print(f"File 2 hash: {file2_hash[:16]}...")
    
    # Upload first file
    print("\n1. Upload first document:")
    result1 = upload_document(file1_content, "insurance_claim.pdf", "test-farmer-003")
    print(f"   Status: {result1['status_code']}")
    print(f"   Success: {result1['success']}")
    
    # Upload different file - should process normally
    print("\n2. Upload different document (should process normally):")
    result2 = upload_document(file2_content, "grievance.pdf", "test-farmer-003")
    print(f"   Status: {result2['status_code']}")
    print(f"   Success: {result2['success']}")
    if result2['response']:
        print(f"   Message: {result2['response'].get('message', 'N/A')}")
        print(f"   Is Re-upload: {result2['response'].get('isReupload', False)}")
        print(f"   Application ID: {result2['response'].get('application', {}).get('id')}")
    
    # Verify expectations
    success = (
        result1['success'] and 
        result2['success'] and
        result2['status_code'] == 201 and
        result2['response'].get('isReupload') != True
    )
    
    print(f"\n✅ SCENARIO 3 {'PASSED' if success else 'FAILED'}")
    return success

def cleanup_all_applications():
    """Clean up all applications for fresh test environment"""
    print("\n🧹 CLEANING UP ALL APPLICATIONS...")
    
    try:
        response = requests.post(f"{API_BASE}/cleanup", json={"mode": "all"})
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cleanup successful: {result.get('message', 'Unknown')}")
            print(f"   Deleted: {result.get('count', 0)} applications")
            return True
        else:
            print(f"❌ Cleanup failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False

def main():
    """Run all test scenarios"""
    print("🧪 TESTING STRICT PRE-SAVE DUPLICATE DETECTION")
    print("=" * 60)
    
    # Clean up first for fresh test environment
    print("\n🧹 STEP 0: Clean up all applications...")
    cleanup_success = cleanup_all_applications()
    if not cleanup_success:
        print("❌ Cleanup failed - cannot proceed with tests")
        return
    
    print("✅ All applications cleaned - starting fresh tests\n")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend health check failed")
            return
        print("✅ Backend is running")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please start the backend server first")
        return
    
    # Run test scenarios
    scenario1_passed = test_scenario_1_block_duplicate()
    scenario2_passed = test_scenario_2_allow_reupload()
    scenario3_passed = test_scenario_3_different_document()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Scenario 1 (Block Duplicate): {'✅ PASSED' if scenario1_passed else '❌ FAILED'}")
    print(f"Scenario 2 (Allow Re-upload): {'✅ PASSED' if scenario2_passed else '❌ FAILED'}")
    print(f"Scenario 3 (Different Document): {'✅ PASSED' if scenario3_passed else '❌ FAILED'}")
    
    all_passed = scenario1_passed and scenario2_passed and scenario3_passed
    print(f"\nOverall: {'🎉 ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n✨ Strict pre-save duplicate detection is working correctly!")
        print("   - Duplicates are blocked before processing")
        print("   - Re-uploads are allowed after completion")
        print("   - Different documents process normally")

if __name__ == "__main__":
    main()
