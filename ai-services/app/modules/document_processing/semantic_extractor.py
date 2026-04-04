"""
Semantic Extractor for Enhanced Document Intelligence
Purpose: Advanced extraction using semantic understanding and context awareness
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from .layout_analyzer import LayoutAnalyzer, SemanticBlock
from .utils import safe_float


@dataclass
class SemanticField:
    """Represents a semantically extracted field"""
    name: str
    value: Any
    confidence: float
    source: str
    context: Dict[str, Any]
    validation: Dict[str, Any]


class SemanticExtractor:
    """Advanced semantic extraction with context awareness"""
    
    def __init__(self):
        self.layout_analyzer = LayoutAnalyzer()
        
        # Semantic field mapping to canonical schema
        self.semantic_mapping = {
            'person_name': ['farmer_name', 'applicant_name', 'complainant', 'claimant'],
            'address': ['location', 'village', 'district', 'address'],
            'contact': ['phone_number', 'mobile_number', 'contact_number'],
            'identification': ['aadhaar_number', 'pan_number', 'id_number'],
            'financial': ['requested_amount', 'claim_amount', 'subsidy_amount', 'amount'],
            'agricultural': ['land_size', 'crop_type', 'season', 'area']
        }
        
        # Contextual validation rules
        self.validation_rules = {
            'person_name': {
                'min_length': 3,
                'max_length': 100,
                'pattern': r'^[A-Za-z\s\.]+$',
                'reject_patterns': [r'\b(Name|Address|Phone|Mobile|Amount)\b', r'^[A-Z]{2,}$']
            },
            'contact': {
                'pattern': r'^\d{10}$',
                'reject_patterns': [r'^0+', r'1234567890']
            },
            'identification': {
                'aadhaar_pattern': r'^\d{4}\s*\d{4}\s*\d{4}$',
                'pan_pattern': r'^[A-Z]{5}\d{4}[A-Z]$',
                'reject_patterns': [r'^0+', r'1234.*1234.*1234']
            },
            'financial': {
                'min_value': 1,
                'max_value': 10000000,
                'pattern': r'^\d{1,8}(?:,\d{3})*(?:\.\d{2})?$'
            }
            ,
            'agricultural': {
                'reject_patterns': [r'field value', r'claimant name', r'aadhaar number', r'insurance claim form', r'section', r'table', r'page', r'\|'],
                'min_length': 1,
                'max_length': 200
            }
        }
        
        # Semantic relationship patterns
        self.relationship_patterns = {
            'name_with_address': [
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,\s*([A-Za-z\s]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+.*\s+([A-Za-z\s]+\s+[A-Za-z\s]+)'
            ],
            'amount_with_scheme': [
                r'(Rs\.?\s*\d+,?\d*(?:\.\d{2})?)\s*(?:under|for|of)\s*([A-Za-z\s]+)',
                r'([A-Za-z\s]+)\s*(?:scheme|benefit)\s*(?:of|for)?\s*(Rs\.?\s*\d+,?\d*)'
            ],
            'land_with_location': [
                r'(\d+(?:\.\d+)?)\s*(?:acre|hectare)\s*(?:at|in)\s*([A-Za-z\s]+)',
                r'([A-Za-z\s]+)\s*.*\s*(\d+(?:\.\d+)?)\s*(?:acre|hectare)'
            ]
        }
    
    def extract_semantic_fields(self, text: str, document_type: Optional[str] = None) -> Dict[str, Any]:
        """Extract fields using semantic understanding"""
        # Analyze layout first
        layout_info = self.layout_analyzer.analyze_layout(text)
        
        # Extract semantic blocks
        semantic_blocks = self.layout_analyzer.extract_semantic_blocks(text)
        
        # Extract base semantic fields
        base_fields = self.layout_analyzer.extract_semantic_fields(text)
        
        # Infer document context if not provided
        if not document_type or document_type == 'unknown':
            context_info = self.layout_analyzer.infer_document_context(text)
            inferred_type = context_info['inferred_type']
            if context_info['confidence'] > 0.5:
                document_type = inferred_type
        
        # Apply semantic mapping to canonical fields
        canonical_fields = self._map_to_canonical_fields(base_fields['semantic_fields'], document_type)
        
        # Extract relationship-based fields
        relationship_fields = self._extract_relationship_fields(text)
        
        # Apply contextual validation
        validated_fields = self._validate_fields(canonical_fields, document_type)

        # Document-type-specific sanitization (e.g., insurance claim strict rules)
        if document_type == 'insurance_claim':
            validated_fields = self._sanitize_insurance_claim_fields(validated_fields)
        
        # Merge all semantic extractions
        all_semantic_fields = {}
        all_semantic_fields.update(validated_fields)
        all_semantic_fields.update(relationship_fields)
        
        # Build reasoning
        reasoning = [
            f"Layout analysis: {layout_info['layout_type']} (confidence: {layout_info['confidence']:.2f})",
            f"Semantic blocks identified: {len(semantic_blocks)}",
            f"Base semantic fields: {len(base_fields['semantic_fields'])}",
            f"Relationship fields: {len(relationship_fields)}",
            f"Validated canonical fields: {len(validated_fields)}"
        ]
        
        if document_type:
            reasoning.append(f"Document context: {document_type}")
        
        return {
            'semantic_fields': all_semantic_fields,
            'layout_info': layout_info,
            'semantic_blocks': len(semantic_blocks),
            'reasoning': reasoning,
            'extraction_method': 'semantic',
            'document_context': document_type or 'unknown'
        }
    
    def _map_to_canonical_fields(self, semantic_fields: Dict[str, Any], document_type: Optional[str] = None) -> Dict[str, Any]:
        """Map semantic fields to canonical schema.

        Be conservative for identification fields: do not duplicate Aadhaar into PAN/ID
        unless the value clearly matches PAN/ID format or the semantic context indicates PAN/ID.
        Also avoid mapping financial fields for supporting documents (handled elsewhere).
        """
        canonical_fields = {}

        for semantic_name, field_data in semantic_fields.items():
            canonical_names = self.semantic_mapping.get(semantic_name, [semantic_name])
            value = field_data.get('value')
            conf = field_data.get('confidence', 0.7)
            source = f"semantic_mapping_{semantic_name}"

            # Special handling for identification type: inspect value to decide mapping
            if semantic_name == 'identification':
                val_str = str(value).strip() if value is not None else ''
                aadhaar_pattern = self.validation_rules.get('identification', {}).get('aadhaar_pattern')
                pan_pattern = self.validation_rules.get('identification', {}).get('pan_pattern')

                is_aadhaar = False
                is_pan = False
                if aadhaar_pattern and re.match(aadhaar_pattern, val_str):
                    is_aadhaar = True
                if pan_pattern and re.match(pan_pattern, val_str):
                    is_pan = True

                # If clearly Aadhaar, map only to aadhaar_number
                if is_aadhaar:
                    canonical_fields.setdefault('aadhaar_number', {
                        'value': val_str,
                        'confidence': min(conf, 0.95),
                        'source': source,
                        'semantic_type': semantic_name,
                        'validation': {}
                    })
                # If clearly PAN, map only to pan_number
                elif is_pan:
                    canonical_fields.setdefault('pan_number', {
                        'value': val_str,
                        'confidence': min(conf, 0.95),
                        'source': source,
                        'semantic_type': semantic_name,
                        'validation': {}
                    })
                else:
                    # For supporting documents, be conservative: prefer aadhaar mapping only when clearly Aadhaar
                    if document_type == 'supporting_document':
                        # Do not create pan_number/id_number from ambiguous identification
                        # Map only to aadhaar if value looks numeric-ish and length ~12
                        digits = re.sub(r'\D', '', val_str)
                        if len(digits) == 12:
                            canonical_fields.setdefault('aadhaar_number', {
                                'value': digits,
                                'confidence': min(conf, 0.75),
                                'source': source,
                                'semantic_type': semantic_name,
                                'validation': {}
                            })
                        else:
                            # Ambiguous identification in supporting document -> skip
                            continue
                    else:
                        # For non-supporting docs, be slightly more permissive: map to id_number only
                        canonical_fields.setdefault('id_number', {
                            'value': val_str,
                            'confidence': conf,
                            'source': source,
                            'semantic_type': semantic_name,
                            'validation': {}
                        })

                continue

            # Default mapping for all other semantic types
            # For agricultural/financial types, be conservative based on document context
            for canonical_name in canonical_names:
                # Skip subsidy mapping for insurance claims
                if semantic_name == 'financial' and document_type == 'insurance_claim' and canonical_name.startswith('subsidy'):
                    continue

                if canonical_name not in canonical_fields:
                    # Encode semantic_type with canonical target to enable field-specific validation later
                    semantic_type_tag = f"{semantic_name}:{canonical_name}"
                    canonical_fields[canonical_name] = {
                        'value': value,
                        'confidence': conf,
                        'source': source,
                        'semantic_type': semantic_type_tag,
                        'validation': {}
                    }

        return canonical_fields
    
    def _extract_relationship_fields(self, text: str) -> Dict[str, Any]:
        """Extract fields based on semantic relationships"""
        relationship_fields = {}
        
        for relationship_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    groups = match.groups()
                    
                    if relationship_type == 'name_with_address' and len(groups) >= 2:
                        name = groups[0].strip()
                        address = groups[1].strip()
                        
                        # Validate name
                        if self._validate_field_value('person_name', name):
                            canonical_name = self._map_to_canonical_name('person_name')
                            if canonical_name not in relationship_fields:
                                relationship_fields[canonical_name] = {
                                    'value': name,
                                    'confidence': 0.8,
                                    'source': 'relationship_name_address',
                                    'semantic_type': 'person_name'
                                }
                        
                        # Validate and add address
                        if self._validate_field_value('address', address):
                            canonical_address = self._map_to_canonical_name('address')
                            if canonical_address not in relationship_fields:
                                relationship_fields[canonical_address] = {
                                    'value': address,
                                    'confidence': 0.7,
                                    'source': 'relationship_name_address',
                                    'semantic_type': 'address'
                                }
                    
                    elif relationship_type == 'amount_with_scheme' and len(groups) >= 2:
                        amount = groups[0] if re.search(r'\d', groups[0]) else groups[1]
                        scheme = groups[1] if re.search(r'\d', groups[0]) else groups[0]
                        
                        # Extract clean amount
                        amount_match = re.search(r'(\d+,?\d*(?:\.\d{2})?)', amount)
                        if amount_match and self._validate_field_value('financial', amount_match.group(1)):
                            canonical_amount = self._map_to_canonical_name('financial')
                            if canonical_amount not in relationship_fields:
                                relationship_fields[canonical_amount] = {
                                    'value': amount_match.group(1),
                                    'confidence': 0.8,
                                    'source': 'relationship_amount_scheme',
                                    'semantic_type': 'financial'
                                }
                        
                        # Add scheme name if it looks like a scheme
                        if len(scheme.split()) >= 2 and re.search(r'[A-Za-z]', scheme):
                            if 'scheme_name' not in relationship_fields:
                                relationship_fields['scheme_name'] = {
                                    'value': scheme.strip(),
                                    'confidence': 0.7,
                                    'source': 'relationship_amount_scheme',
                                    'semantic_type': 'scheme_name'
                                }
                    
                    elif relationship_type == 'land_with_location' and len(groups) >= 2:
                        land_size = groups[0] if re.search(r'\d', groups[0]) else groups[1]
                        location = groups[1] if re.search(r'\d', groups[0]) else groups[0]
                        
                        # Extract land size
                        land_match = re.search(r'(\d+(?:\.\d+)?)', land_size)
                        if land_match:
                            land_value = float(land_match.group(1))
                            if self._validate_field_value('agricultural', land_value):
                                if 'land_size' not in relationship_fields:
                                    relationship_fields['land_size'] = {
                                        'value': land_value,
                                        'confidence': 0.8,
                                        'source': 'relationship_land_location',
                                        'semantic_type': 'agricultural'
                                    }
                        
                        # Add location
                        if self._validate_field_value('address', location):
                            canonical_location = self._map_to_canonical_name('address')
                            if canonical_location not in relationship_fields:
                                relationship_fields[canonical_location] = {
                                    'value': location.strip(),
                                    'confidence': 0.7,
                                    'source': 'relationship_land_location',
                                    'semantic_type': 'address'
                                }
        
        return relationship_fields
    
    def _validate_fields(self, canonical_fields: Dict[str, Any], document_type: Optional[str] = None) -> Dict[str, Any]:
        """Validate canonical fields based on document type context"""
        validated_fields = {}
        
        for field_name, field_data in canonical_fields.items():
            # Skip financial fields for supporting documents
            if document_type == 'supporting_document' and field_name in ['requested_amount', 'claim_amount', 'subsidy_amount', 'loan_amount', 'amount']:
                continue  # Don't extract financial fields from supporting documents
            
            value = field_data['value']
            
            validation_result = self._validate_field_value(field_data['semantic_type'], value)
            
            if validation_result['is_valid']:
                validated_fields[field_name] = {
                    **field_data,
                    'validation': validation_result,
                    'confidence': min(field_data['confidence'], validation_result['confidence'])
                }
            else:
                # Field failed validation, but include with low confidence for review
                validated_fields[field_name] = {
                    **field_data,
                    'validation': validation_result,
                    'confidence': 0.2,  # Low confidence for failed validation
                    'validation_failed': True
                }
        
        return validated_fields
    
    def _validate_field_value(self, field_type: str, value: Any) -> Dict[str, Any]:
        """Validate a field value based on type"""
        validation = {
            'is_valid': True,
            'confidence': 1.0,
            'errors': [],
            'warnings': []
        }
        # Support namespaced semantic types like 'agricultural:land_size'
        base_type = field_type.split(':', 1)[0] if isinstance(field_type, str) and ':' in field_type else field_type

        if base_type not in self.validation_rules:
            # No specific rules - return permissive validation
            return validation

        rules = self.validation_rules[base_type]
        value_str = str(value).strip()
        
        # Length validation
        if 'min_length' in rules and len(value_str) < rules['min_length']:
            validation['is_valid'] = False
            validation['errors'].append(f"Value too short: {len(value_str)} < {rules['min_length']}")
            validation['confidence'] = 0.3
        
        if 'max_length' in rules and len(value_str) > rules['max_length']:
            validation['is_valid'] = False
            validation['errors'].append(f"Value too long: {len(value_str)} > {rules['max_length']}")
            validation['confidence'] = 0.3
        
        # Pattern validation
        if 'pattern' in rules:
            if not re.match(rules['pattern'], value_str):
                validation['is_valid'] = False
                validation['errors'].append(f"Pattern mismatch: {value_str}")
                validation['confidence'] = 0.4
        
        # Reject patterns
        if 'reject_patterns' in rules:
            for reject_pattern in rules['reject_patterns']:
                if re.search(reject_pattern, value_str, re.IGNORECASE):
                    validation['is_valid'] = False
                    validation['errors'].append(f"Rejected pattern: {reject_pattern}")
                    validation['confidence'] = 0.1
                    break
        
        # Field-specific validation (use base_type for namespaced semantic types)
        if base_type == 'identification':
            # Check for Aadhaar
            if re.match(rules['aadhaar_pattern'], value_str):
                validation['confidence'] = 0.9
            # Check for PAN
            elif re.match(rules['pan_pattern'], value_str):
                validation['confidence'] = 0.9
            else:
                validation['confidence'] = 0.6
        
        elif base_type == 'financial':
            try:
                numeric_value = float(re.sub(r'[^\d.]', '', value_str))
                if 'min_value' in rules and numeric_value < rules['min_value']:
                    validation['warnings'].append(f"Low amount: {numeric_value}")
                    validation['confidence'] = 0.7
                elif 'max_value' in rules and numeric_value > rules['max_value']:
                    validation['warnings'].append(f"High amount: {numeric_value}")
                    validation['confidence'] = 0.6
                else:
                    validation['confidence'] = 0.9
            except ValueError:
                validation['is_valid'] = False
                validation['errors'].append("Invalid numeric format")
                validation['confidence'] = 0.2
        
        elif base_type == 'person_name':
            # Check for reasonable name structure
            words = value_str.split()
            if len(words) < 2:
                validation['warnings'].append("Single word name")
                validation['confidence'] = 0.6
            elif any(word.lower() in ['name', 'address', 'village', 'district'] for word in words):
                validation['is_valid'] = False
                validation['errors'].append("Contains generic terms")
                validation['confidence'] = 0.2
            else:
                validation['confidence'] = 0.9
        
        # Agricultural-specific validation for namespaced types like 'agricultural:land_size'
        if base_type == 'agricultural':
            # Determine specific canonical target if provided
            specific = field_type.split(':', 1)[1] if ':' in field_type else None
            # If value is numeric-like and target is land_size/area, validate numeric
            if specific in ('land_size', 'area'):
                # Try to extract numeric token
                m = re.search(r'(-?\d+(?:\.\d+)?)', value_str)
                if not m:
                    validation['is_valid'] = False
                    validation['errors'].append('No numeric land size found')
                    validation['confidence'] = 0.2
                else:
                    try:
                        size = float(m.group(1))
                        # Reject 0 default unless explicitly present
                        if size == 0.0 and not re.search(r'\b0\b', value_str):
                            validation['is_valid'] = False
                            validation['errors'].append('Land size parsed as 0 without explicit zero in source')
                            validation['confidence'] = 0.2
                        elif size <= 0 or size > 10000:
                            validation['is_valid'] = False
                            validation['errors'].append('Land size out of realistic bounds')
                            validation['confidence'] = 0.2
                        else:
                            validation['confidence'] = 0.9
                    except Exception:
                        validation['is_valid'] = False
                        validation['errors'].append('Invalid land size format')
                        validation['confidence'] = 0.2
            else:
                # crop_type/season: reject multiline/table-like or header blobs
                # Reject if contains newline, pipe, or common table/header tokens
                if '\n' in value_str or '|' in value_str or re.search(r'(s\.?no|sno|sr\.?no|table|header|row|column|----)', value_str, re.IGNORECASE):
                    validation['is_valid'] = False
                    validation['errors'].append('Appears to be table/header or multiline blob')
                    validation['confidence'] = 0.1
                elif len(value_str) > 200:
                    validation['is_valid'] = False
                    validation['errors'].append('Too long for an agricultural field')
                    validation['confidence'] = 0.2
                else:
                    # Basic pass-through for likely crop/season short values
                    validation['confidence'] = 0.8
        
        return validation
    
    def _map_to_canonical_name(self, semantic_type: str) -> str:
        """Map semantic type to primary canonical field name"""
        mapping = {
            'person_name': 'farmer_name',
            'address': 'location',
            'contact': 'phone_number',
            'identification': 'aadhaar_number',
            'financial': 'requested_amount',
            'agricultural': 'land_size'
        }
        return mapping.get(semantic_type, semantic_type)

    def _sanitize_insurance_claim_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stricter sanitization for insurance claim semantic fields.

        This removes obvious header/title artifacts and enforces
        field-specific rules for crop, season, area, location, address,
        and land_size as a conservative safety pass.
        """
        if not fields:
            return fields

        allowed_crops = {
            'paddy', 'wheat', 'rice', 'maize', 'corn', 'sorghum', 'millet',
            'bajra', 'ragi', 'jowar', 'cotton', 'soybean', 'groundnut', 'mustard'
        }
        allowed_seasons = {'kharif', 'rabi', 'summer', 'zaid', 'autumn', 'winter', 'monsoon'}

        def is_header_or_title(val: Any) -> bool:
            if val is None:
                return False
            s = str(val).strip()
            if not s:
                return False
            low = s.lower()
            # Exact/substring header tokens
            header_tokens = [
                'insurance claim form',
                'insurance claim form –',
                'insurance claim form -',
                'policy and farmer field value',
                'field value',
                'policy number pmfby',
                'policy number pmfby',
                'policy number pmfby:',
                'policy number pmfb',
            ]
            if any(tok in low for tok in header_tokens):
                return True
            # Multiline or table-like blobs
            if '\n' in s or '|' in s or '\t' in s or re.search(r'-{3,}', s):
                return True
            # Very short all-caps header-ish
            if s.isupper() and len(s) > 8:
                return True
            return False

        sanitized = {}
        for name, meta in fields.items():
            val = meta.get('value') if isinstance(meta, dict) else meta
            conf = meta.get('confidence', 0.0) if isinstance(meta, dict) else 0.0

            # Quick header/title rejection
            if is_header_or_title(val):
                # drop obvious header-like values
                continue

            sval = str(val).strip() if val is not None else ''

            # Field-specific rules
            if name in ('crop_name', 'crop_type'):
                low = sval.lower()
                # Keep only if contains a known crop token
                if any(crop in low for crop in allowed_crops):
                    sanitized[name] = meta
                else:
                    # reject generic title/header text
                    continue
                continue

            if name == 'season':
                low = sval.lower()
                if low in allowed_seasons or any(season in low for season in allowed_seasons):
                    sanitized[name] = meta
                else:
                    # reject non-season strings like headers
                    continue
                continue

            if name == 'area':
                # Accept numeric or area-like tokens only
                if re.search(r'\d', sval) and re.search(r'(acre|hectare|ha|sqm|sq\.m|sqkm|sq\.km)?', sval, re.IGNORECASE):
                    sanitized[name] = meta
                else:
                    continue
                continue

            if name in ('location', 'address'):
                low = sval.lower()
                # Remove policy/reference fragments
                sval = re.sub(r'policy\s*number\s*pmfb[iy]?[:\s\-\w]*', '', sval, flags=re.IGNORECASE)
                sval = re.sub(r'field\s*value[:\s\-\w]*', '', sval, flags=re.IGNORECASE)
                sval = sval.strip(' ,;:\n\t')
                # Reject if left empty or still header-like
                if not sval or is_header_or_title(sval):
                    continue
                # Keep trimmed address
                new_meta = meta.copy() if isinstance(meta, dict) else {'value': sval, 'confidence': conf, 'source': 'sanitized_insurance_address'}
                new_meta['value'] = sval
                sanitized[name] = new_meta
                continue

            if name == 'land_size':
                # If numeric 0 inferred with low confidence, drop
                m = re.search(r'(-?\d+(?:\.\d+)?)', sval)
                if not m:
                    continue
                num = None
                try:
                    num = float(m.group(1))
                except Exception:
                    num = None
                if num is None:
                    continue
                if num == 0.0 and (conf < 0.5 or meta.get('validation', {}).get('confidence', 1.0) < 0.5):
                    # likely fallback-inferred zero
                    continue
                # keep normalized
                nm = meta.copy() if isinstance(meta, dict) else {'value': num, 'confidence': conf, 'source': 'sanitized_land_size'}
                nm['value'] = num
                sanitized[name] = nm
                continue

            # Default: keep the meta as-is
            sanitized[name] = meta

        return sanitized

    def looks_like_header_or_title(self, val: Any) -> bool:
        """Reusable helper: detect header/title-like values across modules."""
        if val is None:
            return False
        s = str(val).strip()
        if not s:
            return False
        low = s.lower()
        header_tokens = [
            'insurance claim form', 'policy and farmer field value', 'field value',
            'policy number pmfb', 'policy number pmfby', 'applicant information', 'personal information'
        ]
        if any(tok in low for tok in header_tokens):
            return True
        if '\n' in s or '|' in s or '\t' in s or re.search(r'-{3,}', s):
            return True
        if s.isupper() and len(s) > 8:
            return True
        return False
