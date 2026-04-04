import re
from typing import Dict, Optional, Any, Tuple

from ..utils import (
    normalize_ocr_text,
    BoundaryAwareExtractor,
    FieldValidators,
    FieldNormalizers
)
from .base_handler import BaseHandler


class SubsidyClaimHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.required_fields = ["farmer_name", "subsidy_type", "requested_amount"]
        self.optional_fields = []
        
        # SUBSIDY-SPECIFIC FIELD MAPPING - ONLY REQUIRED FIELDS
        self.field_synonyms = {
            "farmer_name": ["farmer name", "applicant name", "beneficiary name", "claimant name"],
            "subsidy_type": ["subsidy type", "type of subsidy", "benefit type", "subsidy category", "category"],
            "requested_amount": ["requested amount", "subsidy amount", "amount requested", "benefit amount", "amount"]
        }

    def get_document_type(self) -> str:
        return "subsidy_claim"

    def extract_fields(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not text or not text.strip():
            return self.build_result(
                document_type=self.get_document_type(),
                structured_data={},
                extracted_fields={},
                reasoning=[]
            )

        text = normalize_ocr_text(text)
        structured_data = {}
        extracted_fields = {}
        reasoning = []

        # Extract required fields only
        # Extract farmer name
        farmer_name_result = self._extract_farmer_name(text)
        if farmer_name_result:
            value, confidence, source = farmer_name_result
            self.safe_set_field(structured_data, extracted_fields, "farmer_name", value, confidence, source)

        # Extract subsidy type
        subsidy_type_result = self._extract_subsidy_type(text)
        if subsidy_type_result:
            value, confidence, source = subsidy_type_result
            self.safe_set_field(structured_data, extracted_fields, "subsidy_type", value, confidence, source)

        # Extract requested amount
        requested_amount_result = self._extract_requested_amount(text)
        if requested_amount_result:
            value, confidence, source = requested_amount_result
            self.safe_set_field(structured_data, extracted_fields, "requested_amount", value, confidence, source)

        # Build reasoning
        if structured_data:
            reasoning.append(f"Fields extracted: {', '.join(sorted(structured_data.keys()))}")

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
        # Boundary-aware extraction
        extractor = BoundaryAwareExtractor()
        result = extractor.extract_field_by_boundary(text, "farmer_name", ["farmer name", "applicant name", "beneficiary name", "claimant name", "name"])
        if result:
            value = FieldNormalizers.normalize_person_name(result)
            if FieldValidators.validate_person_name(value):
                return value, 0.9, "boundary_aware"

        # Labeled regex fallback
        patterns = [
            r"(?i)farmer\s*name\s*[:\-]?\s*([A-Za-z\s\.]+)",
            r"(?i)applicant\s*name\s*[:\-]?\s*([A-Za-z\s\.]+)",
            r"(?i)beneficiary\s*name\s*[:\-]?\s*([A-Za-z\s\.]+)",
            r"(?i)claimant\s*name\s*[:\-]?\s*([A-Za-z\s\.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = FieldNormalizers.normalize_person_name(match.group(1).strip())
                if FieldValidators.validate_person_name(value):
                    return value, 0.7, "labeled_regex"

        return None

    def _extract_subsidy_type(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex primary - stricter length limits
        patterns = [
            r"(?i)subsidy\s*type\s*[:\-]?\s*([A-Za-z\s]{1,30})",
            r"(?i)type\s*of\s*subsidy\s*[:\-]?\s*([A-Za-z\s]{1,30})",
            r"(?i)benefit\s*type\s*[:\-]?\s*([A-Za-z\s]{1,30})",
            r"(?i)subsidy\s*category\s*[:\-]?\s*([A-Za-z\s]{1,30})",
            r"(?i)category\s*[:\-]?\s*([A-Za-z\s]{1,30})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip().title()
                # Validation: strict length limits and reject equipment descriptions
                if len(value) > 40:  # Reduced from 50 to 40
                    return None
                # Reject if contains numbers + units (likely equipment description)
                if re.search(r'\d+\s*(?:units?|pcs?|sets?|kits?|nos?)', value, re.IGNORECASE):
                    return None
                # Reject long descriptive phrases with multiple words
                if len(value.split()) > 4:
                    return None
                return value, 0.85, "labeled_regex"

        # Keyword fallback
        inferred = self._infer_subsidy_type_from_keywords(text)
        if inferred:
            return inferred, 0.7, "keyword_inference"

        return None

    def _infer_subsidy_type_from_keywords(self, text: str) -> Optional[str]:
        keywords = {
            "seed subsidy": "Seed Subsidy",
            "fertilizer subsidy": "Fertilizer Subsidy", 
            "equipment subsidy": "Equipment Subsidy",
            "irrigation subsidy": "Irrigation Subsidy",
            "crop subsidy": "Crop Subsidy",
            "power subsidy": "Power Subsidy",
            "loan subsidy": "Loan Subsidy",
            "dairy subsidy": "Dairy Subsidy",
            "livestock subsidy": "Livestock Subsidy"
        }
        
        text_lower = text.lower()
        for keyword, normalized in keywords.items():
            if keyword in text_lower:
                return normalized
        
        return None

    def _extract_requested_amount(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Boundary-aware extraction
        extractor = BoundaryAwareExtractor()
        result = extractor.extract_field_by_boundary(text, "requested_amount", ["requested amount", "subsidy amount", "amount requested", "benefit amount", "amount"])
        if result:
            value = FieldNormalizers.normalize_amount(result)
            if FieldValidators.validate_money_amount(value):
                return value, 0.85, "boundary_aware"

        # Labeled regex fallback
        patterns = [
            r"(?i)requested\s*amount\s*[:\-]?\s*(?:Rs\.?\s*|INR\s*|₹\s*)?([0-9,]+(?:\.[0-9]{2})?)",
            r"(?i)subsidy\s*amount\s*[:\-]?\s*(?:Rs\.?\s*|INR\s*|₹\s*)?([0-9,]+(?:\.[0-9]{2})?)",
            r"(?i)amount\s*requested\s*[:\-]?\s*(?:Rs\.?\s*|INR\s*|₹\s*)?([0-9,]+(?:\.[0-9]{2})?)",
            r"(?i)benefit\s*amount\s*[:\-]?\s*(?:Rs\.?\s*|INR\s*|₹\s*)?([0-9,]+(?:\.[0-9]{2})?)",
            r"(?i)amount\s*[:\-]?\s*(?:Rs\.?\s*|INR\s*|₹\s*)?([0-9,]+(?:\.[0-9]{2})?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = FieldNormalizers.normalize_amount(match.group(1))
                if FieldValidators.validate_money_amount(value):
                    return value, 0.65, "labeled_regex"

        return None

    
