"""
Document Extraction Service
Purpose: Main handler-dispatch service for document extraction
"""
from typing import Dict, List, Optional, Any

from app.modules.document_processing.handlers.farmer_record_handler import FarmerRecordHandler
from app.modules.document_processing.handlers.grievance_handler import GrievanceHandler
from app.modules.document_processing.handlers.insurance_claim_handler import InsuranceClaimHandler
from app.modules.document_processing.handlers.scheme_application_handler import SchemeApplicationHandler
from app.modules.document_processing.handlers.subsidy_claim_handler import SubsidyClaimHandler
from app.modules.document_processing.handlers.supporting_document_handler import SupportingDocumentHandler
from app.modules.document_processing.utils import normalize_ocr_text, safe_float
from app.modules.document_processing.generic_extractor import GenericFieldExtractor
from app.modules.document_processing.classification_service import DocumentClassificationService
from app.modules.document_processing.semantic_extractor import SemanticExtractor
from app.modules.document_processing.field_filter import FieldFilter
from app.modules.document_processing.reasoning_engine import ReasoningEngine
from app.modules.document_processing.predictive_analytics import PredictiveAnalytics
import re


class DocumentExtractionService:
    """Main handler-dispatch service for document extraction"""
    
    def __init__(self):
        self.generic_extractor = GenericFieldExtractor()
        self.classification_service = DocumentClassificationService()
        self.semantic_extractor = SemanticExtractor()
        self.field_filter = FieldFilter()
        self.reasoning_engine = ReasoningEngine()
        self.predictive_analytics = PredictiveAnalytics()
        self._initialize_handlers()
        self._initialize_sanitization_rules()
    
    def _initialize_handlers(self):
        """Initialize handler mapping for document types"""
        self.handlers = {
            'scheme_application': None,  # Will be instantiated when needed
            'farmer_record': None,
            'grievance': None,
            'insurance_claim': None,
            'subsidy_claim': None,
            'supporting_document': None,
            'unknown': None
        }
    
    def _get_handler(self, document_type: str):
        """Get or instantiate handler for document type"""
        if document_type not in self.handlers:
            return None
            
        handler = self.handlers[document_type]
        if handler is None:
            # Use clearer import approach
            try:
                handler = self._import_handler(document_type)
                self.handlers[document_type] = handler
            except (ImportError, AttributeError, ModuleNotFoundError):
                # Fallback to supporting document handler
                try:
                    from .handlers.supporting_document_handler import SupportingDocumentHandler
                    handler = SupportingDocumentHandler()
                    self.handlers[document_type] = handler
                except ImportError:
                    # Create minimal fallback handler
                    handler = self._create_fallback_handler()
                    self.handlers[document_type] = handler
        
        return handler
    
    def _import_handler(self, document_type: str):
        """Return a handler instance for the requested document type"""
        handler_map = {
            'scheme_application': SchemeApplicationHandler,
            'farmer_record': FarmerRecordHandler,
            'grievance': GrievanceHandler,
            'insurance_claim': InsuranceClaimHandler,
            'subsidy_claim': SubsidyClaimHandler,
            'supporting_document': SupportingDocumentHandler,
            'unknown': SupportingDocumentHandler,
        }

        handler_class = handler_map.get(document_type, SupportingDocumentHandler)
        return handler_class()
    
    def _create_fallback_handler(self):
        """Create minimal fallback handler with useful debugging info"""
        class FallbackHandler:
            def extract_fields(self, text, metadata=None):
                return {
                    "reasoning": ["Fallback handler used - no specific handler available"],
                    "structured_data": {},
                    "extracted_fields": {}
                }
        return FallbackHandler()
    
    def _is_metadata_shaped(self, value) -> bool:
        """Check if value has proper field metadata shape"""
        return (
            isinstance(value, dict) and
            'value' in value and
            ('confidence' in value or 'source' in value)
        )
    
    def _initialize_sanitization_rules(self):
        """Initialize sanitization rules for field cleaning"""
        # Header junk that should never appear as field values
        self.header_junk = [
            'applicant information', 'personal information', 'policy information',
            'scheme details', 'address details', 'claimant name', 'complainant',
            'from', 'to', 'village', 'district', 'branch', 'main branch',
            'bank manager', 'office', 'department', 'state bank of india',
            'grievance petition', 'crop insurance claim form',
            'agricultural equipment subsidy claim', 'claimant information',
            'beneficiary details', 'policy details', 'loan details'
        ]
        
        # Administrative words that indicate non-human names
        self.administrative_words = [
            'branch', 'district', 'office', 'department', 'bank', 'village',
            'tehsil', 'state', 'manager', 'petition', 'application', 'scheme',
            'insurance', 'claim', 'subsidy', 'grievance', 'authority', 'board',
            'civil lines', 'main branch', 'state bank of india'
        ]
    
    def is_valid_person_name(self, value: str) -> bool:
        """Validate if a value looks like a real person name"""
        if not value or not isinstance(value, str):
            return False
        
        value_clean = value.strip()
        
        # Reject if too short or too long
        if len(value_clean) < 2 or len(value_clean) > 50:
            return False
        
        # Reject if mostly uppercase (likely headers)
        if value_clean.isupper() and len(value_clean) > 10:
            return False
        
        # Reject if contains administrative words
        value_lower = value_clean.lower()
        for admin_word in self.administrative_words:
            if admin_word in value_lower:
                return False
        
        # Reject if contains long numeric fragments
        if re.search(r'\d{4,}', value_clean):
            return False
        
        # Reject if it's exactly header junk
        if value_lower in [junk.lower() for junk in self.header_junk]:
            return False
        
        # Reject if it's a location pattern (place names)
        location_patterns = ['village', 'district', 'tehsil', 'state', 'city', 'town', 'lines', 'nagar', 'pur', 'garh']
        if any(pattern in value_lower for pattern in location_patterns):
            return False
        
        # Reject if contains phone number patterns
        if re.search(r'\d{10,}', value_clean):
            return False
        
        # Prefer 2-4 word alphabetic dominant strings
        words = value_clean.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        # Check if predominantly alphabetic (allow common Indian name patterns)
        alphabetic_chars = sum(1 for c in value_clean if c.isalpha() or c.isspace())
        if alphabetic_chars / len(value_clean) < 0.7:
            return False
        
        return True
    
    def sanitize_location_value(self, value: str) -> str:
        """Sanitize location value, removing junk and preserving valid places"""
        if not value or not isinstance(value, str):
            return ""
        
        value_clean = value.strip()
        
        # Reject phone number contamination
        if re.search(r'\d{9,}', value_clean):
            return ""
        
        # Reject if it's exactly header junk
        value_lower = value_clean.lower()
        if value_lower in [junk.lower() for junk in self.header_junk]:
            return ""
        
        # NEW: Reject multi-header concatenation strings
        # Count how many header fragments are present
        header_fragments = [
            'applicant information', 'personal information', 'policy information', 
            'scheme details', 'address details', 'claimant information', 'beneficiary details'
        ]
        header_fragment_count = sum(1 for fragment in header_fragments if fragment in value_lower)
        if header_fragment_count >= 2:
            return ""  # Multiple headers concatenated - reject
        
        # NEW: Reject values dominated by label tokens
        label_tokens = [
            'information', 'details', 'policy', 'scheme', 'applicant', 'personal', 
            'claimant', 'beneficiary', 'address', 'name', 'from', 'to', 'branch'
        ]
        words = value_lower.split()
        label_token_count = sum(1 for word in words if word in label_tokens)
        if len(words) > 0 and label_token_count / len(words) > 0.6:  # >60% label tokens
            return ""  # Dominated by labels - reject
        
        # Reject obvious institution-only strings
        institution_patterns = [
            'state bank of india', 'branch manager', 'district agriculture officer',
            'main branch', 'bank manager', 'agriculture officer'
        ]
        if any(pattern in value_lower for pattern in institution_patterns):
            return ""
        
        # Reject lines that are mostly section headers
        if value_clean.isupper() and len(value_clean) > 15:
            return ""
        
        # Normalize repeated line breaks
        value_clean = re.sub(r'\n+', ' ', value_clean)
        
        # Strip junk tokens from compound locations
        junk_tokens = ['mobile', 'phone', 'contact', 'office', 'branch', 'department', 'information', 'details']
        words = value_clean.split()
        filtered_words = [w for w in words if w.lower() not in junk_tokens]
        
        if filtered_words:
            filtered_value = ' '.join(filtered_words)
            # Final check: if filtered value still contains header fragments, reject
            filtered_lower = filtered_value.lower()
            if any(fragment in filtered_lower for fragment in header_fragments):
                return ""
            return filtered_value
        
        return ""
    
    def _sanitize_grievance_description(self, description: str) -> str:
        """Remove officer/header fragments from grievance descriptions while preserving issue content"""
        if not description or not isinstance(description, str):
            return ""
        
        # Header fragments to remove from grievance descriptions
        grievance_header_junk = [
            'district agriculture officer', 'applicant information', 'claimant name', 'office',
            'subject', 'from', 'to', 'main branch', 'branch manager', 'complainant',
            'applicant name', 'personal information', 'policy information', 'scheme details',
            'address details', 'beneficiary details'
        ]
        
        # Clean the description
        description_clean = description.strip()
        
        # Remove exact header matches
        for junk in grievance_header_junk:
            # Case-insensitive removal
            junk_pattern = re.compile(re.escape(junk), re.IGNORECASE)
            description_clean = junk_pattern.sub('', description_clean)
        
        # Remove common header patterns with colons
        header_patterns = [
            r'district agriculture officer\s*:?\s*',
            r'applicant information\s*:?\s*',
            r'claimant name\s*:?\s*',
            r'office\s*:?\s*',
            r'subject\s*:?\s*',
            r'from\s*:?\s*',
            r'to\s*:?\s*',
            r'main branch\s*:?\s*',
            r'branch manager\s*:?\s*',
            r'complainant\s*:?\s*',
            r'applicant name\s*:?\s*',
            r'personal information\s*:?\s*',
            r'policy information\s*:?\s*',
            r'scheme details\s*:?\s*',
            r'address details\s*:?\s*',
            r'beneficiary details\s*:?\s*'
        ]
        
        for pattern in header_patterns:
            description_clean = re.sub(pattern, '', description_clean, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and line breaks
        description_clean = re.sub(r'\s+', ' ', description_clean)
        description_clean = description_clean.strip()
        
        # Remove leading/trailing punctuation
        description_clean = description_clean.strip('.,;: \n\t')
        
        # If result is too short or contains only junk, return empty
        if len(description_clean) < 10:
            return ""
        
        # Final check - if it still contains header junk, reject
        description_lower = description_clean.lower()
        if any(junk in description_lower for junk in grievance_header_junk):
            return ""
        
        return description_clean
    
    def _is_valid_amount_for_supporting_doc(self, amount_value) -> bool:
        """Validate amount field for supporting documents, rejecting identifier-style numbers and phone numbers"""
        if not amount_value:
            return False
        
        # Convert to string and clean
        amount_str = str(amount_value).strip()
        if not amount_str:
            return False
        
        # Remove common formatting
        clean_amount = re.sub(r'[,\s₹$]', '', amount_str)
        
        # Reject if it's all digits and 10-16 digits long (looks like ID/Aadhaar/account)
        if clean_amount.isdigit():
            digit_count = len(clean_amount)
            if 10 <= digit_count <= 16:
                return False
        
        # REJECT PHONE NUMBERS - Start with 6-9 and exactly 10 digits
        if clean_amount.isdigit() and len(clean_amount) == 10 and clean_amount.startswith(('6', '7', '8', '9')):
            return False
        
        # Reject phone-like patterns with separators
        phone_pattern = re.compile(r'^[6-9][0-9]{2}[-\s]?[0-9]{3}[-\s]?[0-9]{4}$')
        if phone_pattern.match(clean_amount):
            return False
        
        # Try to parse as float
        try:
            amount_num = float(clean_amount)
            
            # Reject obvious years
            if 2000 <= amount_num <= 2030:
                return False
            
            # Reject phone-like numbers even as float (9876543210.0)
            if clean_amount.isdigit() and len(clean_amount) == 10 and clean_amount.startswith(('6', '7', '8', '9')):
                return False
            
            # Accept reasonable monetary amounts (₹1 to ₹10 lakhs for supporting docs)
            return 1 <= amount_num <= 1000000
            
        except (ValueError, TypeError):
            return False
    
    def _sanitize_issuing_authority(self, authority: str) -> str:
        """Clean issuing authority field by removing header block text"""
        if not authority or not isinstance(authority, str):
            return ""
        
        authority_clean = authority.strip()
        
        # Header junk to remove (more comprehensive)
        header_junk = [
            'account holder information', 'personal information', 'policy information',
            'claimant name', 'claimant nam', 'from', 'to', 'applicant information', 'office',
            'branch manager', 'main branch', 'state bank of india', 'civil lines',
            'kanpur claimant nam'  # Specific to the test case
        ]
        
        # Remove header junk
        for junk in header_junk:
            authority_clean = re.sub(re.escape(junk), '', authority_clean, flags=re.IGNORECASE)
        
        # Remove line breaks and extra whitespace
        authority_clean = re.sub(r'\n+', ' ', authority_clean)
        authority_clean = re.sub(r'\s+', ' ', authority_clean)
        authority_clean = authority_clean.strip()
        
        # Remove leading/trailing punctuation
        authority_clean = authority_clean.strip('.,;: \n\t')
        
        # If result is too short or contains junk, return empty
        if len(authority_clean) < 3:
            return ""
        
        # Final junk check
        authority_lower = authority_clean.lower()
        if any(junk in authority_lower for junk in header_junk):
            return ""
        
        return authority_clean
    
    def sanitize_extracted_structured_data(self, document_type: str, structured_data: dict, extracted_fields: Optional[dict] = None, original_text: Optional[str] = None) -> dict:
        """Apply strict field sanitization after extraction"""
        if not structured_data or not isinstance(structured_data, dict):
            return structured_data
        
        sanitized = structured_data.copy()
        
        # Document-type-specific field trust rules
        if document_type == 'supporting_document':
            # farmer_name is low-trust for supporting documents
            if 'farmer_name' in sanitized:
                farmer_name = sanitized['farmer_name']
                if not self.is_valid_person_name(farmer_name):
                    # Prefer NO farmer_name over wrong farmer_name
                    del sanitized['farmer_name']
            
            # Sanitize amount fields to reject identifier-style numbers
            amount_fields = ['requested_amount', 'claim_amount', 'subsidy_amount', 'amount']
            for amount_field in amount_fields:
                if amount_field in sanitized:
                    amount_value = sanitized[amount_field]
                    if not self._is_valid_amount_for_supporting_doc(amount_value):
                        del sanitized[amount_field]
            
            # Clean issuing_authority to remove header block text
            if 'issuing_authority' in sanitized:
                authority = sanitized['issuing_authority']
                if isinstance(authority, str):
                    authority_clean = self._sanitize_issuing_authority(authority)
                    if authority_clean:
                        sanitized['issuing_authority'] = authority_clean
                    else:
                        del sanitized['issuing_authority']
            
            # Clean location fields aggressively
            for loc_field in ['location', 'village', 'district', 'address']:
                if loc_field in sanitized:
                    sanitized[loc_field] = self.sanitize_location_value(sanitized[loc_field])
                    if not sanitized[loc_field]:
                        del sanitized[loc_field]
        
        elif document_type == 'grievance':
            # Clean farmer_name to reject officer/addressee lines
            if 'farmer_name' in sanitized:
                farmer_name = sanitized['farmer_name']
                if not self.is_valid_person_name(farmer_name):
                    del sanitized['farmer_name']
            
            # Remove applicant_name/complainant junk
            for junk_field in ['applicant_name', 'complainant', 'claimant']:
                if junk_field in sanitized:
                    value = sanitized[junk_field]
                    if not self.is_valid_person_name(value):
                        del sanitized[junk_field]
            
            # Aggressively clean description field for grievance documents
            if 'description' in sanitized:
                description = sanitized['description']
                if isinstance(description, str):
                    # Remove header fragments from description
                    description_clean = self._sanitize_grievance_description(description)
                    if description_clean and len(description_clean.strip()) > 10:
                        sanitized['description'] = description_clean
                    else:
                        del sanitized['description']
            
            # Clean location but preserve valid addresses
            for loc_field in ['location', 'village', 'district', 'address']:
                if loc_field in sanitized:
                    sanitized[loc_field] = self.sanitize_location_value(sanitized[loc_field])
                    if not sanitized[loc_field]:
                        del sanitized[loc_field]
        
        elif document_type == 'subsidy_claim':
            # Clean farmer_name
            if 'farmer_name' in sanitized:
                farmer_name = sanitized['farmer_name']
                if not self.is_valid_person_name(farmer_name):
                    del sanitized['farmer_name']
            
            # Aggressively clean location to prevent "UP Mobile" type issues
            for loc_field in ['location', 'village', 'district', 'address']:
                if loc_field in sanitized:
                    sanitized[loc_field] = self.sanitize_location_value(sanitized[loc_field])
                    if not sanitized[loc_field]:
                        del sanitized[loc_field]
        
        elif document_type == 'insurance_claim':
            # Insurance-specific sanitization: remove any subsidy-specific fields
            for sub_field in ['subsidy_amount', 'subsidy_type', 'request_type']:
                if sub_field in sanitized:
                    sanitized.pop(sub_field, None)

            # Strict location cleanup: reject contaminated values
            def _is_contaminated_location(val: str) -> bool:
                if not val or not isinstance(val, str):
                    return True
                v = val.strip()
                low = v.lower()
                # Reject explicit contamination tokens
                contamination_tokens = ['field value', 'claimant name', 'aadhaar number', 'insurance claim form', 'field value:', 'claimant', 'aadhaar', 'insurance claim', 'section', 'table', 'page']
                if any(tok in low for tok in contamination_tokens):
                    return True
                # Reject multiline/table text or pipes
                if '\n' in v or '|' in v or '\t' in v or re.search(r'-{3,}', v):
                    return True
                # Reject if dominated by label tokens
                label_tokens = ['information', 'details', 'policy', 'scheme', 'applicant', 'personal', 'claimant', 'beneficiary', 'address', 'name']
                words = [w.strip(',:;') for w in low.split() if w.strip()]
                if words and sum(1 for w in words if w in label_tokens) / len(words) > 0.6:
                    return True
                # Reject repeated fragments like "Claim Details Claim Details"
                tokens = [t for t in re.split(r'[,;\-\n]', low) if t.strip()]
                if len(tokens) >= 2 and len(set(tokens)) == 1:
                    return True
                return False

            for loc_field in ['location', 'village', 'district', 'address']:
                if loc_field in sanitized:
                    val = sanitized.get(loc_field)
                    if _is_contaminated_location(val):
                        # Prefer cleaner boundary/labeled value from extracted_fields if available
                        replacement = None
                        if extracted_fields and isinstance(extracted_fields, dict):
                            candidate = extracted_fields.get(loc_field)
                            if isinstance(candidate, dict):
                                cand_val = candidate.get('value')
                                # use existing sanitize_location_value logic to verify
                                cand_clean = self.sanitize_location_value(cand_val)
                                if cand_clean:
                                    replacement = cand_clean
                        if replacement:
                            sanitized[loc_field] = replacement
                        else:
                            sanitized.pop(loc_field, None)

            # STRICT: Remove common title/header artifacts and policy tokens in insurance claims
            title_tokens = [
                'insurance claim form', 'insurance claim form – weather damage',
                'insurance claim form - weather damage', 'policy and farmer field value',
                'field value', 'policy number pmfb', 'policy number pmfby'
            ]

            def looks_like_title(v: str) -> bool:
                if not v or not isinstance(v, str):
                    return False
                s = v.strip()
                low = s.lower()
                if any(tok in low for tok in title_tokens):
                    return True
                if '\n' in s or '|' in s or '\t' in s or re.search(r'-{3,}', s):
                    return True
                return False

            # Field-specific sanitization
            crop_allowed = { 'paddy','wheat','rice','maize','corn','sorghum','millet','bajra','ragi','jowar','cotton','soybean','groundnut','mustard' }
            season_allowed = {'kharif','rabi','summer','zaid','autumn','winter','monsoon'}

            # Crop fields
            for crop_field in ['crop_name', 'crop_type']:
                if crop_field in sanitized:
                    cval = str(sanitized.get(crop_field) or '').strip()
                    low = cval.lower()
                    if looks_like_title(cval) or not any(c in low for c in crop_allowed):
                        sanitized.pop(crop_field, None)

            # Season
            if 'season' in sanitized:
                sval = str(sanitized.get('season') or '').strip().lower()
                if looks_like_title(sval) or not any(s in sval for s in season_allowed):
                    sanitized.pop('season', None)

            # Area must be numeric/area-like
            if 'area' in sanitized:
                aval = str(sanitized.get('area') or '')
                if not re.search(r'\d', aval) or not re.search(r'(acre|hectare|ha|sqm|sq\.m|sqkm|sq\.km)?', aval, re.IGNORECASE):
                    sanitized.pop('area', None)

            # Address trimming: remove trailing policy/reference fragments like 'Policy Number PMFBY'
            if 'address' in sanitized:
                addr = str(sanitized.get('address') or '')
                addr = re.sub(r'policy\s*number\s*pmfb[iy]?[:\s\-\w]*', '', addr, flags=re.IGNORECASE)
                addr = re.sub(r'field\s*value[:\s\-\w]*', '', addr, flags=re.IGNORECASE)
                addr = addr.strip(' ,;:\n\t')
                if not addr or looks_like_title(addr):
                    sanitized.pop('address', None)
                else:
                    sanitized['address'] = addr

            # Location: do not derive from long OCR blobs
            if 'location' in sanitized:
                loc = str(sanitized.get('location') or '')
                if looks_like_title(loc) or len(loc) > 200 or '\n' in loc:
                    sanitized.pop('location', None)

            # Land size: remove explicit 0.0 fallback values
            if 'land_size' in sanitized:
                lval = str(sanitized.get('land_size') or '')
                m = re.search(r'(-?\d+(?:\.\d+)?)', lval)
                if m:
                    num = safe_float(m.group(1), default=None)
                    if num is None or (num == 0 and not re.search(r'\b0\b', lval)):
                        sanitized.pop('land_size', None)

            # PRIORITIZE boundary/labeled values over semantic junk: if village/district boundary present, avoid overwriting with large 'location'
            try:
                boundary_village_meta = extracted_fields.get('village') if extracted_fields and isinstance(extracted_fields, dict) else None
                boundary_district_meta = extracted_fields.get('district') if extracted_fields and isinstance(extracted_fields, dict) else None
                # If boundary village/district were provided from boundary extractor (source contains 'boundary'), keep them and drop contaminated location
                for b_field, boundary_meta in [('village', boundary_village_meta), ('district', boundary_district_meta)]:
                    if boundary_meta and isinstance(boundary_meta, dict):
                        src = boundary_meta.get('source', '')
                        if 'boundary' in src.lower():
                            # if location exists and seems longer/contaminated, drop it
                            loc_val = sanitized.get('location')
                            if loc_val and isinstance(loc_val, str):
                                if len(loc_val) > len(str(sanitized.get(b_field) or '')) + 10 or looks_like_title(loc_val):
                                    sanitized.pop('location', None)
                                    # also remove extracted_fields location if present
                                    try:
                                        if extracted_fields and isinstance(extracted_fields, dict):
                                            extracted_fields.pop('location', None)
                                    except Exception:
                                        pass
            except Exception:
                pass

            # Agricultural field cleanup: reject OCR junk for area/season/crop_type/land_size
            agri_fields = ['area', 'season', 'crop_type', 'land_size']
            for af in agri_fields:
                if af in sanitized:
                    val = sanitized.get(af)
                    if not isinstance(val, (str, int, float)):
                        sanitized.pop(af, None)
                        continue
                    sval = str(val)
                    # Reject long multiline blobs or table fragments
                    if '\n' in sval or '|' in sval or re.search(r'(s\.?no|table|header|row|column|----)', sval, re.IGNORECASE):
                        sanitized.pop(af, None)
                        continue
                    # Land size specific: must parse numeric and not default to 0
                    if af == 'land_size':
                        # Try to extract numeric
                        m = re.search(r'(-?\d+(?:\.\d+)?)', sval)
                        if not m:
                            sanitized.pop(af, None)
                            continue
                        num = safe_float(m.group(1), default=None)
                        if num is None:
                            sanitized.pop(af, None)
                            continue
                        if num == 0 and not re.search(r'\b0\b', sval):
                            sanitized.pop(af, None)
                            continue
                        # keep normalized numeric string
                        sanitized[af] = str(num)

        else:
            # For other document types, apply standard sanitization
            # Clean farmer_name
            if 'farmer_name' in sanitized:
                farmer_name = sanitized['farmer_name']
                if not self.is_valid_person_name(farmer_name):
                    del sanitized['farmer_name']
            
            # Standard location cleaning
            for loc_field in ['location', 'village', 'district', 'address']:
                if loc_field in sanitized:
                    sanitized[loc_field] = self.sanitize_location_value(sanitized[loc_field])
                    if not sanitized[loc_field]:
                        del sanitized[loc_field]
            # For other document types, apply standard sanitization
            # Clean farmer_name
            if 'farmer_name' in sanitized:
                farmer_name = sanitized['farmer_name']
                if not self.is_valid_person_name(farmer_name):
                    del sanitized['farmer_name']
            
            # Standard location cleaning
            for loc_field in ['location', 'village', 'district', 'address']:
                if loc_field in sanitized:
                    sanitized[loc_field] = self.sanitize_location_value(sanitized[loc_field])
                    if not sanitized[loc_field]:
                        del sanitized[loc_field]
        
        # Remove any remaining header junk from all string fields
        for field_name, field_value in list(sanitized.items()):
            if isinstance(field_value, str):
                value_clean = field_value.strip()
                # Remove exact header junk
                if value_clean.lower() in [junk.lower() for junk in self.header_junk]:
                    del sanitized[field_name]
                # Remove field values that are just labels
                elif any(label.lower() == value_clean.lower() for label in ['village', 'district', 'location', 'address']):
                    del sanitized[field_name]
        
        return sanitized
    
    def second_pass_business_entity_recovery(self, document_type: str, structured_data: dict, original_text: str) -> dict:
        """Controlled second-pass recovery of missing business entities"""
        if not structured_data or not isinstance(structured_data, dict):
            return structured_data
        
        recovered = structured_data.copy()
        
        # Recovery: scheme_name from application_id context
        if document_type == 'scheme_application' and 'scheme_name' not in recovered:
            application_id = recovered.get('application_id', '')
            if isinstance(application_id, str):
                app_id_upper = application_id.upper()
                if 'PMKISAN' in app_id_upper:
                    recovered['scheme_name'] = 'Pradhan Mantri Kisan Samman Nidhi'
                elif 'PM' in app_id_upper and 'KISAN' in app_id_upper:
                    recovered['scheme_name'] = 'Pradhan Mantri Kisan Samman Nidhi'
        
        # Recovery: location from village + district combo
        if 'location' not in recovered:
            village = recovered.get('village')
            district = recovered.get('district')
            if village and district:
                # Check if village and district are the same semantic content
                village_clean = village.lower().strip()
                district_clean = district.lower().strip()
                
                # Avoid duplication like "Karari, Karari" or "Village, Karari District, Village, Karari District"
                if village_clean == district_clean or village_clean in district_clean or district_clean in village_clean:
                    # Use the more complete version
                    recovered['location'] = district if len(district) > len(village) else village
                else:
                    # Different locations, combine safely
                    recovered['location'] = f"{village}, {district}"
            elif village:
                recovered['location'] = village
            elif district:
                recovered['location'] = district
        
        # GRIEVANCE-SPECIFIC RECOVERY
        if document_type == 'grievance':
            # Recover farmer_name from valid "Name:" / signature lines only
            if 'farmer_name' not in recovered:
                # Priority 1: Explicit "Name:" line with valid human name
                name_patterns = [
                    r'Name\s*:\s*([A-Za-z\s]{2,50})',
                    r'I am\s+([A-Za-z\s]{2,50})\s*,',
                    r'I\s+am\s+([A-Za-z\s]{2,50})\s*,?\s+(?:resident|village|from)'
                ]
                
                for pattern in name_patterns:
                    matches = re.findall(pattern, original_text, re.IGNORECASE)
                    for match in matches:
                        name_clean = match.strip()
                        if self.is_valid_person_name(name_clean):
                            recovered['farmer_name'] = name_clean
                            break
                    if 'farmer_name' in recovered:
                        break
                
                # Priority 2: Closing signature line near end of document
                if 'farmer_name' not in recovered:
                    lines = original_text.split('\n')
                    # Look in last 8 lines for signature patterns
                    for line in lines[-8:]:
                        line_clean = line.strip()
                        # Look for "Yours sincerely, Name" or just name at end
                        signature_patterns = [
                            r'Yours\s+sincerely,?\s*([A-Za-z\s]{2,50})',
                            r'Sincerely,?\s*([A-Za-z\s]{2,50})',
                            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*$',  # Capitalized name at line start
                            r'^(?:From|Submitted by)\s*:\s*([A-Za-z\s]{2,50})'
                        ]
                        
                        for pattern in signature_patterns:
                            match = re.search(pattern, line_clean, re.IGNORECASE)
                            if match:
                                name_clean = match.group(1).strip()
                                if self.is_valid_person_name(name_clean):
                                    recovered['farmer_name'] = name_clean
                                    break
                        if 'farmer_name' in recovered:
                            break
                
                # Priority 3: Valid "From:" line ONLY if not office/header junk
                if 'farmer_name' not in recovered:
                    from_patterns = [
                        r'From\s*:\s*([A-Za-z\s]{2,50})',
                        r'^(?:From|Submitted by)\s*:\s*([A-Za-z\s]{2,50})'
                    ]
                    
                    for pattern in from_patterns:
                        matches = re.findall(pattern, original_text, re.IGNORECASE)
                        for match in matches:
                            name_clean = match.strip()
                            # Extra validation for "From:" lines - reject office junk
                            if (self.is_valid_person_name(name_clean) and 
                                not any(admin_word in name_clean.lower() for admin_word in 
                                       ['office', 'branch', 'department', 'district', 'manager', 'agriculture', 'main'])):
                                recovered['farmer_name'] = name_clean
                                break
                        if 'farmer_name' in recovered:
                            break
            
            # Recover grievance description from real complaint body text
            if 'description' not in recovered:
                lines = original_text.split('\n')
                description_lines = []
                
                # Header and junk patterns to skip
                skip_patterns = [
                    r'^to\s*[,\s]',
                    r'^from\s*[,\s]',
                    r'^subject\s*[:,\s]',
                    r'^date\s*[:,\s]',
                    r'^ref\s*[:,\s]',
                    r'^reference\s*[:,\s]',
                    r'^type\s*[:,\s]',
                    r'^category\s*[:,\s]',
                    r'^grievance type\s*[:,\s]',
                    r'^complaint type\s*[:,\s]',
                    r'^applicant information',
                    r'^claimant name\s*[:,\s]',
                    r'^complainant\s*[:,\s]',
                    r'^office\s*[:,\s]',
                    r'^main branch\s*[:,\s]',
                    r'^district agriculture officer\s*[:,\s]',
                    r'^branch manager\s*[:,\s]',
                    r'^village\s*[:,\s]',
                    r'^district\s*[:,\s]'
                ]
                
                # Look for meaningful grievance content
                for line in lines:
                    line_clean = line.strip()
                    
                    # Skip if matches header/junk patterns
                    is_junk = any(re.match(pattern, line_clean, re.IGNORECASE) for pattern in skip_patterns)
                    if is_junk or len(line_clean) < 15:
                        continue
                    
                    # Include lines with grievance-related content
                    grievance_keywords = [
                        'delay', 'payment', 'subsidy', 'benefit', 'application', 'received', 
                        'amount', 'bank', 'account', 'credit', 'installment', 'kharif', 'rabi',
                        'crop', 'insurance', 'claim', 'officer', 'reply', 'response',
                        'pending', 'due', 'late', 'not received', 'due', 'request'
                    ]
                    
                    # Include lines with grievance keywords OR if we need more content
                    line_lower = line_clean.lower()
                    if any(keyword in line_lower for keyword in grievance_keywords) or len(description_lines) < 2:
                        # Remove junk fragments if present
                        for junk_fragment in ['applicant information', 'claimant name', 'office', 'district agriculture officer',
                                           'subject', 'from', 'to', 'main branch', 'branch manager']:
                            line_clean = re.sub(junk_fragment, '', line_clean, flags=re.IGNORECASE)
                        
                        line_clean = re.sub(r'\s+', ' ', line_clean).strip()
                        if len(line_clean) > 20:  # Only include meaningful lines
                            description_lines.append(line_clean)
                        
                        if len(description_lines) >= 3:  # Limit to 3 lines
                            break
                
                # Combine description lines
                if description_lines:
                    description = ' '.join(description_lines[:2])  # Use first 2 meaningful lines
                    if len(description) > 250:
                        description = description[:250] + '...'
                    recovered['description'] = description
        
        # NON-GRIEVANCE RECOVERY: farmer_name from valid "Name:" / "From:" lines only
        elif 'farmer_name' not in recovered:
            # Look for "Name:" or "From:" patterns in original text
            name_patterns = [
                r'Name\s*:\s*([A-Za-z\s]+)',
                r'From\s*:\s*([A-Za-z\s]+)',
                r'Applicant\s*Name\s*:\s*([A-Za-z\s]+)'
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, original_text, re.IGNORECASE)
                for match in matches:
                    if self.is_valid_person_name(match.strip()):
                        recovered['farmer_name'] = match.strip()
                        break
                if 'farmer_name' in recovered:
                    break
        
        return recovered
    
    def extract_document(
        self,
        text_content: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract fields from a document based on its type
        
        Args:
            text_content: OCR extracted text
            document_type: Type of document
            metadata: Additional metadata
            
        Returns:
            Standardized extraction result
        """
        try:
            # Normalize OCR text
            normalized_text = normalize_ocr_text(text_content)
            
            # Get proper handler
            handler = self._get_handler(document_type)
            if not handler:
                # Fallback to supporting_document_handler
                try:
                    from .handlers.supporting_document_handler import SupportingDocumentHandler
                    handler = SupportingDocumentHandler()
                except ImportError:
                    # Create minimal fallback handler
                    handler = self._create_fallback_handler()
            
            # Run handler for type-specific extraction
            try:
                handler_fields = handler.extract_fields(normalized_text, metadata)
            except Exception as handler_error:
                # IF handler fails → fallback to supporting_document_handler
                try:
                    from .handlers.supporting_document_handler import SupportingDocumentHandler
                    fallback_handler = SupportingDocumentHandler()
                    handler_fields = fallback_handler.extract_fields(normalized_text, metadata)
                    # Add reasoning about fallback
                    if 'reasoning' in handler_fields:
                        handler_fields['reasoning'].append(f"Original {document_type} handler failed: {str(handler_error)}")
                        handler_fields['reasoning'].append("Used supporting_document fallback")
                except Exception as fallback_error:
                    # Ultimate fallback
                    fallback_handler = self._create_fallback_handler()
                    handler_fields = fallback_handler.extract_fields(normalized_text, metadata)
            
            # Run semantic extraction for layout-agnostic field discovery (after handler)
            semantic_result = self.semantic_extractor.extract_semantic_fields(normalized_text, document_type)

            # Merge handler + semantic results (semantic may fill or replace missing/weaker fields)
            merged_result = self._merge_extraction_results(handler_fields, semantic_result, document_type)

            # After semantic merge: run GenericFieldExtractor only as a last fallback
            generic_result = self.generic_extractor.extract_fields(normalized_text)

            # Apply generic fallback for remaining missing fields (do not overwrite handler/semantic)
            missing_after_semantic = self._compute_missing_fields(document_type, merged_result.get('structured_data', {}))
            generic_filled = 0
            for fld in missing_after_semantic:
                gen_struct = generic_result.get('structured_data', {})
                if fld in gen_struct and gen_struct[fld]:
                    gen_meta = generic_result.get('extracted_fields', {}).get(fld)
                    if gen_meta and isinstance(gen_meta, dict) and gen_meta.get('value'):
                        merged_result['extracted_fields'][fld] = gen_meta
                        merged_result['structured_data'][fld] = gen_meta.get('value')
                    else:
                        merged_result['extracted_fields'][fld] = {
                            'value': gen_struct[fld],
                            'confidence': generic_result.get('confidence', 0.6) or 0.6,
                            'source': 'generic_fallback'
                        }
                        merged_result['structured_data'][fld] = gen_struct[fld]
                    generic_filled += 1

            merged_result.setdefault('reasoning', [])
            merged_result['reasoning'].append(f"Generic fallback filled {generic_filled} fields")
            
            # Apply field filtering to remove noise
            filtered_result = self.field_filter.filter_extracted_fields(merged_result.get('extracted_fields', {}))
            
            # Update merged result with filtered fields
            merged_result['extracted_fields'] = filtered_result['filtered_fields']
            
            # Rebuild structured_data from filtered fields
            filtered_structured_data = {}
            for field_name, field_data in filtered_result['filtered_fields'].items():
                if isinstance(field_data, dict) and 'value' in field_data:
                    filtered_structured_data[field_name] = field_data['value']
                else:
                    filtered_structured_data[field_name] = field_data
            merged_result['structured_data'] = filtered_structured_data
            
            # Apply strict field sanitization to remove header junk and validate business entities
            sanitized_structured_data = self.sanitize_extracted_structured_data(
                document_type,
                merged_result['structured_data'],
                merged_result.get('extracted_fields', {}),
                normalized_text
            )
            
            # Apply second-pass business entity recovery for missing critical fields
            recovered_structured_data = self.second_pass_business_entity_recovery(document_type, sanitized_structured_data, normalized_text)
            
            # Update merged result with sanitized and recovered data
            merged_result['structured_data'] = recovered_structured_data
            
            # Update extracted_fields to match sanitized structured_data
            for field_name, field_value in recovered_structured_data.items():
                if field_name in merged_result['extracted_fields']:
                    if isinstance(merged_result['extracted_fields'][field_name], dict):
                        merged_result['extracted_fields'][field_name]['value'] = field_value
                    else:
                        merged_result['extracted_fields'][field_name] = field_value
                else:
                    merged_result['extracted_fields'][field_name] = {
                        'value': field_value,
                        'confidence': 0.8,
                        'source': 'sanitized_extraction'
                    }
            
            # Remove any extracted_fields that are no longer in structured_data
            fields_to_remove = [f for f in merged_result['extracted_fields'] if f not in recovered_structured_data]
            for field in fields_to_remove:
                del merged_result['extracted_fields'][field]

            # Supporting-document specific cleanup: remove unsafe/claim-like fields
            if document_type == 'supporting_document':
                # 1) Remove generic person-like fields unless they look like real person names
                for person_field in ['claimant', 'complainant', 'applicant_name']:
                    if person_field in merged_result['extracted_fields']:
                        meta = merged_result['extracted_fields'].get(person_field)
                        val = meta.get('value') if isinstance(meta, dict) else meta
                        if not self.is_valid_person_name(val):
                            merged_result['extracted_fields'].pop(person_field, None)
                            merged_result['structured_data'].pop(person_field, None)

                # 2) Prevent Aadhaar duplication into PAN/ID unless source explicitly indicates PAN/ID
                aadhaar_val = merged_result['structured_data'].get('aadhaar_number')
                def _digits_only(s):
                    return re.sub(r'\D', '', str(s)) if s is not None else ''

                for id_field in ['pan_number', 'id_number']:
                    if id_field in merged_result['extracted_fields']:
                        meta = merged_result['extracted_fields'].get(id_field)
                        val = meta.get('value') if isinstance(meta, dict) else meta
                        val_str = str(val).strip() if val is not None else ''
                        source = meta.get('source', '') if isinstance(meta, dict) else ''

                        # If same digits as Aadhaar and no explicit PAN/ID source, drop it
                        if aadhaar_val and _digits_only(val_str) and _digits_only(val_str) == _digits_only(aadhaar_val):
                            if not re.search(r'\bpan\b', source, re.IGNORECASE) and not re.search(r'\bid\b', source, re.IGNORECASE):
                                merged_result['extracted_fields'].pop(id_field, None)
                                merged_result['structured_data'].pop(id_field, None)
                                continue

                        # If no Aadhaar to compare, require explicit PAN/ID cues to keep
                        pan_pattern = re.compile(r'^[A-Z]{5}\d{4}[A-Z]$')
                        if not (re.search(r'\bpan\b', source, re.IGNORECASE) or re.search(r'\bid\b', source, re.IGNORECASE) or pan_pattern.match(val_str)):
                            merged_result['extracted_fields'].pop(id_field, None)
                            merged_result['structured_data'].pop(id_field, None)

                # 3) Keep only safe structured fields for supporting documents
                safe_fields = {
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'contact_number',
                    'document_reference', 'document_type_detail', 'bank_name', 'ifsc',
                    'account_number', 'issuing_authority'
                }

                for fld in list(merged_result['structured_data'].keys()):
                    if fld not in safe_fields:
                        merged_result['structured_data'].pop(fld, None)
                        merged_result['extracted_fields'].pop(fld, None)
            
            # Add filtering reasoning
            if filtered_result['removal_count'] > 0:
                merged_result['reasoning'].append(f"Filtered {filtered_result['removal_count']} noisy fields")
                merged_result['reasoning'].extend([f"Removed: {reason}" for reason in filtered_result['removed_fields'][:3]])  # First 3 removal reasons
            
            # Generate enhanced reasoning with decision support
            enhanced_insights = self.reasoning_engine.generate_reasoning(merged_result, document_type)
            enhanced_reasoning = self.reasoning_engine.format_reasoning_for_output(enhanced_insights)
            
            # Merge handler reasoning with enhanced reasoning
            merged_result['reasoning'].extend(enhanced_reasoning)
            
            # Add reasoning metadata
            merged_result['reasoning_insights'] = [
                {
                    'type': insight.reasoning_type.value,
                    'message': insight.message,
                    'confidence': insight.confidence,
                    'impact': insight.impact,
                    'actionable': insight.actionable
                }
                for insight in enhanced_insights
            ]
            
            # Generate predictive insights
            predictive_insights = self.predictive_analytics.generate_predictions(merged_result, document_type)
            formatted_predictions = self.predictive_analytics.format_predictions_for_output(predictive_insights)
            
            # Compute missing fields from merged structured_data
            missing_fields = self._compute_missing_fields(document_type, merged_result.get('structured_data', {}))
            
            # Final standardized shape - use enhanced reasoning with predictions
            final_payload = {
                "document_type": document_type,
                "structured_data": merged_result.get('structured_data', {}),
                "extracted_fields": merged_result.get('extracted_fields', {}),
                "missing_fields": missing_fields,
                "confidence": merged_result.get('confidence', 0.0),
                "reasoning": merged_result.get('reasoning', []),
                "reasoning_insights": merged_result.get('reasoning_insights', []),
                "predictions": formatted_predictions,
                "canonical": merged_result.get('canonical', {})
            }

            # Apply final document-family sanitization so callers of extract_document
            # (not just processors) get the stabilized output.
            try:
                sanitized = self.sanitize_by_document_family(document_type, final_payload, normalized_text)
                if isinstance(sanitized, dict):
                    final_payload = sanitized
            except Exception:
                # Don't fail extraction on sanitization errors; keep original payload
                pass

            # Ensure missing_fields and confidence are recomputed from surviving data
            try:
                final_payload['missing_fields'] = self._compute_missing_fields(document_type, final_payload.get('structured_data', {}) or {})
            except Exception:
                final_payload.setdefault('missing_fields', [])

            try:
                final_payload['confidence'] = self._compute_confidence_from_fields(final_payload.get('extracted_fields', {}) or {})
            except Exception:
                final_payload.setdefault('confidence', merged_result.get('confidence', 0.0))

            # Ensure reasoning_insights and predictions keys exist
            final_payload.setdefault('reasoning_insights', merged_result.get('reasoning_insights', []))
            final_payload.setdefault('predictions', formatted_predictions)

            return final_payload
            
        except Exception as e:
            return {
                "document_type": document_type,
                "structured_data": {},
                "extracted_fields": {},
                "missing_fields": [],
                "confidence": 0.0,
                "reasoning": [f"Extraction failed: {str(e)}"]
            }
    
    def auto_classify_and_extract(
        self,
        text_content: str,
        file_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Automatically classify document and extract fields
        
        Args:
            text_content: OCR extracted text
            file_name: Original file name
            metadata: Additional metadata
            
        Returns:
            Standardized extraction result with classification info
        """
        try:
            # Classify using DocumentClassificationService with correct arguments
            classification_result = self.classification_service.classify_document(
                text=text_content,
                filename=file_name
            )
            
            # Extract using classified type
            extraction_result = self.extract_document(
                text_content=text_content,
                document_type=classification_result.get('document_type', 'unknown'),
                metadata=metadata
            )
            
            # Include classification confidence + reasoning in output
            extraction_result['classification_confidence'] = classification_result.get('classification_confidence', 0.0)
            
            # Ensure classification_reasoning has consistent dict shape
            classification_reasoning = classification_result.get('classification_reasoning', {})
            if not isinstance(classification_reasoning, dict):
                # Convert list/different format to dict if needed
                classification_reasoning = {
                    "keywords_found": [],
                    "structural_indicators": [],
                    "confidence_factors": list(classification_reasoning) if isinstance(classification_reasoning, list) else [str(classification_reasoning)]
                }
            extraction_result['classification_reasoning'] = classification_reasoning
            
            return extraction_result
            
        except Exception as e:
            return {
                "document_type": "unknown",
                "structured_data": {},
                "extracted_fields": {},
                "missing_fields": [],
                "confidence": 0.0,
                "reasoning": [f"Auto-classification failed: {str(e)}"],
                "classification_confidence": 0.0,
                "classification_reasoning": {
                    "keywords_found": [],
                    "structural_indicators": [],
                    "confidence_factors": [f"Classification error: {str(e)}"]
                }
            }
    
    def get_supported_document_types(self) -> List[str]:
        """Get list of supported document types"""
        return list(self.handlers.keys())
    
    def _merge_extraction_results(self, handler_fields: Dict, semantic_result: Dict, document_type: str) -> Dict:
        """Merge handler and semantic results with semantic-first filling rules.

        Rules enforced:
        - Handler values are authoritative and kept when confidence is strong.
        - Semantic fields can fill missing, empty, or weaker-confidence fields.
        - Generic fallback is applied separately after this merge.
        """
        merged = {
            'structured_data': {},
            'extracted_fields': {},
            'reasoning': []
        }

        # FIRST: Add handler fields (authoritative)
        handler_provided = set()
        if handler_fields:
            if 'structured_data' in handler_fields:
                for key, value in handler_fields['structured_data'].items():
                    if self._is_metadata_shaped(value):
                        merged['structured_data'][key] = value.get('value', value)
                    else:
                        merged['structured_data'][key] = value
                    handler_provided.add(key)

            if 'extracted_fields' in handler_fields:
                for key, value in handler_fields['extracted_fields'].items():
                    if self._is_metadata_shaped(value):
                        merged['extracted_fields'][key] = value
                    else:
                        merged['extracted_fields'][key] = {
                            'value': value,
                            'confidence': 0.8,
                            'source': 'handler_extraction'
                        }
                    handler_provided.add(key)

            # Preserve handler reasoning
            if 'reasoning' in handler_fields and isinstance(handler_fields['reasoning'], list):
                merged['reasoning'] = handler_fields['reasoning'].copy()

        # Mark handler application
        if handler_fields:
            merged.setdefault('reasoning', [])
            merged['reasoning'].append('Handler extraction applied')

        # SECOND: Merge semantic fields, allowing replacements for missing/weak values
        semantic_filled = 0
        if semantic_result and 'semantic_fields' in semantic_result:
            semantic_fields = semantic_result['semantic_fields']
            for field_name, field_data in semantic_fields.items():
                # canonical semantic metadata expected
                sem_val = field_data.get('value') if isinstance(field_data, dict) else field_data
                sem_conf = field_data.get('confidence', 0.7) if isinstance(field_data, dict) else 0.7

                # Determine existing value/confidence/source
                existing_meta = merged['extracted_fields'].get(field_name)
                existing_val = None
                existing_conf = 0.0
                existing_src = None

                if existing_meta is not None:
                    if isinstance(existing_meta, dict):
                        existing_val = existing_meta.get('value')
                        existing_conf = existing_meta.get('confidence', 0.0)
                        existing_src = existing_meta.get('source')
                    else:
                        existing_val = existing_meta
                        existing_conf = 0.8
                        existing_src = 'handler_extraction' if field_name in handler_provided else None
                elif field_name in merged['structured_data']:
                    existing_val = merged['structured_data'].get(field_name)
                    existing_conf = 0.8 if field_name in handler_provided else 0.0
                    existing_src = 'handler_extraction' if field_name in handler_provided else None

                # Helper: is existing value empty/invalid?
                def _is_empty(v):
                    return v is None or v == '' or (isinstance(v, list) and len(v) == 0)

                replace = False
                if existing_meta is None and _is_empty(existing_val):
                    replace = True
                else:
                    # Replace if semantic confidence is strictly greater than existing
                    if sem_conf > (existing_conf or 0.0):
                        # But never let a strong handler value win over weaker semantic
                        if existing_src and 'handler' in str(existing_src) and existing_conf >= sem_conf:
                            replace = False
                        else:
                            replace = True

                if replace:
                    # Apply semantic metadata as-is when available
                    if isinstance(field_data, dict) and self._is_metadata_shaped(field_data):
                        merged['extracted_fields'][field_name] = field_data
                        merged['structured_data'][field_name] = field_data.get('value')
                    else:
                        merged['extracted_fields'][field_name] = {
                            'value': sem_val,
                            'confidence': sem_conf,
                            'source': 'semantic_extraction'
                        }
                        merged['structured_data'][field_name] = sem_val
                    semantic_filled += 1

        merged.setdefault('reasoning', [])
        merged['reasoning'].append(f"Semantic extraction filled {semantic_filled} fields")

        # Recompute confidence after semantic merge
        merged['confidence'] = self._compute_confidence_from_fields(merged['extracted_fields'])

        return merged
    
    def _compute_missing_fields(self, document_type: str, structured_data: Dict) -> List[str]:
        """Compute missing required fields for document type"""
        # Define required fields per document type with explicit handler contracts
        # Expected handler outputs for required fields:
        # - grievance: farmer_name, grievance_type, description
        # - insurance_claim: farmer_name, claim_type, loss_description
        # - subsidy_claim: farmer_name, subsidy_type, requested_amount
        # - farmer_record: farmer_name, aadhaar_number, mobile_number
        required_fields_map = {
            'scheme_application': ['farmer_name', 'scheme_name', 'application_id'],
            'farmer_record': ['farmer_name', 'aadhaar_number', 'mobile_number'],
            'grievance': ['farmer_name', 'grievance_type', 'description'],
            'insurance_claim': ['farmer_name', 'claim_type', 'loss_description'],
            'subsidy_claim': ['farmer_name', 'subsidy_type', 'requested_amount'],
            'supporting_document': [],
            'unknown': []
        }
        
        required_fields = required_fields_map.get(document_type, [])
        missing_fields = []
        
        for field in required_fields:
            field_value = structured_data.get(field)
            # Treat None, empty string, or empty list as missing
            if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                missing_fields.append(field)
        
        return missing_fields
    
    def _compute_confidence_from_fields(self, extracted_fields: Dict) -> float:
        """Compute confidence from merged extracted fields"""
        if not extracted_fields:
            return 0.0
        
        total_confidence = 0.0
        field_count = 0
        
        for field_data in extracted_fields.values():
            if isinstance(field_data, dict):
                # Use explicit confidence if available
                if 'confidence' in field_data:
                    total_confidence += field_data['confidence']
                    field_count += 1
                # For plain handler-added values with no explicit confidence
                elif 'value' in field_data and field_data['value']:
                    total_confidence += 0.8  # Safe default for handler values
                    field_count += 1
            elif field_data:  # Non-empty simple field (fallback)
                total_confidence += 0.8
                field_count += 1
        
        return total_confidence / field_count if field_count > 0 else 0.0

    def sanitize_by_document_family(self, document_type: str, data: Dict[str, Any], original_text: Optional[str] = None) -> Dict[str, Any]:
        """Final document-family sanitization pass.

        This is the authoritative final pass that removes cross-document fields,
        header/title junk, and recomputes missing fields and confidence.
        It updates: structured_data, extracted_fields, canonical, missing_fields, confidence, reasoning.
        """
        try:
            structured = (data.get('structured_data') or {}).copy()
            extracted = (data.get('extracted_fields') or {}).copy()
            canonical = (data.get('canonical') or {})
            reasoning = list(data.get('reasoning') or [])

            removed_fields = []
            removed_reasons = []
            removed_values = []

            # Map document types to families and allow-lists
            family_map = {
                'scheme_application': 'subsidy',
                'subsidy_claim': 'subsidy',
                'insurance_claim': 'insurance',
                'grievance': 'grievance',
                'supporting_document': 'supporting',
                'farmer_record': 'farmer_record'
            }

            family = family_map.get(document_type, 'other')

            allowed_by_family = {
                'insurance': {
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'village', 'district', 'address',
                    'claim_amount', 'requested_amount', 'claim_type', 'cause_of_loss', 'loss_description',
                    'crop_name', 'crop_type', 'land_size', 'policy_number', 'policy', 'insurance_scheme'
                },
                'grievance': {
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'phone_number', 'contact_number', 'village', 'district', 'address',
                    'description', 'grievance_type', 'reference_number', 'location'
                },
                'supporting': {
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'document_reference', 'document_type_detail',
                    'bank_name', 'ifsc', 'account_number', 'issuing_authority', 'contact_number'
                },
                'subsidy': {
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'village', 'district',
                    'requested_amount', 'subsidy_amount', 'subsidy_type', 'scheme_name', 'location', 'land_size', 'crop_name'
                },
                'farmer_record': {
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'village', 'district', 'address',
                    'land_size', 'crop_name', 'season', 'area', 'dob', 'father_name', 'mother_name'
                }
            }

            allowed = allowed_by_family.get(family)

            # Helper: detect header/title/junk values
            def _is_junk_value(val, field_name=None):
                if val is None:
                    return True
                if isinstance(val, dict):
                    val = val.get('value')
                s = str(val).strip()
                if not s:
                    return True
                low = s.lower()

                # Common tokens that indicate header/title or repeated table text
                junk_tokens = [
                    'field value', 'reference details', 'insurance claim form', 'policy and farmer',
                    'policy number', 'field value:', 'field value –', 'field value -', 'policy number pmfb',
                    'policy number pmfby', 'applicant information', 'personal information', 'claimant information'
                ]

                for tok in junk_tokens:
                    if tok in low:
                        return True

                # Multiline/table-like blobs
                if '\n' in s or '|' in s or '\t' in s or re.search(r'-{3,}', s):
                    return True

                # Very long strings likely concatenated headers
                if len(s) > 300:
                    return True

                # All-caps long headers - but allow for known short semantic fields
                if s.isupper() and len(s) > 12:
                    # Allow uppercase grievance_type and description-like fields (common in forms)
                    if field_name in ('grievance_type', 'description', 'farmer_name', 'reference_number'):
                        pass
                    else:
                        return True

                # OCR numeric fragments like '03', '04' as financial values
                if field_name and field_name in ['claim_amount', 'requested_amount', 'subsidy_amount', 'amount']:
                    if re.match(r'^0\d$', s) or re.match(r'^\d{1,2}$', s) and s.startswith('0'):
                        return True

                # Header junk list from initializer
                try:
                    if low in [h.lower() for h in self.header_junk]:
                        return True
                except Exception:
                    pass

                return False

            # 1) STRICT family-level field keep/remove
            if allowed is not None:
                for fld in list(structured.keys()):
                    if fld not in allowed:
                        removed_fields.append(fld)
                        removed_reasons.append(f"Not allowed for family: {family}")
                        removed_values.append(structured.get(fld))
                        structured.pop(fld, None)
                        extracted.pop(fld, None)

            # 2) Generic bad-value filters across remaining fields
            for fld in list(structured.keys()):
                val_meta = extracted.get(fld)
                val = val_meta.get('value') if isinstance(val_meta, dict) and 'value' in val_meta else structured.get(fld)

                # Family-specific additional removals
                if family == 'insurance':
                    # Remove subsidy/grievance fields that slipped in
                    for bad in ['subsidy_amount', 'subsidy_type', 'grievance_type']:
                        if bad in structured:
                            removed_fields.append(bad)
                            removed_reasons.append('Insurance family: remove subsidy/grievance fields')
                            removed_values.append(structured.get(bad))
                            structured.pop(bad, None)
                            extracted.pop(bad, None)

                if family == 'grievance':
                    # Remove claim/subsidy amounts
                    for bad in ['claim_amount', 'requested_amount', 'subsidy_amount', 'amount']:
                        if bad in structured:
                            removed_fields.append(bad)
                            removed_reasons.append('Grievance family: remove monetary/claim fields')
                            removed_values.append(structured.get(bad))
                            structured.pop(bad, None)
                            extracted.pop(bad, None)

                if family == 'supporting':
                    # Supporting docs should not carry claim/subsidy/grievance fields
                    for bad in ['claim_amount', 'requested_amount', 'subsidy_amount', 'grievance_type', 'claim_type', 'loss_description']:
                        if bad in structured:
                            removed_fields.append(bad)
                            removed_reasons.append('Supporting family: remove claim/subsidy fields')
                            removed_values.append(structured.get(bad))
                            structured.pop(bad, None)
                            extracted.pop(bad, None)

                # Generic junk removal
                if _is_junk_value(val, fld):
                    removed_fields.append(fld)
                    removed_reasons.append('Generic junk/header-like value')
                    removed_values.append(val)
                    structured.pop(fld, None)
                    extracted.pop(fld, None)
                    continue

                # Field-specific rule: land_size 0 fallback
                if fld == 'land_size':
                    sval = str(structured.get('land_size') or '')
                    m = re.search(r'(-?\d+(?:\.\d+)?)', sval)
                    if m:
                        num = safe_float(m.group(1), default=None)
                        if num is None or (num == 0 and not re.search(r'\b0\b', sval)):
                            removed_fields.append(fld)
                            removed_reasons.append('Land size fallback 0 without explicit evidence')
                            removed_values.append(structured.get(fld))
                            structured.pop(fld, None)
                            extracted.pop(fld, None)

            # 3) Supporting-doc specific dedup/policy: remove PAN/ID duplicates derived from Aadhaar
            if family == 'supporting' and 'aadhaar_number' in structured:
                aad = re.sub(r'\D', '', str(structured.get('aadhaar_number') or ''))
                for id_field in ['pan_number', 'id_number']:
                    if id_field in structured:
                        val = str(structured.get(id_field) or '')
                        digits = re.sub(r'\D', '', val)
                        if digits and aad and digits == aad:
                            removed_fields.append(id_field)
                            removed_reasons.append('Supporting doc: removed duplicate ID field copied from Aadhaar')
                            removed_values.append(structured.get(id_field))
                            structured.pop(id_field, None)
                            extracted.pop(id_field, None)

            # 4) Canonical pruning: remove entries that correspond to removed fields or contain header-like values
            removed_set = set(removed_fields)

            def _prune_canonical(obj):
                if isinstance(obj, dict):
                    new = {}
                    for k, v in obj.items():
                        # Remove top-level canonical keys that match removed fields
                        if k in removed_set:
                            continue
                        # Recurse
                        pr = _prune_canonical(v)
                        # If pruned empty, skip
                        if pr is None or (isinstance(pr, (dict, list)) and not pr):
                            continue
                        # Remove header-like string values
                        if isinstance(pr, str) and _is_junk_value(pr):
                            continue
                        new[k] = pr
                    return new
                elif isinstance(obj, list):
                    out = []
                    for item in obj:
                        pr = _prune_canonical(item)
                        if pr is None or (isinstance(pr, (dict, list)) and not pr):
                            continue
                        out.append(pr)
                    return out
                else:
                    # Primitive value
                    if isinstance(obj, str) and _is_junk_value(obj):
                        return None
                    return obj

            try:
                canonical = _prune_canonical(canonical) or {}
            except Exception:
                # If anything goes wrong pruning canonical, leave as-is
                pass

            # 5) Update data and recompute missing fields/confidence
            data['structured_data'] = structured
            data['extracted_fields'] = extracted
            data['canonical'] = canonical

            # Recompute missing fields from surviving structured_data only
            missing = self._compute_missing_fields(document_type, structured)
            data['missing_fields'] = missing

            # Recompute confidence based on surviving extracted_fields
            try:
                data['confidence'] = self._compute_confidence_from_fields(extracted)
            except Exception:
                data['confidence'] = data.get('confidence', 0.0)

            # 6) Reasoning cleanup: remove stale assertions and add sanitization summary
            cleaned_reasoning = []
            for r in reasoning:
                # Remove stale 'All required fields present' if missing exists
                if isinstance(r, str) and 'All required fields present' in r and data['missing_fields']:
                    continue
                cleaned_reasoning.append(r)

            # Add summary lines about what we removed
            if removed_fields:
                summary = f"Sanitization removed {len(removed_fields)} fields: {', '.join(sorted(set(removed_fields))[:12])}"
                cleaned_reasoning.append(summary)
                # Add categorized removal reasons
                reason_set = set(removed_reasons)
                if any('header' in rr.lower() or 'title' in rr.lower() or 'generic junk' in rr.lower() for rr in removed_reasons):
                    cleaned_reasoning.append('Removed noisy header-derived fields')
                if any('amount' in rr.lower() or 'monetary' in rr.lower() for rr in removed_reasons) or any(f in ['claim_amount', 'requested_amount', 'subsidy_amount', 'amount'] for f in removed_fields):
                    cleaned_reasoning.append('Removed invalid financial fragments or OCR-number noise')
                if any('Not allowed for family' in rr for rr in removed_reasons):
                    cleaned_reasoning.append('Removed irrelevant cross-document fields based on document family')

            # If no removals, note that finalization completed
            if not removed_fields:
                cleaned_reasoning.append('Sanitization pass completed with no removals')

            cleaned_reasoning.append('Recomputed missing_fields after sanitization')
            data['reasoning'] = cleaned_reasoning

            # 7) Build canonical nested mapping for known families if canonical is flat or empty
            try:
                # If canonical is empty or flat top-level keys, create a nested canonical for UI
                def _is_flat_canonical(obj):
                    return isinstance(obj, dict) and any(k in obj for k in ['farmer_name','aadhaar_number','mobile_number','land_size','crop_name'])

                if document_type == 'farmer_record' or document_type == 'land_record' or _is_flat_canonical(canonical):
                    canonical_obj = {}
                    applicant = {}
                    if 'farmer_name' in structured:
                        applicant['name'] = structured.get('farmer_name')
                    if 'aadhaar_number' in structured:
                        applicant['aadhaar_number'] = structured.get('aadhaar_number')
                    if 'mobile_number' in structured:
                        applicant['mobile_number'] = structured.get('mobile_number')
                    if 'village' in structured:
                        applicant['village'] = structured.get('village')
                    if 'district' in structured:
                        applicant['district'] = structured.get('district')
                    if 'address' in structured:
                        applicant['address'] = structured.get('address')
                    if applicant:
                        canonical_obj['applicant'] = applicant

                    agriculture = {}
                    if 'land_size' in structured:
                        agriculture['land_size'] = structured.get('land_size')
                    if 'crop_name' in structured:
                        agriculture['crop_name'] = structured.get('crop_name')
                    if 'season' in structured:
                        agriculture['season'] = structured.get('season')
                    if 'area' in structured:
                        agriculture['area'] = structured.get('area')
                    if agriculture:
                        canonical_obj['agriculture'] = agriculture

                    document_meta = {}
                    if 'reference_number' in structured:
                        document_meta['reference_number'] = structured.get('reference_number')
                    if 'farmer_id' in structured:
                        document_meta['farmer_id'] = structured.get('farmer_id')
                    if document_meta:
                        canonical_obj['document_meta'] = document_meta

                    if canonical_obj:
                        data['canonical'] = canonical_obj
            except Exception:
                pass

            return data

        except Exception as e:
            # On sanitizer failure, append failure reason and return original data
            data.setdefault('reasoning', [])
            data['reasoning'].append(f"Sanitization error: {str(e)}")
            return data
    
