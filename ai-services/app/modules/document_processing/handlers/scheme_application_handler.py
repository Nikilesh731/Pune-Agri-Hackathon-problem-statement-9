"""
Scheme Application Handler
Purpose: Extract fields from scheme application documents
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


class SchemeApplicationHandler(BaseHandler):
    """Handler for scheme application documents"""
    
    def __init__(self):
        super().__init__()
        self.required_fields = [
            'farmer_name',
            'scheme_name'
        ]
        self.optional_fields = [
            'aadhaar_number',
            'phone_number',
            'location',
            'village',
            'district',
            'land_size',
            'requested_amount'
        ]
        
        self.field_synonyms = {
            'farmer_name': ['applicant name', 'name of applicant', 'farmer', 'applicant'],
            'scheme_name': ['scheme', 'scheme name', 'government scheme', 'benefit scheme'],
            'aadhaar_number': ['aadhaar', 'aadhaar no', 'uid', 'uid number'],
            'village': ['village', 'village name', 'gram'],
            'district': ['district', 'district name'],
            'location': ['address', 'location', 'village address', 'farm location'],
            'land_size': ['land area', 'area', 'total land', 'land holding', 'acre', 'hectare'],
            'requested_amount': ['amount', 'requested amount', 'benefit amount', 'subsidy amount', 'loan amount'],
            'crop_type': ['crop', 'crop name', 'cultivation', 'agricultural crop'],
            'season': ['season', 'cropping season', 'kharif', 'rabi', 'zaid'],
            'phone_number': ['phone', 'mobile', 'contact', 'contact number'],
            'application_id': ['application id', 'application no', 'application number', 'reference no', 'form no']
        }
    
    def get_document_type(self) -> str:
        return "scheme_application"
    
    def extract_fields(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract fields from scheme application text"""
        # Normalize text
        normalized_text = normalize_ocr_text(text)
        
        # Initialize result containers
        structured_data = {}
        extracted_fields = {}
        reasoning = []
        
        # Extract core scheme fields
        farmer_result = self._extract_farmer_name(normalized_text)
        if farmer_result:
            value, confidence, source = farmer_result
            self.safe_set_field(structured_data, extracted_fields, 'farmer_name', value, confidence, source)
        
        scheme_result = self._extract_scheme_name(normalized_text)
        if scheme_result:
            value, confidence, source = scheme_result
            self.safe_set_field(structured_data, extracted_fields, 'scheme_name', value, confidence, source)
        
        # Extract location-related fields
        location_results = self._extract_location_fields(normalized_text)
        for field_name, result in location_results.items():
            if result:
                value, confidence, source = result
                self.safe_set_field(structured_data, extracted_fields, field_name, value, confidence, source)
        
        # Combine village and district into location
        village = structured_data.get('village')
        district = structured_data.get('district')
        if village and district:
            location = f"{village}, {district}"
            location_confidence = 0.9
            self.safe_set_field(structured_data, extracted_fields, 'location', location, location_confidence, "Combined village and district")
        elif village:
            self.safe_set_field(structured_data, extracted_fields, 'location', village, 0.8, "Village only")
        elif district:
            self.safe_set_field(structured_data, extracted_fields, 'location', district, 0.8, "District only")
        
        # Extract remaining scheme-specific core fields only
        remaining_fields = [
            ('aadhaar_number', self._extract_aadhaar_number),
            ('land_size', self._extract_land_size),
            ('requested_amount', self._extract_requested_amount),
            ('phone_number', self._extract_phone_number),
            ('application_id', self._extract_application_id)
        ]
        
        for field_name, extractor in remaining_fields:
            result = extractor(normalized_text)
            if result:
                value, confidence, source = result
                self.safe_set_field(structured_data, extracted_fields, field_name, value, confidence, source)
        
        # Add structured reasoning in correct order
        if structured_data:
            reasoning.append(f"Fields extracted: {', '.join(sorted(structured_data.keys()))}")
        
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
    
    def _extract_farmer_name(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract farmer name using boundary-aware extraction with junk rejection"""
        extractor = BoundaryAwareExtractor()
        
        # JUNK REJECTION FILTER - Explicitly reject these header/label values
        junk_values = {
            'field value', 'details', 'information', 'applicant details', 
            'account holder details', 'as per', 'farmer', 'insured farmer details', 
            'claim details', 'policy information', 'claimant details', 'beneficiary details',
            'form', 'application', 'applicant', 'name', 'farmer name'
        }
        
        # Try boundary-aware extraction first
        labels = ['applicant name', 'farmer name', 'name of applicant', 'farmer', 'applicant', 'name']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'farmer_name', [label])
            if result:
                value = FieldNormalizers.normalize_person_name(result)
                # Apply rejection filter
                if (value.lower() not in junk_values and
                    not value.lower().startswith(('field', 'details', 'information', 'applicant', 'name')) and
                    FieldValidators.validate_person_name(value)):
                    return value, 0.9, f"Boundary-aware extraction with label '{label}'"
        
        # Strong labeled regex fallback with junk rejection
        patterns = [
            r'(?:applicant name|farmer name|name of applicant)[:\s\-]+([A-Za-z.\s]{3,60})',
            r'(?:name of farmer)[:\s\-]+([A-Za-z.\s]{3,60})',
            r'Name[:\s]+([A-Za-z.\s]{3,60})',
            r'Applicant[:\s]+([A-Za-z.\s]{3,60})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = FieldNormalizers.normalize_person_name(match.group(1).strip())
                # Apply rejection filter
                if (value.lower() not in junk_values and
                    not value.lower().startswith(('field', 'details', 'information', 'applicant', 'name')) and
                    FieldValidators.validate_person_name(value)):
                    return value, 0.85, f"Labeled regex fallback: {pattern}"
        
        return None
    
    def _extract_scheme_name(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract scheme name using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        labels = ['scheme name', 'scheme', 'government scheme', 'benefit scheme']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'scheme_name', [label])
            if result:
                value = FieldNormalizers.normalize_scheme_name(result)
                if FieldValidators.validate_scheme_name(value):
                    return value, 0.9, f"Boundary-aware extraction with label '{label}'"
        
        # Fallback regex for specific patterns
        patterns = [
            r'Scheme Name[:\s]+(.+?)(?=\n|$)',
            r'Scheme[:\s]+(.+?)(?=\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                scheme = match.group(1).strip()
                scheme = FieldNormalizers.normalize_scheme_name(scheme)
                if FieldValidators.validate_scheme_name(scheme):
                    return scheme, 0.65, f"Regex fallback pattern: {pattern}"
        
        return None
    
    def _extract_aadhaar_number(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract Aadhaar number using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        labels = ['aadhaar', 'aadhaar no', 'uid', 'uid number']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'aadhaar_number', [label])
            if result:
                value = FieldNormalizers.normalize_aadhaar(result)
                if FieldValidators.validate_aadhaar_number(value):
                    return value, 0.95, f"Boundary-aware extraction with label '{label}'"
        
        # Fallback regex for 12-digit Aadhaar pattern
        pattern = r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b'
        match = re.search(pattern, text)
        if match:
            aadhaar = re.sub(r'[\s-]', '', match.group(1))
            if FieldValidators.validate_aadhaar_number(aadhaar):
                return aadhaar, 0.7, "Regex fallback for 12-digit pattern"
        
        return None
    
    def _extract_location_fields(self, text: str) -> Dict[str, Optional[Tuple[str, float, str]]]:
        """Extract village and district using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        results = {}
        
        # Extract village
        village_result = extractor.extract_field_by_boundary(text, 'village')
        if village_result:
            value = FieldNormalizers.normalize_location(village_result)
            if FieldValidators.validate_location(value):
                results['village'] = (value, 0.85, "Boundary-aware extraction for village")
        
        # Extract district
        district_result = extractor.extract_field_by_boundary(text, 'district')
        if district_result:
            value = FieldNormalizers.normalize_location(district_result)
            if FieldValidators.validate_location(value):
                results['district'] = (value, 0.85, "Boundary-aware extraction for district")
        
        return results
    
    def _extract_land_size(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract land size using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        result = extractor.extract_field_by_boundary(text, 'land_size')
        if result:
            value = FieldNormalizers.normalize_land_size(result)
            if FieldValidators.validate_land_size(value):
                return value, 0.85, "Boundary-aware extraction for land_size"
        
        # Fallback regex with units
        pattern = r'(\d+(?:\.\d+)?)\s*(acre|hectare|bigha)s?'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            size = match.group(1)
            unit = match.group(2)
            land_size = f"{size} {unit}"
            if FieldValidators.validate_land_size(land_size):
                return land_size, 0.65, f"Regex fallback with unit: {unit}"
        
        return None
    
    def _extract_requested_amount(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract requested amount using boundary-aware extraction with strict label priority"""
        extractor = BoundaryAwareExtractor()
        
        # PRIORITIZE these specific labels for scheme/subsidy/benefit amounts
        priority_labels = ['requested amount', 'subsidy amount', 'amount requested', 'benefit amount', 'loan amount', 'benefit type']
        for label in priority_labels:
            result = extractor.extract_field_by_boundary(text, 'requested_amount', [label])
            if result:
                value = FieldNormalizers.normalize_amount(result)
                if FieldValidators.validate_money_amount(value):
                    return value, 0.9, f"Priority label extraction: '{label}'"
        
        # Field-aware regex patterns with the same strict labels, including benefit type
        patterns = [
            r'(?:Rs|Rs\.|INR|₹)\s*Requested\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:Rs|Rs\.|INR|₹)\s*Subsidy\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:Rs|Rs\.|INR|₹)\s*Benefit\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:Rs|Rs\.|INR|₹)\s*Loan\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:Rs|Rs\.|INR|₹)\s*Benefit\s+Type[:\s]+(?:.*?Rs\.?\s*|.*?INR\s*|.*?₹\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Requested\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Subsidy\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Benefit\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Loan\s+Amount[:\s]+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Benefit\s+Type[:\s]+(?:.*?Rs\.?\s*|.*?INR\s*|.*?₹\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(',', '')
                if FieldValidators.validate_money_amount(amount):
                    return amount, 0.8, f"Field-aware regex: {pattern}"
        
        # DO NOT extract generic "amount" without specific scheme/subsidy/benefit context
        # This prevents leakage into wrong fields
        
        return None
    
    def _extract_crop_type(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract crop type using fallback-driven extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction (lower priority)
        labels = ['crop', 'crop type', 'cultivated crop']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'crop_type', [label])
            if result:
                value = result.strip().title()
                if len(value) > 0 and len(value) < 50:  # Reasonable length check
                    return value, 0.65, f"Boundary-aware extraction with label '{label}'"
        
        # Primary: label-based regex
        patterns = [
            r'(?:crop|crop type|cultivated crop)[:\s]+([A-Za-z\s]{3,30})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                crop = match.group(1).strip().title()
                if len(crop) > 0 and len(crop) < 50:
                    return crop, 0.8, "Label-based regex primary"
        
        # Secondary: keyword matching with whole word boundaries
        crops = ['wheat', 'rice', 'paddy', 'cotton', 'sugarcane', 'pulses', 'maize', 'bajra', 'jowar']
        text_lower = text.lower()
        for crop in crops:
            if re.search(r'\b' + crop + r'\b', text_lower):
                return crop.title(), 0.75, f"Keyword matching for crop: {crop}"
        
        return None
    
    def _extract_season(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract season using controlled vocabulary"""
        seasons = ['kharif', 'rabi', 'zaid']
        text_lower = text.lower()
        
        for season in seasons:
            if season in text_lower:
                return season.title(), 0.75, f"Controlled vocabulary match: {season}"
        
        return None
    
    def _extract_phone_number(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract phone number using boundary-aware extraction"""
        extractor = BoundaryAwareExtractor()
        
        # Try boundary-aware extraction first
        labels = ['phone', 'mobile', 'contact number']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'mobile_number', [label])
            if result:
                value = FieldNormalizers.normalize_mobile(result)
                if FieldValidators.validate_mobile_number(value):
                    return value, 0.85, f"Boundary-aware extraction with label '{label}'"
        
        # Fallback regex for 10-digit numbers in reasonable context
        pattern = r'(?:phone|mobile|contact)[:\s]+(\d{10})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            phone = match.group(1)
            if FieldValidators.validate_mobile_number(phone):
                return phone, 0.65, "Regex fallback for 10-digit pattern"
        
        return None
    
    def _extract_application_id(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract application ID using regex-primary extraction"""
        # Primary: strong regex pattern with prefixes
        patterns = [
            r'\b(APP|REF|FORM|PMKISAN)[-/]?[A-Za-z0-9]{2,}[-/A-Za-z0-9]*\b',  # With prefixes
            r'\bapplication\s+(?:id|no|ref|reference)\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})\b',  # Labeled
            r'\bform\s+(?:no|number|id)\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})\b',  # Form numbers
            r'\breference\s+(?:no|number)\s*[:\-]?\s*([A-Za-z0-9\-/]{5,30})\b'  # Reference numbers
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                app_id = match.group(1) if match.groups() else match.group(0)
                # Strict validation: prefer alphanumeric with prefixes, reject plain 6-digit pin codes
                if (5 <= len(app_id) <= 30 and 
                    re.search(r'\d', app_id) and 
                    re.match(r'^[A-Za-z0-9\-/]+$', app_id) and
                    not re.match(r'^\d{6}$', app_id)):  # Reject plain 6-digit pin codes
                    return app_id, 0.85, f"Strong regex pattern: {pattern}"
        
        return None
