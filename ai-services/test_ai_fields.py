#!/usr/bin/env python3
"""Quick test to verify AI fields are present in extraction"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from modules.document_processing.document_processing_service import DocumentProcessingService

async def test_ai_fields():
    """Test that AI fields are present in extraction results"""
    
    service = DocumentProcessingService()
    
    # Simple OCR text for testing
    ocr_text = """
    Name: Test Farmer
    Aadhaar: 1234 5678 9012
    Application ID: APP-2024-001
    Date: 15/03/2024
    Scheme: Pradhan Mantri Kisan Samman Nidhi
    Amount: 6000
    Village: Test Village
    District: Test District
    """
    
    result = await service.process_document(
        file_data=b'', 
        filename='test.txt', 
        processing_type='full_process', 
        options={'ocr_text': ocr_text}
    )
    
    data = result.data.dict() if result.data else {}
    structured_data = data.get('structured_data', {}) if data else {}
    
    print("Keys in result:")
    for attr in ['request_id', 'success', 'processing_time_ms', 'processing_type', 'filename', 'data', 'metadata', 'error_message']:
        if hasattr(result, attr):
            value = getattr(result, attr)
            print(f"  - {attr}: {type(value).__name__}")
    
    if data:
        print("\nKeys in data:")
        for key in data.keys():
            print(f"  - {key}")
        
        print(f"\nStructured data length: {len(structured_data)}")
        print("Keys in structured_data:")
        for key in structured_data.keys():
            print(f"  - {key}")
    
    print("\n=== AI Fields Check ===")
    if data and 'ai_summary' in data:
        print(f"✅ ai_summary: {data['ai_summary']}")
    else:
        print("❌ ai_summary: MISSING")
    
    if data and 'risk_flags' in data:
        print(f"✅ risk_flags: {data['risk_flags']}")
    else:
        print("❌ risk_flags: MISSING")
    
    if data and 'decision_support' in data:
        print(f"✅ decision_support: {data['decision_support']}")
    else:
        print("❌ decision_support: MISSING")
    
    print(f"\nOverall result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ai_fields())
