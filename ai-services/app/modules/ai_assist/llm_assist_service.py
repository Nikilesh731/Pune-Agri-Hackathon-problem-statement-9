"""
LLM Assist Service for Agricultural Document Processing

This service adds AI-based intelligence on top of extracted data without modifying
the core extraction logic. It provides summaries, risk analysis, and decision hints.
"""

import json
from typing import Dict, List, Any


def analyze_application(extracted_data: dict) -> dict:
    """
    Analyze extracted application data using rule-based logic to provide AI insights.
    
    Args:
        extracted_data: Dictionary containing extracted fields from document processing
        
    Returns:
        Dictionary with AI analysis including summary, risk flags, missing insights, and decision hint
    """
    try:
        # Rule-based analysis for now (can be enhanced with actual LLM later)
        ai_analysis = _generate_rule_based_analysis(extracted_data)
        return ai_analysis
        
    except Exception as e:
        # Fallback response if analysis fails
        return {
            "ai_summary": f"Application processed with {len(extracted_data)} extracted fields. AI analysis fallback was used.",
            "risk_flags": [
                {
                    "code": "AI_ANALYSIS_UNAVAILABLE",
                    "severity": "medium",
                    "message": f"Analysis unavailable: {str(e)}"
                }
            ],
            "missing_insights": ["Analysis temporarily unavailable"],
            "decision_support": {
                "decision": "review",
                "confidence": 0.5,
                "reasoning": ["AI analysis unavailable, manual review recommended"]
            }
        }


def _get_required_fields(document_type: str):
    """Get required fields based on document type"""
    mapping = {
        "scheme_application": ["farmer_name", "scheme_name"],
        "subsidy_claim": ["farmer_name", "subsidy_type", "requested_amount"],
        "insurance_claim": ["farmer_name", "claim_amount"],
        "grievance": ["farmer_name"],
        "farmer_record": ["farmer_name"],
        "supporting_document": []
    }
    return mapping.get(document_type, [])


def _generate_rule_based_analysis(extracted_data: dict) -> dict:
    """Generate rule-based analysis from extracted data"""
    
    # Basic summary
    doc_type = extracted_data.get("document_type", "unknown")
    confidence = extracted_data.get("confidence", 0)
    summary = f"{doc_type.replace('_', ' ').title()} processed with {len(extracted_data)} fields extracted at {confidence:.1%} confidence"
    
    # Risk analysis - convert to expected schema format
    risk_flags = []
    
    # Check confidence
    if confidence < 0.7:
        risk_flags.append({
            "code": "LOW_CONFIDENCE",
            "severity": "medium",
            "message": f"Low extraction confidence ({confidence:.1%})"
        })
    
    # Check missing required fields (document-type specific)
    required_fields = _get_required_fields(doc_type)
    missing_fields = []
    
    for field in required_fields:
        if field not in extracted_data or not extracted_data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        risk_flags.append({
            "code": "MISSING_REQUIRED_FIELDS",
            "severity": "high",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        })
    
    # Check for suspicious values
    if "amount" in extracted_data:
        try:
            amount = float(extracted_data["amount"])
            if amount > 1000000:  # Very large amount
                risk_flags.append({
                    "code": "UNUSUALLY_LARGE_AMOUNT",
                    "severity": "medium",
                    "message": "Unusually large amount detected"
                })
        except (ValueError, TypeError):
            risk_flags.append({
                "code": "INVALID_AMOUNT_FORMAT",
                "severity": "medium",
                "message": "Invalid amount format"
            })
    
    # Missing insights (helpful but not required fields)
    missing_insights = []
    helpful_fields = ["contact_number", "email", "address", "crop_type", "land_area"]
    
    for field in helpful_fields:
        if field not in extracted_data or not extracted_data[field]:
            missing_insights.append(f"Consider adding {field.replace('_', ' ')}")
    
    # Decision hint - convert to DecisionSupport format
    has_high = any(r["severity"] == "high" for r in risk_flags)
    has_medium = any(r["severity"] == "medium" for r in risk_flags)
    
    if not risk_flags:
        decision_hint = "approve"
        decision_confidence = 0.9
    elif has_high:
        decision_hint = "review"   # NOT reject directly
        decision_confidence = 0.75
    elif has_medium:
        decision_hint = "review"
        decision_confidence = 0.7
    else:
        decision_hint = "approve"
        decision_confidence = 0.8
    
    decision_support = {
        "decision": decision_hint,
        "confidence": decision_confidence,
        "reasoning": [
            f"Analysis based on {len(extracted_data)} extracted fields",
            f"Classification confidence: {confidence:.1%}",
            f"Risk flags identified: {len(risk_flags)}"
        ]
    }
    
    return {
        "ai_summary": summary,
        "risk_flags": risk_flags,
        "missing_insights": missing_insights,
        "decision_support": decision_support
    }
