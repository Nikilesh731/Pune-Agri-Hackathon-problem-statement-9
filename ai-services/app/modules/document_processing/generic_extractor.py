"""
Generic Field Extractor
Purpose: Extract common agricultural document fields using label-aware and boundary-aware parsing
Works as a shared extractor for common fields across all document types
"""
import re
from typing import Dict, Any, Optional, List
from .utils import (
    normalize_ocr_text, 
    BoundaryAwareExtractor, 
    FieldValidators, 
    FieldNormalizers
)


class GenericFieldExtractor:
    """Generic field extractor for agricultural documents - focuses on common/shared fields only"""
    
    def __init__(self):
        # Initialize boundary-aware extractor for label-first parsing
        self.boundary_extractor = BoundaryAwareExtractor()
        
        # Define common fields to extract
        self.common_fields = [
            'farmer_name',
            'aadhaar_number', 
            'location',
            'land_size',
            'annual_income',
            'requested_amount',
            'scheme_name',
            'application_id'
        ]
        
        # Fallback regex patterns for when boundary-aware extraction fails
        self.fallback_patterns = {
            'farmer_name': [
                r'(?:mr|ms|shri|smt)\.?\s*([A-Za-z]{2,}\s+[A-Za-z]{2,})(?=\s|\n|$)',  # Title + at least 2 words
            ],
            'aadhaar_number': [
                r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b',  # Generic 12-digit pattern
            ],
            'scheme_name': [
                r'(?:pradhan\s*mantri|pm\s*kisan|kisan\s*credit|crop\s*insurance|soil\s*health|paramparagat|national\s*mission|rkvy)[A-Za-z0-9\s\-]{5,30}',
            ],
            'location': [
                r'(?:village|gram)\s+([A-Za-z]{2,}\s+[A-Za-z]{2,})\s+(?:district|tehsil)',
                r'([A-Za-z]{2,}\s+[A-Za-z]{2,})\s+district',  # At least 2 words before district
            ],
            'land_size': [
                r'(\d+(?:\.\d+)?)\s*(acre|hectare|bigha|sq\.?m|square\s*meter)s?',
            ],
            'annual_income': [
                r'(?:annual\s*income|income)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)',
            ],
            'requested_amount': [
                # Strict patterns requiring explicit financial context
                r'(?:requested\s*amount|claim\s*amount|subsidy\s*amount|amount\s*requested|compensation\s*amount|premium\s*paid|tax\s*paid|fee\s*paid)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]{1,3}(?:[0-9,]{3})*(?:\.[0-9]{2})?)',
                r'(?:subsidy\s+release|grant\s+amount|financial\s+assistance)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]{1,3}(?:[0-9,]{3})*(?:\.[0-9]{2})?)',
                # Reject generic "apply for amount" patterns - too ambiguous
            ],
            'application_id': [
                r'(?:application\s*id|app\s*id|ref\s*no)\s*[:\-]?\s*([A-Za-z0-9\-]{5,20})',
            ]
        }
    
    def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract common fields from agricultural document text.
        
        Args:
            text: OCR text from document
            
        Returns:
            Dict with structured extraction results including field-level confidence
        """
        # Normalize input text
        normalized_text = normalize_ocr_text(text)
        
        extracted_fields = {}
        missing_fields = []
        reasoning = []
        
        # Extract each common field using label-first approach
        for field_name in self.common_fields:
            field_result = self._extract_single_field(normalized_text, field_name)
            
            if field_result['value']:
                extracted_fields[field_name] = field_result
            else:
                missing_fields.append(field_name)
        
        # Calculate overall confidence
        if extracted_fields:
            overall_confidence = sum(result['confidence'] for result in extracted_fields.values()) / len(extracted_fields)
        else:
            overall_confidence = 0.0
        
        # Build structured data with all fields (missing ones as None)
        structured_data = {}
        for field_name in self.common_fields:
            if field_name in extracted_fields:
                structured_data[field_name] = extracted_fields[field_name]['value']
            else:
                structured_data[field_name] = None
        
        # Generate summary reasoning instead of per-field spam
        boundary_count = sum(1 for result in extracted_fields.values() if result['source'] == 'label_boundary')
        regex_count = sum(1 for result in extracted_fields.values() if result['source'] == 'regex_fallback')
        field_specific_count = sum(1 for result in extracted_fields.values() if result.get('source') in ['field_specific_location', 'field_specific_income', 'field_specific_id'])
        
        reasoning = []
        if boundary_count > 0:
            reasoning.append(f"Boundary extraction used for {boundary_count} fields")
        if field_specific_count > 0:
            reasoning.append(f"Field-specific extraction used for {field_specific_count} fields")
        if regex_count > 0:
            reasoning.append(f"Regex fallback used for {regex_count} fields")
        if missing_fields:
            reasoning.append(f"Missing common fields: {', '.join(missing_fields)}")
        
        return {
            "structured_data": structured_data,
            "extracted_fields": extracted_fields,
            "missing_fields": missing_fields,
            "confidence": overall_confidence,
            "reasoning": reasoning
        }
    
    def _extract_single_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """
        Extract a single field using multiple strategies with confidence scoring.
        
        Args:
            text: Normalized text to search
            field_name: Name of field to extract
            
        Returns:
            Dict with value, confidence, and source information
        """
        # Strategy 1: Boundary-aware extraction for supported fields only
        boundary_supported_fields = {
            'farmer_name', 'aadhaar_number', 'land_size', 'scheme_name', 'requested_amount'
        }
        
        if field_name in boundary_supported_fields:
            boundary_value = self.boundary_extractor.extract_field_by_boundary(text, field_name)
            if boundary_value:
                normalized_value = self._normalize_field_value(boundary_value, field_name)
                if self._validate_field_value(normalized_value, field_name):
                    return {
                        "value": normalized_value,
                        "confidence": 0.9,
                        "source": "label_boundary"
                    }
        
        # Strategy 2: Field-specific extraction for unsupported fields
        if field_name == 'location':
            location_value = self._extract_location_field(text)
            if location_value:
                return location_value
        elif field_name == 'annual_income':
            income_value = self._extract_annual_income_field(text)
            if income_value:
                return income_value
        elif field_name == 'application_id':
            id_value = self._extract_application_id_field(text)
            if id_value:
                return id_value
        
        # Strategy 3: Fallback regex patterns (lower confidence)
        if field_name in self.fallback_patterns:
            for pattern in self.fallback_patterns[field_name]:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip() if match.groups() else match.group(0).strip()
                    normalized_value = self._normalize_field_value(value, field_name)
                    
                    if self._validate_field_value(normalized_value, field_name):
                        return {
                            "value": normalized_value,
                            "confidence": 0.6,
                            "source": "regex_fallback"
                        }
        
        # No value found
        return {
            "value": None,
            "confidence": 0.0,
            "source": None
        }
    
    def _normalize_field_value(self, value: str, field_name: str) -> str:
        """
        Normalize field value using appropriate normalizer.
        
        Args:
            value: Raw extracted value
            field_name: Type of field
            
        Returns:
            Normalized field value
        """
        if not value:
            return ""
        
        # Field-specific normalization using utils
        if field_name == 'farmer_name':
            return FieldNormalizers.normalize_person_name(value)
        elif field_name == 'aadhaar_number':
            return FieldNormalizers.normalize_aadhaar(value)
        elif field_name == 'land_size':
            return FieldNormalizers.normalize_land_size(value)
        elif field_name in ['annual_income', 'requested_amount']:
            return FieldNormalizers.normalize_amount(value)
        elif field_name == 'location':
            return FieldNormalizers.normalize_location(value)
        elif field_name == 'scheme_name':
            return FieldNormalizers.normalize_scheme_name(value)
        else:
            # Generic cleanup for application_id and others
            return re.sub(r'\s+', ' ', value.strip())
    
    def _validate_field_value(self, value: str, field_name: str) -> bool:
        """
        Validate field value using appropriate validator.
        
        Args:
            value: Normalized field value
            field_name: Type of field
            
        Returns:
            True if value is valid for the field type
        """
        if not value:
            return False
        
        # Field-specific validation using utils
        if field_name == 'farmer_name':
            return FieldValidators.validate_person_name(value)
        elif field_name == 'aadhaar_number':
            return FieldValidators.validate_aadhaar_number(value)
        elif field_name == 'land_size':
            return FieldValidators.validate_land_size(value)
        elif field_name in ['annual_income', 'requested_amount']:
            return FieldValidators.validate_money_amount(value)
        elif field_name == 'location':
            return FieldValidators.validate_location(value)
        elif field_name == 'scheme_name':
            return FieldValidators.validate_scheme_name(value)
        elif field_name == 'application_id':
            # Must be 5-30 chars, contain at least one digit, and only allowed characters
            if not re.match(r'^[A-Za-z0-9\-\/]{5,30}$', value):
                return False
            if not re.search(r'\d', value):
                return False
            return True
        else:
            return True  # No validation for unknown fields
    
    def _extract_location_field(self, text: str) -> Dict[str, Any]:
        """Extract location by combining village and district separately"""
        # Extract village and district using boundary extractor
        village = self.boundary_extractor.extract_field_by_boundary(text, 'village')
        district = self.boundary_extractor.extract_field_by_boundary(text, 'district')
        
        if village and district:
            location = f"{village.strip()}, {district.strip()}"
            normalized = self._normalize_field_value(location, 'location')
            if self._validate_field_value(normalized, 'location'):
                return {
                    "value": normalized,
                    "confidence": 0.85,
                    "source": "field_specific_location"
                }
        elif village:
            normalized = self._normalize_field_value(village, 'location')
            if self._validate_field_value(normalized, 'location'):
                return {
                    "value": normalized,
                    "confidence": 0.8,
                    "source": "field_specific_location"
                }
        elif district:
            normalized = self._normalize_field_value(district, 'location')
            if self._validate_field_value(normalized, 'location'):
                return {
                    "value": normalized,
                    "confidence": 0.75,
                    "source": "field_specific_location"
                }
        
        return {"value": None, "confidence": 0.0, "source": None}
    
    def _extract_annual_income_field(self, text: str) -> Dict[str, Any]:
        """Extract annual income with field-aware patterns"""
        patterns = [
            r'(?:annual\s*income|yearly\s*income|income)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]{1,8}(?:\.[0-9]{2})?)',
            r'(?:rs\.?|inr|₹)?\s*([0-9,]{3,8})\s*(?:\/year|per\syear|annually)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                normalized = self._normalize_field_value(value, 'annual_income')
                if self._validate_field_value(normalized, 'annual_income'):
                    return {
                        "value": normalized,
                        "confidence": 0.7,
                        "source": "field_specific_income"
                    }
        
        return {"value": None, "confidence": 0.0, "source": None}
    
    def _extract_application_id_field(self, text: str) -> Dict[str, Any]:
        """Extract application ID with field-aware patterns"""
        patterns = [
            r'(?:application\s*id|app\s*id|ref\s*no|reference\s*no)\s*[:\-]?\s*([A-Za-z0-9\-]{5,20})',
            r'\b([A-Z]{2,4}[-/]\d{4,8})\b'  # More specific ID pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                normalized = self._normalize_field_value(value, 'application_id')
                if self._validate_field_value(normalized, 'application_id'):
                    return {
                        "value": normalized,
                        "confidence": 0.7,
                        "source": "field_specific_id"
                    }
        
        return {"value": None, "confidence": 0.0, "source": None}
