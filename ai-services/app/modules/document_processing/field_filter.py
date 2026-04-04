"""
Field Filter for Noise Reduction
Purpose: Filter out low-quality and noisy extracted fields
"""
import re
from typing import Dict, List, Optional, Any, Set


class FieldFilter:
    """Filters extracted fields to remove noise and improve quality"""
    
    def __init__(self):
        # Header/footer noise patterns
        self.noise_patterns = {
            'document_headers': [
                r'^(APPLICATION|FORM|CERTIFICATE|RECORD|CLAIM|PETITION|GRIEVANCE)\s*$',
                r'^(SCHEME|INSURANCE|SUBSIDY|BENEFIT|GOVERNMENT)\s*$',
                r'^(PERSONAL|POLICY|APPLICANT|POLICYHOLDER)\s+(INFORMATION|DETAILS|DATA)\s*$',
                r'^(BANK|STATE|DISTRICT|VILLAGE|TEHSIL)\s*$'
            ],
            'generic_labels': [
                r'^(Name|Address|Phone|Mobile|Amount|Details|Information|Data)\s*$',
                r'^(To|From|Subject|Date|Ref|Reference)\s*$',
                r'^(Applicant|Claimant|Complainant|Petitioner|Farmer)\s*$'
            ],
            'section_titles': [
                r'^(Section|Part|Clause|Article)\s+[A-Z0-9]+\s*$',
                r'^(Chapter|Page|Form)\s+[A-Z0-9]+\s*$'
            ]
        }
        
        # Low-quality field indicators
        self.low_quality_indicators = {
            'single_words': [
                'FORM', 'APPLICATION', 'CERTIFICATE', 'RECORD', 'CLAIM', 
                'PETITION', 'GRIEVANCE', 'SCHEME', 'INSURANCE', 'SUBSIDY',
                'BENEFIT', 'GOVERNMENT', 'BANK', 'STATE', 'DISTRICT',
                'VILLAGE', 'TEHSIL', 'PERSONAL', 'POLICY', 'APPLICANT',
                'POLICYHOLDER', 'INFORMATION', 'DETAILS', 'DATA'
            ],
            'generic_placeholders': [
                'Name', 'Address', 'Phone', 'Mobile', 'Amount', 'Details',
                'To', 'From', 'Subject', 'Date', 'Ref', 'Reference'
            ],
            'document_titles': [
                'FARMER REGISTRATION RECORD',
                'GRIEVANCE PETITION',
                'CROP INSURANCE CLAIM FORM',
                'AGRICULTURAL EQUIPMENT SUBSIDY CLAIM',
                'BANK PASSBOOK CERTIFICATE'
            ]
        }
        
        # Valid field patterns
        self.valid_field_patterns = {
            'person_name': [
                r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
                r'^(?:Mr|Mrs|Ms|Shri|Smt)\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$'
            ],
            'location': [
                r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
                r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$'
            ],
            'contact': [
                r'^\d{10}$',
                r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
            ],
            'identification': [
                r'^\d{4}\s*\d{4}\s*\d{4}$',
                r'^[A-Z]{5}\d{4}[A-Z]$'
            ],
            'financial': [
                r'^\d{1,8}(?:,\d{3})*(?:\.\d{2})?$'
            ]
        }
    
    def filter_extracted_fields(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out low-quality and noisy fields"""
        filtered_fields = {}
        removal_reasons = []
        
        for field_name, field_data in extracted_fields.items():
            value = field_data.get('value', '') if isinstance(field_data, dict) else str(field_data)
            source = field_data.get('source', 'unknown') if isinstance(field_data, dict) else 'unknown'
            
            # Check if field should be removed
            removal_reason = self._should_remove_field(field_name, value, source)
            
            if removal_reason:
                removal_reasons.append(f"{field_name}: {removal_reason}")
            else:
                # Keep field but potentially adjust confidence
                adjusted_field = self._adjust_field_confidence(field_name, field_data)
                filtered_fields[field_name] = adjusted_field
        
        return {
            'filtered_fields': filtered_fields,
            'removed_fields': removal_reasons,
            'original_count': len(extracted_fields),
            'filtered_count': len(filtered_fields),
            'removal_count': len(removal_reasons)
        }
    
    def _should_remove_field(self, field_name: str, value: str, source: str) -> Optional[str]:
        """Determine if a field should be removed"""
        value = str(value).strip()
        
        # Remove empty or whitespace-only values
        if not value or value.isspace():
            return "Empty value"
        
        # Remove fields that match noise patterns
        for noise_type, patterns in self.noise_patterns.items():
            for pattern in patterns:
                if re.match(pattern, value, re.IGNORECASE):
                    return f"Matches {noise_type} pattern"
        
        # Remove single-word generic terms
        if value in self.low_quality_indicators['single_words']:
            return "Generic single word"
        
        # Remove document titles
        if value in self.low_quality_indicators['document_titles']:
            return "Document title"
        
        # Remove fields with semantic mapping that are actually noise
        if source == 'semantic_mapping_person_name':
            # Check if it's actually a header/label
            if any(word in value.upper() for word in ['APPLICATION', 'FORM', 'CERTIFICATE', 'RECORD', 'CLAIM']):
                return "Header misidentified as name"
        
        # Remove location fields that are actually headers
        if source in ['semantic_mapping_address', 'semantic_extraction'] and len(value.split()) < 3:
            if any(word in value.upper() for word in ['DISTRICT', 'VILLAGE', 'TEHSIL', 'STATE', 'BANK']):
                return "Location header"
        
        # Remove contact fields that are too short or invalid
        if source == 'semantic_mapping_contact':
            if len(value) < 10 or not re.search(r'\d', value):
                return "Invalid contact format"
        
        return None
    
    def _adjust_field_confidence(self, field_name: str, field_data: Any) -> Any:
        """Adjust field confidence based on quality indicators"""
        if not isinstance(field_data, dict):
            return field_data
        
        value = str(field_data.get('value', '')).strip()
        source = field_data.get('source', 'unknown')
        confidence = field_data.get('confidence', 0.5)
        
        # Boost confidence for high-quality patterns
        for field_type, patterns in self.valid_field_patterns.items():
            if any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns):
                confidence = min(confidence + 0.1, 1.0)
                break
        
        # Reduce confidence for suspicious patterns
        if len(value.split()) == 1 and len(value) > 10:  # Long single word
            confidence = max(confidence - 0.2, 0.1)
        
        if source == 'semantic_extraction' and len(value) < 5:  # Very short semantic extraction
            confidence = max(confidence - 0.3, 0.1)
        
        # Update field data
        adjusted_field = field_data.copy()
        adjusted_field['confidence'] = confidence
        
        return adjusted_field
    
    def get_field_quality_report(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a quality report for extracted fields"""
        total_fields = len(extracted_fields)
        high_confidence = sum(1 for f in extracted_fields.values() 
                            if isinstance(f, dict) and f.get('confidence', 0) > 0.8)
        medium_confidence = sum(1 for f in extracted_fields.values() 
                              if isinstance(f, dict) and 0.5 < f.get('confidence', 0) <= 0.8)
        low_confidence = sum(1 for f in extracted_fields.values() 
                           if isinstance(f, dict) and f.get('confidence', 0) <= 0.5)
        
        sources = {}
        for field_data in extracted_fields.values():
            if isinstance(field_data, dict):
                source = field_data.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_fields': total_fields,
            'confidence_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            },
            'source_distribution': sources,
            'quality_score': (high_confidence * 1.0 + medium_confidence * 0.7 + low_confidence * 0.3) / total_fields if total_fields > 0 else 0.0
        }
