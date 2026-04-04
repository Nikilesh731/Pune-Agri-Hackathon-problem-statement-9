#!/usr/bin/env python3
"""
Intelligence Layer Test Script
Tests the new intelligence service with all document types
"""

import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

from modules.intelligence.intelligence_service import IntelligenceService


def create_test_extracted_data(document_type: str) -> dict:
    """Create realistic extracted data for testing"""
    
    base_data = {
        "document_type": document_type,
        "structured_data": {},
        "extracted_fields": {},
        "missing_fields": [],
        "confidence": 0.85,
        "reasoning": ["Fields extracted: farmer_name, scheme_name"],
        "classification_confidence": 0.92,
        "classification_reasoning": ["Keywords matched", "Structure matches"]
    }
    
    if document_type == "scheme_application":
        base_data["structured_data"] = {
            "farmer_name": "Rajesh Kumar Sharma",
            "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
            "application_id": "PMKISAN/2024/UP/012345",
            "village": "Rampur",
            "district": "Jalaun",
            "aadhaar_number": "2345678901234",
            "mobile_number": "9876543210",
            "land_size": "2.5 hectares"
        }
        base_data["missing_fields"] = ["bank_account"]
        
    elif document_type == "subsidy_claim":
        base_data["structured_data"] = {
            "farmer_name": "Ram Singh Yadav",
            "claim_amount": "80000",
            "claim_id": "SUB/2024/UP/0678",
            "village": "Chandpur",
            "district": "Auraiya",
            "mobile_number": "7654321098",
            "purchase_date": "15/01/2024"
        }
        base_data["missing_fields"] = ["bank_details"]
        
    elif document_type == "grievance":
        base_data["structured_data"] = {
            "farmer_name": "Mohan Lal Verma",
            "issue_type": "Delay in subsidy payment",
            "issue_description": "Subsidy for tractor purchase not received for 3 months",
            "village": "Badi",
            "district": "Jalaun",
            "mobile_number": "9123456789",
            "grievance_date": "10/03/2024"
        }
        base_data["missing_fields"] = ["reference_number"]
        
    elif document_type == "insurance_claim":
        base_data["structured_data"] = {
            "farmer_name": "Shiv Kumar Singh",
            "claim_amount": "150000",
            "crop_type": "Wheat",
            "claim_id": "INS/2024/UP/0234",
            "village": "Nagla",
            "district": "Etawah",
            "damage_area": "1.8 hectares"
        }
        base_data["missing_fields"] = ["insurance_policy_number"]
        
    elif document_type == "farmer_record":
        base_data["structured_data"] = {
            "farmer_name": "Gopal Prasad Yadav",
            "farmer_id": "FMR/2024/UP/0456",
            "village": "Kachhara",
            "district": "Kanpur Rural",
            "land_holdings": "3.2 hectares",
            "aadhaar_number": "3456789012345"
        }
        base_data["missing_fields"] = ["family_details"]
        
    elif document_type == "supporting_document":
        base_data["structured_data"] = {
            "farmer_name": "Amit Kumar",
            "document_type": "Land ownership proof",
            "village": "Shivrajpur",
            "district": "Kanpur Nagar",
            "reference_number": "DOC/2024/789"
        }
        base_data["missing_fields"] = ["document_date"]
        base_data["confidence"] = 0.73  # Lower confidence for supporting docs
    
    return base_data


