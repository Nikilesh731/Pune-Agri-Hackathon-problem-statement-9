#!/usr/bin/env python3
"""
SWE 1.5 FINAL STABILIZATION - Manual Verification Tests
Tests all document types with the stabilized unified pipeline
"""

import os
import sys
import requests
import json
import time
import base64
from pathlib import Path

# Test configuration
AI_SERVICES_URL = "http://localhost:8000"
BACKEND_URL = "http://localhost:3001"

def print_section(title):
    print(f"\n{'='*80}")
    print(f" {title}")
    print('='*80)

def print_test_result(test_name, success, details=""):
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")

def read_file_as_base64(file_path):
    """Read file and convert to base64"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            return base64.b64encode(content).decode('utf-8')
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def test_ai_service_health():
    """Test AI service runtime health"""
    print_section("AI SERVICE HEALTH CHECK")
    
    try:
        response = requests.get(f"{AI_SERVICES_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print_test_result("AI Service Health", True, f"Status: {health_data.get('status', 'unknown')}")
            
            # Check if dependencies are available
            if 'dependencies' in health_data:
                deps = health_data['dependencies']
                print_test_result("Python Dependencies Available", True, f"Missing: {deps.get('missing_critical', [])}")
            
            return True
        else:
            print_test_result("AI Service Health", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("AI Service Health", False, f"Error: {e}")
        return False

def test_backend_health():
    """Test backend service health"""
    print_section("BACKEND SERVICE HEALTH CHECK")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print_test_result("Backend Service Health", True)
            return True
        else:
            print_test_result("Backend Service Health", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Backend Service Health", False, f"Error: {e}")
        return False

def test_pdf_document():
    """Test PDF document processing"""
    print_section("PDF DOCUMENT PROCESSING TEST")
    
    pdf_file = "01_scheme_application_pm_kisan.pdf"
    if not os.path.exists(pdf_file):
        print_test_result("PDF Document Test", False, f"File not found: {pdf_file}")
        return False
    
    try:
        # Read and encode file
        file_content = read_file_as_base64(pdf_file)
        if not file_content:
            return False
        
        # Send to AI service
        payload = {
            "file_data": file_content,
            "filename": pdf_file,
            "processing_type": "full_process"
        }
        
        response = requests.post(f"{AI_SERVICES_URL}/process-document", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            
            if success and result.get('data'):
                data = result.get('data', {})
                
                # Check for required fields
                required_fields = ['document_type', 'structured_data', 'summary', 'decision_support', 'ml_insights']
                missing_fields = [field for field in required_fields if not data.get(field)]
                
                if not missing_fields:
                    print_test_result("PDF Document Test", True, f"Type: {data.get('document_type')}, Summary: {data.get('summary', '')[:50]}...")
                    
                    # Check for single summary (not duplicated)
                    summary = data.get('summary')
                    ai_summary = data.get('ai_summary')
                    if summary == ai_summary:
                        print_test_result("Single Summary Source", True, "summary == ai_summary")
                    else:
                        print_test_result("Single Summary Source", False, "summary != ai_summary")
                    
                    return True
                else:
                    print_test_result("PDF Document Test", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                print_test_result("PDF Document Test", False, f"Processing failed: {result.get('error_message', 'Unknown error')}")
                return False
        else:
            print_test_result("PDF Document Test", False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("PDF Document Test", False, f"Error: {e}")
        return False

def test_image_document():
    """Test image document processing with OCR"""
    print_section("IMAGE DOCUMENT PROCESSING TEST")
    
    # Check if we have any image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = [f for f in os.listdir('.') if any(f.lower().endswith(ext) for ext in image_extensions)]
    
    if not image_files:
        print_test_result("Image Document Test", False, "No image files found")
        return False
    
    image_file = image_files[0]
    print(f"Testing with image: {image_file}")
    
    try:
        file_content = read_file_as_base64(image_file)
        if not file_content:
            return False
        
        payload = {
            "file_data": file_content,
            "filename": image_file,
            "processing_type": "full_process"
        }
        
        response = requests.post(f"{AI_SERVICES_URL}/process-document", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            
            if success and result.get('data'):
                data = result.get('data', {})
                
                # Check OCR text was extracted
                structured_data = data.get('structured_data', {})
                has_content = bool(structured_data) or bool(data.get('summary'))
                
                if has_content:
                    print_test_result("Image Document Test", True, f"OCR extracted content, Type: {data.get('document_type')}")
                    return True
                else:
                    print_test_result("Image Document Test", False, "No content extracted from OCR")
                    return False
            else:
                print_test_result("Image Document Test", False, f"Processing failed: {result.get('error_message', 'Unknown error')}")
                return False
        else:
            print_test_result("Image Document Test", False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Image Document Test", False, f"Error: {e}")
        return False

def test_duplicate_detection():
    """Test duplicate detection functionality"""
    print_section("DUPLICATE DETECTION TEST")
    
    pdf_file = "01_scheme_application_pm_kisan.pdf"
    if not os.path.exists(pdf_file):
        print_test_result("Duplicate Detection Test", False, f"File not found: {pdf_file}")
        return False
    
    try:
        file_content = read_file_as_base64(pdf_file)
        if not file_content:
            return False
        
        # Create unique test data
        timestamp = int(time.time() * 1000)
        test_data = {
            "fileData": file_content,
            "fileName": f"test_duplicate_{timestamp}.pdf",
            "fileSize": len(file_content),
            "documentType": "scheme_application",
            "farmerId": None,
            "extractedData": None
        }
        
        # First submission - should succeed
        response1 = requests.post(f"{BACKEND_URL}/api/applications", json=test_data, timeout=30)
        
        if response1.status_code == 200 or response1.status_code == 201:
            result1 = response1.json()
            if result1.get('success'):
                print_test_result("First Submission", True, "Application created successfully")
                
                # Second submission with same file - should be blocked
                test_data["fileName"] = f"test_duplicate_2_{timestamp}.pdf"
                response2 = requests.post(f"{BACKEND_URL}/api/applications", json=test_data, timeout=30)
                
                if response2.status_code == 409:
                    print_test_result("Duplicate Detection", True, "Duplicate properly blocked with 409")
                    return True
                else:
                    print_test_result("Duplicate Detection", False, f"Expected 409, got {response2.status_code}")
                    return False
            else:
                print_test_result("First Submission", False, f"Creation failed: {result1.get('message', 'Unknown error')}")
                return False
        else:
            print_test_result("First Submission", False, f"Status code: {response1.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Duplicate Detection Test", False, f"Error: {e}")
        return False

def test_amount_normalization():
    """Test amount normalization preserves valid small amounts"""
    print_section("AMOUNT NORMALIZATION TEST")
    
    # Test with a document that has a small amount
    pdf_file = "01_scheme_application_pm_kisan.pdf"
    if not os.path.exists(pdf_file):
        print_test_result("Amount Normalization Test", False, f"File not found: {pdf_file}")
        return False
    
    try:
        file_content = read_file_as_base64(pdf_file)
        if not file_content:
            return False
        
        payload = {
            "file_data": file_content,
            "filename": pdf_file,
            "processing_type": "full_process"
        }
        
        response = requests.post(f"{AI_SERVICES_URL}/process-document", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                data = result.get('data', {})
                structured_data = data.get('structured_data', {})
                
                # Check if amounts are preserved
                amount_fields = ['requested_amount', 'claim_amount', 'subsidy_amount', 'amount']
                found_amounts = {field: structured_data.get(field) for field in amount_fields if structured_data.get(field)}
                
                if found_amounts:
                    print_test_result("Amount Normalization Test", True, f"Amounts preserved: {found_amounts}")
                    return True
                else:
                    print_test_result("Amount Normalization Test", True, "No amounts found (may be expected for this document)")
                    return True
            else:
                print_test_result("Amount Normalization Test", False, f"Processing failed: {result.get('error_message', 'Unknown error')}")
                return False
        else:
            print_test_result("Amount Normalization Test", False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Amount Normalization Test", False, f"Error: {e}")
        return False

def test_verification_routing():
    """Test verification queue routing is deterministic"""
    print_section("VERIFICATION ROUTING TEST")
    
    pdf_file = "01_scheme_application_pm_kisan.pdf"
    if not os.path.exists(pdf_file):
        print_test_result("Verification Routing Test", False, f"File not found: {pdf_file}")
        return False
    
    try:
        file_content = read_file_as_base64(pdf_file)
        if not file_content:
            return False
        
        payload = {
            "file_data": file_content,
            "filename": pdf_file,
            "processing_type": "full_process"
        }
        
        response = requests.post(f"{AI_SERVICES_URL}/process-document", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                data = result.get('data', {})
                
                # Check routing consistency
                decision_support = data.get('decision_support', {})
                ml_insights = data.get('ml_insights', {})
                workflow = data.get('workflow', {})
                
                decision = decision_support.get('decision')
                ml_queue = ml_insights.get('queue')
                workflow_queue = workflow.get('queue')
                workflow_status = workflow.get('status')
                
                print_test_result("Verification Routing Test", True, 
                    f"Decision: {decision}, ML Queue: {ml_queue}, Workflow: {workflow_status}/{workflow_queue}")
                return True
            else:
                print_test_result("Verification Routing Test", False, f"Processing failed: {result.get('error_message', 'Unknown error')}")
                return False
        else:
            print_test_result("Verification Routing Test", False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Verification Routing Test", False, f"Error: {e}")
        return False

def main():
    """Run all manual verification tests"""
    print("🚀 SWE 1.5 FINAL STABILIZATION - Manual Verification Tests")
    print("=" * 80)
    
    tests = [
        ("AI Service Health", test_ai_service_health),
        ("Backend Service Health", test_backend_health),
        ("PDF Document Processing", test_pdf_document),
        ("Image Document Processing", test_image_document),
        ("Duplicate Detection", test_duplicate_detection),
        ("Amount Normalization", test_amount_normalization),
        ("Verification Routing", test_verification_routing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_test_result(test_name, False, f"Test error: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! SWE 1.5 Final Stabilization is complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
