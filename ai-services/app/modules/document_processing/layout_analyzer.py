"""
Layout Analyzer for Document Generalization
Purpose: Extract semantic structure from diverse document layouts without rigid field boundaries
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class LayoutType(Enum):
    """Document layout patterns"""
    FORM = "form"           # Structured form with labels
    LETTER = "letter"       # Letter/memo format
    TABLE = "table"         # Tabular data
    MIXED = "mixed"         # Mixed layout elements
    UNKNOWN = "unknown"     # Unrecognized layout


@dataclass
class SemanticBlock:
    """Represents a semantic block of content"""
    content: str
    block_type: str        # header, paragraph, field, table_row, etc.
    confidence: float
    position: Dict[str, Any]  # line_start, line_end, char_start, char_end
    metadata: Dict[str, Any]


class LayoutAnalyzer:
    """Analyzes document layout and extracts semantic structure"""
    
    def __init__(self):
        # Layout pattern signatures
        self.layout_patterns = {
            'form_labels': [
                r'^[A-Za-z\s]+:.*$',           # Label: Value
                r'^[A-Za-z\s]+\s*\[.*\].*$',   # Label [Value] 
                r'^[A-Za-z\s]+\s*\(.*\).*$',   # Label (Value)
            ],
            'letter_headers': [
                r'^From:.*$',
                r'^To:.*$', 
                r'^Subject:.*$',
                r'^Date:.*$',
                r'^Ref:.*$'
            ],
            'table_rows': [
                r'^\|.*\|.*$',                 # Pipe-separated
                r'^\s*[A-Za-z\s]+\s+\|\s+.*$', # Column | Value
            ],
            'paragraph_text': [
                r'^[A-Z][a-z].*[.!?]$',        # Sentences
                r'^[A-Z][a-z].*$',             # Title case
            ]
        }
        
        # Semantic field indicators (layout-agnostic)
        self.semantic_indicators = {
            'person_name': [
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b(Mr|Mrs|Ms|Shri|Smt)\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
                r'\bName:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
            ],
            'address': [
                r'\b(Village|Gram|Tehsil|District|State|Pin)\s*:?\s*([A-Za-z\s]+)\b',
                r'\b([A-Za-z\s]+),\s*([A-Za-z\s]+),\s*([A-Z]{2,})\b',
                r'\bPin\s*Code?\s*:?\s*(\d{6})\b'
            ],
            'contact': [
                r'\b(Mobile|Phone|Contact)\s*:?\s*(\d{10})\b',
                r'\b(\d{10})\b',
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'identification': [
                r'\b(Aadhaar|UID)\s*(?:No|Number|#)?\s*:?\s*(\d{4}\s*\d{4}\s*\d{4})\b',
                r'\b(\d{12})\b',
                r'\b(PAN)\s*(?:No|Number|#)?\s*:?\s*([A-Z]{5}\d{4}[A-Z])\b'
            ],
            'financial': [
                r'\b(Rs\.?|INR|₹)\s*(\d+,?\d*(?:\.\d{2})?)\b',
                r'\b(Amount|Sum|Total)\s*:?\s*(\d+,?\d*(?:\.\d{2})?)\b',
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:Rs\.?|INR|₹)?\b',
                r'\b(\d{1,6}(?:\.\d{2})?)\s*(?:thousand|lakh|crore|k|lac)\b'
            ],
            'agricultural': [
                r'\b(Land|Area|Acre|Hectare)\s*:?\s*(\d+(?:\.\d+)?)\s*(?:acre|hectare)?\b',
                r'\b(Crop|Cultivation)\s*:?\s*([A-Za-z\s]+)\b',
                r'\b(Season|Kharif|Rabi|Zaid)\s*:?\s*([A-Za-z\s]+)\b'
            ]
        }
        
        # Contextual patterns for field disambiguation
        self.context_patterns = {
            'scheme_application': [
                r'\b(Scheme|Government|Benefit|Subsidy|Application|Form)\b',
                r'\b(Pradhan Mantri|PM|Kisan|Samman|Nidhi)\b'
            ],
            'grievance': [
                r'\b(Complaint|Grievance|Issue|Problem|Delay|Pending)\b',
                r'\b(Officer|Department|Authority|Request)\b'
            ],
            'insurance_claim': [
                r'\b(Insurance|Claim|Crop|Loss|Damage|Compensation)\b',
                r'\b(Policy|Claimant|Insured|Coverage)\b'
            ],
            'subsidy_claim': [
                r'\b(Subsidy|Grant|Assistance|Financial|Equipment)\b',
                r'\b(Machinery|Tools|Irrigation|Seeds|Fertilizer)\b'
            ]
        }
    
    def analyze_layout(self, text: str) -> Dict[str, Any]:
        """Analyze document layout and detect structure patterns"""
        lines = text.split('\n')
        
        layout_scores = {
            LayoutType.FORM: 0,
            LayoutType.LETTER: 0,
            LayoutType.TABLE: 0,
            LayoutType.MIXED: 0
        }
        
        form_indicators = 0
        letter_indicators = 0  
        table_indicators = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for form patterns
            for pattern in self.layout_patterns['form_labels']:
                if re.match(pattern, line, re.IGNORECASE):
                    form_indicators += 1
                    break
            
            # Check for letter patterns
            for pattern in self.layout_patterns['letter_headers']:
                if re.match(pattern, line, re.IGNORECASE):
                    letter_indicators += 1
                    break
            
            # Check for table patterns
            for pattern in self.layout_patterns['table_rows']:
                if re.match(pattern, line, re.IGNORECASE):
                    table_indicators += 1
                    break
        
        # Calculate scores
        total_lines = len([l for l in lines if l.strip()])
        if total_lines > 0:
            layout_scores[LayoutType.FORM] = form_indicators / total_lines
            layout_scores[LayoutType.LETTER] = letter_indicators / total_lines  
            layout_scores[LayoutType.TABLE] = table_indicators / total_lines
            
            # Mixed layout if multiple patterns present
            patterns_present = sum(1 for score in layout_scores.values() if score > 0.1)
            if patterns_present > 1:
                layout_scores[LayoutType.MIXED] = 0.5
        
        # Determine dominant layout
        dominant_layout = max(layout_scores, key=layout_scores.get)
        confidence = layout_scores[dominant_layout]
        
        return {
            'layout_type': dominant_layout.value,
            'confidence': confidence,
            'scores': {k.value: v for k, v in layout_scores.items()},
            'indicators': {
                'form': form_indicators,
                'letter': letter_indicators,
                'table': table_indicators
            }
        }
    
    def extract_semantic_blocks(self, text: str) -> List[SemanticBlock]:
        """Extract semantic blocks from document text"""
        lines = text.split('\n')
        blocks = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            block_type = self._classify_line_type(line)
            confidence = self._calculate_line_confidence(line, block_type)
            
            block = SemanticBlock(
                content=line,
                block_type=block_type,
                confidence=confidence,
                position={
                    'line_start': i,
                    'line_end': i,
                    'char_start': 0,
                    'char_end': len(line)
                },
                metadata={}
            )
            
            blocks.append(block)
        
        return blocks
    
    def extract_semantic_fields(self, text: str) -> Dict[str, Any]:
        """Extract fields using semantic patterns (layout-agnostic)"""
        extracted_fields = {}
        reasoning = []
        
        for field_type, patterns in self.semantic_indicators.items():
            field_values = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if field_type == 'person_name':
                        # Extract the name group
                        groups = match.groups()
                        value = groups[0] if groups else match.group(0)
                        if len(value.split()) >= 2:  # At least first + last name
                            field_values.append((value, 0.8, f"semantic_pattern_{field_type}"))
                    
                    elif field_type == 'address':
                        groups = match.groups()
                        if groups:
                            value = groups[0] if len(groups) == 1 else ', '.join(groups)
                            field_values.append((value, 0.7, f"semantic_pattern_{field_type}"))
                    
                    elif field_type == 'contact':
                        groups = match.groups()
                        if groups:
                            value = groups[-1]  # Take the last group (usually the actual number)
                            field_values.append((value, 0.9, f"semantic_pattern_{field_type}"))
                    
                    elif field_type == 'identification':
                        groups = match.groups()
                        if groups:
                            value = groups[-1]  # Take the identification number
                            field_values.append((value, 0.9, f"semantic_pattern_{field_type}"))
                    
                    elif field_type == 'financial':
                        groups = match.groups()
                        if groups:
                            value = groups[-1]  # Take the amount
                            # REJECT PHONE NUMBERS - Check if this looks like a phone number
                            clean_value = re.sub(r'[,\s]', '', value)
                            if (clean_value.isdigit() and len(clean_value) == 10 and 
                                clean_value.startswith(('6', '7', '8', '9'))):
                                continue  # Skip phone numbers
                            # REJECT OBVIOUS YEARS
                            if clean_value.isdigit() and 2000 <= int(clean_value) <= 2030:
                                continue  # Skip years
                            field_values.append((value, 0.8, f"semantic_pattern_{field_type}"))
                    
                    elif field_type == 'agricultural':
                        groups = match.groups()
                        if groups:
                            value = groups[-1] if len(groups) > 1 else groups[0]
                            field_values.append((value, 0.7, f"semantic_pattern_{field_type}"))
            
            # Keep the best match for each field type
            if field_values:
                best_value = max(field_values, key=lambda x: x[1])
                extracted_fields[field_type] = {
                    'value': best_value[0],
                    'confidence': best_value[1], 
                    'source': best_value[2]
                }
                reasoning.append(f"Semantic extraction: {field_type} = {best_value[0]}")
        
        return {
            'semantic_fields': extracted_fields,
            'reasoning': reasoning,
            'field_count': len(extracted_fields)
        }
    
    def infer_document_context(self, text: str) -> Dict[str, Any]:
        """Infer document context from semantic patterns"""
        context_scores = {}
        
        for doc_type, patterns in self.context_patterns.items():
            score = 0
            matches = []
            
            for pattern in patterns:
                pattern_matches = re.findall(pattern, text, re.IGNORECASE)
                if pattern_matches:
                    score += len(pattern_matches)
                    matches.extend(pattern_matches)
            
            if score > 0:
                context_scores[doc_type] = {
                    'score': score,
                    'matches': list(set(matches)),  # Unique matches
                    'confidence': min(score / 5, 1.0)  # Normalize to 0-1
                }
        
        # Determine most likely context
        if context_scores:
            best_context = max(context_scores.items(), key=lambda x: x[1]['score'])
            return {
                'inferred_type': best_context[0],
                'confidence': best_context[1]['confidence'],
                'evidence': best_context[1]['matches'],
                'all_scores': context_scores
            }
        
        return {
            'inferred_type': 'unknown',
            'confidence': 0.0,
            'evidence': [],
            'all_scores': {}
        }
    
    def _classify_line_type(self, line: str) -> str:
        """Classify the type of a line"""
        if re.match(r'^[A-Z][A-Z\s]*$', line):  # ALL CAPS
            return 'header'
        elif re.match(r'^[A-Za-z\s]+:.*$', line):  # Label: Value
            return 'field'
        elif re.match(r'^\|.*\|.*$', line):  # Table
            return 'table_row'
        elif len(line) > 50:  # Long text
            return 'paragraph'
        else:
            return 'text'
    
    def _calculate_line_confidence(self, line: str, line_type: str) -> float:
        """Calculate confidence for line classification"""
        base_confidence = 0.7
        
        # Boost confidence for clear patterns
        if line_type == 'field' and ':' in line:
            return 0.9
        elif line_type == 'table_row' and line.count('|') >= 2:
            return 0.9
        elif line_type == 'header' and line.isupper():
            return 0.8
        elif line_type == 'paragraph' and len(line) > 100:
            return 0.8
        
        return base_confidence
