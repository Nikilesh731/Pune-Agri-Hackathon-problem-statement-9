#!/usr/bin/env python3
"""
End-to-end test to verify Aadhaar detection and AI summary display in the frontend
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

from modules.document_processing.document_processing_service import DocumentProcessingService
import asyncio
import json

async def test_end_to_end():
    """Test the complete pipeline as it would work in production"""
    
    print("=" * 60)
    print("END-TO-END AADHAAR DETECTION AND AI SUMMARY TEST")
    print("=" * 60)
    
    # Sample insurance claim text with Aadhaar
    text = """Claimant Name: Suresh Patel
Aadhaar Number: 345678901234
Mobile Number: 9988776655
Address: Village, Mahua District Chitrakoot State Uttar Pradesh
Policy Number: PMFBY
Claim Type: Crop Insurance
Claim Amount: ₹75
Loss Description: Crop damage due to flood"""
    
    print("\n1. AI Service Processing")
    print("-" * 40)
    
    service = DocumentProcessingService()
    result = await service.process_document(
        file_data=b'',
        filename='insurance_claim_test.pdf',
        processing_type='full_process',
        options={'ocr_text': text}
    )
    
    if not result.success:
        print(f"❌ AI Service Failed: {result.error_message}")
        return
    
    data = result.data
    structured_data = data.structured_data or {}
    
    print(f"✅ Document Type: {data.document_type}")
    print(f"✅ Classification Confidence: {data.classification_confidence:.2%}")
    print(f"✅ Aadhaar Number: {structured_data.get('aadhaar_number', 'NOT FOUND')}")
    print(f"✅ AI Summary: {data.summary[:100]}..." if data.summary else "❌ NO SUMMARY")
    
    print("\n2. Backend Mapping Simulation")
    print("-" * 40)
    
    # Simulate backend AI orchestrator mapping
    backend_extracted_data = {
        "document_type": data.document_type,
        "structured_data": data.structured_data,
        "extracted_fields": data.extracted_fields,
        "missing_fields": data.missing_fields,
        "confidence": data.decision_support.confidence if data.decision_support else 0.5,
        "reasoning": data.reasoning,
        "classification_confidence": data.classification_confidence,
        "classification_reasoning": data.classification_reasoning,
        "risk_flags": data.risk_flags,
        "decision_support": data.decision_support,
        "summary": data.summary,
        "case_insight": data.case_insight,
        "predictions": data.predictions,
        "ai_summary": data.summary,  # Map summary to ai_summary for compatibility
        "aadhaar_number": structured_data.get('aadhaar_number'),  # Extract for fraud detection
        "farmer_name": structured_data.get('farmer_name'),
        "land_size": structured_data.get('land_size')
    }
    
    print(f"✅ Mapped aadhaar_number: {backend_extracted_data['aadhaar_number']}")
    print(f"✅ Mapped ai_summary: {backend_extracted_data['ai_summary'][:50] if backend_extracted_data['ai_summary'] else 'None'}...")
    
    print("\n3. Fraud Detection")
    print("-" * 40)
    
    from app.api.fraud_detection import detect_fraud
    
    fraud_result = detect_fraud(backend_extracted_data)
    print(f"✅ Fraud Score: {fraud_result['fraud_score']:.2%}")
    print(f"✅ Risk Level: {fraud_result['risk_level']}")
    print(f"✅ Fraud Flags: {len(fraud_result['indicators'])}")
    if fraud_result['indicators']:
        for flag in fraud_result['indicators']:
            print(f"   - {flag}")
    
    # Simulate backend response
    backend_response = {
        "success": True,
        "data": {
            "extractedData": backend_extracted_data,
            "aiSummary": backend_extracted_data["ai_summary"],
            "fraudRiskScore": fraud_result["fraud_score"],
            "fraudFlags": fraud_result["indicators"],
            "priorityScore": 50,
            "verificationRecommendation": data.decision_support.decision if data.decision_support else "review",
            "aiProcessingStatus": "completed"
        }
    }
    
    print("\n4. Frontend Mapping Simulation")
    print("-" * 40)
    
    # Simulate frontend mapping
    frontend_data = {
        "extractedData": backend_response["data"]["extractedData"],
        "aiSummary": backend_response["data"]["aiSummary"],
        "fraudRiskScore": backend_response["data"]["fraudRiskScore"],
        "fraudFlags": backend_response["data"]["fraudFlags"],
        "verificationRecommendation": backend_response["data"]["verificationRecommendation"],
        "aiProcessingStatus": backend_response["data"]["aiProcessingStatus"]
    }
    
    # Check what the frontend would display
    display_aadhaar = frontend_data["extractedData"].get("structured_data", {}).get("aadhaar_number")
    display_summary = frontend_data["extractedData"].get("summary") or frontend_data.get("aiSummary")
    display_fraud_flags = frontend_data.get("fraudFlags", [])
    
    print(f"✅ Frontend Aadhaar Display: {display_aadhaar}")
    print(f"✅ Frontend Summary Display: {display_summary[:50] if display_summary else 'None'}...")
    print(f"✅ Frontend Fraud Flags: {len(display_fraud_flags)}")
    if display_fraud_flags:
        for flag in display_fraud_flags:
            print(f"   - {flag}")
    
    print("\n5. Final Verification")
    print("-" * 40)
    
    # Check all conditions
    aadhaar_extracted = bool(display_aadhaar)
    aadhaar_not_flagged = not any("Missing Aadhaar" in flag for flag in display_fraud_flags)
    summary_generated = bool(display_summary)
    
    print(f"✅ Aadhaar Extracted: {aadhaar_extracted}")
    print(f"✅ Aadhaar Not Flagged as Missing: {aadhaar_not_flagged}")
    print(f"✅ AI Summary Generated: {summary_generated}")
    
    if aadhaar_extracted and aadhaar_not_flagged and summary_generated:
        print("\n🎉 SUCCESS: All issues have been fixed!")
        print("   - Aadhaar number is correctly extracted")
        print("   - Fraud detection correctly recognizes Aadhaar presence")
        print("   - AI summary is generated and displayed")
        print("\nThe user should now see:")
        print("   • Aadhaar number in extracted fields")
        print("   • No 'Missing Aadhaar number' flag in AI Analysis")
        print("   • AI-analyzed summary from document content")
    else:
        print("\n❌ FAILURE: Some issues persist")
        if not aadhaar_extracted:
            print("   - Aadhaar not extracted")
        if not aadhaar_not_flagged:
            print("   - Aadhaar still flagged as missing")
        if not summary_generated:
            print("   - AI summary not generated")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
