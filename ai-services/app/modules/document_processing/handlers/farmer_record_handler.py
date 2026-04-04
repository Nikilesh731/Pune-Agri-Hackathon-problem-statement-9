"""
Farmer Record Handler
Purpose: Extract fields from farmer registration and profile documents
"""
import re
from typing import Dict, Optional, Any, Tuple

from .base_handler import BaseHandler
from ..utils import (
    normalize_ocr_text,
    BoundaryAwareExtractor,
    FieldValidators,
    FieldNormalizers
)


class FarmerRecordHandler(BaseHandler):
    """Handler for farmer registration and profile documents"""
    
    def __init__(self):
        super().__init__()
        self.required_fields = [
            'farmer_name',
            'aadhaar_number',
            'mobile_number'
        ]
        self.optional_fields = []
        
        self.field_synonyms = {
            'farmer_name': ['name', 'farmer name', 'cultivator name', 'applicant name'],
            'aadhaar_number': ['aadhaar', 'aadhaar no', 'uid', 'identity number'],
            'mobile_number': ['phone', 'mobile', 'contact', 'telephone']
        }
    
    def get_document_type(self) -> str:
        return "farmer_record"
    
    def extract_fields(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract fields from farmer record text"""
        # Normalize text
        normalized_text = normalize_ocr_text(text)
        
        # Initialize result containers
        structured_data = {}
        extracted_fields = {}
        reasoning = []
        
        # Extract required fields only
        # Extract farmer name
        farmer_name_result = self._extract_farmer_name(normalized_text)
        if farmer_name_result:
            value, confidence, source = farmer_name_result
            self.safe_set_field(structured_data, extracted_fields, 'farmer_name', value, confidence, source)
        
        # Extract Aadhaar number
        aadhaar_result = self._extract_aadhaar_number(normalized_text)
        if aadhaar_result:
            value, confidence, source = aadhaar_result
            self.safe_set_field(structured_data, extracted_fields, 'aadhaar_number', value, confidence, source)
        
        # Extract mobile number
        mobile_result = self._extract_mobile_number(normalized_text)
        if mobile_result:
            value, confidence, source = mobile_result
            self.safe_set_field(structured_data, extracted_fields, 'mobile_number', value, confidence, source)
        
        # Add structured reasoning in correct order
        if structured_data:
            reasoning.append(f"Fields extracted: {', '.join(sorted(structured_data.keys()))}")
        else:
            reasoning.append("Fields extracted: none")
        
        # Check for missing required fields
        missing_required = [field for field in self.required_fields if field not in structured_data]
        if missing_required:
            reasoning.append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Build final result
        return self.build_result(
            document_type=self.get_document_type(),
            structured_data=structured_data,
            extracted_fields=extracted_fields,
            reasoning=reasoning
        )
    
    def _extract_mobile_number(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract mobile number using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        labels = ['phone', 'mobile', 'contact', 'telephone']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'mobile_number', [label])
            if result:
                value = FieldNormalizers.normalize_mobile(result)
                if FieldValidators.validate_mobile_number(value):
                    return value, 0.85, f"Boundary-aware extraction with label '{label}'"
        
        # Fallback regex for 10-digit numbers in reasonable context
        pattern = r'(?:phone|mobile|contact|telephone)[:\s]*(\d{10})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            phone = match.group(1)
            if FieldValidators.validate_mobile_number(phone):
                return phone, 0.65, "Regex fallback for labeled 10-digit pattern"
        
        return None
    
    def _extract_farmer_name(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract farmer name using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        labels = ['farmer name', 'cultivator name', 'applicant name', 'name']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'farmer_name', [label])
            if result:
                value = FieldNormalizers.normalize_person_name(result)
                if FieldValidators.validate_person_name(value):
                    return value, 0.9, f"Boundary-aware extraction with label '{label}'"
        
        # Fallback regex (labeled capture only)
        patterns = [
            r'(?:farmer name|cultivator name|applicant name|name)[:\s]+([A-Za-z\s]{3,50})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = FieldNormalizers.normalize_person_name(name)
                if FieldValidators.validate_person_name(name):
                    return name, 0.7, f"Labeled regex fallback: {pattern}"
        
        return None
    
    def _extract_aadhaar_number(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract Aadhaar number using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        labels = ['aadhaar', 'aadhaar no', 'uid', 'identity number']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'aadhaar_number', [label])
            if result:
                value = FieldNormalizers.normalize_aadhaar(result)
                if FieldValidators.validate_aadhaar_number(value):
                    return value, 0.95, f"Boundary-aware extraction with label '{label}'"
        
        # Fallback regex for 12-digit Aadhaar pattern
        pattern = r'(?:aadhaar|uid|aadhaar number)[:\s]*(\d{4}[\s-]?\d{4}[\s-]?\d{4})'
        match = re.search(pattern, text)
        if match:
            aadhaar = re.sub(r'[\s-]', '', match.group(1))
            if FieldValidators.validate_aadhaar_number(aadhaar):
                return aadhaar, 0.7, "Regex fallback for 12-digit pattern"
        
        return None
    
    
