"""
Document Processing Utilities

Clean shared helper module for normalization, boundary-aware extraction, 
validation, and field normalization in the document-processing pipeline.
"""
import re
from typing import Dict, List, Optional, Any, Union


def normalize_ocr_text(value: Union[str, List, Dict, int, float, None]) -> str:
    """
    Normalize OCR text input to consistent string format.
    
    Args:
        value: OCR text input (can be str, list, dict, int, float, or None)
    
    Returns:
        str: Normalized OCR text string
    """
    if value is None:
        return ""
    
    # Handle dict with preference for specific keys
    if isinstance(value, dict):
        preferred_keys = ['text', 'raw_text', 'content']
        for key in preferred_keys:
            if key in value:
                return normalize_ocr_text(value[key])
        else:
            # If no preferred key found, use first scalar/string-like value
            for v in value.values():
                if isinstance(v, (str, int, float)):
                    return normalize_ocr_text(v)
            # Fallback to string representation
            return str(value)
    
    # Handle list - preserve line structure
    if isinstance(value, list):
        normalized_items = [normalize_ocr_text(item) for item in value]
        # Discard blank normalized items
        normalized_items = [item for item in normalized_items if item.strip()]
        return "\n".join(normalized_items)
    
    # Handle numbers
    if isinstance(value, (int, float)):
        return str(value)
    
    # Handle string
    if isinstance(value, str):
        # Normalize line endings
        value = value.replace('\r\n', '\n').replace('\r', '\n')
        # Collapse repeated whitespace lightly (preserve single spaces)
        value = re.sub(r'[ \t]+', ' ', value)
        # Preserve useful line structure but normalize multiple newlines
        value = re.sub(r'\n\s*\n\s*\n', '\n\n', value)
        return value.strip()
    
    # Fallback to string conversion
    return str(value)


def is_missing_value(value: Any) -> bool:
    """
    Check if a value should be considered missing/empty.
    
    Args:
        value: Value to check
    
    Returns:
        bool: True if value is missing/empty
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        return not value.strip() or value.lower() in ['', 'null', 'none', 'n/a', '-']
    
    if isinstance(value, (list, dict)):
        return len(value) == 0
    
    return False


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with default fallback.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        float: Converted value or default
    """
    try:
        if value is None:
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Normalize whitespace
            clean_value = value.strip()
            
            # Remove common currency words safely
            clean_value = re.sub(r'\b(rs\.?|inr|rupee|rupees|₹)\b', '', clean_value, flags=re.IGNORECASE)
            
            # Remove commas
            clean_value = clean_value.replace(',', '')
            
            # Extract the first clean numeric token only if valid
            match = re.search(r'-?\d+(?:\.\d+)?', clean_value)
            if match:
                numeric_token = match.group(0)
                return float(numeric_token)
        
        return default
    except (ValueError, TypeError):
        return default


