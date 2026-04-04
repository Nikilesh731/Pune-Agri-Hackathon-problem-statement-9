"""
Base Document Handler
Purpose: Abstract base class for all document type handlers in the rebuilt extraction pipeline
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseHandler(ABC):
    """Abstract base class for document type handlers"""
    
    def __init__(self):
        self.required_fields: List[str] = []
        self.optional_fields: List[str] = []
        self.field_synonyms: Dict[str, List[str]] = {}
    
    @abstractmethod
    def get_document_type(self) -> str:
        """Return the standardized document type string this handler handles
        
        Examples:
        - "scheme_application"
        - "farmer_record"
        - "grievance"
        """
        pass
    
    @abstractmethod
    def extract_fields(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract fields from document text
        
        Returns standardized handler result shape:
        {
            "document_type": str,
            "structured_data": Dict[str, Any],
            "extracted_fields": Dict[str, Dict[str, Any]],
            "missing_fields": List[str],
            "confidence": float,
            "reasoning": List[str]
        }
        """
        pass
    
    def build_field(
        self,
        field_name: str,
        value: Any,
        confidence: float,
        source: str
    ) -> Dict[str, Any]:
        """Build a standardized field metadata dictionary
        
        Args:
            field_name: Name of the field
            value: Extracted value
            confidence: Confidence score between 0.0 and 1.0
            source: Source description (e.g., "keyword_matching", "regex")
            
        Returns:
            Standardized field metadata dict
        """
        return {
            "value": value,
            "confidence": self.normalize_confidence(confidence),
            "source": source
        }
    
    def build_result(
        self,
        document_type: str,
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Dict[str, Any]],
        reasoning: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build a standardized handler result dictionary
        
        Args:
            document_type: Document type string
            structured_data: Plain field values for downstream processing
            extracted_fields: Field metadata with confidence and source info
            reasoning: Optional list of reasoning strings
            
        Returns:
            Standardized result dict compatible with extraction_service.py
        """
        # Compute missing fields from required fields
        missing_fields = [
            field for field in self.required_fields
            if self.is_missing(structured_data.get(field))
        ]
        
        # CONFIDENCE LOGIC: ≥0.7 if required fields present, <0.5 otherwise
        if not missing_fields and self.required_fields:
            # All required fields present - high confidence
            overall_confidence = 0.8
        elif missing_fields and self.required_fields:
            # Missing required fields - low confidence
            overall_confidence = 0.4
        elif extracted_fields:
            # No required fields defined, but some fields extracted - medium confidence
            confidences = [
                field_meta.get("confidence", 0.0)
                for field_meta in extracted_fields.values()
            ]
            overall_confidence = sum(confidences) / len(confidences)
        else:
            # No fields extracted
            overall_confidence = 0.0
        
        return {
            "document_type": document_type,
            "structured_data": structured_data,
            "extracted_fields": extracted_fields,
            "missing_fields": missing_fields,
            "confidence": self.normalize_confidence(overall_confidence),
            "reasoning": self.combine_reasoning(reasoning or [])
        }
    
    def get_field_synonyms(self, field_name: str) -> List[str]:
        """Get synonyms for a field name
        
        Args:
            field_name: Base field name
            
        Returns:
            List of synonym strings
        """
        return self.field_synonyms.get(field_name, [])
    
    def is_missing(self, value: Any) -> bool:
        """Check if a value should be considered missing
        
        Args:
            value: Value to check
            
        Returns:
            True if value is missing (None, "", [], {})
        """
        return value is None or value == "" or value == [] or value == {}
    
    def safe_set_field(
        self,
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Dict[str, Any]],
        field_name: str,
        value: Any,
        confidence: float,
        source: str
    ) -> None:
        """Safely set a field in both structured_data and extracted_fields
        
        Only sets the field if value is not missing.
        
        Args:
            structured_data: Dictionary to store plain values
            extracted_fields: Dictionary to store field metadata
            field_name: Name of the field
            value: Extracted value
            confidence: Confidence score
            source: Source description
        """
        if not self.is_missing(value):
            structured_data[field_name] = value
            extracted_fields[field_name] = self.build_field(
                field_name, value, confidence, source
            )
    
    def normalize_confidence(self, confidence: float) -> float:
        """Normalize confidence to [0.0, 1.0] range
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            Clamped confidence value
        """
        return max(0.0, min(1.0, confidence))
    
    def combine_reasoning(self, *parts) -> List[str]:
        """Combine reasoning parts into a flat list
        
        Args:
            *parts: Reasoning strings or lists of strings
            
        Returns:
            Flattened list of non-empty reasoning strings
        """
        combined = []
        for part in parts:
            if isinstance(part, str):
                if part.strip():
                    combined.append(part.strip())
            elif isinstance(part, list):
                for item in part:
                    if isinstance(item, str) and item.strip():
                        combined.append(item.strip())
        
        # Sanitize reasoning: remove duplicates and enforce order
        return self._sanitize_reasoning(combined)
    
    def _sanitize_reasoning(self, reasoning: List[str]) -> List[str]:
        """Sanitize reasoning list to follow strict contract
        
        Args:
            reasoning: Raw reasoning list
            
        Returns:
            Sanitized reasoning list following contract:
            1) "Fields extracted: ..."
            2) "Missing required fields: ..." (ONLY if missing)
        """
        sanitized = []
        seen = set()
        
        for reason in reasoning:
            # Remove "missing required fields: none" messages
            if reason.lower().startswith("missing required fields: none"):
                continue
            
            # Remove duplicates
            if reason in seen:
                continue
            seen.add(reason)
            
            sanitized.append(reason)
        
        # Enforce order: fields extracted first, missing fields second
        fields_extracted = [r for r in sanitized if r.startswith("Fields extracted:")]
        missing_fields = [r for r in sanitized if r.startswith("Missing required fields:")]
        other = [r for r in sanitized if not (r.startswith("Fields extracted:") or r.startswith("Missing required fields:"))]
        
        # Return in proper order
        return fields_extracted + missing_fields + other
