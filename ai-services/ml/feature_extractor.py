#!/usr/bin/env python3
"""
Feature Extractor for Agricultural Document Processing
Extracts features from extracted data for Random Forest classification
"""

import re
from typing import Dict, Any, List
from datetime import datetime

class FeatureExtractor:
    """Extract features from document extraction results for ML classification"""
    
    def __init__(self):
        # Feature names for consistency
        self.feature_names = [
            'missing_fields_count',
            'confidence_score',
            'document_type_encoded',
            'text_length',
            'risk_flags_count',
            'has_aadhaar',
            'has_mobile',
            'has_amount',
            'amount_value',
            'extraction_completeness'
        ]
    
    def extract_features(self, extracted_data: Dict[str, Any]) -> List[float]:
        """
        Extract features from extracted data
        
        Args:
            extracted_data: Dictionary containing extraction results
            
        Returns:
            List of feature values in the same order as feature_names
        """
        features = []
        
        # 1. Missing fields count
        missing_fields = extracted_data.get('missing_fields', [])
        missing_count = len(missing_fields) if missing_fields else 0
        features.append(float(missing_count))
        
        # 2. Confidence score
        confidence = extracted_data.get('confidence', 0.0)
        features.append(float(confidence))
        
        # 3. Document type encoded
        doc_type = extracted_data.get('document_type', '').lower()
        doc_type_encoding = self._encode_document_type(doc_type)
        features.append(float(doc_type_encoding))
        
        # 4. Text length (combined from all text fields)
        text_length = self._calculate_text_length(extracted_data)
        features.append(float(text_length))
        
        # 5. Risk flags count
        risk_flags = extracted_data.get('risk_flags', [])
        risk_count = len(risk_flags) if risk_flags else 0
        features.append(float(risk_count))
        
        # 6. Has Aadhaar (binary)
        has_aadhaar = self._has_aadhaar(extracted_data)
        features.append(float(has_aadhaar))
        
        # 7. Has mobile (binary)
        has_mobile = self._has_mobile(extracted_data)
        features.append(float(has_mobile))
        
        # 8. Has amount (binary)
        has_amount = self._has_amount(extracted_data)
        features.append(float(has_amount))
        
        # 9. Amount value (normalized)
        amount_value = self._extract_amount_value(extracted_data)
        features.append(float(amount_value))
        
        # 10. Extraction completeness (ratio of present to expected fields)
        completeness = self._calculate_extraction_completeness(extracted_data)
        features.append(float(completeness))
        
        return features
    
    def _encode_document_type(self, doc_type: str) -> int:
        """Encode document type as integer"""
        type_mapping = {
            'scheme_application': 0,
            'subsidy_claim': 1,
            'grievance': 2,
            'insurance_claim': 3,
            'farmer_record': 4,
            'supporting_document': 5,
            'unknown': 6
        }
        return type_mapping.get(doc_type, 6)
    
    def _calculate_text_length(self, extracted_data: Dict[str, Any]) -> int:
        """Calculate total text length from all extracted fields"""
        total_length = 0
        
        # Check structured_data
        structured_data = extracted_data.get('structured_data', {})
        if isinstance(structured_data, dict):
            for key, value in structured_data.items():
                if isinstance(value, str):
                    total_length += len(value)
        
        # Check canonical data
        canonical = extracted_data.get('canonical', {})
        if isinstance(canonical, dict):
            # Applicant section
            applicant = canonical.get('applicant', {})
            if isinstance(applicant, dict):
                for key, value in applicant.items():
                    if isinstance(value, str):
                        total_length += len(value)
            
            # Agriculture section
            agriculture = canonical.get('agriculture', {})
            if isinstance(agriculture, dict):
                for key, value in agriculture.items():
                    if isinstance(value, str):
                        total_length += len(value)
            
            # Request section
            request = canonical.get('request', {})
            if isinstance(request, dict):
                for key, value in request.items():
                    if isinstance(value, str):
                        total_length += len(value)
        
        return total_length
    
    def _has_aadhaar(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if Aadhaar number is present and valid"""
        # Check canonical applicant
        canonical = extracted_data.get('canonical', {})
        applicant = canonical.get('applicant', {})
        aadhaar = applicant.get('aadhaar_number', '')
        
        if aadhaar and self._is_valid_aadhaar(aadhaar):
            return True
        
        # Check structured data
        structured_data = extracted_data.get('structured_data', {})
        aadhaar_alt = structured_data.get('aadhaar_number', '')
        
        return bool(aadhaar_alt and self._is_valid_aadhaar(aadhaar_alt))
    
    def _has_mobile(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if mobile number is present and valid"""
        # Check canonical applicant
        canonical = extracted_data.get('canonical', {})
        applicant = canonical.get('applicant', {})
        mobile = applicant.get('mobile_number', '')
        
        if mobile and self._is_valid_mobile(mobile):
            return True
        
        # Check structured data
        structured_data = extracted_data.get('structured_data', {})
        mobile_alt = structured_data.get('phone_number', '')
        
        return bool(mobile_alt and self._is_valid_mobile(mobile_alt))
    
    def _has_amount(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if monetary amount is present"""
        # Check canonical request
        canonical = extracted_data.get('canonical', {})
        request = canonical.get('request', {})
        amount = request.get('requested_amount', '')
        
        if amount and self._extract_numeric_amount(amount):
            return True
        
        # Check structured data
        structured_data = extracted_data.get('structured_data', {})
        amount_alt = structured_data.get('requested_amount', '')
        
        return bool(amount_alt and self._extract_numeric_amount(amount_alt))
    
    def _extract_amount_value(self, extracted_data: Dict[str, Any]) -> float:
        """Extract and normalize monetary amount"""
        # Check canonical request
        canonical = extracted_data.get('canonical', {})
        request = canonical.get('request', {})
        amount = request.get('requested_amount', '')
        
        if amount:
            numeric_amount = self._extract_numeric_amount(amount)
            if numeric_amount:
                # Normalize to 0-1 range (assuming max 100,000)
                return min(numeric_amount / 100000.0, 1.0)
        
        # Check structured data
        structured_data = extracted_data.get('structured_data', {})
        amount_alt = structured_data.get('requested_amount', '')
        
        if amount_alt:
            numeric_amount = self._extract_numeric_amount(amount_alt)
            if numeric_amount:
                return min(numeric_amount / 100000.0, 1.0)
        
        return 0.0
    
    def _calculate_extraction_completeness(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate extraction completeness as ratio of present to expected fields"""
        expected_fields = [
            'document_type',
            'canonical.applicant.name',
            'canonical.applicant.aadhaar_number',
            'canonical.applicant.mobile_number',
            'canonical.agriculture.land_size',
            'canonical.request.requested_amount'
        ]
        
        present_fields = 0
        
        # Check document_type
        if extracted_data.get('document_type'):
            present_fields += 1
        
        # Check canonical fields
        canonical = extracted_data.get('canonical', {})
        applicant = canonical.get('applicant', {})
        agriculture = canonical.get('agriculture', {})
        request = canonical.get('request', {})
        
        if applicant.get('name'):
            present_fields += 1
        if applicant.get('aadhaar_number'):
            present_fields += 1
        if applicant.get('mobile_number'):
            present_fields += 1
        if agriculture.get('land_size'):
            present_fields += 1
        if request.get('requested_amount'):
            present_fields += 1
        
        return present_fields / len(expected_fields)
    
    def _is_valid_aadhaar(self, aadhaar: str) -> bool:
        """Validate Aadhaar number format"""
        # Remove spaces and hyphens
        clean_aadhaar = re.sub(r'[\s-]', '', aadhaar)
        return bool(re.match(r'^\d{12}$', clean_aadhaar))
    
    def _is_valid_mobile(self, mobile: str) -> bool:
        """Validate mobile number format"""
        # Remove spaces, hyphens, and parentheses
        clean_mobile = re.sub(r'[\s\-\(\)]', '', mobile)
        return bool(re.match(r'^\+?\d{10,15}$', clean_mobile))
    
    def _extract_numeric_amount(self, amount_str: str) -> float:
        """Extract numeric value from amount string"""
        if not amount_str:
            return 0.0
        
        # Remove common currency symbols and text
        cleaned = re.sub(r'[₹$Rsrs.,\s]', '', amount_str)
        
        # Extract numbers
        match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names.copy()
    
    def get_training_data_from_samples(self, samples: List[Dict[str, Any]]) -> tuple:
        """
        Convert sample data to training features and labels
        
        Args:
            samples: List of sample extraction results with labels
            
        Returns:
            Tuple of (features, labels) for training
        """
        features = []
        labels = []
        
        for sample in samples:
            # Extract features
            feature_vector = self.extract_features(sample['extracted_data'])
            features.append(feature_vector)
            
            # Extract label (risk level)
            label = sample.get('risk_level', 'medium')
            labels.append(label)
        
        return features, labels
