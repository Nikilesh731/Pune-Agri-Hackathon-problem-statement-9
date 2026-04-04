"""
Candidate Extraction & Scoring Engine
Purpose: Multi-stage extraction pipeline that collects candidates from multiple sources
and selects the best valid candidate based on semantic scoring

This is the heart of the new extraction architecture - replacing regex-as-primary with
a multi-source candidate approach.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re


class CandidateSource(Enum):
    """Source of a candidate extraction"""
    SEMANTIC_EXTRACTOR = "semantic_extractor"
    LAYOUT_ANALYZER = "layout_analyzer"
    HANDLER_SPECIALIST = "handler_specialist"
    BOUNDARY_LABEL = "boundary_label"
    REGEX_FALLBACK = "regex_fallback"
    KEYWORD_MATCH = "keyword_match"


class ValidationStatus(Enum):
    """Result of field validation"""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_RANGE = "invalid_range"
    CONTAMINATED = "contaminated"
    SEMANTIC_REJECTION = "semantic_rejection"
    CONTEXT_REJECTION = "context_rejection"
    REJECTED_ALTERNATIVE = "rejected_alternative"


@dataclass
class ExtractionCandidate:
    """Represents a single candidate value for a field"""
    value: Any
    source: CandidateSource
    confidence: float  # 0.0 to 1.0
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)  # Context where value was found
    rejection_reason: Optional[str] = None
    semantic_type_detected: Optional[str] = None  # e.g., "person_name", "mobile", "amount"
    
    def is_valid(self) -> bool:
        """Check if candidate passed validation"""
        return self.validation_status == ValidationStatus.VALID
    
    def get_score(self) -> float:
        """Calculate composite score for ranking"""
        if not self.is_valid():
            return 0.0
        
        # Higher confidence source = higher score
        source_weights = {
            CandidateSource.SEMANTIC_EXTRACTOR: 1.0,
            CandidateSource.LAYOUT_ANALYZER: 0.95,
            CandidateSource.HANDLER_SPECIALIST: 0.9,
            CandidateSource.BOUNDARY_LABEL: 0.85,
            CandidateSource.KEYWORD_MATCH: 0.7,
            CandidateSource.REGEX_FALLBACK: 0.5,
        }
        
        source_weight = source_weights.get(self.source, 0.5)
        return self.confidence * source_weight


@dataclass
class CandidateSet:
    """Collection of candidates for a single field"""
    field_name: str
    candidates: List[ExtractionCandidate] = field(default_factory=list)
    selected_candidate: Optional[ExtractionCandidate] = None
    selection_reason: str = ""
    
    def add_candidate(self, candidate: ExtractionCandidate) -> None:
        """Add a candidate for consideration"""
        self.candidates.append(candidate)
    
    def get_valid_candidates(self) -> List[ExtractionCandidate]:
        """Get only valid (non-rejected) candidates"""
        return [c for c in self.candidates if c.is_valid()]
    
    def select_best(self) -> Optional[ExtractionCandidate]:
        """Select best valid candidate"""
        valid = self.get_valid_candidates()
        if not valid:
            return None
        
        # Sort by score (descending)
        sorted_candidates = sorted(valid, key=lambda c: c.get_score(), reverse=True)
        
        if sorted_candidates:
            self.selected_candidate = sorted_candidates[0]
            self.selection_reason = f"Selected from {len(self.candidates)} candidates, {len(valid)} valid, score: {self.selected_candidate.get_score():.3f}"
            return self.selected_candidate
        
        return None
    
    def get_rejected_alternatives_count(self) -> int:
        """Count of rejected alternatives"""
        return len([c for c in self.candidates if c.validation_status == ValidationStatus.REJECTED_ALTERNATIVE])


class CandidateExtractionEngine:
    """
    Multi-stage extraction engine that:
    1. Collects candidates from multiple sources
    2. Validates each candidate
    3. Scores and ranks them
    4. Selects best valid candidate
    """
    
    def __init__(self):
        self.candidate_sets: Dict[str, CandidateSet] = {}
        
        # Semantic rejection patterns - values that should never be field values
        self.semantic_rejections = {
            "person_name": [
                r"^(Applicant|Supporting|Insurance|Claim|Subsidy|Scheme|Application|Document|Information|Details|Personal|Policy|Farmers|Officer|District|Branch|Department|Bank|Mobile|Phone|Contact|Name|Address|Village|District|Amount|From|To|Manager|Reference|Subject|Claimant|Beneficiary|Subject|Header|Title|Page|Form)\s*(Name|Details|Information)?$",
                r"^[A-Z]{2,}$",  # All caps acronyms
                r".*\b(?:office|department|branch|manager|authority|officer)\b.*",
            ],
            "mobile_number": [
                r"^0+$",
                r"^1{10}$",
                r"^\d{4}\s*\d{4}\s*\d{4}$",  # Aadhaar-like pattern
            ],
            "aadhaar_number": [
                r"^0+$",
                r"^1{4}\s*1{4}\s*1{4}$",
            ],
            "money": [
                r"^(2020|2021|2022|2023|2024|2025)$",  # Year values
                r"^[a-z]+",  # Starts with letters
            ],
        }
        
        # Context rejection rules - reject if certain patterns in surrounding context
        self.context_rejections = {
            "person_name": [
                "metadata",
                "header",
                "footer",
                "reference_number",
                "document_id",
            ],
        }
    
    def create_candidate_set(self, field_name: str) -> CandidateSet:
        """Create a new candidate set for a field"""
        candidate_set = CandidateSet(field_name=field_name)
        self.candidate_sets[field_name] = candidate_set
        return candidate_set
    
    def get_candidate_set(self, field_name: str) -> CandidateSet:
        """Get candidate set for a field (create if not exists)"""
        if field_name not in self.candidate_sets:
            return self.create_candidate_set(field_name)
        return self.candidate_sets[field_name]
    
    def add_candidate(
        self,
        field_name: str,
        value: Any,
        source: CandidateSource,
        confidence: float,
        semantic_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractionCandidate:
        """
        Add a candidate value for a field
        
        Auto-validates using semantic rules
        """
        candidate_set = self.get_candidate_set(field_name)
        
        # Create candidate
        candidate = ExtractionCandidate(
            value=value,
            source=source,
            confidence=confidence,
            semantic_type_detected=semantic_type,
            context=context or {}
        )
        
        # Apply semantic validation
        self._validate_candidate(candidate, semantic_type or field_name)
        
        # Add to set
        candidate_set.add_candidate(candidate)
        
        return candidate
    
    def _validate_candidate(self, candidate: ExtractionCandidate, field_type: str) -> None:
        """Validate candidate using semantic rules"""
        
        # Check semantic rejection patterns
        rejection_patterns = self.semantic_rejections.get(field_type, [])
        value_str = str(candidate.value).strip()
        
        for pattern in rejection_patterns:
            if re.match(pattern, value_str, re.IGNORECASE):
                candidate.validation_status = ValidationStatus.SEMANTIC_REJECTION
                candidate.validation_message = f"Matched rejection pattern: {pattern}"
                return
        
        # Check context rejection
        context_type = candidate.context.get("type", "")
        if context_type in self.context_rejections.get(field_type, []):
            candidate.validation_status = ValidationStatus.CONTEXT_REJECTION
            candidate.validation_message = f"Found in context: {context_type}"
            return
        
        # Check if contaminated (e.g., contains header junk)
        contamination_indicators = [
            "applicant", "information", "details", "header", "policy",
            "scheme", "claim", "insurance", "subsidy", "form"
        ]
        
        lower_value = value_str.lower()
        contamination_count = sum(1 for ind in contamination_indicators if ind in lower_value)
        
        if contamination_count >= 2:
            candidate.validation_status = ValidationStatus.CONTAMINATED
            candidate.validation_message = "Value appears contaminated with metadata"
            return
        
        # Pass validation
        candidate.validation_status = ValidationStatus.VALID
    
    def select_all_best_candidates(self) -> Dict[str, Optional[ExtractionCandidate]]:
        """
        Select best candidate for each field
        
        Returns:
            Dict mapping field_name -> best_candidate (or None)
        """
        result = {}
        
        for field_name, candidate_set in self.candidate_sets.items():
            best = candidate_set.select_best()
            result[field_name] = best
        
        return result
    
    def get_extraction_result(self) -> Dict[str, Any]:
        """
        Get final extraction result with all fields and metadata
        
        Returns:
            Dict with:
            - structured_data: clean field values
            - extracted_fields: fields with metadata (confidence, source, etc.)
            - candidate_summary: how many candidates were considered for each field
        """
        structured_data = {}
        extracted_fields = {}
        candidate_summary = {}
        
        for field_name, candidate_set in self.candidate_sets.items():
            best = candidate_set.selected_candidate
            
            if best and best.is_valid():
                # Add to structured data
                structured_data[field_name] = best.value
                
                # Add to extracted fields with metadata
                extracted_fields[field_name] = {
                    "value": best.value,
                    "confidence": best.confidence,
                    "source": best.source.value,
                    "semantic_type": best.semantic_type_detected,
                }
                
                candidate_summary[field_name] = {
                    "total_candidates": len(candidate_set.candidates),
                    "valid_candidates": len(candidate_set.get_valid_candidates()),
                    "rejected_alternatives": candidate_set.get_rejected_alternatives_count(),
                    "selection_reason": candidate_set.selection_reason,
                }
        
        return {
            "structured_data": structured_data,
            "extracted_fields": extracted_fields,
            "candidate_summary": candidate_summary,
            "total_candidate_sets": len(self.candidate_sets),
        }
    
    def get_missing_fields(self, required_fields: Set[str]) -> List[str]:
        """Get list of required fields that were not extracted"""
        extracted_field_names = set(
            name for name, candidate_set in self.candidate_sets.items()
            if candidate_set.selected_candidate and candidate_set.selected_candidate.is_valid()
        )
        
        return list(required_fields - extracted_field_names)
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get statistics about extraction process"""
        total_sets = len(self.candidate_sets)
        total_candidates = sum(len(cs.candidates) for cs in self.candidate_sets.values())
        valid_candidates = sum(len(cs.get_valid_candidates()) for cs in self.candidate_sets.values())
        selected = sum(1 for cs in self.candidate_sets.values() if cs.selected_candidate and cs.selected_candidate.is_valid())
        
        avg_candidates_per_field = total_candidates / total_sets if total_sets > 0 else 0
        valid_ratio = valid_candidates / total_candidates if total_candidates > 0 else 0
        selection_ratio = selected / total_sets if total_sets > 0 else 0
        
        return {
            "total_candidate_sets": total_sets,
            "total_candidates": total_candidates,
            "valid_candidates": valid_candidates,
            "selected_candidates": selected,
            "avg_candidates_per_field": round(avg_candidates_per_field, 2),
            "valid_ratio": round(valid_ratio, 3),
            "selection_ratio": round(selection_ratio, 3),
        }
