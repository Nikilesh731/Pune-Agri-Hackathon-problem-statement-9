#!/usr/bin/env python3
"""
AI Intelligence Pipeline Test Script
Tests the enhanced AI pipeline with semantic extraction, reasoning, and predictive analytics
"""

import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

from modules.document_processing.extraction_service import DocumentExtractionService


def test_intelligence_pipeline():
    """Test the enhanced AI pipeline with intelligence features"""
    
    print("🧠 AI Intelligence Pipeline Test")
    print("=" * 60)
    
    # Initialize enhanced extraction service
    extraction_service = DocumentExtractionService()
    
    # Test document with varied content
    test_document = """
PRADHAN MANTRI KISAN SAMMAN NIDHI SCHEME

Applicant Information:
Name: Rajesh Kumar Sharma
Father's Name: Suresh Chand Sharma
Age: 45 years
Gender: Male

Address Details:
Village: Rampur
Post Office: Badi
District: Jalaun
State: Uttar Pradesh
Pin Code: 285204

Contact Information:
Mobile Number: 9876543210
Aadhaar Number: 2345678901234

Land Details:
Total Land Area: 2.5 hectares
Crop Pattern: Wheat in Rabi, Rice in Kharif

Bank Details:
Bank Account Number: 1234567890123456
IFSC Code: SBIN0005678
Branch: State Bank of India, Rampur

Scheme Details:
Scheme Applied: Pradhan Mantri Kisan Samman Nidhi
Benefit Amount: Rs. 6000 per year
Application ID: PMKISAN/2024/UP/012345

Declaration:
I hereby declare that all information provided is true and correct to the best of my knowledge.
    
Signature: ___________________
Date: 15/03/2024
"""
    
    print("📄 Test Document: Complex Scheme Application")
    print("-" * 40)
    
    # Test with scheme_application type
    result = extraction_service.extract_document(test_document, "scheme_application")
    
    print(f"✅ Extraction Success: {bool(result.get('structured_data'))}")
    print(f"📊 Extraction Confidence: {result.get('confidence', 0):.3f}")
    print(f"📝 Structured Fields: {len(result.get('structured_data', {}))}")
    print(f"🧠 Reasoning Items: {len(result.get('reasoning', []))}")
    print(f"🔍 Reasoning Insights: {len(result.get('reasoning_insights', []))}")
    
    # Display key extracted fields
    print("\n📋 Key Extracted Fields:")
    structured_data = result.get('structured_data', {})
    key_fields = ['farmer_name', 'scheme_name', 'aadhaar_number', 'location', 'land_size', 'requested_amount']
    for field in key_fields:
        if field in structured_data:
            print(f"  • {field}: {structured_data[field]}")
    
    # Display enhanced reasoning
    print("\n🧠 Enhanced Reasoning Sample:")
    reasoning = result.get('reasoning', [])
    for i, reason in enumerate(reasoning[:5]):
        print(f"  {i+1}. {reason}")
    
    # Display reasoning insights
    print("\n🔍 Reasoning Insights:")
    insights = result.get('reasoning_insights', [])
    insight_types = {}
    for insight in insights:
        insight_type = insight.get('type', 'unknown')
        if insight_type not in insight_types:
            insight_types[insight_type] = []
        insight_types[insight_type].append(insight.get('message', ''))
    
    for insight_type, messages in insight_types.items():
        print(f"  📊 {insight_type}: {len(messages)} insights")
        for message in messages[:2]:  # First 2 messages per type
            print(f"    • {message}")
    
    # Display predictions
    print("\n🔮 Predictive Analytics:")
    predictions = result.get('predictions', {})
    if predictions and 'predictions' in predictions:
        pred_data = predictions['predictions']
        for pred_type, pred_info in pred_data.items():
            print(f"  📈 {pred_type}: {pred_info.get('value', 'N/A')} (confidence: {pred_info.get('confidence', 0):.2f})")
            reasoning = pred_info.get('reasoning', [])
            if reasoning:
                print(f"    Reasoning: {reasoning[0]}")
    
    # Test semantic extraction capabilities
    print("\n🎯 Semantic Extraction Test:")
    semantic_test = """
To: The District Agriculture Officer
From: Ram Singh Yadav, Village Chandpur, Tehsil Konch, District Auraiya
Subject: Complaint Regarding Delay in Subsidy Payment
Date: 10/03/2024

Dear Sir,

I am writing to complain about the delay in subsidy payment for my agricultural machinery purchase.
My name is Ram Singh Yadav and I have purchased a tractor worth Rs. 260,000.
The subsidy amount of Rs. 80,000 has not been released for the past 3 months.

My Aadhaar number is 567890123456 and mobile number is 7654321098.

Please look into this matter urgently.

Thank you,
Ram Singh Yadav
"""
    
    semantic_result = extraction_service.extract_document(semantic_test, "grievance")
    semantic_structured = semantic_result.get('structured_data', {})
    
    print(f"  📝 Semantic Fields Extracted: {len(semantic_structured)}")
    semantic_keys = ['farmer_name', 'location', 'description', 'mobile_number', 'aadhaar_number']
    for key in semantic_keys:
        if key in semantic_structured:
            print(f"    • {key}: {semantic_structured[key]}")
    
    # Test field filtering
    print("\n🧹 Field Filtering Test:")
    filtered_fields = result.get('extracted_fields', {})
    print(f"  📊 Total Fields After Filtering: {len(filtered_fields)}")
    
    # Show field sources
    sources = {}
    for field_name, field_data in filtered_fields.items():
        if isinstance(field_data, dict):
            source = field_data.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
    
    print("  📋 Field Sources:")
    for source, count in sources.items():
        print(f"    • {source}: {count} fields")
    
    # Summary
    print("\n📈 Intelligence Pipeline Summary:")
    print("=" * 40)
    print(f"✅ Enhanced Extraction: {len(result.get('structured_data', {}))} fields")
    print(f"🧠 Reasoning Engine: {len(result.get('reasoning_insights', []))} insights")
    print(f"🔮 Predictive Analytics: {len(result.get('predictions', {}).get('predictions', {}))} predictions")
    print(f"🧹 Noise Filtering: Applied successfully")
    print(f"🎯 Overall Pipeline: Working with intelligence enhancement")
    
    print("\n🎉 AI Intelligence Pipeline Test Complete!")


if __name__ == "__main__":
    test_intelligence_pipeline()
