#!/usr/bin/env python3
"""
Debug classification for insurance claim test
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

from modules.document_processing.classification_service import DocumentClassificationService

# Insurance claim test text
insurance_text = """
CROP INSURANCE CLAIM FORM

Policy Information:
Policy Number: CROP-INS-2023-456789
Insurance Company: Pradhan Mantri Fasal Bima Yojana
Policy Period: 01/04/2023 to 31/03/2024
Premium Paid: Rs. 3,500

Insured Farmer Details:
Name: Suresh Kumar Patel
Father Name: Ramesh Patel
Address: Village Pipri, District Banda, UP
Mobile: 8765432109
Aadhaar: 456789012345

Crop Information:
Crop Type: Wheat
Season: Rabi 2023-24
Area Insured: 3.0 hectares
Expected Yield: 25 quintals per hectare

Loss Information:
Date of Loss: 15/01/2024
Cause of Loss: Untimely rainfall and hailstorm
Percentage of Damage: 70%
Actual Yield: 7.5 quintals per hectare

Claim Details:
Claim Amount Requested: Rs. 75,000
Claim Date: 05/02/2024
Claim Reference: CLAIM-2024-001234

Supporting Documents:
1. Crop cutting experiment report
2. Weather department report
3. Land ownership documents
"""

def main():
    classifier = DocumentClassificationService()
    
    print("🔍 Debugging Insurance Claim Classification")
    print("=" * 50)
    
    # Test classification
    result = classifier.classify_document(insurance_text)
    
    print(f"📋 Classified Type: {result['document_type']}")
    print(f"📊 Confidence: {result['classification_confidence']}")
    print(f"🧠 Reasoning:")
    
    reasoning = result['classification_reasoning']
    print(f"  Keywords found: {reasoning['keywords_found']}")
    print(f"  Structural indicators: {reasoning['structural_indicators']}")
    print(f"  Confidence factors: {reasoning['confidence_factors']}")
    
    # Test subsidy priority detection
    print("\n🎯 Testing Subsidy Priority Detection")
    print("-" * 40)
    
    text_lower = insurance_text.lower()
    subsidy_score, subsidy_reasoning = classifier._detect_subsidy_priority(text_lower)
    
    print(f"Subsidy Score: {subsidy_score}")
    print(f"Subsidy Reasoning: {subsidy_reasoning}")
    
    # Test insurance priority detection
    print("\n🛡️ Testing Insurance Priority Detection")
    print("-" * 40)
    
    insurance_score, insurance_reasoning = classifier._detect_insurance_priority(text_lower)
    
    print(f"Insurance Score: {insurance_score}")
    print(f"Insurance Reasoning: {insurance_reasoning}")

if __name__ == "__main__":
    main()
