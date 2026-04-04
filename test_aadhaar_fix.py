#!/usr/bin/env python3
"""
Test script to verify Aadhaar detection and AI summary display
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

from modules.document_processing.document_processing_service import DocumentProcessingService
import asyncio

async def test_aadhaar_detection():
    """Test that Aadhaar is properly detected and not flagged as missing"""
    
    # Sample insurance claim text with Aadhaar
    text = """Claimant Name: Suresh Patel
Aadhaar Number: 345678901234
Mobile Number: 9988776655
Address: Village, Mahua District Chitrakoot State Uttar Pradesh
Policy Number: PMFBY
Claim Type: Crop Insurance
Claim Amount: ₹75
Loss Description: Crop damage due to flood"""
    
    print("Testing Aadhaar Detection and AI Summary")
    print("=" * 50)
    
    service = DocumentProcessingService()
    result = await service.process_document(
        file_data=b'',
        filename='insurance_claim_test.pdf',
        processing_type='full_process',
        options={'ocr_text': text}
    )
    
    if result.success and result.data:
        print("\n✅ Document Processing Success")
        
        # Check structured data
        structured_data = result.data.structured_data or {}
        print(f"\n📋 Structured Data Fields: {len(structured_data)}")
        print(f"   Aadhaar Number Present: {'aadhaar_number' in structured_data}")
        if 'aadhaar_number' in structured_data:
            print(f"   Aadhaar Value: {structured_data['aadhaar_number']}")
        
        # Check AI summary
        print(f"\n📄 AI Summary: {result.data.summary or 'NOT GENERATED'}")
        
        # Check decision support
        if result.data.decision_support:
            print(f"\n💡 Decision Support:")
            print(f"   Decision: {result.data.decision_support.decision}")
            print(f"   Confidence: {result.data.decision_support.confidence:.2%}")
            print(f"   Reasoning: {', '.join(result.data.decision_support.reasoning)}")
        
        # Check risk flags
        risk_flags = result.data.risk_flags or []
        print(f"\n🚨 Risk Flags: {len(risk_flags)}")
        for flag in risk_flags:
            print(f"   - {flag.get('message', flag.get('code', 'Unknown'))}")
        
        # Check missing fields
        missing_fields = result.data.missing_fields or []
        print(f"\n⚠️ Missing Fields: {len(missing_fields)}")
        if missing_fields:
            for field in missing_fields:
                print(f"   - {field}")
        
        # Test fraud detection logic
        from app.api.fraud_detection import detect_fraud
        
        fraud_data = {
            'farmer_name': structured_data.get('farmer_name', ''),
            'aadhaar_number': structured_data.get('aadhaar_number', ''),
            'land_size': structured_data.get('land_size', '')
        }
        
        fraud_result = detect_fraud(fraud_data)
        print(f"\n🔍 Fraud Detection:")
        print(f"   Score: {fraud_result['fraud_score']:.2%}")
        print(f"   Risk Level: {fraud_result['risk_level']}")
        print(f"   Indicators: {', '.join(fraud_result['indicators']) if fraud_result['indicators'] else 'None'}")
        
        # Verify fix
        has_aadhaar = 'aadhaar_number' in structured_data and structured_data['aadhaar_number']
        fraud_flags_missing_aadhaar = any('Missing Aadhaar' in ind for ind in fraud_result['indicators'])
        
        print("\n" + "=" * 50)
        print("VERIFICATION RESULTS:")
        print(f"✅ Aadhaar Extracted: {has_aadhaar}")
        print(f"✅ Not Flagged as Missing: {not fraud_flags_missing_aadhaar}")
        print(f"✅ AI Summary Generated: {bool(result.data.summary)}")
        
        if has_aadhaar and not fraud_flags_missing_aadhaar and result.data.summary:
            print("\n🎉 ALL TESTS PASSED - Aadhaar issue is fixed!")
        else:
            print("\n❌ Some tests failed - Issue persists")
    else:
        print(f"❌ Document Processing Failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(test_aadhaar_detection())
