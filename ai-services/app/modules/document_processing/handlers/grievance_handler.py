"""
Grievance Handler
Purpose: Extract fields from grievance letters and complaints
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


class GrievanceHandler(BaseHandler):
    """Handler for grievance letters and complaints"""
    
    def __init__(self):
        super().__init__()
        self.required_fields = [
            'farmer_name',
            'grievance_type',
            'description'
        ]
        self.optional_fields = []
        
        # GRIEVANCE-SPECIFIC FIELD MAPPING - ONLY REQUIRED FIELDS
        self.field_synonyms = {
            'farmer_name': ['complainant', 'applicant', 'grievant', 'from', 'submitted by', 'name of complainant'],
            'grievance_type': ['grievance type', 'complaint type', 'issue type', 'problem type', 'category'],
            'description': ['complaint', 'grievance', 'issue', 'problem', 'description', 'details']
        }
    
    def get_document_type(self) -> str:
        return "grievance"
    
    def extract_fields(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract fields from grievance text"""
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
        
        # Extract grievance type
        grievance_type_result = self._extract_grievance_type(normalized_text)
        if grievance_type_result:
            value, confidence, source = grievance_type_result
            self.safe_set_field(structured_data, extracted_fields, 'grievance_type', value, confidence, source)
        
        # Extract description
        description_result = self._extract_description(normalized_text)
        if description_result:
            value, confidence, source = description_result
            self.safe_set_field(structured_data, extracted_fields, 'description', value, confidence, source)
        
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
            'details', 'complainant details', 'applicant details', 'field value',
            'grievance', 'complaint', 'letter', 'from', 'submitted by',
            'name', 'complainant', 'applicant', 'petitioner',
            'farmer', 'grievant', 'claimant'
        }
        
        # Try boundary-aware extraction first - include complainant name, petitioner name labels
        labels = ['from', 'submitted by', 'complainant', 'applicant', 'name of complainant', 'complainant name', 'petitioner name']
        for label in labels:
            result = extractor.extract_field_by_boundary(text, 'farmer_name', [label])
            if result:
                value = FieldNormalizers.normalize_person_name(result)
                # Skip if the extracted value is junk or just a label
                if (value.lower() not in junk_values and
                    not value.lower().startswith(('from', 'submitted by', 'complainant', 'applicant', 'name', 'petitioner')) and
                    FieldValidators.validate_person_name(value)):
                    return value, 0.85, f"Boundary-aware extraction with label '{label}'"
        
        # Strong labeled regex fallback with junk rejection
        patterns = [
            r'(?:applicant name|complainant name|claimant name|petitioner name)[:\s]+([A-Za-z.\s]{3,60})',
            r'(?:from|submitted by)[:\s]+([A-Za-z.\s]{3,60})',
            r'From[:\s]+([A-Za-z.\s]{3,60})',
            r'(?:name of complainant)[:\s]+([A-Za-z.\s]{3,60})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = FieldNormalizers.normalize_person_name(name)
                # Apply junk rejection filter
                if (name.lower() not in junk_values and
                    not name.lower().startswith(('from', 'submitted by', 'complainant', 'applicant', 'name', 'petitioner')) and
                    FieldValidators.validate_person_name(name)):
                    return name, 0.7, f"Labeled regex fallback: {pattern}"
        
        # Additional fallback: look for "I am [Name]" pattern in grievance text
        i_am_pattern = r'I\s+am\s+([A-Za-z.\s]{3,60})\s*,?'
        match = re.search(i_am_pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = FieldNormalizers.normalize_person_name(name)
            if name.lower() not in junk_values and FieldValidators.validate_person_name(name):
                return name, 0.6, "I am pattern fallback"
        
        return None
    
    def _extract_grievance_type(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract grievance type from keywords or labeled patterns"""
        # Labeled extraction first
        patterns = [
            r'(?:grievance type|complaint type|issue type|problem type|category)[\s:.-]+(.+?)(?=\n|$)',
            r'Type[:\s]+(.+?)(?=\n|$)',
            r'Category[:\s]+(.+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                grievance_type = match.group(1).strip()
                # Keep it short and clean
                if len(grievance_type) <= 50:
                    return grievance_type, 0.85, f"Labeled grievance type: {pattern}"
        
        # Extract from subject line
        subject_patterns = [
            r'Subject[:\s]+(.+?)(?=\n|$)',
            r'SUBJECT[:\s]+(.+?)(?=\n|$)',
            r'Re[:\s]+(.+?)(?=\n|$)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                # Clean up subject and use as grievance type
                if len(subject) <= 50:
                    return subject, 0.8, f"Extracted from subject: {pattern}"
        
        # Keyword inference for common grievance types
        grievance_keywords = {
            "payment delay": ["payment delay", "delay in payment", "late payment", "pending payment"],
            "benefit issue": ["benefit not received", "no benefit", "subsidy not received", "amount not received"],
            "application issue": ["duplicate application", "multiple applications", "duplicate entry", "document rejected"],
            "insurance claim": ["insurance claim", "claim rejected", "insurance not paid", "claim settlement"],
            "officer delay": ["officer delay", "official delay", "bureaucratic delay", "not responding"],
            "corruption": ["corruption", "bribe", "illegal demand", "money demanded"],
            "infrastructure": ["road", "water", "electricity", "irrigation", "facility"],
            "land dispute": ["land dispute", "boundary issue", "land problem", "survey issue"]
        }
        
        text_lower = text.lower()
        for grievance_type, keywords in grievance_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return grievance_type, 0.7, f"Keyword inference: {keywords[0]}"
        
        return None
    
    def _extract_description(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Extract main grievance description, avoiding headers and focusing on meaningful content"""
        lines = text.split('\n')
        grievance_lines = []
        
        # Header patterns to skip - avoid swallowing document structure
        header_patterns = [
            r'^to[:\s]+',
            r'^from[:\s]+',
            r'^date[:\s]+',
            r'^subject[:\s]+',
            r'^ref[:\s]+',
            r'^reference[:\s]+',
            r'^type[:\s]+',
            r'^category[:\s]+',
            r'^grievance type[:\s]+',
            r'^complaint type[:\s]+',
            r'^farmer grievance letter',
            r'^sample grievance letter',
            r'^applicant name[:\s]+',
            r'^complainant name[:\s]+',
            r'^petitioner name[:\s]+',
            # Also skip pure label lines
            r'^[A-Za-z\s]+[:\s]+$'
        ]
        
        # Find the start of actual grievance content
        content_started = False
        for line in lines:
            line = line.strip()
            
            # Mark content start after common headers
            if not content_started:
                if any(phrase in line.lower() for phrase in ['dear sir', 'dear madam', 'respectfully', 'i am writing', 'i wish to', 'i would like to']):
                    content_started = True
                elif re.match(r'^(dear\s+sir|dear\s+madam|subject|to|from|date)', line, re.IGNORECASE):
                    continue
                elif len(line) > 30 and any(keyword in line.lower() for keyword in ['grievance', 'complaint', 'issue', 'problem', 'delay', 'payment']):
                    content_started = True
                else:
                    continue
            
            # Skip if line matches any header pattern
            is_header = any(re.match(pattern, line, re.IGNORECASE) for pattern in header_patterns)
            if is_header:
                continue
                
            # Include meaningful lines that describe actual grievance
            if len(line) > 15:
                # Prefer lines that look like actual grievance content
                grievance_keywords = ['delay', 'payment', 'subsidy', 'benefit', 'application', 'officer', 'issue', 'problem', 'request', 'complaint', 'grievance', 'received', 'amount', 'bank', 'account', 'credit']
                line_lower = line.lower()
                
                # Include lines with grievance keywords OR if we need more content
                if any(keyword in line_lower for keyword in grievance_keywords) or len(grievance_lines) < 2:
                    # Clean the line - remove header fragments if present
                    clean_line = line
                    for junk_fragment in ['applicant information', 'claimant name', 'office', 'district agriculture officer',
                                       'subject', 'from', 'to', 'main branch', 'branch manager', 'complainant']:
                        clean_line = re.sub(junk_fragment, '', clean_line, flags=re.IGNORECASE)
                    
                    clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                    if len(clean_line) > 20:  # Only include meaningful lines
                        grievance_lines.append(clean_line)
                        
                    if len(grievance_lines) >= 3:  # Limit to 3 lines
                        break
        
        if grievance_lines:
            # Combine first 2-3 meaningful lines, keep it concise
            grievance_text = ' '.join(grievance_lines[:2])  # Use first 2 lines for clarity
            if len(grievance_text) > 300:  # Keep description concise
                grievance_text = grievance_text[:300] + '...'
            return grievance_text, 0.75, "Extracted main grievance description"
        
        return None
    
    