class BoundaryAwareExtractor:
    """
    Reusable boundary-aware field extraction framework for agricultural documents.
    Handles dense OCR text where multiple labeled fields may appear on the same line.
    """
    
    def __init__(self):
        # Field-specific stop tokens that define extraction boundaries
        self.field_stop_tokens = {
            'farmer_name': [
                'Farmer ID', 'Father', 'Spouse', 'Guardian', 'Mobile', 'Phone', 'Village', 'District',
                'Scheme', 'Aadhaar', 'Land', 'Area', 'Bank', 'Account', 'Season', 'Crop'
            ],
            'guardian_name': [
                'Mobile', 'Phone', 'Village', 'District', 'Scheme', 'Aadhaar', 'Land', 'Area', 'Bank'
            ],
            'aadhaar_number': [
                'Bank', 'Account', 'IFSC', 'Branch', 'Land', 'Area', 'Crop', 'Season', 'Village', 'District'
            ],
            'mobile_number': [
                'Village', 'District', 'Scheme', 'Aadhaar', 'Land', 'Area', 'Bank', 'Account'
            ],
            'village': [
                'District', 'State', 'Pin', 'Aadhaar', 'Land', 'Area', 'Crop', 'Season'
            ],
            'district': [
                'State', 'Pin', 'Aadhaar', 'Land', 'Area', 'Crop', 'Season', 'Village',
                'Scheme', 'Scheme Name', 'Government', 'Benefit'
            ],
            'land_size': [
                'Crop', 'Season', 'Scheme', 'Village', 'District', 'Aadhaar', 'Bank'
            ],
            'crop_type': [
                'Season', 'Scheme', 'Village', 'District', 'Land', 'Area', 'Aadhaar'
            ],
            'scheme_name': [
                'Amount', 'Claim', 'Type', 'Season', 'Land', 'Area', 'Village', 'District',
                'Requested', 'Benefit', 'Subsidy', 'Loan'
            ],
            'requested_amount': [
                'Season', 'Scheme', 'Land', 'Area', 'Crop', 'Village', 'District'
            ],
            'season': [
                'Crop', 'Scheme', 'Amount', 'Land', 'Area', 'Village', 'District'
            ]
        }
        
        # Common label variations for each field
        self.field_labels = {
            'farmer_name': ['Farmer Name', 'Applicant Name', 'Name', 'Applicant', 'Farmer'],
            'guardian_name': ['Father Name', 'Guardian Name', 'Spouse Name', 'Father/Spouse Name'],
            'aadhaar_number': ['Aadhaar', 'Aadhaar No', 'Aadhaar Number', 'UID', 'UID Number', 'Identity Number'],
            'mobile_number': ['Mobile', 'Mobile Number', 'Phone', 'Contact', 'Contact Number'],
            'village': ['Village', 'Village Name', 'Gram'],
            'district': ['District', 'District Name'],
            'land_size': ['Land Area', 'Land Size', 'Area', 'Total Land', 'Land Holding'],
            'crop_type': ['Crop', 'Crop Type', 'Cultivation', 'Agricultural Crop'],
            'scheme_name': ['Scheme', 'Scheme Name', 'Government Scheme', 'Benefit Scheme'],
            'requested_amount': ['Amount', 'Requested Amount', 'Benefit Amount', 'Subsidy Amount', 'Loan Amount'],
            'season': ['Season', 'Cropping Season', 'Kharif', 'Rabi', 'Zaid']
        }
    
    def extract_field_by_boundary(self, text: str, field_type: str, candidate_labels: Optional[List[str]] = None) -> Optional[str]:
        """
        Extract field value using boundary-aware parsing.
        
        Args:
            text: OCR text to search within
            field_type: Type of field being extracted (defines stop tokens)
            candidate_labels: Specific labels to look for (optional, uses defaults if None)
        
        Returns:
            Extracted field value or None if not found
        """
        if field_type not in self.field_stop_tokens:
            return None
        
        # Use provided labels or default labels for this field type
        labels = candidate_labels or self.field_labels.get(field_type, [])
        stop_tokens = self.field_stop_tokens[field_type]
        
        # Build stop pattern for boundary detection
        stop_pattern = '|'.join(re.escape(token) for token in stop_tokens)
        
        for label in labels:
            # Pattern: label + optional separator + value until stop token or end
            # Use word boundaries to avoid partial matches
            pattern = rf"\b{re.escape(label)}\b\s*[:\-]?\s*(.+?)(?=\s*\b(?:{stop_pattern})\b|\s*$|\s*\n)"
            
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                
                # Apply contamination guard
                cleaned_value = self._guard_against_contamination(value, field_type)
                if cleaned_value:
                    return cleaned_value
        
        return None
    
    def _guard_against_contamination(self, value: str, field_type: str) -> Optional[str]:
        """
        Guard against field contamination from neighboring labels.
        
        Args:
            value: Raw extracted value
            field_type: Type of field being extracted
        
        Returns:
            Cleaned value or None if contamination detected
        """
        if not value:
            return None
        
        # Check if value contains any stop tokens (indicates contamination)
        if field_type in self.field_stop_tokens:
            stop_tokens = self.field_stop_tokens[field_type]
            value_lower = value.lower()
            
            # Find earliest contamination point
            earliest_pos = len(value)
            for token in stop_tokens:
                token_lower = token.lower()
                pos = value_lower.find(token_lower)
                if pos >= 0 and pos < earliest_pos:
                    earliest_pos = pos
            
            # Truncate at earliest contamination point
            if earliest_pos < len(value):
                if earliest_pos > 0:
                    value = value[:earliest_pos].strip()
                else:
                    # Contamination at start - reject this extraction
                    return None
        
        # Additional field-specific contamination checks
        if field_type == 'aadhaar_number':
            # Aadhaar should not contain other numeric patterns
            if re.search(r'(bank|account|ifsc|branch|mobile|phone)', value, re.IGNORECASE):
                return None
        
        elif field_type == 'requested_amount':
            # Amount should not be just a year
            if re.match(r'^\s*(19|20)\d{2}\s*$', value):
                return None
        
        elif field_type in ['farmer_name', 'guardian_name']:
            # Names should not contain document headers or field labels
            if re.search(r'(application|form|scheme|department|office|farmer id|mobile|village|district)', value, re.IGNORECASE):
                return None
        
        elif field_type == 'crop_type':
            # Crop type should not contain field labels
            if re.search(r'(crop|type|season|scheme|village|district)', value, re.IGNORECASE):
                # Try to extract just the crop name - look for actual crop words
                # Common crop names that should be preserved
                crop_keywords = [
                    'wheat', 'rice', 'paddy', 'cotton', 'sugarcane', 'pulses', 'maize',
                    'bajra', 'jowar', 'ragi', 'gram', 'tur', 'urad', 'moong', 'masoor'
                ]
                
                words = value.split()
                for word in words:
                    word_clean = word.lower().strip(',:;')
                    if len(word_clean) > 2 and word_clean not in ['crop', 'type', 'season', 'scheme', 'village', 'district']:
                        # Check if it's a known crop or reasonable crop name
                        if word_clean in crop_keywords or len(word_clean) >= 4:
                            return word.title()
                return None
        
        # Clean up common prefixes that might remain
        value = re.sub(r'^(name|type|no|number)\s*[:\-]?\s*', '', value, flags=re.IGNORECASE)
        
        return value.strip()


