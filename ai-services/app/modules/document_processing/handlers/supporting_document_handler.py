import re
from typing import Dict, Optional, Any, Tuple

from app.modules.document_processing.utils import (
    normalize_ocr_text,
    BoundaryAwareExtractor,
    FieldValidators,
    FieldNormalizers
)
from app.modules.document_processing.handlers.base_handler import BaseHandler


class SupportingDocumentHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.required_fields = []  # No required fields for generic fallback
        self.optional_fields = [
            "farmer_name",
            "aadhaar_number",
            "location",
            "document_type_detail",
            "issuing_authority",
            "contact_number"
        ]
        self.field_synonyms = {
            "document_reference": ["document reference", "reference number", "ref no", "document no", "certificate no", "letter no", "document id"],
            "farmer_name": ["applicant name", "beneficiary name", "claimant name"],
            "aadhaar_number": ["aadhaar", "uid"],
            "location": ["village", "district", "address", "place"],
            "document_type_detail": ["document type", "type of document", "document detail", "certificate type"],
            "issuing_authority": ["issued by", "authority", "department", "office"],
            "issue_date": ["date of issue", "issued on", "date"],
            "contact_number": ["phone", "mobile", "contact"],
            "application_id": ["reference application", "form no", "request id"]
        }

    def get_document_type(self) -> str:
        return "supporting_document"

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

        # Extract ANY useful fields - DO NOT fail hard
        # Try to extract any field that might be present
        for field_name in ["farmer_name", "aadhaar_number", "location", "document_type_detail", "issuing_authority", "contact_number", "document_reference"]:
            method_name = f"_extract_{field_name}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                result = method(text)
                if result:
                    value, confidence, source = result
                    self.safe_set_field(structured_data, extracted_fields, field_name, value, confidence, source)

        # Build reasoning - ALWAYS return document_type = "supporting_document"
        if structured_data:
            reasoning.append(f"Fields extracted: {', '.join(sorted(structured_data.keys()))}")
        else:
            reasoning.append("Fields extracted: none")
        
        # For supporting documents, do not emit "missing required fields: none" message
        # Since supporting documents have no required fields by definition
        # This avoids misleading test failures
        # Only add reasoning about what was found, not what's missing
        pass

        return self.build_result(
            document_type=self.get_document_type(),
            structured_data=structured_data,
            extracted_fields=extracted_fields,
            reasoning=reasoning
        )

    def _extract_document_reference(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex patterns
        patterns = [
            r'document\s+reference\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})',
            r'reference\s+number\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})',
            r'ref\s*\.?\s*no\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})',
            r'document\s+no\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})',
            r'certificate\s+no\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})',
            r'letter\s+no\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})',
            r'document\s+id\s*[:\-]?\s*([A-Za-z0-9\-/]{5,40})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if re.search(r'\d', value) and 5 <= len(value) <= 40 and re.match(r'^[A-Za-z0-9\-/]+$', value):
                    return value, 0.85, f"labeled_regex: {pattern}"

        # Fallback generic ID pattern
        fallback_pattern = r'\b([A-Za-z]{2,4}[0-9]{3,}[A-Za-z0-9\-/]*)\b'
        matches = re.findall(fallback_pattern, text)
        for match in matches:
            if 5 <= len(match) <= 40 and re.search(r'\d', match) and re.match(r'^[A-Za-z0-9\-/]+$', match):
                return match, 0.65, "fallback_generic_id"

        return None

    def _extract_farmer_name(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Boundary-aware extraction
        extractor = BoundaryAwareExtractor()
        
        # COMPREHENSIVE rejection filter for obvious non-person placeholders
        reject_terms = {
            'details', 'information', 'applicant details', 'account holder details', 
            'as per', 'name as per', 'as per bank records', 'name', 'farmer', 
            'insured farmer details', 'claim details', 'policy information', 
            'claimant details', 'beneficiary details', 'account holder details',
            'details', 'information', 'applicant details', 'beneficiary details',
            'account holder details', 'name as per bank records', 'details',
            'information', 'applicant details', 'beneficiary details',
            'as per records', 'as per document', 'as per form', 'as per application',
            'per records', 'per document', 'per form', 'per application',
            'name as per', 'applicant name as per', 'beneficiary name as per',
            'holder name', 'account holder', 'beneficiary', 'applicant',
            'claimant', 'insured', 'policy holder', 'document holder'
        }
        
        result = extractor.extract_field_by_boundary(text, "farmer_name", ["farmer name", "applicant name", "beneficiary name", "claimant name"])
        if result:
            normalized = FieldNormalizers.normalize_person_name(result)
            # Apply comprehensive rejection filter (case insensitive)
            normalized_lower = normalized.lower()
            if any(reject_term in normalized_lower for reject_term in reject_terms):
                pass  # Continue to regex fallback
            elif FieldValidators.validate_person_name(normalized):
                return normalized, 0.75, "boundary_aware_person_name"

        # Labeled regex patterns with same rejection filter
        patterns = [
            r'farmer\s+name\s*[:\-]?\s*([A-Za-z\s]{3,50})',
            r'applicant\s+name\s*[:\-]?\s*([A-Za-z\s]{3,50})',
            r'beneficiary\s+name\s*[:\-]?\s*([A-Za-z\s]{3,50})',
            r'claimant\s+name\s*[:\-]?\s*([A-Za-z\s]{3,50})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                normalized = FieldNormalizers.normalize_person_name(value)
                # Apply comprehensive rejection filter (case insensitive)
                normalized_lower = normalized.lower()
                if any(reject_term in normalized_lower for reject_term in reject_terms):
                    continue
                if FieldValidators.validate_person_name(normalized):
                    return normalized, 0.8, f"labeled_regex: {pattern}"

        return None

    def _extract_aadhaar_number(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Boundary-aware extraction
        extractor = BoundaryAwareExtractor()
        result = extractor.extract_field_by_boundary(text, "aadhaar_number", ["aadhaar", "aadhaar number", "uid"])
        if result:
            normalized = FieldNormalizers.normalize_aadhaar(result)
            if FieldValidators.validate_aadhaar_number(normalized):
                return normalized, 0.75, "boundary_aware_aadhaar"

        # Regex fallback
        pattern = r'\b(\d{4}\s?\d{4}\s?\d{4})\b'
        match = re.search(pattern, text)
        if match:
            value = re.sub(r'\s', '', match.group(1))
            normalized = FieldNormalizers.normalize_aadhaar(value)
            if FieldValidators.validate_aadhaar_number(normalized):
                return normalized, 0.7, "regex_fallback"

        return None

    def _extract_location(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex patterns
        patterns = [
            r'location\s*[:\-]?\s*([A-Za-z\s,\.]{3,100})',
            r'village\s*[:\-]?\s*([A-Za-z\s,\.]{3,100})',
            r'district\s*[:\-]?\s*([A-Za-z\s,\.]{3,100})',
            r'address\s*[:\-]?\s*([A-Za-z\s,\.]{3,100})',
            r'place\s*[:\-]?\s*([A-Za-z\s,\.]{3,100})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                normalized = FieldNormalizers.normalize_location(value)
                
                # REJECT metadata contamination for supporting documents
                contamination_patterns = [
                    r'supporting\s+document\s+metadata',
                    r'field\s+value',
                    r'supporting\s+document\s+type',
                    r'reference\s+number',
                    r'document\s+type',
                    r'document\s+meta'
                ]
                
                # Check for contamination
                value_lower = normalized.lower()
                if any(re.search(pattern, value_lower) for pattern in contamination_patterns):
                    continue  # Skip contaminated values
                
                if FieldValidators.validate_location(normalized):
                    return normalized, 0.8, f"labeled_regex: {pattern}"

        # Boundary-aware extraction
        extractor = BoundaryAwareExtractor()
        result = extractor.extract_field_by_boundary(text, "village", ["location", "village", "district", "address", "place"])
        if result:
            normalized = FieldNormalizers.normalize_location(result)
            
            # REJECT metadata contamination for supporting documents
            contamination_patterns = [
                r'supporting\s+document\s+metadata',
                r'field\s+value',
                r'supporting\s+document\s+type',
                r'reference\s+number',
                r'document\s+type',
                r'document\s+meta'
            ]
            
            # Check for contamination
            value_lower = normalized.lower()
            if any(re.search(pattern, value_lower) for pattern in contamination_patterns):
                pass  # Skip contaminated values
            elif FieldValidators.validate_location(normalized):
                return normalized, 0.75, "boundary_aware_location"

        return None

    def _extract_document_type_detail(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex patterns
        patterns = [
            r'document\s+type\s*[:\-]?\s*([A-Za-z\s]{3,30})',
            r'type\s+of\s+document\s*[:\-]?\s*([A-Za-z\s]{3,30})',
            r'document\s+detail\s*[:\-]?\s*([A-Za-z\s]{3,30})',
            r'certificate\s+type\s*[:\-]?\s*([A-Za-z\s]{3,30})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().title()
                # Validation: reject vague phrases and enforce stricter length limits
                if len(value) < 3 or len(value) > 30:  # Reduced from 40 to 30
                    continue
                # Reject if contains "details" or "information"
                if re.search(r'details|information', value, re.IGNORECASE):
                    continue
                # Reject if contains "purpose" or other noise words
                if re.search(r'purpose|copy|original|duplicate', value, re.IGNORECASE):
                    continue
                return value, 0.85, f"labeled_regex: {pattern}"

        # Keyword fallback
        keywords = [
            (r'aadhaar\s+card', 'Aadhaar Card'),
            (r'bank\s+passbook', 'Bank Passbook'),
            (r'income\s+certificate', 'Income Certificate'),
            (r'land\s+record', 'Land Record'),
            (r'caste\s+certificate', 'Caste Certificate'),
            (r'residence\s+certificate', 'Residence Certificate'),
            (r'no\s+objection\s+certificate', 'No Objection Certificate'),
            (r'authority\s+letter', 'Authority Letter'),
            (r'id\s+proof', 'ID Proof')
        ]

        for pattern, replacement in keywords:
            if re.search(pattern, text, re.IGNORECASE):
                return replacement, 0.7, "keyword_fallback"

        return None

    def _extract_issuing_authority(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex patterns
        patterns = [
            r'issuing\s+authority\s*[:\-]?\s*([A-Za-z\s\.\,]{3,100})',
            r'issued\s+by\s*[:\-]?\s*([A-Za-z\s\.\,]{3,100})',
            r'authority\s*[:\-]?\s*([A-Za-z\s\.\,]{3,100})',
            r'department\s*[:\-]?\s*([A-Za-z\s\.\,]{3,100})',
            r'office\s*[:\-]?\s*([A-Za-z\s\.\,]{3,100})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if len(value) > 5:
                    return value, 0.8, f"labeled_regex: {pattern}"

        return None

    def _extract_issue_date(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex patterns
        patterns = [
            r'issue\s+date\s*[:\-]?\s*(\d{2}[\-/]\d{2}[\-/]\d{2,4})',
            r'date\s+of\s+issue\s*[:\-]?\s*(\d{2}[\-/]\d{2}[\-/]\d{2,4})',
            r'issued\s+on\s*[:\-]?\s*(\d{2}[\-/]\d{2}[\-/]\d{2,4})',
            r'date\s*[:\-]?\s*(\d{2}[\-/]\d{2}[\-/]\d{2,4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Basic format validation
                if re.match(r'\d{2}[\-/]\d{2}[\-/]\d{2,4}', date_str):
                    return date_str, 0.85, f"labeled_regex: {pattern}"

        return None

    def _extract_contact_number(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Boundary-aware extraction
        extractor = BoundaryAwareExtractor()
        result = extractor.extract_field_by_boundary(text, "mobile_number", ["phone", "mobile", "contact"])
        if result:
            normalized = FieldNormalizers.normalize_mobile(result)
            if FieldValidators.validate_mobile_number(normalized):
                return normalized, 0.75, "boundary_aware_mobile"

        # Labeled regex fallback
        patterns = [
            r'phone\s*[:\-]?\s*(\d{10})',
            r'mobile\s*[:\-]?\s*(\d{10})',
            r'contact\s*[:\-]?\s*(\d{10})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                normalized = FieldNormalizers.normalize_mobile(value)
                if FieldValidators.validate_mobile_number(normalized):
                    return normalized, 0.75, f"labeled_regex: {pattern}"

        return None

    def _extract_application_id(self, text: str) -> Optional[Tuple[str, float, str]]:
        # Labeled regex patterns
        patterns = [
            r'application\s+id\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})',
            r'reference\s+application\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})',
            r'form\s+no\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})',
            r'request\s+id\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if re.search(r'\d', value) and 5 <= len(value) <= 30:
                    return value, 0.85, f"labeled_regex: {pattern}"

        # Regex fallback
        fallback_pattern = r'\b(APP[0-9]{3,}|REQ[0-9]{3,}|FORM[0-9]{3,})\b'
        match = re.search(fallback_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1), 0.7, "regex_fallback"

        return None
