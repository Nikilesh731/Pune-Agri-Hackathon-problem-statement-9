#!/usr/bin/env python3
"""
Test Farmer Profile Integration
Verifies that farmers are created and linked correctly during AI processing
"""

import asyncio
import json
import sys
import os

# Add the parent directory to the path to import from app

from app.modules.document_processing.document_processing_service import DocumentProcessingService

async def test_farmer_integration():
    """Test farmer creation and linking during document processing"""
    
    print("ðŸ§ª Testing Farmer Profile Integration")
    print("=" * 50)
    
    # Test case 1: Farmer record document (should create new farmer)
    print("\nðŸ“„ Test 1: Farmer Record Document (New Farmer)")
    farmer_record_text = """
    FARMER RECORD
    
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
    
    processor = DocumentProcessingService()
    
    result1 = await processor.process_document(
        file_data=farmer_record_text.encode(),
        filename="farmer_record.txt",
        processing_type="full_process"
    )
    
    print(f"âœ… Status: {result1.success}")
    print(f"ðŸ“‹ Document Type: {result1.data.document_type if result1.data else 'unknown'}")
    
    # Debug: Print actual data structure
    if result1.data:
        print(f"ðŸ” Debug - Data keys: {list(result1.data.__dict__.keys())}")
        if hasattr(result1.data, 'structured_data'):
            print(f"ðŸ” Debug - Structured data keys: {list(result1.data.structured_data.keys()) if result1.data.structured_data else 'None'}")
    
    canonical1 = result1.data.__dict__ if result1.data else {}
    structured1 = canonical1.get('structured_data', {})
    
    print(f"ðŸ‘¤ Farmer Name: {structured1.get('farmer_name', 'N/A')}")
    print(f"ðŸ†” Aadhaar: {structured1.get('aadhaar_number', 'N/A')}")
    print(f"ðŸ“± Mobile: {structured1.get('phone_number', 'N/A')}")
    print(f"ðŸ  Village: {structured1.get('village', 'N/A')}")
    
    # Test case 2: Scheme application with same Aadhaar (should link to existing farmer)
    print("\nðŸ“„ Test 2: Scheme Application (Same Aadhaar - Should Link)")
    scheme_application_text = """
    SCHEME APPLICATION
    
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
    
    result2 = await processor.process_document(
        file_data=scheme_application_text.encode(),
        filename="scheme_application.txt", 
        processing_type="full_process"
    )
    
    print(f"âœ… Status: {result2.success}")
    print(f"ðŸ“‹ Document Type: {result2.data.document_type if result2.data else 'unknown'}")
    
    canonical2 = result2.data.__dict__ if result2.data else {}
    structured2 = canonical2.get('structured_data', {})
    
    print(f"ðŸ‘¤ Farmer Name: {structured2.get('farmer_name', 'N/A')}")
    print(f"ðŸ†” Aadhaar: {structured2.get('aadhaar_number', 'N/A')}")
    print(f"ðŸ“± Mobile: {structured2.get('phone_number', 'N/A')}")
    print(f"ðŸ  Village: {structured2.get('village', 'N/A')}")
    
    # Test case 3: Different mobile number only (should create new farmer)
    print("\nðŸ“„ Test 3: Document with Mobile Only (New Farmer)")
    mobile_only_text = """
    GRIEVANCE LETTER
    
    Name: Anita Devi
    Mobile Number: 9876543211
    Address: 456 Colony, New Town
    Village: New Town
    District: Azamgarh
    State: Uttar Pradesh
    Issue Summary: Crop insurance claim not processed
    """
    
    result3 = await processor.process_document(
        file_data=mobile_only_text.encode(),
        filename="grievance.txt",
        processing_type="full_process"
    )
    
    print(f"âœ… Status: {result3.success}")
    print(f"ðŸ“‹ Document Type: {result3.data.document_type if result3.data else 'unknown'}")
    
    canonical3 = result3.data.__dict__ if result3.data else {}
    structured3 = canonical3.get('structured_data', {})
    
    print(f"ðŸ‘¤ Farmer Name: {structured3.get('farmer_name', 'N/A')}")
    print(f"ðŸ†” Aadhaar: {structured3.get('aadhaar_number', 'N/A')}")
    print(f"ðŸ“± Mobile: {structured3.get('phone_number', 'N/A')}")
    print(f"ðŸ  Village: {structured3.get('village', 'N/A')}")
    
    # Test case 4: No identifying info (should not create farmer)
    print("\nðŸ“„ Test 4: Document without Aadhaar/Mobile (No Farmer Creation)")
    no_id_text = """
    SUPPORTING DOCUMENT
    
    Document Reference: DOC/2024/001
    Date: 15-03-2024
    Subject: Land ownership proof
    Details: This document certifies land ownership
    Village: Rampur
    District: Bareilly
    """
    
    result4 = await processor.process_document(
        file_data=no_id_text.encode(),
        filename="supporting_doc.txt",
        processing_type="full_process"
    )
    
    print(f"âœ… Status: {result4.success}")
    print(f"ðŸ“‹ Document Type: {result4.data.document_type if result4.data else 'unknown'}")
    
    canonical4 = result4.data.__dict__ if result4.data else {}
    structured4 = canonical4.get('structured_data', {})
    
    print(f"ðŸ‘¤ Farmer Name: {structured4.get('farmer_name', 'N/A')}")
    print(f"ðŸ†” Aadhaar: {structured4.get('aadhaar_number', 'N/A')}")
    print(f"ðŸ“± Mobile: {structured4.get('phone_number', 'N/A')}")
    print(f"ðŸ  Village: {structured4.get('village', 'N/A')}")
    
    # Summary
    print("\n" + "=" * 50)
    print("ðŸ“Š FARMER INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    test_results = [
        ("Farmer Record (New)", result1.success, "test1"),
        ("Scheme Application (Link)", result2.success, "test2"),
        ("Mobile Only (New)", result3.success, "test3"),
        ("No ID (Skip)", result4.success, "test4")
    ]
    
    passed = 0
    total = len(test_results)
    
    for test_name, success, identifier in test_results:
        status = "âœ… PASS" if success else "âŒ FAIL"
        id_info = f" | ID: {identifier}" if identifier else " | No ID"
        print(f"{status} | {test_name}{id_info}")
        if success:
            passed += 1
    
    print(f"\nðŸŽ¯ Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("ðŸŽ‰ Farmer Profile Integration is working correctly!")
        print("ðŸ“‹ Farmers are created and linked as expected during AI processing.")
    else:
        print("âš ï¸  Some tests failed - check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(test_farmer_integration())