class FieldValidators:
    """Reusable field-type validators for agricultural document extraction"""
    
    @staticmethod
    def validate_person_name(value: str) -> bool:
        """Validate person name field"""
        if not value or len(value.strip()) < 2:
            return False
        
        # Reject header/title pollution
        invalid_patterns = [
            'agriculture office', 'application form', 'sample document', 'intake testing',
            'smart agriculture', 'scheme application', 'form sample', 'department',
            'government', 'official', 'certificate'
        ]
        
        value_lower = value.lower()
        if any(pattern in value_lower for pattern in invalid_patterns):
            return False
        
        # Should contain at least 2 words OR be a reasonable single-word name
        words = value.split()
        if len(words) >= 2:
            return True
        elif len(words) == 1 and len(words[0]) >= 3 and words[0].replace('.', '').replace('-', '').isalpha():
            return True
        
        return False
    
    @staticmethod
    def validate_aadhaar_number(value: str) -> bool:
        """Validate Aadhaar number (12 digits)"""
        if not value:
            return False
        
        # Remove spaces and dashes
        clean_aadhaar = re.sub(r'[\s\-]', '', value)
        
        # Must be exactly 12 digits
        return len(clean_aadhaar) == 12 and clean_aadhaar.isdigit()
    
    @staticmethod
    def validate_mobile_number(value: str) -> bool:
        """Validate Indian mobile number"""
        if not value:
            return False
        
        # Remove spaces, dashes, parentheses
        clean_phone = re.sub(r'[\s\-\(\)]', '', value)
        
        # Should be 10 digits (may start with 0 for landline)
        if len(clean_phone) == 10 and clean_phone.isdigit() and clean_phone[0] in '6789':
            return True
        
        # May include +91 or 0 prefix
        if len(clean_phone) in [11, 12] and clean_phone[-10:].isdigit():
            return clean_phone[-10] in '6789'
        
        return False
    
    @staticmethod
    def validate_money_amount(value: str) -> bool:
        """Validate money amount field with strict rules to reject malformed values"""
        if not value:
            return False
        
        # Remove common formatting but preserve structure for validation
        clean_amount = re.sub(r'[\s₹$]', '', value)  # Remove spaces and currency symbols
        
        # Reject malformed comma patterns like "2,60" or "6,00"
        if ',' in clean_amount:
            # Only allow commas as thousand separators (groups of 3 digits from right)
            parts = clean_amount.split(',')
            if len(parts) > 1:
                # Check each part except the last one has exactly 3 digits
                for part in parts[:-1]:
                    if len(part) != 3 or not part.isdigit():
                        return False
                # Last part can have 1-3 digits
                if len(parts[-1]) == 0 or len(parts[-1]) > 3 or not parts[-1].isdigit():
                    return False
            else:
                return False  # Single comma with no digits after
        
        # Should be numeric with optional decimal
        if re.match(r'^\d+(\.\d{1,2})?$', clean_amount):
            try:
                amount = float(clean_amount)
                
                # Reject obvious years/IDs
                if 2000 <= amount <= 2030:
                    return False
                
                # Reject phone-like numbers (10 digits starting with 6-9)
                if clean_amount.isdigit() and len(clean_amount) == 10 and clean_amount.startswith(('6', '7', '8', '9')):
                    return False
                
                # Reject Aadhaar-like numbers (12 digits)
                if clean_amount.isdigit() and len(clean_amount) == 12:
                    return False
                
                # Reasonable range for agricultural amounts (1 to 10,00,000)
                return 1 <= amount <= 1000000
                
            except ValueError:
                return False
        
        return False
    
    @staticmethod
    def validate_land_size(value: str) -> bool:
        """Validate land size with units"""
        if not value:
            return False
        
        # Extract numeric part and unit
        land_match = re.match(r'^([0-9]+(?:\.[0-9]*)?)\s*([a-zA-Z\.]+)?', value.strip())
        if not land_match:
            return False
        
        number, unit = land_match.groups()
        
        # Validate numeric part
        try:
            size = float(number)
            if size <= 0 or size > 10000:  # Reasonable land size range
                return False
        except ValueError:
            return False
        
        # Validate unit
        unit = (unit or '').lower().replace('.', '').replace(' ', '')
        
        unit_mapping = {
            'acre': 'acre', 'acres': 'acre',
            'hectare': 'hectare', 'hectares': 'hectare',
            'bigha': 'bigha', 'bighas': 'bigha',
            'sqm': 'sqm', 'squaremeter': 'sqm', 'squaremeters': 'sqm'
        }
        
        return unit in unit_mapping or not unit  # Allow missing unit
    
    @staticmethod
    def validate_location(value: str) -> bool:
        """Validate village/district/location field"""
        if not value or len(value.strip()) < 2:
            return False
        
        # Should not be just numbers or special characters
        if re.match(r'^[0-9\s\-\.,]+$', value):
            return False
        
        # Should contain at least some alphabetic characters
        if not re.search(r'[a-zA-Z]', value):
            return False
        
        return True
    
    @staticmethod
    def validate_scheme_name(value: str) -> bool:
        """Validate scheme name field"""
        if not value or len(value.strip()) < 3:
            return False
        
        # Reject obvious document headers
        header_patterns = [
            'application form', 'scheme application', 'government scheme',
            'department of', 'ministry of', 'sample document'
        ]
        
        value_lower = value.lower()
        if any(pattern in value_lower for pattern in header_patterns):
            return False
        
        return True


