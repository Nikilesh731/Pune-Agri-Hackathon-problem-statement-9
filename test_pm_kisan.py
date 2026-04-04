#!/usr/bin/env python3
"""Test PM-KISAN document processing"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services'))

sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

from app.modules.document_processing.document_processing_service import DocumentProcessingService

# Test with OCR text from the PM-KISAN document
ocr_text = '''Applicant Details
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
Requested Amount: Rs. 6,000'''

def test_pm_kisan_processing():
    service = DocumentProcessingService()
    
    print("Testing PM-KISAN document processing...")
    print("=" * 50)
    
    result = service.processor.process_document_workflow(
        file_data=b'', 
        filename='test.pdf', 
        processing_type='full_process', 
        options={'ocr_text': ocr_text}
    )
    
    print(f'Success: {result.get("success")}')
    print(f'Document Type: {result.get("data", {}).get("document_type")}')
    print(f'Confidence: {result.get("data", {}).get("confidence")}')
    print(f'Structured Data: {result.get("data", {}).get("structured_data", {})}')
    print(f'Missing Fields: {result.get("data", {}).get("missing_fields", [])}')
    print(f'Error: {result.get("error_message")}')
    
    # Test intelligence layer if extraction worked
    if result.get("success") and result.get("data"):
        print("\n" + "=" * 50)
        print("TESTING INTELLIGENCE LAYER")
        print("=" * 50)
        
        extracted_data = {
            "document_type": result["data"].get("document_type", "unknown"),
            "structured_data": result["data"].get("structured_data", {}),
            "missing_fields": result["data"].get("missing_fields", []),
            "confidence": result["data"].get("confidence", 0)
        }
        
        summary = service.intelligence_service.generate_document_summary(extracted_data)
        case_insight = service.intelligence_service.generate_case_insight(extracted_data)
        decision_support = service.intelligence_service.generate_decision_support(extracted_data)
        predictions = service.intelligence_service.generate_predictions(extracted_data)
        
        print(f"Summary: {summary}")
        print(f"Case Insight: {case_insight}")
        print(f"Decision Support: {decision_support}")
        print(f"Predictions: {predictions}")

if __name__ == "__main__":
    test_pm_kisan_processing()
