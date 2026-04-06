"""
Extraction Integration Helper
Purpose: Integrates the new unified orchestrator with the existing extraction pipeline

This helper bridges the old extraction service with the new multi-stage pipeline,
ensuring that:
1. Old extraction output is used as a baseline
2. New semantic and validation passes are applied
3. Money extraction is strictly validated
4. Missing fields are authoritative
"""

from typing import Dict, Any, Optional
from app.modules.document_processing.unified_extraction_orchestrator import UnifiedExtractionOrchestrator
from app.modules.document_processing.money_extraction_validator import MoneyExtractionValidator
from app.modules.document_processing.document_schemas import get_schema
import logging


logger = logging.getLogger(__name__)


class ExtractionIntegrationHelper:
    """
    Bridges old and new extraction pipelines
    """
    
    def __init__(self):
        self.orchestrator = UnifiedExtractionOrchestrator()
        self.money_validator = MoneyExtractionValidator()
    
    def enhance_extraction_result(
        self,
        extraction_result: Dict[str, Any],
        document_type: str,
        text_content: str
    ) -> Dict[str, Any]:
        """
        Enhance extraction result with new validation and semantic improvements
        
        Args:
            extraction_result: Original extraction result from extraction_service
            document_type: Document type classification
            text_content: Original text content for context
        
        Returns:
            Enhanced extraction result with:
            - Validated money fields
            - Authoritative missing fields
            - Better structured output
        """
        
        try:
            structured_data = extraction_result.get("structured_data", {})
            extracted_fields = extraction_result.get("extracted_fields", {})
            
            # STEP 1: Validate and sanitize money fields
            sanitized_data = self._sanitize_money_fields(
                structured_data=structured_data,
                extracted_fields=extracted_fields,
                document_type=document_type,
                text_content=text_content
            )
            
            # STEP 2: Calculate authoritative missing fields
            schema = get_schema(document_type) or get_schema("supporting_document")
            extracted_field_names = set(sanitized_data.keys())
            required_field_names = schema.get_required_field_names()
            authoritative_missing = sorted(list(required_field_names - extracted_field_names))
            
            # STEP 3: Build risk flags based on AUTHORITATIVE data
            risk_flags = self._build_authoritative_risk_flags(
                structured_data=sanitized_data,
                missing_fields=authoritative_missing,
                document_type=document_type,
                confidence=extraction_result.get("confidence", 0.5)
            )
            
            # STEP 4: Return enhanced result
            enhanced_result = extraction_result.copy()
            enhanced_result["structured_data"] = sanitized_data
            enhanced_result["missing_fields"] = authoritative_missing
            enhanced_result["risk_flags"] = risk_flags
            enhanced_result["validation_note"] = "Enhanced with strict money validation and authoritative field reconciliation"
            
            return enhanced_result
        
        except Exception as e:
            logger.error(f"Error enhancing extraction: {e}")
            # Return original if enhancement fails
            return extraction_result
    
    def _sanitize_money_fields(
        self,
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any],
        document_type: str,
        text_content: str
    ) -> Dict[str, Any]:
        """
        Remove, validate, or correct money fields based on strict rules
        """
        
        sanitized = {}
        
        for field_name, field_value in structured_data.items():
            # Check if this is a money field
            is_money_field = any(keyword in field_name.lower() for keyword in [
                "amount", "claim", "subsidy", "requested", "compensation", "premium", "loan"
            ])
            
            if is_money_field:
                # Get surrounding text context for this field
                surrounding_text = self._extract_surrounding_context(
                    field_name=field_name,
                    text_content=text_content
                )
                
                # Validate the money field
                is_valid, confidence, reason = self.money_validator.validate_money_extraction(
                    value=field_value,
                    field_name=field_name,
                    surrounding_text=surrounding_text,
                    document_type=document_type
                )
                
                if is_valid:
                    # Normalize the money value
                    normalized = self.money_validator.normalize_money_value(str(field_value))
                    sanitized[field_name] = normalized
                else:
                    # Skip invalid money field
                    logger.debug(f"Rejecting money field {field_name}: {reason}")
                    continue
            else:
                # Non-money fields pass through
                if field_value is not None and str(field_value).strip():
                    sanitized[field_name] = field_value
        
        return sanitized
    
    def _extract_surrounding_context(
        self,
        field_name: str,
        text_content: str,
        context_window: int = 200
    ) -> str:
        """Extract text surrounding field for context analysis"""
        
        if not text_content:
            return ""
        
        # Look for field name in text
        lower_text = text_content.lower()
        lower_field = field_name.lower()
        
        # Find position of field name
        pos = lower_text.find(lower_field)
        if pos == -1:
            # Field name not found, return surrounding text
            start = max(0, len(text_content) // 2 - context_window)
            end = min(len(text_content), start + context_window * 2)
            return text_content[start:end]
        
        # Extract context around field name
        start = max(0, pos - context_window)
        end = min(len(text_content), pos + len(field_name) + context_window)
        
        return text_content[start:end]
    
    def _build_authoritative_risk_flags(
        self,
        structured_data: Dict[str, Any],
        missing_fields: list,
        document_type: str,
        confidence: float
    ) -> list:
        """Build risk flags based on FINAL extracted data"""
        
        risk_flags = []
        
        # Risk 1: Missing required fields
        if missing_fields:
            if len(missing_fields) >= 3:
                risk_flags.append("CRITICAL_MISSING_MULTIPLE_REQUIRED")
            else:
                risk_flags.append(f"WARNING_MISSING_{len(missing_fields)}_REQUIRED")
        
        # Risk 2: Low confidence
        if confidence < 0.5:
            risk_flags.append("WARNING_LOW_EXTRACTION_CONFIDENCE")
        
        # Risk 3: No money field for financial documents
        has_amount = any(k for k in structured_data.keys() if "amount" in k.lower())
        if document_type in ["scheme_application", "subsidy_claim", "insurance_claim"]:
            if not has_amount:
                risk_flags.append("INFO_NO_AMOUNT_EXTRACTED")
        
        # Risk 4: No identity for identity-required documents
        has_identity = "aadhaar_number" in structured_data or "farmer_name" in structured_data
        if document_type in ["scheme_application", "farmer_record"]:
            if not has_identity:
                risk_flags.append("WARNING_NO_IDENTITY_FIELDS")
        
        # Risk 5: Supporting documents should not have financial fields
        if document_type == "supporting_document":
            has_financial = any(k for k in structured_data.keys() if any(word in k.lower() for word in ["amount", "claim", "subsidy"]))
            if has_financial:
                risk_flags.append("WARNING_FINANCIAL_FIELDS_IN_SUPPORTING_DOC")
        
        return risk_flags
