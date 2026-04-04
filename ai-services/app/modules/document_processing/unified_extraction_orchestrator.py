"""
Unified Extraction Orchestrator
Purpose: Orchestrates the multi-stage extraction pipeline using:
- Document schemas for validation
- Candidate extraction engine for candidate collection/scoring
- Semantic extraction for field inference
- Handler specialists for document-specific extraction
- Authoritative validation pass for final output

This orchestrator is the main entry point for extraction and produces
reliable, schema-validated output
"""

from typing import Dict, List, Optional, Any, Set
from .document_schemas import DocumentSchema, get_schema, FieldSchema, FieldType, DOCUMENT_SCHEMAS
from .candidate_extraction_engine import (
    CandidateExtractionEngine, ExtractionCandidate, CandidateSource, ValidationStatus
)
from .semantic_extractor import SemanticExtractor
from .extraction_service import DocumentExtractionService
from .reasoning_engine import ReasoningEngine
import logging


logger = logging.getLogger(__name__)


class UnifiedExtractionOrchestrator:
    """
    Orchestrates multi-stage extraction pipeline:
    
    1. Collect candidates from multiple sources
    2. Validate against document schema
    3. Score and rank candidates
    4. Select best candidate for each field
    5. Validate completeness
    6. Generate reasoning
    """
    
    def __init__(self):
        self.semantic_extractor = SemanticExtractor()
        self.extraction_service = DocumentExtractionService()
        self.reasoning_engine = ReasoningEngine()
        self.document_schemas = DOCUMENT_SCHEMAS
    
    def process_document_unified(
        self,
        text_content: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process document using unified multi-stage extraction pipeline
        
        Args:
            text_content: OCR extracted text
            document_type: Classified document type
            metadata: Additional metadata
        
        Returns:
            Unified extraction result with:
            - structured_data: clean field values
            - extracted_fields: fields with metadata
            - missing_fields: required fields not extracted
            - risk_flags: high-confidence risk indicators
            - reasoning: explanation of extraction process
            - candidate_summary: how many candidates considered for each field
        """
        
        try:
            # Get schema for document type
            schema = get_schema(document_type) or get_schema("supporting_document")
            
            # Initialize candidate engine
            engine = CandidateExtractionEngine()
            
            # Get extraction candidates from existing extraction_service
            existing_extraction = self._get_existing_extraction(text_content, document_type, metadata)
            
            # Get semantic candidates
            semantic_candidates = self._get_semantic_candidates(text_content, document_type)
            
            # Get handler candidates
            handler_candidates = self._get_handler_candidates(text_content, document_type, metadata)
            
            # Collect all candidates into engine
            self._collect_all_candidates(
                engine=engine,
                schema=schema,
                existing_extraction=existing_extraction,
                semantic_candidates=semantic_candidates,
                handler_candidates=handler_candidates,
                document_type=document_type
            )
            
            # Select best candidates
            selected_candidates = engine.select_all_best_candidates()
            
            # Build result
            result = self._build_unified_result(
                engine=engine,
                schema=schema,
                document_type=document_type,
                text_content=text_content,
                metadata=metadata
            )
            
            # Apply authoritative validation pass
            result = self._apply_authoritative_validation(result, schema, document_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Unified extraction error: {e}")
            return self._get_error_result(document_type, str(e))
    
    def _get_existing_extraction(
        self,
        text_content: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get extraction from existing extraction_service"""
        try:
            return self.extraction_service.extract_document(
                text_content=text_content,
                document_type=document_type,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Existing extraction failed: {e}")
            return {"structured_data": {}, "extracted_fields": {}}
    
    def _get_semantic_candidates(
        self,
        text_content: str,
        document_type: str
    ) -> Dict[str, ExtractionCandidate]:
        """Extract semantic candidates"""
        candidates = {}
        
        try:
            semantic_result = self.semantic_extractor.extract_semantic_fields(
                text_content,
                document_type
            )
            
            # Convert semantic fields to candidates
            for field_name, field_data in semantic_result.get("semantic_fields", {}).items():
                value = field_data.get("value")
                confidence = field_data.get("confidence", 0.5)
                semantic_type = field_data.get("semantic_type", "other")
                
                if value is not None:
                    candidate = ExtractionCandidate(
                        value=value,
                        source=CandidateSource.SEMANTIC_EXTRACTOR,
                        confidence=confidence,
                        semantic_type_detected=semantic_type
                    )
                    candidates[field_name] = candidate
        
        except Exception as e:
            logger.warning(f"Semantic extraction failed: {e}")
        
        return candidates
    
    def _get_handler_candidates(
        self,
        text_content: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, ExtractionCandidate]:
        """Extract handler-specific candidates"""
        candidates = {}
        
        try:
            handler = self.extraction_service._get_handler(document_type)
            if handler:
                handler_result = handler.extract_fields(text_content, metadata)
                
                # Convert handler fields to candidates
                for field_name, field_data in handler_result.get("extracted_fields", {}).items():
                    if isinstance(field_data, dict):
                        value = field_data.get("value")
                        confidence = field_data.get("confidence", 0.7)
                    else:
                        value = field_data
                        confidence = 0.7
                    
                    if value is not None:
                        candidate = ExtractionCandidate(
                            value=value,
                            source=CandidateSource.HANDLER_SPECIALIST,
                            confidence=confidence
                        )
                        candidates[field_name] = candidate
        
        except Exception as e:
            logger.warning(f"Handler extraction failed: {e}")
        
        return candidates
    
    def _collect_all_candidates(
        self,
        engine: CandidateExtractionEngine,
        schema: DocumentSchema,
        existing_extraction: Dict[str, Any],
        semantic_candidates: Dict[str, ExtractionCandidate],
        handler_candidates: Dict[str, ExtractionCandidate],
        document_type: str
    ) -> None:
        """Collect candidates from all sources into engine"""
        
        # Get all possible field names from schema
        all_field_names = set(schema.get_all_fields().keys())
        
        # Process each field
        for field_name in all_field_names:
            field_schema = schema.get_all_fields().get(field_name)
            if not field_schema:
                continue
            
            # Collect candidates from existing extraction
            if field_name in existing_extraction.get("structured_data", {}):
                value = existing_extraction["structured_data"][field_name]
                engine.add_candidate(
                    field_name=field_name,
                    value=value,
                    source=CandidateSource.REGEX_FALLBACK,
                    confidence=0.6,
                    semantic_type=field_schema.field_type.value,
                    context={"source": "existing_extraction"}
                )
            
            # Collect semantic candidates
            if field_name in semantic_candidates:
                candidate = semantic_candidates[field_name]
                engine.add_candidate(
                    field_name=field_name,
                    value=candidate.value,
                    source=candidate.source,
                    confidence=candidate.confidence,
                    semantic_type=candidate.semantic_type_detected or field_schema.field_type.value,
                    context=candidate.context
                )
            
            # Collect handler candidates
            if field_name in handler_candidates:
                candidate = handler_candidates[field_name]
                engine.add_candidate(
                    field_name=field_name,
                    value=candidate.value,
                    source=candidate.source,
                    confidence=candidate.confidence,
                    semantic_type=candidate.semantic_type_detected or field_schema.field_type.value,
                    context=candidate.context
                )
    
    def _build_unified_result(
        self,
        engine: CandidateExtractionEngine,
        schema: DocumentSchema,
        document_type: str,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build unified extraction result"""
        
        # Get extraction result from engine
        extraction_result = engine.get_extraction_result()
        
        # Calculate statistics
        stats = engine.get_extraction_statistics()
        
        # Get missing fields
        required_field_names = schema.get_required_field_names()
        extracted_field_names = set(extraction_result["structured_data"].keys())
        missing_fields = schema.get_missing_fields(extracted_field_names - required_field_names)
        
        # Calculate completeness
        completeness = schema.calculate_completeness(extracted_field_names)
        is_complete = completeness >= schema.completeness_threshold
        
        # Build result
        result = {
            "document_type": document_type,
            "structured_data": extraction_result["structured_data"],
            "extracted_fields": extraction_result["extracted_fields"],
            "missing_fields": missing_fields,
            "extracted_count": len(extracted_field_names),
            "required_count": len(required_field_names),
            "completeness": completeness,
            "is_complete": is_complete,
            "candidate_summary": extraction_result.get("candidate_summary", {}),
            "extraction_statistics": stats,
            "reasoning": self._generate_reasoning(
                schema=schema,
                extracted_fields=extracted_field_names,
                missing_fields=missing_fields,
                document_type=document_type,
                completeness=completeness
            )
        }
        
        return result
    
    def _apply_authoritative_validation(
        self,
        result: Dict[str, Any],
        schema: DocumentSchema,
        document_type: str
    ) -> Dict[str, Any]:
        """
        Apply authoritative validation pass
        
        This is the FINAL validation pass that ensures:
        - missing_fields only contain fields not in structured_data
        - risk_flags are based on final extracted fields
        - reasoning is not contradictory
        - All outputs are consistent
        """
        
        structured_data = result.get("structured_data", {})
        extracted_field_names = set(structured_data.keys())
        required_field_names = schema.get_required_field_names()
        
        # AUTHORITATIVE missing fields
        missing_fields = sorted(list(required_field_names - extracted_field_names))
        
        # Build risk flags based on FINAL data
        risk_flags = []
        
        if len(missing_fields) > 0:
            if len(missing_fields) == len(required_field_names):
                risk_flags.append("CRITICAL_MISSING_ALL_REQUIRED")
            elif len(missing_fields) >= len(required_field_names) * 0.5:
                risk_flags.append("WARNING_MISSING_MULTIPLE_REQUIRED")
            else:
                risk_flags.append(f"INFO_MISSING_{len(missing_fields)}_REQUIRED")
        
        # Update result with authoritative values
        result["missing_fields"] = missing_fields
        result["risk_flags"] = risk_flags
        
        # Build authoritative reasoning
        result["reasoning"] = self._build_authoritative_reasoning(
            schema=schema,
            extracted_fields=extracted_field_names,
            missing_fields=missing_fields,
            structured_data=structured_data,
            document_type=document_type,
            risk_flags=risk_flags
        )
        
        return result
    
    def _generate_reasoning(
        self,
        schema: DocumentSchema,
        extracted_fields: Set[str],
        missing_fields: List[str],
        document_type: str,
        completeness: float
    ) -> List[str]:
        """Generate reasoning for extraction process"""
        reasoning = []
        
        reasoning.append(f"Unified extraction completed for {document_type}")
        reasoning.append(f"Extracted {len(extracted_fields)} fields")
        
        if missing_fields:
            reasoning.append(f"Missing {len(missing_fields)} required fields: {', '.join(missing_fields[:3])}")
        else:
            reasoning.append("All required fields extracted")
        
        reasoning.append(f"Completeness: {completeness:.1%}")
        
        return reasoning
    
    def _build_authoritative_reasoning(
        self,
        schema: DocumentSchema,
        extracted_fields: Set[str],
        missing_fields: List[str],
        structured_data: Dict[str, Any],
        document_type: str,
        risk_flags: List[str]
    ) -> List[str]:
        """Build authoritative reasoning based on final validated data"""
        reasoning = []
        
        reasoning.append(f"Document type: {document_type}")
        reasoning.append(f"Extracted fields: {', '.join(sorted(extracted_fields)[:5])}")
        
        if missing_fields:
            reasoning.append(f"Missing required: {', '.join(missing_fields)}")
        else:
            reasoning.append("All required fields present")
        
        if risk_flags:
            reasoning.append(f"Risk flags: {', '.join(risk_flags)}")
        
        # Document type specific reasoning
        if document_type == "scheme_application":
            if "farmer_name" in extracted_fields and "scheme_name" in extracted_fields:
                reasoning.append("Core scheme application fields present")
        elif document_type == "supporting_document":
            if "issuing_authority" in extracted_fields or "document_reference" in extracted_fields:
                reasoning.append("Supporting document linkage fields identified")
        
        return reasoning
    
    def _get_error_result(self, document_type: str, error_msg: str) -> Dict[str, Any]:
        """Get error result"""
        return {
            "document_type": document_type,
            "structured_data": {},
            "extracted_fields": {},
            "missing_fields": [],
            "error": error_msg,
            "extraction_statistics": {
                "total_candidate_sets": 0,
                "total_candidates": 0,
                "valid_candidates": 0,
                "selected_candidates": 0
            },
            "reasoning": [f"Extraction failed: {error_msg}"]
        }
