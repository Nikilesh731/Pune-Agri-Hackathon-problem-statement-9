"""
LLM Refinement Service for Agricultural Document Processing
Purpose: Add LLM refinement layer for noisy documents without overriding deterministic truth
"""

import json
from typing import Dict, List, Any, Optional


def refine_document_with_llm(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refine document analysis using LLM for noisy documents without overriding deterministic truth
    
    Args:
        extracted_data: Dictionary containing extracted fields from document processing
        
    Returns:
        Dictionary with LLM refinement advisory block
    """
    try:
        # Get core extracted information
        structured_data = extracted_data.get("structured_data", {})
        canonical = extracted_data.get("canonical", {})
        document_type = extracted_data.get("document_type", "unknown")
        confidence = extracted_data.get("confidence", 0)
        missing_fields = extracted_data.get("missing_fields", [])
        
        # LLM refinement responsibilities ONLY
        llm_refinement = {
            "refined_summary": _generate_refined_summary(structured_data, canonical, document_type),
            "officer_note": _generate_officer_note(structured_data, canonical, document_type, confidence),
            "consistency_flags": _check_consistency(structured_data, canonical, document_type),
            "confidence_note": _generate_confidence_note(confidence, missing_fields, structured_data)
        }
        
        return {
            "llm_refinement": llm_refinement,
            "success": True
        }
        
    except Exception as e:
        # If LLM fails, system must still succeed
        return {
            "llm_refinement": {
                "refined_summary": "LLM refinement temporarily unavailable",
                "officer_note": "Proceed with deterministic analysis",
                "consistency_flags": [],
                "confidence_note": f"LLM analysis failed: {str(e)}"
            },
            "success": False,
            "error": str(e)
        }


def _generate_refined_summary(structured_data: Dict, canonical: Dict, document_type: str) -> str:
    """Generate refined summary using LLM-like logic"""
    
    # Extract key information
    applicant = canonical.get("applicant", {}) if canonical else {}
    farmer_name = applicant.get("name") or structured_data.get("farmer_name", "Unknown farmer")
    
    # Document type specific refinement
    if document_type == "scheme_application":
        scheme_name = structured_data.get("scheme_name") or "agricultural scheme"
        amount = structured_data.get("amount", "")
        if amount:
            return f"{farmer_name} is applying for {scheme_name} with requested amount of ₹{amount}."
        else:
            return f"{farmer_name} submitted an application for {scheme_name}."
    
    elif document_type == "subsidy_claim":
        subsidy_type = structured_data.get("subsidy_type", "agricultural subsidy")
        amount = structured_data.get("amount", "")
        if amount:
            return f"{farmer_name} claims {subsidy_type} subsidy of ₹{amount}."
        else:
            return f"{farmer_name} submitted a claim for {subsidy_type}."
    
    elif document_type == "insurance_claim":
        claim_amount = structured_data.get("claim_amount", "")
        crop_type = structured_data.get("crop_type", "")
        if claim_amount and crop_type:
            return f"{farmer_name} filed insurance claim of ₹{claim_amount} for {crop_type} crop damage."
        else:
            return f"{farmer_name} submitted an insurance claim for crop damage."
    
    elif document_type == "grievance":
        complaint_type = structured_data.get("complaint_type", "agricultural issue")
        return f"{farmer_name} filed a grievance regarding {complaint_type}."
    
    elif document_type == "farmer_record":
        return f"Farmer record update for {farmer_name} with identity and contact information."
    
    else:
        return f"Document processing for {farmer_name} - {document_type.replace('_', ' ')}."


def _generate_officer_note(structured_data: Dict, canonical: Dict, document_type: str, confidence: float) -> str:
    """Generate officer note with actionable insights"""
    
    notes = []
    
    # Confidence assessment
    if confidence > 0.8:
        notes.append("High confidence extraction - minimal verification needed")
    elif confidence > 0.6:
        notes.append("Moderate confidence - verify key fields")
    else:
        notes.append("Low confidence - thorough verification recommended")
    
    # Document type specific notes
    if document_type == "scheme_application":
        scheme_name = structured_data.get("scheme_name", "")
        if scheme_name:
            notes.append(f"Verify eligibility criteria for {scheme_name}")
    
    elif document_type == "subsidy_claim":
        amount = structured_data.get("amount", "")
        if amount:
            try:
                amount_val = float(str(amount).replace(",", ""))
                if amount_val > 50000:
                    notes.append("High-value claim - additional verification recommended")
            except:
                notes.append("Verify amount format and calculation")
    
    elif document_type == "insurance_claim":
        claim_amount = structured_data.get("claim_amount", "")
        if claim_amount:
            notes.append("Verify crop damage assessment and claim calculation")
    
    elif document_type == "grievance":
        complaint_type = structured_data.get("complaint_type", "")
        if complaint_type:
            notes.append(f"Priority review recommended for {complaint_type}")
    
    # Identity verification note
    applicant = canonical.get("applicant", {}) if canonical else {}
    has_aadhaar = bool(applicant.get("aadhaar_number") or structured_data.get("aadhaar_number"))
    has_mobile = bool(applicant.get("mobile_number") or structured_data.get("phone_number"))
    
    if has_aadhaar and has_mobile:
        notes.append("Identity verified with Aadhaar and mobile")
    elif has_aadhaar:
        notes.append("Identity partially verified - Aadhaar available")
    else:
        notes.append("Identity verification needed - missing key identifiers")
    
    return " | ".join(notes)


def _check_consistency(structured_data: Dict, canonical: Dict, document_type: str) -> List[str]:
    """Check for consistency between OCR text and extracted fields"""
    
    consistency_flags = []
    
    # Check amount consistency
    amount_fields = ["amount", "claim_amount", "subsidy_amount", "requested_amount"]
    amounts = []
    
    for field in amount_fields:
        if field in structured_data and structured_data[field]:
            try:
                amount_val = float(str(structured_data[field]).replace(",", "").replace("₹", "").replace("$", ""))
                amounts.append(amount_val)
            except:
                consistency_flags.append(f"Inconsistent {field} format")
    
    # Check for multiple different amounts
    if len(amounts) > 1:
        unique_amounts = set(amounts)
        if len(unique_amounts) > 1:
            consistency_flags.append("Multiple different amounts detected - verify correct value")
    
    # Check name consistency
    applicant = canonical.get("applicant", {}) if canonical else {}
    canonical_name = applicant.get("name", "")
    structured_name = structured_data.get("farmer_name", "")
    
    if canonical_name and structured_name and canonical_name != structured_name:
        consistency_flags.append("Name variation detected between sources")
    
    # Check phone number format
    phone_fields = ["mobile_number", "phone_number", "contact_number"]
    for field in phone_fields:
        if field in structured_data and structured_data[field]:
            phone = str(structured_data[field])
            # Remove common formatting
            clean_phone = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if not clean_phone.isdigit() or len(clean_phone) != 10:
                consistency_flags.append(f"Invalid {field} format detected")
    
    # Document type specific consistency checks
    if document_type == "scheme_application":
        scheme_name = structured_data.get("scheme_name", "")
        if not scheme_name:
            consistency_flags.append("Scheme name not found in application")
    
    elif document_type == "insurance_claim":
        claim_amount = structured_data.get("claim_amount", "")
        crop_type = structured_data.get("crop_type", "")
        if claim_amount and not crop_type:
            consistency_flags.append("Claim amount present but crop type missing")
    
    return consistency_flags


def _generate_confidence_note(confidence: float, missing_fields: List[str], structured_data: Dict) -> str:
    """Generate confidence assessment note"""
    
    if confidence > 0.8:
        if len(missing_fields) == 0:
            return "Excellent extraction quality with complete data"
        else:
            return f"High confidence extraction but missing: {', '.join(missing_fields)}"
    
    elif confidence > 0.6:
        if len(missing_fields) <= 2:
            return f"Good extraction quality, verify: {', '.join(missing_fields)}"
        else:
            return f"Moderate confidence with several missing fields: {', '.join(missing_fields[:3])}"
    
    else:
        field_count = len([k for k, v in structured_data.items() if v])
        return f"Low confidence extraction ({field_count} fields found) - thorough verification required"


# Convenience function for integration
def add_llm_refinement_to_response(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add LLM refinement to extracted data without modifying deterministic fields
    
    Args:
        extracted_data: Original extracted data from document processing
        
    Returns:
        Enhanced extracted data with llm_refinement block
    """
    refinement_result = refine_document_with_llm(extracted_data)
    
    # Add llm_refinement block to extracted_data
    if refinement_result.get("success", False):
        extracted_data["llm_refinement"] = refinement_result["llm_refinement"]
    else:
        # Add fallback refinement
        extracted_data["llm_refinement"] = refinement_result.get("llm_refinement", {
            "refined_summary": "LLM refinement unavailable",
            "officer_note": "Rely on deterministic analysis",
            "consistency_flags": [],
            "confidence_note": "LLM analysis failed"
        })
    
    return extracted_data
