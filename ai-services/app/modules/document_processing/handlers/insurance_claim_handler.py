import re
from typing import Dict, Optional, Any, Tuple

from .base_handler import BaseHandler
from ..utils import (
    normalize_ocr_text,
    BoundaryAwareExtractor,
    FieldValidators,
    FieldNormalizers
)


class InsuranceClaimHandler(BaseHandler):
    """Handler for agricultural insurance claim documents."""
    
    def __init__(self):
        super().__init__()
        self.required_fields = ["farmer_name", "claim_type", "loss_description"]
        self.optional_fields = []
        # INSURANCE-SPECIFIC FIELD MAPPING - ONLY REQUIRED FIELDS
        self.field_synonyms = {
            "farmer_name": ["farmer name", "insured farmer", "claimant name", "applicant name"],
            "claim_type": ["claim type", "insurance type", "policy type", "claim category"],
            "loss_description": ["loss description", "damage description", "incident description", "claim details", "loss details"]
        }
    
    def get_document_type(self) -> str:
        return "insurance_claim"
    
    def extract_fields(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract fields from insurance claim document text."""
        if not text or not text.strip():
            return self.build_result(
                document_type=self.get_document_type(),
                structured_data={},
                extracted_fields={},
                reasoning=[]
            )
        
        # Normalize text
        normalized_text = normalize_ocr_text(text)
        
        # Initialize containers
        structured_data = {}
        extracted_fields = {}
        reasoning = []
        
        # Extract required fields only
        # Extract farmer name
        farmer_name_result = self._extract_farmer_name(normalized_text)
        if farmer_name_result:
            value, confidence, source = farmer_name_result
            self.safe_set_field(structured_data, extracted_fields, "farmer_name", value, confidence, source)
        
        # Extract claim type
        claim_type_result = self._extract_claim_type(normalized_text)
        if claim_type_result:
            value, confidence, source = claim_type_result
            self.safe_set_field(structured_data, extracted_fields, "claim_type", value, confidence, source)
        
        # Extract loss description
        loss_description_result = self._extract_loss_description(normalized_text)
        if loss_description_result:
            value, confidence, source = loss_description_result
            self.safe_set_field(structured_data, extracted_fields, "loss_description", value, confidence, source)

        # Additional prioritized fields for insurance claims
        # Aadhaar
        aadhaar = None
        aadhaar_match = re.search(r'(\d{4}\s*\d{4}\s*\d{4})', normalized_text)
        if aadhaar_match:
            aadhaar = FieldNormalizers.normalize_aadhaar(aadhaar_match.group(1))
            if FieldValidators.validate_aadhaar_number(aadhaar):
                self.safe_set_field(structured_data, extracted_fields, 'aadhaar_number', aadhaar, 0.95, 'regex_aadhaar')

        # Mobile number
        mobile = None
        mobile_match = re.search(r'\b[6-9]\d{9}\b', normalized_text)
        if mobile_match:
            mobile = FieldNormalizers.normalize_mobile(mobile_match.group(0))
            if FieldValidators.validate_mobile_number(mobile):
                self.safe_set_field(structured_data, extracted_fields, 'mobile_number', mobile, 0.9, 'regex_mobile')

        # Claim amount / requested amount
        claim_amt_patterns = [r'(?:claim amount|amount claimed|amount requested|requested amount|amount)[\s:\-₹]*([₹\d,\.\s]+)']
        for pat in claim_amt_patterns:
            m = re.search(pat, normalized_text, re.IGNORECASE)
            if m:
                raw_amt = m.group(1).strip()
                norm_amt = FieldNormalizers.normalize_amount(raw_amt)
                if FieldValidators.validate_money_amount(norm_amt):
                    # Prefer claim_amount label
                    self.safe_set_field(structured_data, extracted_fields, 'claim_amount', norm_amt, 0.9, f'regex_claim_amount:{pat}')
                    break

        # Village / District (try boundary-aware extraction)
        boundary = BoundaryAwareExtractor()
        v = boundary.extract_field_by_boundary(normalized_text, 'village')
        if v and FieldValidators.validate_location(v):
            vnorm = FieldNormalizers.normalize_location(v)
            self.safe_set_field(structured_data, extracted_fields, 'village', vnorm, 0.8, 'boundary_village')

        d = boundary.extract_field_by_boundary(normalized_text, 'district')
        if d and FieldValidators.validate_location(d):
            dnorm = FieldNormalizers.normalize_location(d)
            self.safe_set_field(structured_data, extracted_fields, 'district', dnorm, 0.8, 'boundary_district')

        # Crop name and land size if present (conservative)
        crop = boundary.extract_field_by_boundary(normalized_text, 'crop_type')
        if crop:
            # Avoid table-ish or long blobs
            if isinstance(crop, str) and len(crop) < 80 and '\n' not in crop and '|' not in crop:
                self.safe_set_field(structured_data, extracted_fields, 'crop_name', crop.title(), 0.7, 'boundary_crop')

        land = boundary.extract_field_by_boundary(normalized_text, 'land_size')
        if land:
            # Normalize and validate
            lnorm = FieldNormalizers.normalize_land_size(land)
            if FieldValidators.validate_land_size(lnorm):
                self.safe_set_field(structured_data, extracted_fields, 'land_size', lnorm, 0.75, 'boundary_land_size')
        
        # Add structured reasoning in correct order
        if structured_data:
            reasoning.append(f"Fields extracted: {', '.join(sorted(structured_data.keys()))}")
        
        # Check for missing required fields
        missing_required = [field for field in self.required_fields if field not in structured_data]
        if missing_required:
            reasoning.append(f"Missing required fields: {', '.join(missing_required)}")
        
        return self.build_result(
            document_type=self.get_document_type(),
            structured_data=structured_data,
            extracted_fields=extracted_fields,
            reasoning=reasoning
        )
    
    def _extract_farmer_name(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract farmer name using boundary-aware and labeled regex with junk rejection"""
        extractor = BoundaryAwareExtractor()
        
        # JUNK REJECTION FILTER - Explicitly reject these header/label values
        junk_values = {
            'field value', 'details', 'information', 'applicant details', 
            'account holder details', 'as per', 'farmer', 'insured farmer details', 
            'claim details', 'policy information', 'claimant details', 'beneficiary details',
            'form', 'insurance claim', 'claim form', 'policy holder'
        }
        
        # Try boundary-aware extraction first
        labels = ['farmer name', 'insured farmer', 'claimant name', 'applicant name', 'name']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'farmer_name', [label])
            if result:
                value = FieldNormalizers.normalize_person_name(result)
                # Apply rejection filter
                if (value.lower() not in junk_values and
                    not value.lower().startswith(('field', 'details', 'information', 'claimant', 'applicant', 'policy')) and
                    FieldValidators.validate_person_name(value)):
                    return (value, 0.9, f"boundary-aware farmer_name with label: {label}")
        
        # Strong labeled regex fallback with junk rejection
        patterns = [
            r'(?:farmer name|insured farmer|claimant name|applicant name)[:\s\-]+([A-Za-z.\s]{3,60})',
            r'(?:policy holder|insured person)[:\s\-]+([A-Za-z.\s]{3,60})',
            r'(?:name of farmer|name of claimant)[:\s\-]+([A-Za-z.\s]{3,60})',
            r'Name[:\s]+([A-Za-z.\s]{3,60})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = FieldNormalizers.normalize_person_name(match.group(1).strip())
                # Apply rejection filter
                if (value.lower() not in junk_values and
                    not value.lower().startswith(('field', 'details', 'information', 'claimant', 'applicant', 'policy')) and
                    FieldValidators.validate_person_name(value)):
                    return (value, 0.85, f"labeled regex: {pattern}")
        
        return None
    
    def _extract_claim_type(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract claim type using labeled patterns and keyword inference"""
        # Labeled extraction first
        patterns = [
            r'(?:claim type|insurance type|policy type|claim category)[\s:.-]+(.+?)(?=\n|$)',
            r'Type[:\s]+(.+?)(?=\n|$)',
            r'Category[:\s]+(.+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                claim_type = match.group(1).strip()
                # Keep it short and clean
                if len(claim_type) <= 40:
                    return claim_type, 0.85, f"Labeled claim type: {pattern}"
        
        # Keyword inference for common claim types
        claim_keywords = {
            "crop damage": ["crop damage", "crop loss", "damage to crop", "crop failure"],
            "flood damage": ["flood", "flooding", "flood damage", "water damage"],
            "drought loss": ["drought", "dry spell", "drought loss", "water scarcity"],
            "pest damage": ["pest", "insect", "pest attack", "pest damage"],
            "storm damage": ["storm", "wind damage", "storm damage", "cyclone"],
            "hailstorm damage": ["hail", "hailstorm", "hail damage"],
            "fire damage": ["fire", "fire damage", "burning"],
            "livestock loss": ["livestock", "animal loss", "cattle loss"]
        }
        
        text_lower = text.lower()
        for claim_type, keywords in claim_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return claim_type, 0.7, f"Keyword inference: {keywords[0]}"
        
        return None
    
    def _extract_loss_description(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract loss description from the document text"""
        lines = text.split('\n')
        loss_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip header lines and include meaningful loss/damage content
            if (len(line) > 20 and 
                not line.lower().startswith(('to:', 'from:', 'date:', 'subject:', 'ref:', 'reference:', 'claim type:', 'policy number:')) and
                not re.match(r'^[A-Za-z\s]+[:\s]+$', line)):
                # Include lines that seem to describe damage/loss
                if any(keyword in line.lower() for keyword in ['damage', 'loss', 'destroy', 'affect', 'impact', 'ruin', 'spoil']):
                    loss_lines.append(line)
                elif len(loss_lines) < 2:  # Include up to 2 lines of general context
                    loss_lines.append(line)
        
        if loss_lines:
            # Combine first 2-3 meaningful lines, keep it concise
            loss_text = ' '.join(loss_lines[:3])
            if len(loss_text) > 300:  # Keep description concise
                loss_text = loss_text[:300] + '...'
            return loss_text, 0.75, "Extracted loss description"
        
        return None
    
    
