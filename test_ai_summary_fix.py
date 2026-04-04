#!/usr/bin/env python3
"""
Test script to verify AI Summary fix is working properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services'))

from app.modules.document_processing.document_processing_service import DocumentProcessingService
from app.modules.document_processing.service_schema import DocumentProcessingRequest
import asyncio

async def test_ai_summary_fix():
    """Test that AI Summary is properly mapped from intelligence service"""
    
    print("🔧 Testing AI Summary Mapping Fix")
    print("=" * 50)
    
    service = DocumentProcessingService()
    
    # Test Case 1: Insurance Claim
    print("\n📄 Test Case 1: Insurance Claim")
    request1 = DocumentProcessingRequest(
        processing_type='full_process',
        options={
            'filename': 'insurance_claim.pdf',
            'ocr_text': 'Rajesh Kumar from Maharashtra submitted an insurance claim for crop insurance requesting ₹50000 for crop damage due to drought. Policy number INS12345.'
        }
    )
    
    result1 = await service.process_request(request1)
    
    if result1.success and result1.data:
        print("✅ Processing successful")
        print(f"📋 Document Type: {result1.data.document_type}")
        print(f"🤖 AI Summary: {result1.data.ai_summary}")
        print(f"📝 Summary: {result1.data.summary}")
        
        # Verify the summary is contextual, not generic
        if "Rajesh Kumar" in str(result1.data.ai_summary) and "insurance claim" in str(result1.data.ai_summary):
            print("✅ AI Summary contains contextual information")
        else:
            print("❌ AI Summary appears to be generic fallback")
    else:
        print(f"❌ Processing failed: {result1.error_message}")
    
    # Test Case 2: Scheme Application
    print("\n📄 Test Case 2: Scheme Application")
    request2 = DocumentProcessingRequest(
        processing_type='full_process',
        options={
            'filename': 'scheme_application.pdf',
            'ocr_text': 'Meera Devi from Uttar Pradesh applied for Pradhan Mantri Kisan Samman Nidhi scheme. Application ID PMKISAN/2024/UP/012345. Seeking financial assistance for agricultural development.'
        }
    )
    
    result2 = await service.process_request(request2)
    
    if result2.success and result2.data:
        print("✅ Processing successful")
        print(f"📋 Document Type: {result2.data.document_type}")
        print(f"🤖 AI Summary: {result2.data.ai_summary}")
        
        # Verify the summary is contextual
        if "Meera Devi" in str(result2.data.ai_summary) and "scheme" in str(result2.data.ai_summary):
            print("✅ AI Summary contains contextual information")
        else:
            print("❌ AI Summary appears to be generic fallback")
    else:
        print(f"❌ Processing failed: {result2.error_message}")
    
    print("\n" + "=" * 50)
    print("🎯 AI Summary Mapping Test Complete")
    print("The fix ensures intelligence service summaries are properly mapped to ai_summary field")

if __name__ == "__main__":
    asyncio.run(test_ai_summary_fix())