class FieldNormalizers:
    """Reusable field normalizers for consistent data formatting"""
    
    @staticmethod
    def normalize_person_name(value: str) -> str:
        """Normalize person name field"""
        if not value:
            return value
        
        # Remove trailing identifiers
        value = re.sub(r'\s+(farmer\s+id|frm-[^\s]+).*$', '', value, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        # Title case for proper name formatting
        return value.title()
    
    @staticmethod
    def normalize_aadhaar(value: str) -> str:
        """Normalize Aadhaar number to readable format"""
        if not value:
            return value
        
        # Remove all non-digit characters
        clean_aadhaar = re.sub(r'[^\d]', '', value)
        
        # Format as XXXX XXXX XXXX if 12 digits
        if len(clean_aadhaar) == 12:
            return f"{clean_aadhaar[:4]} {clean_aadhaar[4:8]} {clean_aadhaar[8:12]}"
        
        return clean_aadhaar
    
    @staticmethod
    def normalize_mobile(value: str) -> str:
        """Normalize mobile number to 10-digit format"""
        if not value:
            return value
        
        # Remove all non-digit characters
        clean_phone = re.sub(r'[^\d]', '', value)
        
        # Take last 10 digits for mobile
        if len(clean_phone) >= 10:
            return clean_phone[-10:]
        
        return clean_phone
    
    @staticmethod
    def normalize_amount(value: str) -> str:
        """Normalize money amount to clean number with Indian format support"""
        if not value:
            return value
        
        # Remove currency labels more robustly
        clean_amount = value.strip()
        clean_amount = re.sub(r'\b(rs\.?|inr|rupee|rupees|₹)\b', '', clean_amount, flags=re.IGNORECASE)
        clean_amount = re.sub(r'^\.\s*', '', clean_amount)  # Remove any leading dots from currency removal
        
        # Handle Indian numbering format: 6,50,000 should become 650000
        # Indian format uses commas after every 2 digits after the first 3 digits
        # Simple approach: remove all commas and validate the result
        clean_amount_no_currency = re.sub(r'\b(rs\.?|inr|rupee|rupees|₹)\b', '', clean_amount, flags=re.IGNORECASE)
        clean_amount_no_currency = re.sub(r'^\.\s*', '', clean_amount_no_currency)
        
        # Remove all commas and check if result makes sense
        raw_number = clean_amount_no_currency.replace(',', '')
        
        # Validate that it's a proper number and reasonable length
        if re.match(r'^\d+$', raw_number) and len(raw_number) >= 3:
            # For Indian format validation, check if original had Indian-style commas
            # Indian format: 2,60,000 (2-digit groups after first 3)
            # Western format: 260,000 or 2,600,00 (3-digit groups)
            
            # If the cleaned number is much shorter than original, it was likely Indian format
            # that got truncated. Try to detect and fix this.
            original_length = len(clean_amount_no_currency.replace(',', ''))
            if len(raw_number) < original_length * 0.5:  # Significant truncation detected
                # This was likely Indian format that got truncated, 
                # but we can't recover the exact original. Return the best we can.
                pass  # Fall through to normal processing
            
            # Check if this looks like a valid amount (reasonable range)
            if len(raw_number) <= 7:  # Up to crores (10 million)
                return raw_number

        # For non-Indian format, just remove commas normally
        clean_amount = clean_amount.replace(',', '')
        clean_amount = re.sub(r'\s+', ' ', clean_amount)

        
        # Strip simple field labels if present at the start
        clean_amount = re.sub(r'^(amount|requested amount|subsidy amount|benefit amount|loan amount)\s*[:\-]?\s*', '', clean_amount, flags=re.IGNORECASE)
        
        # Extract the first valid numeric token
        match = re.search(r'-?\d+(?:\.\d+)?', clean_amount)
        if match:
            numeric_token = match.group(0)
            
            # Ensure proper decimal format
            if '.' in numeric_token:
                parts = numeric_token.split('.')
                if len(parts) == 2:
                    integer_part = parts[0]
                    decimal_part = parts[1][:2]  # Keep max 2 decimal places
                    return f"{integer_part}.{decimal_part}"
            
            return numeric_token
        
        # Return original value stripped if no valid numeric found
        return value.strip()
    
    @staticmethod
    def normalize_land_size(value: str) -> str:
        """Normalize land size to standard format"""
        if not value:
            return value
        
        # Extract numeric part and unit
        land_match = re.match(r'^([0-9]+(?:\.[0-9]*)?)\s*([a-zA-Z\.\s]+)?', value.strip())
        if not land_match:
            return value
        
        number, unit = land_match.groups()
        
        # Normalize unit
        unit = (unit or '').lower().replace('.', '').replace(' ', '')
        unit_mapping = {
            'acre': 'acre', 'acres': 'acre',
            'hectare': 'hectare', 'hectares': 'hectare',
            'bigha': 'bigha', 'bighas': 'bigha',
            'sqm': 'sqm', 'squaremeter': 'sqm', 'squaremeters': 'sqm'
        }
        
        normalized_unit = unit_mapping.get(unit, unit or 'acre')
        
        # Ensure proper decimal format - preserve integer-style formatting when possible
        try:
            size = float(number)
            # Preserve original formatting if it was an integer
            if '.' not in number:
                return f"{int(size)} {normalized_unit}"
            else:
                # Preserve decimal places from original input
                decimal_places = len(number.split('.')[1])
                return f"{size:.{decimal_places}f} {normalized_unit}"
        except ValueError:
            return value
    
    @staticmethod
    def normalize_location(value: str) -> str:
        """Normalize location (village/district) field"""
        if not value:
            return value
        
        # Only remove location labels in a safer targeted way
        # Remove labels at the beginning or end, not in the middle
        value = re.sub(r'^\s*(village|district|gram)\s*[:\-]?\s*', '', value, flags=re.IGNORECASE)
        value = re.sub(r'\s*[:\-]?\s*(village|district|gram)\s*$', '', value, flags=re.IGNORECASE)
        
        # Split by comma and remove duplicates while preserving order
        parts = [part.strip() for part in value.split(',')]
        unique_parts = []
        for part in parts:
            if part and part not in unique_parts:
                unique_parts.append(part)
        
        return ', '.join(unique_parts)
    
    @staticmethod
    def normalize_scheme_name(value: str) -> str:
        """Normalize scheme name field"""
        if not value:
            return value
        
        # Remove common prefixes
        value = re.sub(r'^(scheme|scheme name|government scheme)\s*[:\-]?\s*', '', value, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        # Title case for proper formatting
        return value.title()
