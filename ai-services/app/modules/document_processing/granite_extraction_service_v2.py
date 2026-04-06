"""
Granite Semantic Extraction Service (Production-Ready)
Purpose: Lightweight semantic extraction layer WITHOUT external dependencies
Uses: Rule-based + pattern matching on Docling output
"""
import logging
import json
import re
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


class GraniteExtractionServiceV2:
    """
    Lightweight Granite-like semantic extraction service
    
    Key characteristics:
    - NO external HTTP calls - fully internal
    - NO LLM/transformer models
    - Rule-based semantic analysis
    - Pattern matching for field extraction
    - Confidence scoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("[GRANITE-V2] Granite extraction service initialized (lightweight mode)")
        
        # Semantic extraction rules
        self._initialize_extraction_patterns()
    
    def _initialize_extraction_patterns(self):
        """Initialize regex patterns for field extraction"""
        self._patterns = {
            "aadhaar": r"(?:aadhaar|aadhar)\s*(?:num|no|number)?[\s:=-]*(\d{4}\s?\d{4}\s?\d{4}|\d{12})",
            "pan": r"(?:pan\s+)?([A-Z]{5}[0-9]{4}[A-Z]{1})",
            "bank_account": r"(?:account|bank|acn|ac|a/c)[\s:=-]*(\d{9,18})",
            "ifsc": r"(?:ifsc|ifsc\s+code)[\s:=-]*([A-Z]{4}[0-9]{7})",
            "mobile": r"(?:phone|mobile|number|contact)[\s:=-]*(\+?91[-.\s]?[6-9]\d{9}|\+?91[-.\s]?\d{2}[-.\s]?\d{4}[-.\s]?\d{4})",
            "land_area": r"(?:land|area|hectare|acre|bigha)[\s:=-]*(\d+(?:\.\d+)?)\s*(?:hectare|ha|acre|ac|bigha|sq\.?m|sqm|bigha)?",
            "amount": r"(?:amount|requested|claim|subsidy|requested\s+amount)[\s:=-]*(?:rs|₹|inr)?[\s]*(\d+(?:,\d{3})*(?:\.\d+)?)",
            "date": r"(?:date|applied|application|submitted)[\s:=-]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            "application_id": r"(?:id|application\s+id|app\s+id|ref|reference|ref\s+no|reference\s+no|application\s+no)[\s:=-]*([A-Z0-9]{6,20})"
        }
    
    def _extract_field_simple(self, text: str, field_type: str) -> Optional[str]:
        """Extract single field using regex pattern"""
        if field_type not in self._patterns:
            return None
        
        pattern = self._patterns[field_type]
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if matches:
            # Return first match, cleaned
            value = matches[0].strip()
            return value if value else None
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract farmer/applicant name from text"""
        # Look for patterns like "Name: XYZ" or "Farmer Name: XYZ"
        name_patterns = [
            r"(?:farmer\s+)?name[\s:=-]*([A-Zა-ჯ\u0900-\u097F\u0980-\u09FF\u0900-\u0963]{2,}(?:\s+[A-Zა-ჯ\u0900-\u097F\u0980-\u09FF\u0900-\u0963]{2,})*)",
            r"applicant[\s:=-]*([A-Zა-ჯ\u0900-\u097F\u0980-\u09FF\u0900-\u0963]{2,}(?:\s+[A-Zა-ჯ\u0900-\u097F\u0980-\u09FF\u0900-\u0963]{2,})*)"
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_location(self, text: str) -> Dict[str, Optional[str]]:
        """Extract village, district, state"""
        location = {}
        
        # Location patterns
        location_patterns = {
            "village": r"(?:village|gram|gaon)[\s:=-]*([A-Za-z\u0900-\u097F\u0980-\u09FF\u0900-\u0963]+(?:\s+[A-Za-z\u0900-\u097F\u0980-\u09FF\u0900-\u0963]+)?)",
            "district": r"(?:district|tehsil|taluka)[\s:=-]*([A-Za-z\u0900-\u097F\u0980-\u09FF\u0900-\u0963]+(?:\s+[A-Za-z\u0900-\u097F\u0980-\u09FF\u0900-\u0963]+)?)",
            "state": r"(?:state|province|pradesh)[\s:=-]*([A-Za-z\u0900-\u097F\u0980-\u09FF\u0900-\u0963\s]+)(?:[\.,]|$)"
        }
        
        for location_type, pattern in location_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            location[location_type] = matches[0].strip() if matches else None
        
        return location
    
    def _extract_crop(self, text: str) -> Optional[str]:
        """Extract crop type from text"""
        crop_keywords = {
            "wheat": r"\b(?:wheat|gehun|गेहूं|ಗೋಧಿ)\b",
            "rice": r"\b(?:rice|chawal|चावल|ಅಕ್ಕಿ)\b",
            "sugarcane": r"\b(?:sugarcane|sugar\s+cane|ganna|गन्ना|ಕಬ್ಬು)\b",
            "cotton": r"\b(?:cotton|kapas|कपास|棉花)\b",
            "maize": r"\b(?:maize|corn|makka|मक्का|ಜೋಳ)\b",
            "soybean": r"\b(?:soybean|soya|सोया|ಸೋಯಾ)\b",
            "lentil": r"\b(?:lentil|dal|दाल|ಡಾಲ್)\b",
            "groundnut": r"\b(?:groundnut|peanut|moongphali|मूंगफली|ಕಡಲೆ)\b",
        }
        
        for crop, pattern in crop_keywords.items():
            if re.search(pattern, text, re.IGNORECASE):
                return crop
        
        # Try to extract from general crop field
        matches = re.findall(r"(?:crop|type|variety)[\s:=-]*([A-Za-z\u0900-\u097F\u0980-\u09FF\u0900-\u0963]{3,})", text, re.IGNORECASE)
        return matches[0].strip() if matches else None
    
    def _extract_structured_data(self, raw_text: str) -> Dict[str, Any]:
        """Extract all relevant fields from raw Docling text"""
        structured = {}
        
        # Basic fields
        structured["farmer_name"] = self._extract_name(raw_text)
        structured["applicant_name"] = structured["farmer_name"]
        structured["aadhaar_number"] = self._extract_field_simple(raw_text, "aadhaar")
        structured["bank_account_number"] = self._extract_field_simple(raw_text, "bank_account")
        structured["ifsc_code"] = self._extract_field_simple(raw_text, "ifsc")
        structured["mobile_number"] = self._extract_field_simple(raw_text, "mobile")
        
        # Land and crop
        land_area = self._extract_field_simple(raw_text, "land_area")
        structured["land_area"] = land_area
        structured["crop_type"] = self._extract_crop(raw_text)
        
        # Financial
        amount = self._extract_field_simple(raw_text, "amount")
        if amount:
            # Clean and convert to numeric
            amount_clean = re.sub(r"[^\d.]", "", amount)
            structured["requested_amount"] = amount_clean if amount_clean else amount
        else:
            structured["requested_amount"] = None
        
        # Location
        location = self._extract_location(raw_text)
        structured.update(location)
        
        # Reference numbers
        structured["application_id"] = self._extract_field_simple(raw_text, "application_id")
        
        # Date
        date_str = self._extract_field_simple(raw_text, "date")
        structured["date_of_application"] = date_str
        
        # Filter out None values
        return {k: v for k, v in structured.items() if v is not None}
    
    def _identify_document_type(self, raw_text: str, pre_identified: Optional[str] = None) -> tuple[str, float]:
        """
        Identify document type using keyword analysis
        Returns: (document_type, confidence)
        """
        text_lower = raw_text.lower()
        
        # Document type scoring
        scores = {
            "scheme_application": 0.0,
            "subsidy_claim": 0.0,
            "insurance_claim": 0.0,
            "grievance": 0.0,
            "farmer_record": 0.0,
            "supporting_document": 0.0,
            "official_letter": 0.0,
        }
        
        # Scheme application keywords & patterns
        scheme_keywords = ["scheme", "application", "benefit", "applicant", "pm kisan", "pradhan mantri", "kisan samman nidhi"]
        scheme_score = sum(text_lower.count(kw) for kw in scheme_keywords) * 0.1
        scores["scheme_application"] = min(0.9, scheme_score)
        
        # Subsidy claim keywords
        subsidy_keywords = ["subsidy", "financial assistance", "grant", "drip irrigation", "micro irrigation", "per drop more crop"]
        subsidy_score = sum(text_lower.count(kw) for kw in subsidy_keywords) * 0.15
        scores["subsidy_claim"] = min(0.9, subsidy_score)
        
        # Insurance claim keywords
        insurance_keywords = ["insurance", "claim", "policy", "crop damage", "compensation", "loss", "insured"]
        insurance_score = sum(text_lower.count(kw) for kw in insurance_keywords) * 0.12
        scores["insurance_claim"] = min(0.9, insurance_score)
        
        # Grievance keywords
        grievance_keywords = ["grievance", "complaint", "issue", "problem", "delay", "pending", "resolve"]
        grievance_score = sum(text_lower.count(kw) for kw in grievance_keywords) * 0.15
        scores["grievance"] = min(0.9, grievance_score)
        
        # Farmer record keywords
        farmer_keywords = ["farmer id", "farmer profile", "land record", "holdings", "demographics"]
        farmer_score = sum(text_lower.count(kw) for kw in farmer_keywords) * 0.15
        scores["farmer_record"] = min(0.9, farmer_score)
        
        # Supporting document keywords
        support_keywords = ["receipt", "certificate", "land ownership", "certificate", "document", "supporting"]
        support_score = sum(text_lower.count(kw) for kw in support_keywords) * 0.10
        scores["supporting_document"] = min(0.9, support_score)
        
        # If pre-identified type provided, boost its score
        if pre_identified and pre_identified in scores:
            scores[pre_identified] += 0.3
        
        # Get highest score
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # If score is too low, mark as unknown
        if best_score < 0.2:
            return "unknown", 0.0
        
        return best_type, min(best_score, 0.95)
    
    def _build_risk_flags(self, structured_data: Dict[str, Any], document_type: str) -> List[Dict[str, str]]:
        """Identify risk flags"""
        flags = []
        
        # Missing critical fields for scheme applications
        if document_type == "scheme_application":
            critical_fields = ["farmer_name", "aadhaar_number", "requested_amount"]
            missing = [f for f in critical_fields if not structured_data.get(f)]
            if len(missing) > 1:
                flags.append({
                    "code": "MISSING_CRITICAL_FIELDS",
                    "severity": "high",
                    "message": f"Missing critical fields: {', '.join(missing)}"
                })
        
        # PII masking patterns
        aadhaar = structured_data.get("aadhaar_number")
        if aadhaar:
            flags.append({
                "code": "PII_DETECTED_AADHAAR",
                "severity": "info",
                "message": "Aadhaar number detected - ensure proper masking before storage"
            })
        
        return flags
    
    def extract_with_granite(self, docling_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction entry point
        Takes Docling output and returns semantically enriched result
        """
        try:
            raw_text = docling_output.get("raw_text", "")
            pre_identified = docling_output.get("pre_identified_type")
            
            if not raw_text or len(raw_text.strip()) < 20:
                self.logger.warning("[GRANITE-V2] Text too short for semantic extraction")
                return self._build_failure_response("insufficient_text")
            
            # Step 1: Extract structured data
            structured_data = self._extract_structured_data(raw_text)
            
            # Step 2: Identify document type
            doc_type, confidence = self._identify_document_type(raw_text, pre_identified)
            
            # Step 3: Build risk flags
            risk_flags = self._build_risk_flags(structured_data, doc_type)
            
            # Step 4: Build reasoning
            reasoning = []
            if structured_data.get("farmer_name"):
                reasoning.append(f"Identified applicant: {structured_data['farmer_name']}")
            if structured_data.get("requested_amount"):
                reasoning.append(f"Financial amount detected: {structured_data['requested_amount']}")
            if structured_data.get("crop_type"):
                reasoning.append(f"Crop type identified: {structured_data['crop_type']}")
            if doc_type != "unknown":
                reasoning.append(f"Document classification: {doc_type}")
            
            if not reasoning:
                reasoning.append("Basic document processing completed")
            
            # Step 5: Build AI summary
            ai_summary = self._build_ai_summary(structured_data, doc_type)
            
            # Step 6: Build canonical data
            canonical = {k: v for k, v in structured_data.items() if v is not None}
            
            # Step 7: Build response
            response = {
                "document_type": doc_type,
                "structured_data": structured_data,
                "extracted_fields": structured_data,  # Same for lightweight version
                "missing_fields": [],  # Could be populated with expected fields
                "confidence": confidence,
                "reasoning": reasoning,
                "classification_confidence": confidence,
                "classification_reasoning": {
                    "keywords_found": list(structured_data.keys()),
                    "structural_indicators": [doc_type],
                    "confidence_factors": ["semantic_analysis", "field_extraction"]
                },
                "risk_flags": risk_flags,
                "decision_support": {
                    "decision": "review" if confidence < 0.7 else "process",
                    "confidence": confidence,
                    "reasoning": reasoning
                },
                "canonical": canonical,
                "summary": self._build_officer_summary(structured_data, doc_type),
                "ai_summary": ai_summary,
                "processing_metadata": {
                    "processing_method": "granite_v2_lightweight",
                    "model_name": "rule_based_semantic",
                    "input_text_length": len(raw_text),
                    "processing_timestamp": datetime.now().isoformat(),
                    "granite_unavailable": False,
                    "lightweight_mode": True
                }
            }
            
            self.logger.info(f"[GRANITE-V2] Extraction complete: {doc_type} (confidence: {confidence})")
            return response
            
        except Exception as e:
            self.logger.error(f"[GRANITE-V2] Extraction failed: {e}")
            return self._build_failure_response(str(e))
    
    def _build_ai_summary(self, structured_data: Dict[str, Any], doc_type: str) -> str:
        """Build officer-facing AI summary"""
        parts = []
        
        name = structured_data.get("farmer_name") or "Unknown applicant"
        location = structured_data.get("village") or "Unknown location"
        amount = structured_data.get("requested_amount")
        crop = structured_data.get("crop_type")
        
        # Build narrative
        type_name = doc_type.replace("_", " ").title()
        parts.append(f"{type_name} received from {name} in {location}.")
        
        if amount:
            parts.append(f"Requested amount: ₹{amount}.")
        
        if crop:
            parts.append(f"Crop identified: {crop}.")
        
        if structured_data.get("aadhaar_number"):
            parts.append("Identity verification available.")
        
        completion = []
        expected_for_type = {
            "scheme_application": ["farmer_name", "aadhaar_number", "requested_amount"],
            "subsidy_claim": ["requested_amount", "crop_type"],
            "insurance_claim": ["farmer_name", "requested_amount"],
        }
        
        if doc_type in expected_for_type:
            missing = [f for f in expected_for_type[doc_type] if not structured_data.get(f)]
            completion_rate = (len(expected_for_type[doc_type]) - len(missing)) / len(expected_for_type[doc_type])
            parts.append(f"Form completion: {int(completion_rate * 100)}%.")
        
        return " ".join(parts)
    
    def _build_officer_summary(self, structured_data: Dict[str, Any], doc_type: str) -> str:
        """Build summary for processing"""
        return self._build_ai_summary(structured_data, doc_type)
    
    def _build_failure_response(self, error: str) -> Dict[str, Any]:
        """Build safe failure response"""
        return {
            "document_type": "unknown",
            "structured_data": {},
            "extracted_fields": {},
            "missing_fields": [],
            "confidence": 0.0,
            "reasoning": [f"Extraction failed: {error}"],
            "classification_confidence": 0.0,
            "classification_reasoning": {
                "keywords_found": [],
                "structural_indicators": [],
                "confidence_factors": [f"error: {error}"]
            },
            "risk_flags": [{
                "code": "EXTRACTION_FAILURE",
                "severity": "high",
                "message": error
            }],
            "decision_support": {
                "decision": "manual_review_required",
                "confidence": 0.0,
                "reasoning": [error]
            },
            "canonical": {},
            "summary": f"Document processing failed: {error}",
            "ai_summary": f"Unable to process document: {error}",
            "processing_metadata": {
                "processing_method": "granite_v2_lightweight",
                "processing_failure": True,
                "error": error
            }
        }