def test_intelligence_service():
    """Test the intelligence service with all document types"""
    
    print("🧠 Intelligence Layer Test")
    print("=" * 60)
    
    intelligence_service = IntelligenceService()
    
    # Test all document types
    document_types = [
        "scheme_application",
        "subsidy_claim", 
        "grievance",
        "insurance_claim",
        "farmer_record",
        "supporting_document"
    ]
    
    results = []
    
    for doc_type in document_types:
        print(f"\n📄 Testing {doc_type.replace('_', ' ').title()}")
        print("-" * 40)
        
        # Create test data
        test_data = create_test_extracted_data(doc_type)
        
        try:
            # Test document summary
            summary = intelligence_service.generate_document_summary(test_data)
            print(f"📝 Summary: {summary}")
            
            # Test case insight
            case_insight = intelligence_service.generate_case_insight(test_data)
            print(f"🔍 Case Insight:")
            for insight in case_insight:
                print(f"  • {insight}")
            
            # Test decision support
            decision_support = intelligence_service.generate_decision_support(test_data)
            print(f"⚖️  Decision: {decision_support['decision'].upper()}")
            print(f"📊 Confidence: {decision_support['confidence']:.2f}")
            print(f"💭 Reasoning:")
            for reason in decision_support['reasoning']:
                print(f"    • {reason}")
            
            # Test predictions
            predictions = intelligence_service.generate_predictions(test_data)
            print(f"🔮 Predictions:")
            print(f"  ⏱️  Processing Time: {predictions['processing_time']}")
            print(f"  📈 Approval Likelihood: {predictions['approval_likelihood']}")
            print(f"  ⚠️  Risk Level: {predictions['risk_level']}")
            
            # Validate outputs
            validation_result = validate_intelligence_output(
                summary, case_insight, decision_support, predictions, doc_type
            )
            
            results.append({
                "document_type": doc_type,
                "success": validation_result["success"],
                "issues": validation_result["issues"]
            })
            
            if validation_result["success"]:
                print("✅ PASSED")
            else:
                print("❌ FAILED:")
                for issue in validation_result["issues"]:
                    print(f"    • {issue}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "document_type": doc_type,
                "success": False,
                "issues": [f"Exception: {str(e)}"]
            })
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 40)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    # Show failed tests
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print("\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  • {test['document_type']}: {', '.join(test['issues'])}")
    
    print(f"\n🎉 Intelligence Layer Test Complete!")
    return results


def validate_intelligence_output(summary, case_insight, decision_support, predictions, doc_type):
    """Validate intelligence outputs meet requirements"""
    
    issues = []
    
    # Validate summary
    if not summary or len(summary) < 10:
        issues.append("Summary too short or empty")
    if len(summary.split('\n')) > 3:
        issues.append("Summary exceeds 3 lines")
    
    # Validate case insight
    if not isinstance(case_insight, list):
        issues.append("Case insight not a list")
    elif len(case_insight) > 5:
        issues.append("Case insight exceeds 5 bullet points")
    elif len(case_insight) == 0:
        issues.append("Case insight empty")
    
    # Validate decision support
    required_decision_fields = ["decision", "confidence", "reasoning"]
    for field in required_decision_fields:
        if field not in decision_support:
            issues.append(f"Missing decision field: {field}")
    
    if "decision" in decision_support:
        valid_decisions = ["approve", "review", "reject"]
        if decision_support["decision"] not in valid_decisions:
            issues.append(f"Invalid decision: {decision_support['decision']}")
    
    if "confidence" in decision_support:
        confidence = decision_support["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            issues.append(f"Invalid confidence: {confidence}")
    
    if "reasoning" in decision_support:
        reasoning = decision_support["reasoning"]
        if not isinstance(reasoning, list) or len(reasoning) > 3:
            issues.append("Invalid reasoning format or too many points")
    
    # Validate predictions
    required_prediction_fields = ["processing_time", "approval_likelihood", "risk_level"]
    for field in required_prediction_fields:
        if field not in predictions:
            issues.append(f"Missing prediction field: {field}")
    
    if "risk_level" in predictions:
        valid_risks = ["Low", "Medium", "High"]
        if predictions["risk_level"] not in valid_risks:
            issues.append(f"Invalid risk level: {predictions['risk_level']}")
    
    if "processing_time" in predictions:
        time_str = predictions["processing_time"]
        if not time_str.endswith(" days"):
            issues.append(f"Invalid processing time format: {time_str}")
    
    if "approval_likelihood" in predictions:
        likelihood_str = predictions["approval_likelihood"]
        if not likelihood_str.endswith("%"):
            issues.append(f"Invalid approval likelihood format: {likelihood_str}")
    
    return {
        "success": len(issues) == 0,
        "issues": issues
    }


if __name__ == "__main__":
    test_intelligence_service()
