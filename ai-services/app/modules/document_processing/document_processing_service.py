"""
Document Processing Service
Purpose: Clean orchestration layer over rebuilt schema, classifier, extraction service, and processor
"""
from typing import Optional, Dict, Any, List
import uuid
import sys
import os

# Add ML service path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml'))

from .service_schema import DocumentProcessingRequest, DocumentProcessingResult
from .classification_service import DocumentClassificationService
from .extraction_service import DocumentExtractionService
from .processors import DocumentProcessor
from ..ai_assist.llm_assist_service import analyze_application
from ..ai_assist.llm_refinement_service import add_llm_refinement_to_response
from ..intelligence.intelligence_service import IntelligenceService
from .ml_priority import predict_application_priority
from .workflow_service import WorkflowService

# Import new ML service
try:
    from ml_service import analyze_document_risk
    ML_SERVICE_AVAILABLE = True
except ImportError:
    print("ML service not available, using fallback")
    ML_SERVICE_AVAILABLE = False


class DocumentProcessingService:
    """Clean orchestration service for document processing operations"""
    
    def __init__(self):
        # Initialize rebuilt services
        self.classification_service = DocumentClassificationService()
        self.extraction_service = DocumentExtractionService()
        self.intelligence_service = IntelligenceService()
        self.workflow_service = WorkflowService()
        self.processor = DocumentProcessor(
            self.classification_service,
            self.extraction_service
        )

    # --- Defensive helpers -------------------------------------------------
    def _safe_dict(self, val: Any) -> Dict[str, Any]:
        return val if isinstance(val, dict) else {}

    def _safe_list(self, val: Any) -> List[Any]:
        return val if isinstance(val, list) else []

    def _safe_str(self, val: Any) -> str:
        return val if isinstance(val, str) else ""

    def _safe_number(self, val: Any, default: float = 0.0) -> float:
        try:
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                s = val.strip().rstrip('%')
                import re
                s = re.sub(r"[^0-9.\.-]", "", s)
                if s:
                    return float(s)
        except Exception:
            pass
        return float(default)

    def _build_officer_summary(self, extracted_data: Dict[str, Any]) -> str:
        """Build a deterministic, officer-facing summary from extracted fields."""
        structured = self._safe_dict(extracted_data.get("structured_data", {}))
        name = structured.get("farmer_name") or structured.get("applicant_name") or structured.get("applicant") or "Unknown"
        doc_type = extracted_data.get("document_type", "document").replace("_", " ")
        location = structured.get("location") or structured.get("village") or ""
        # requested amount if present
        amount = None
        for f in ["requested_amount", "claim_amount", "subsidy_amount", "amount"]:
            if f in structured and structured.get(f):
                amount = structured.get(f)
                break

        parts = []
        parts.append(f"{name} submitted a {doc_type}.")
        if location:
            parts.append(f"Location: {location}.")
        if amount:
            try:
                amt = self._safe_number(amount)
                parts.append(f"Requested amount extracted: {int(amt) if amt>=1 else amt}.")
            except Exception:
                parts.append(f"Requested amount extracted: {amount}.")

        # If scheme/subsidy specifics are missing, call that out
        if doc_type and ("subsid" in doc_type or "scheme" in doc_type):
            parts.append("Key identity fields are available; subsidy type or application details may be missing.")

        return " ".join(parts)
    
    async def process_document(
        self,
        file_data: bytes,
        filename: str,
        processing_type: str = "full_process",
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentProcessingResult:
        """
        Process document based on specified type
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            processing_type: Type of processing to apply
            options: Additional processing options
        
        Returns:
            DocumentProcessingResult with processing results
        """
        processing_result = self.processor.process_document_workflow(
            file_data, filename, processing_type, options
        )
        
        return self._convert_to_result_format(processing_result)
    
    async def process_batch(
        self,
        documents: List[Dict[str, Any]],
        processing_type: str = "full_process"
    ) -> List[DocumentProcessingResult]:
        """
        Process multiple documents in batch
        
        Args:
            documents: List of document data with metadata
            processing_type: Type of processing to apply
        
        Returns:
            List of DocumentProcessingResult objects
        """
        # Set processing type for each document unless explicitly provided
        for doc in documents:
            if 'processing_type' not in doc:
                doc['processing_type'] = processing_type
        
        batch_results = self.processor.process_batch_documents(documents)
        
        return [self._convert_to_result_format(result) for result in batch_results]
    
    async def classify_document(
        self,
        file_data: bytes,
        filename: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify document type
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            options: Additional options
        
        Returns:
            Document classification result
        """
        result = self.processor.process_document_workflow(
            file_data, filename, "classify", options
        )
        
        if result.get("success", False) and result.get("data"):
            return {
                "document_type": result["data"].get("document_type", "unknown"),
                "classification_confidence": result["data"].get("classification_confidence", 0.0),
                "classification_reasoning": result["data"].get("classification_reasoning", {
                    "keywords_found": [],
                    "structural_indicators": [],
                    "confidence_factors": []
                }),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "request_id": result.get("request_id", "")
            }
        else:
            return {
                "document_type": "unknown",
                "classification_confidence": 0.0,
                "classification_reasoning": {},
                "processing_time_ms": result.get("processing_time_ms", 0),
                "request_id": result.get("request_id", "")
            }
    
    def get_supported_processing_types(self) -> List[Dict[str, str]]:
        """Get supported document processing types"""
        return [
            {
                "type": "full_process",
                "description": "Run complete document processing workflow including classification, extraction, validation, risk flags, and decision support"
            },
            {
                "type": "extract_structured",
                "description": "Classify and extract structured fields without full risk/decision analysis"
            },
            {
                "type": "classify",
                "description": "Classify document type only"
            }
        ]
    
    def get_processing_statistics(self, results: List[DocumentProcessingResult]) -> Dict[str, Any]:
        """Get processing statistics for batch results"""
        # Convert DocumentProcessingResult to processor format
        processor_results = []
        for result in results:
            processor_result = {
                'success': result.success,
                'processing_time_ms': result.processing_time_ms,
                'data': {"confidence": result.data.confidence} if result.data else None,
                'error_message': result.error_message
            }
            processor_results.append(processor_result)
        
        return self.processor.get_processing_statistics(processor_results)
    
    def validate_request(self, request: DocumentProcessingRequest) -> Dict[str, Any]:
        """
        Validate document processing request
        
        Args:
            request: Document processing request
        
        Returns:
            Validation result
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate processing type
        supported_types = ["full_process", "extract_structured", "classify"]
        if request.processing_type not in supported_types:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported processing type: {request.processing_type}")
        
        # Validate options
        if request.options:
            if 'max_file_size' in request.options and request.options['max_file_size'] > 50 * 1024 * 1024:
                validation_result["warnings"].append("Large file size may affect processing performance")
        
        return validation_result
    
    async def process_request(self, request: DocumentProcessingRequest) -> DocumentProcessingResult:
        """
        Process document processing request (main API method)
        
        Args:
            request: Document processing request
        
        Returns:
            DocumentProcessingResult
        """
        # Validate request
        validation = self.validate_request(request)
        if not validation["valid"]:
            return DocumentProcessingResult(
                request_id=str(uuid.uuid4()),
                success=False,
                processing_time_ms=0,
                processing_type=request.processing_type,
                filename=(request.options or {}).get("filename"),
                data=None,
                metadata={},
                error_message="; ".join(validation["errors"])
            )
        
        # Process the document
        file_content = b""  # Empty file content since we're using OCR text from options
        filename = (request.options or {}).get("filename", "uploaded_document")
        
        processing_result = self.processor.process_document_workflow(
            file_content, filename, request.processing_type, request.options or {}
        )
        
        return self._convert_to_result_format(processing_result)
    
    def _convert_to_result_format(self, processing_result: Dict[str, Any]) -> DocumentProcessingResult:
        """
        Convert processor result to DocumentProcessingResult format
        
        Args:
            processing_result: Raw processor result
        
        Returns:
            DocumentProcessingResult model
        """
        data = processing_result.get("data")
        
        # Add LLM analysis if we have extracted data
        if data and isinstance(data, dict):
            try:
                # Get extracted data for LLM analysis - CRITICAL: Preserve all fields including canonical
                extracted_data = {
                    "document_type": data.get("document_type", "unknown"),
                    "structured_data": data.get("structured_data", {}),
                    "extracted_fields": data.get("extracted_fields", {}),
                    "missing_fields": data.get("missing_fields", []),
                    "confidence": data.get("confidence") or data.get("extraction_confidence") or 0,
                    "reasoning": data.get("reasoning", []),
                    "canonical": data.get("canonical", {}),  # CRITICAL: Preserve canonical field
                    "classification_confidence": data.get("classification_confidence", 0),
                    "classification_reasoning": data.get("classification_reasoning", [])
                }
                
                if extracted_data.get("structured_data") or extracted_data.get("canonical"):
                    # Ensure extraction_confidence is set in final output (this is the field in the Pydantic model)
                    data["extraction_confidence"] = extracted_data["confidence"]

                    # Defensive: initialize intelligence outputs with safe defaults
                    summary = ""
                    case_insight = []
                    decision_support = {"decision": "review", "confidence": 0.5, "reasoning": []}
                    predictions = {}

                    # Generate intelligence outputs independently so one failing piece doesn't cascade
                    try:
                        try:
                            tmp_summary = self.intelligence_service.generate_document_summary(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_document_summary failed: {ie}")
                            tmp_summary = None

                        try:
                            tmp_case_insight = self.intelligence_service.generate_case_insight(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_case_insight failed: {ie}")
                            tmp_case_insight = None

                        try:
                            tmp_decision_support = self.intelligence_service.generate_decision_support(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_decision_support failed: {ie}")
                            tmp_decision_support = None

                        try:
                            tmp_predictions = self.intelligence_service.generate_predictions(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_predictions failed: {ie}")
                            tmp_predictions = None

                        # Coerce to safe types and apply defaults
                        summary = self._safe_str(tmp_summary)
                        if not summary:
                            # Deterministic officer summary fallback built from extracted facts
                            summary = self._build_officer_summary(extracted_data)

                        case_insight = self._safe_list(tmp_case_insight)
                        decision_support = self._safe_dict(tmp_decision_support)
                        # Ensure decision_support contract
                        decision_support.setdefault("decision", "review")
                        decision_support.setdefault("confidence", 0.5)
                        if not isinstance(decision_support.get("reasoning"), list):
                            decision_support["reasoning"] = self._safe_list(decision_support.get("reasoning"))

                        predictions = self._safe_dict(tmp_predictions)

                        # Attach intelligence outputs to extracted_data and response data
                        extracted_data["summary"] = summary
                        extracted_data["case_insight"] = case_insight
                        extracted_data["decision_support"] = decision_support
                        extracted_data["predictions"] = predictions
                        extracted_data["decision"] = decision_support.get("decision", "review")

                        if isinstance(data, dict):
                            data["summary"] = summary
                            data["ai_summary"] = summary
                            data["case_insight"] = case_insight
                            data["decision_support"] = decision_support
                            data["predictions"] = predictions
                            data["decision"] = extracted_data["decision"]
                        else:
                            data.summary = summary
                            data.ai_summary = summary
                            data.case_insight = case_insight
                            data.decision_support = decision_support
                            data.predictions = predictions
                            data.decision = extracted_data["decision"]

                    except Exception as e:
                        # Defensive catch-all: keep deterministic summary and facts; do not cascade to full failure
                        print(f"DEBUG: Unexpected intelligence processing error: {e}")
                        # Ensure safe minimal outputs
                        summary = summary or self._build_officer_summary(extracted_data)
                        case_insight = case_insight or []
                        decision_support = self._safe_dict(decision_support)
                        decision_support.setdefault("decision", "review")
                        decision_support.setdefault("confidence", 0.5)
                        predictions = predictions or {}

                        extracted_data["summary"] = summary
                        extracted_data["case_insight"] = case_insight
                        extracted_data["decision_support"] = decision_support
                        extracted_data["predictions"] = predictions
                        extracted_data["decision"] = decision_support.get("decision", "review")

                        if isinstance(data, dict):
                            data["summary"] = summary
                            data["ai_summary"] = summary
                            data["case_insight"] = case_insight
                            data["decision_support"] = decision_support
                            data["predictions"] = predictions
                            data["decision"] = extracted_data["decision"]
                        else:
                            data.summary = summary
                            data.ai_summary = summary
                            data.case_insight = case_insight
                            data.decision_support = decision_support
                            data.predictions = predictions
                            data.decision = extracted_data["decision"]

                    # RANDOM FOREST ML INTEGRATION (separate, defensive)
                    if ML_SERVICE_AVAILABLE:
                        try:
                            ml_analysis = None
                            try:
                                ml_analysis = analyze_document_risk(extracted_data)
                            except Exception as ml_error:
                                print(f"Random Forest ML call failed: {ml_error}")
                                ml_analysis = {}

                            ml_analysis = self._safe_dict(ml_analysis)

                            # Safe nested fields
                            pte = self._safe_dict(ml_analysis.get("processing_time_estimate", {}))
                            priority_score = self._safe_number(ml_analysis.get("priority_score", 50.0), default=50.0)
                            queue = ml_analysis.get("queue") if isinstance(ml_analysis.get("queue"), str) else "NORMAL"
                            risk_level = ml_analysis.get("risk_level") if isinstance(ml_analysis.get("risk_level"), str) else "Medium"
                            processing_time_days = pte.get("estimated_days") if isinstance(pte.get("estimated_days"), (int, float)) else 2
                            approval_likelihood_num = self._safe_number(ml_analysis.get("approval_likelihood", 50), default=50)
                            approval_likelihood = f"{int(round(approval_likelihood_num))}%"
                            model_confidence = self._safe_number(ml_analysis.get("confidence_score", 0.5), default=0.5)
                            auto_decision = ml_analysis.get("auto_decision") if isinstance(ml_analysis.get("auto_decision"), str) else "manual_review"

                            ml_insights = {
                                "priority_score": priority_score,
                                "queue": queue,
                                "risk_level": risk_level,
                                "processing_time": processing_time_days,
                                "approval_likelihood": approval_likelihood,
                                "model_confidence": model_confidence,
                                "auto_decision": auto_decision,
                                "prediction_method": "random_forest"
                            }

                            # If ML signals high risk, add reasoning and escalate if appropriate
                            if str(risk_level).lower() == "high":
                                if not isinstance(decision_support.get("reasoning"), list):
                                    decision_support["reasoning"] = self._safe_list(decision_support.get("reasoning"))
                                decision_support["reasoning"].append("High risk detected by ML model")
                                # Escalate to manual review only if not an explicit approve
                                if decision_support.get("decision") != "approve":
                                    decision_support["decision"] = "manual_review"
                                    extracted_data["decision"] = "manual_review"
                                    if isinstance(data, dict):
                                        data["decision"] = "manual_review"

                            extracted_data["ml_insights"] = ml_insights
                            if isinstance(data, dict):
                                data["ml_insights"] = ml_insights
                            else:
                                data.ml_insights = ml_insights

                            ml_predictions = {
                                "priority_score": priority_score,
                                "queue": queue,
                                "risk_level": risk_level,
                                "model_confidence": model_confidence,
                                "prediction_method": "random_forest",
                                "processing_time": f"{processing_time_days} days",
                                "approval_likelihood": approval_likelihood
                            }

                            extracted_data["predictions"] = ml_predictions
                            if isinstance(data, dict):
                                data["predictions"] = ml_predictions
                            else:
                                data.predictions = ml_predictions

                        except Exception as ml_error:
                            print(f"Random Forest ML error: {ml_error}")
                            # Fall back to deterministic priority computation (does not overwrite intelligence outputs)
                            self._fallback_ml_priority(extracted_data, data, decision_support)
                    else:
                        # No ML service available -> deterministic fallback
                        self._fallback_ml_priority(extracted_data, data, decision_support)
                
                # Apply supporting document sanitization
                if extracted_data.get("document_type") == "supporting_document":
                    extracted_data = self._sanitize_supporting_document(extracted_data)
                    if isinstance(data, dict):
                        data["structured_data"] = extracted_data.get("structured_data", {})
                        data["extracted_fields"] = extracted_data.get("extracted_fields", {})
                    else:
                        data.structured_data = extracted_data.get("structured_data", {})
                        data.extracted_fields = extracted_data.get("extracted_fields", {})
                    
                    # Add intelligence data to main data object for final response
                    if isinstance(data, dict):
                        data["summary"] = summary
                        data["ai_summary"] = summary
                        data["case_insight"] = case_insight
                        data["decision_support"] = decision_support
                        data["predictions"] = predictions
                        data["decision"] = extracted_data.get("decision", "review")
                    else:
                        data.summary = summary
                        data.ai_summary = summary
                        data.case_insight = case_insight
                        data.decision_support = decision_support
                        data.predictions = predictions
                        data.decision = extracted_data.get("decision", "review")

                    # Run LLM analysis defensively
                    try:
                        ai_output = analyze_application(extracted_data)
                    except Exception as ai_err:
                        print(f"DEBUG: analyze_application failed: {ai_err}")
                        ai_output = {}

                    ai_output = self._safe_dict(ai_output)

                    # Add AI analysis to the main data object (not nested under extracted_data)
                    if isinstance(data, dict):
                        data["ai_summary"] = self._safe_str(ai_output.get("ai_summary", ""))
                    else:
                        data.ai_summary = self._safe_str(ai_output.get("ai_summary", ""))

                    # Merge AI risk flags with existing ones (AI flags come first)
                    ai_risk_flags = self._safe_list(ai_output.get("risk_flags", []))
                    if isinstance(data, dict):
                        existing_risk_flags = self._safe_list(data.get("risk_flags", []))
                        data["risk_flags"] = ai_risk_flags + existing_risk_flags
                    else:
                        existing_risk_flags = data.risk_flags or []
                        data.risk_flags = ai_risk_flags + existing_risk_flags

                    # FIX 1: SINGLE SOURCE OF TRUTH - Deterministic decision_support ALWAYS takes precedence
                    deterministic_decision_support = self._safe_dict(extracted_data.get("decision_support"))
                    ai_decision_support = self._safe_dict(ai_output.get("decision_support"))

                    if deterministic_decision_support:
                        # Ensure top-level decision matches deterministic decision_support (SINGLE SOURCE OF TRUTH)
                        if isinstance(data, dict):
                            data["decision"] = deterministic_decision_support.get("decision", "review")
                        else:
                            data.decision = deterministic_decision_support.get("decision", "review")
                    elif ai_decision_support:
                        # Only use AI decision_support if deterministic one is absent
                        if isinstance(data, dict):
                            data["decision_support"] = ai_decision_support
                            # Sync top-level decision with AI decision_support
                            data["decision"] = ai_decision_support.get("decision", "review")
                        else:
                            data.decision_support = ai_decision_support
                            # Sync top-level decision with AI decision_support
                            data.decision = ai_decision_support.get("decision", "review")
                    
                    # STEP 7: LLM REFINEMENT LAYER - Add advisory block without overriding deterministic truth
                    try:
                        extracted_data_with_refinement = add_llm_refinement_to_response(extracted_data)
                        
                        # Add llm_refinement to main data object
                        if isinstance(data, dict):
                            data["llm_refinement"] = extracted_data_with_refinement.get("llm_refinement", {})
                        else:
                            data.llm_refinement = extracted_data_with_refinement.get("llm_refinement", {})
                            
                    except Exception as e:
                        # LLM refinement failure should not break the pipeline
                        fallback_refinement = {
                            "refined_summary": "LLM refinement temporarily unavailable",
                            "officer_note": "Proceed with deterministic analysis",
                            "consistency_flags": [],
                            "confidence_note": f"LLM refinement failed: {str(e)}"
                        }
                        
                        if isinstance(data, dict):
                            data["llm_refinement"] = fallback_refinement
                        else:
                            data.llm_refinement = fallback_refinement
            except Exception as e:
                # If LLM analysis fails, keep deterministic outputs and add minimal AI fallbacks
                fallback_decision = "review"
                if isinstance(data, dict):
                    data["ai_summary"] = "AI analysis temporarily unavailable"
                    data["risk_flags"] = [{
                        "code": "AI_ANALYSIS_FAILED",
                        "severity": "medium",
                        "message": f"AI analysis failed: {str(e)}"
                    }]
                    # Only set decision_support if not already present
                    if not data.get("decision_support"):
                        data["decision_support"] = {
                            "decision": fallback_decision,
                            "confidence": 0.5,
                            "reasoning": [f"AI analysis failed: {str(e)}"]
                        }
                    # Do not override an existing deterministic decision
                    data.setdefault("decision", fallback_decision)
                else:
                    data.ai_summary = "AI analysis temporarily unavailable"
                    data.risk_flags = [{
                        "code": "AI_ANALYSIS_FAILED",
                        "severity": "medium",
                        "message": f"AI analysis failed: {str(e)}"
                    }]
                    if not getattr(data, "decision_support", None):
                        data.decision_support = {
                            "decision": fallback_decision,
                            "confidence": 0.5,
                            "reasoning": [f"AI analysis failed: {str(e)}"]
                        }
                    if not getattr(data, "decision", None):
                        data.decision = fallback_decision
        
        # STRICT VALIDATION: Ensure all required intelligence fields are present
        if data and (isinstance(data, dict) or hasattr(data, '__dict__')):
            # Convert to dict for easier validation
            data_dict = data if isinstance(data, dict) else data.__dict__
            
            # AMOUNT VALIDATION: remove unrealistic amounts before final output
            structured_data = data_dict.get("structured_data", {})
            amount_fields = ["requested_amount", "claim_amount", "subsidy_amount", "amount"]
            invalid_amount_removed = False
            for amt_field in amount_fields:
                if amt_field in structured_data and structured_data.get(amt_field) is not None and str(structured_data.get(amt_field)).strip():
                    raw_val = structured_data.get(amt_field)
                    try:
                        # Clean numeric value
                        clean = str(raw_val).replace(",", "").replace("₹", "").replace("$", "").strip()
                        import re
                        clean = re.sub(r"[^0-9.]", "", clean)
                        if clean:
                            amount_num = float(clean)
                            if amount_num > 10000000 or amount_num < 100:
                                # Remove invalid amount from both structured_data and extracted_data
                                del structured_data[amt_field]
                                if isinstance(data, dict):
                                    data["structured_data"] = structured_data
                                else:
                                    data.structured_data = structured_data
                                if extracted_data.get("structured_data") and amt_field in extracted_data["structured_data"]:
                                    del extracted_data["structured_data"][amt_field]
                                invalid_amount_removed = True
                    except Exception:
                        # If parsing fails, do not hallucinate or remove
                        pass

            if invalid_amount_removed:
                # Add explicit reasoning about removed invalid amount(s)
                extracted_data.setdefault("reasoning", [])
                extracted_data["reasoning"].append("Invalid amount removed")
                if isinstance(data, dict):
                    data.setdefault("reasoning", [])
                    data["reasoning"].append("Invalid amount removed")
                else:
                    if not getattr(data, "reasoning", None):
                        data.reasoning = []
                    data.reasoning.append("Invalid amount removed")

            # DYNAMIC SCORE: compute score from confidence and missing fields
            try:
                doc_type_for_score = data_dict.get("document_type") or extracted_data.get("document_type", "unknown")
                required_fields_list = self.extraction_service._compute_missing_fields(doc_type_for_score, {})
                required_count = len(required_fields_list) if required_fields_list is not None else 0
                missing_count = len(extracted_data.get("missing_fields", []))
                confidence_val = extracted_data.get("confidence", extracted_data.get("extraction_confidence", 0.0)) or 0.0
                missing_ratio = missing_count / max(required_count, 1)
                score_val = confidence_val * (1 - missing_ratio)
                # Clamp score between 0 and 1
                score_val = max(0.0, min(1.0, score_val))
                # Persist score in both extracted_data and output data
                extracted_data["score"] = score_val
                if isinstance(data, dict):
                    data["score"] = score_val
                else:
                    setattr(data, "score", score_val)
            except Exception:
                pass

            # Validate summary is meaningful (not generic)
            summary = data_dict.get("summary")
            if not summary or "temporarily unavailable" in summary or "scheme application regarding scheme application" in summary:
                # Build a minimal, non-hallucinated officer-facing summary using only extracted fields
                document_type = data_dict.get("document_type", "document")
                structured_data = data_dict.get("structured_data", {}) or {}
                name = structured_data.get("farmer_name") or structured_data.get("applicant_name") or structured_data.get("applicant") or "Unknown"

                fixed_summary = f"Applicant {name} submitted a {document_type.replace('_', ' ')} related request."

                # If an amount exists (and wasn't removed), include it
                amt_val = None
                for af in amount_fields:
                    if af in structured_data and structured_data.get(af) is not None and str(structured_data.get(af)).strip():
                        amt_val = structured_data.get(af)
                        break
                if amt_val:
                    # Format numeric amounts cleanly when possible
                    try:
                        clean_amt = str(amt_val).replace(",", "").replace("₹", "").replace("$", "").strip()
                        import re
                        clean_amt_digits = re.sub(r"[^0-9.]", "", clean_amt)
                        if clean_amt_digits:
                            amt_num = float(clean_amt_digits)
                            if amt_num >= 100:
                                if amt_num >= 100000:
                                    formatted = f"₹{int(amt_num):,}"
                                else:
                                    formatted = f"₹{int(amt_num)}"
                                fixed_summary += f" The requested amount is {formatted}."
                            else:
                                fixed_summary += f" The requested amount is {amt_val}."
                        else:
                            fixed_summary += f" The requested amount is {amt_val}."
                    except Exception:
                        fixed_summary += f" The requested amount is {amt_val}."

                # Include a short list of key fields if present
                important_keys = ["scheme_name", "application_id", "aadhaar_number", "village", "location"]
                key_parts = []
                for k in important_keys:
                    if k in structured_data and structured_data.get(k):
                        key_parts.append(f"{k}: {structured_data.get(k)}")
                if key_parts:
                    fixed_summary += f" Key details include {', '.join(key_parts)}."

                if isinstance(data, dict):
                    data["summary"] = fixed_summary
                    data["ai_summary"] = fixed_summary
                else:
                    data.summary = fixed_summary
                    data.ai_summary = fixed_summary
            
            # Validate decision exists
            decision = data_dict.get("decision")
            if not decision or decision not in ["approve", "review", "reject"]:
                # Auto-fix with conservative decision
                if isinstance(data, dict):
                    data["decision"] = "review"
                else:
                    data.decision = "review"
            
            # Validate ml_insights exists
            ml_insights = data_dict.get("ml_insights")
            if not ml_insights or not isinstance(ml_insights, dict):
                print(f"DEBUG: ml_insights validation failed, using fallback")
                # Auto-fix with fallback ML insights using real deterministic method
                ml_prediction = predict_application_priority(data_dict)
                fallback_ml = {
                    "priority_score": ml_prediction.get("priority_score", 0.4),
                    "queue": ml_prediction.get("queue", "LOW"),
                    "review_type": ml_prediction.get("review_type", "MANUAL_REVIEW"),
                    "model_confidence": ml_prediction.get("model_confidence", 0.4),
                    "prediction_method": ml_prediction.get("prediction_method", "rule_based_fallback")
                }
                # Add generic predictions for non-ML fields
                fallback_ml.update({
                    "processing_time": "3 days",
                    "approval_likelihood": "50%",
                    "risk_level": "Medium"
                })
                if isinstance(data, dict):
                    data["ml_insights"] = fallback_ml
                    data["predictions"] = fallback_ml  # Also update predictions!
                else:
                    data.ml_insights = fallback_ml
                    data.predictions = fallback_ml  # Also update predictions!
            else:
                print(f"DEBUG: ml_insights validation passed, keeping existing")
                # Ensure predictions field matches ml_insights prediction_method
                if isinstance(data, dict):
                    data["predictions"] = {
                        "priority_score": ml_insights.get("priority_score", 0.5),
                        "queue": ml_insights.get("queue", "NORMAL"),
                        "review_type": ml_insights.get("review_type", "AUTO"),
                        "model_confidence": ml_insights.get("model_confidence", 0.5),
                        "prediction_method": ml_insights.get("prediction_method", "trained_random_forest")
                    }
                    # Add generic predictions for non-ML fields
                    data["predictions"].update({
                        "processing_time": ml_insights.get("processing_time", "2 days"),
                        "approval_likelihood": ml_insights.get("approval_likelihood", "50%"),
                        "risk_level": ml_insights.get("risk_level", "Medium")
                    })
                else:
                    data.predictions = {
                        "priority_score": ml_insights.priority_score,
                        "queue": ml_insights.queue,
                        "review_type": ml_insights.review_type,
                        "model_confidence": ml_insights.model_confidence,
                        "prediction_method": ml_insights.prediction_method
                    }
                    # Add generic predictions for non-ML fields
                    data.predictions.update({
                        "processing_time": ml_insights.processing_time,
                        "approval_likelihood": ml_insights.approval_likelihood,
                        "risk_level": ml_insights.risk_level
                    })
            
            # Validate case_insight has at least 3 useful lines
            case_insight = data_dict.get("case_insight", [])
            if not case_insight or len(case_insight) < 3:
                # Auto-fix with basic case insight
                structured_data = data_dict.get("structured_data", {})
                farmer_name = structured_data.get("farmer_name", "Unknown farmer") if structured_data else "Unknown farmer"
                document_type = data_dict.get("document_type", "document")
                
                fixed_insight = [
                    f"Farmer: {farmer_name}",
                    f"Request: {document_type.replace('_', ' ')}",
                    "Status: Requires review"
                ]
                
                if isinstance(data, dict):
                    data["case_insight"] = fixed_insight
                else:
                    data.case_insight = fixed_insight
            
            # WORKFLOW INTEGRATION: Add workflow information
            try:
                workflow_summary = self.workflow_service.get_workflow_summary(data_dict)
                if isinstance(data, dict):
                    data["workflow"] = workflow_summary["workflow"]
                    data["next_steps"] = workflow_summary["next_steps"]
                    data["sla_timeline"] = workflow_summary["sla_timeline"]
                else:
                    data.workflow = workflow_summary["workflow"]
                    data.next_steps = workflow_summary["next_steps"]
                    data.sla_timeline = workflow_summary["sla_timeline"]
            except Exception as e:
                print(f"DEBUG: Workflow integration failed: {e}")
                # Add fallback workflow
                fallback_workflow = {
                    "status": "PENDING_REVIEW",
                    "queue": "NORMAL",
                    "estimated_processing_time": "2 days",
                    "requires_manual_review": True,
                    "risk_level": "Medium"
                }
                if isinstance(data, dict):
                    data["workflow"] = fallback_workflow
                    data["next_steps"] = ["Standard processing", "Review required"]
                    data["sla_timeline"] = {"initial_review": "3-5 business days", "final_decision": "7-10 business days"}
                else:
                    data.workflow = fallback_workflow
                    data.next_steps = ["Standard processing", "Review required"]
                    data.sla_timeline = {"initial_review": "3-5 business days", "final_decision": "7-10 business days"}

        return DocumentProcessingResult(
            request_id=processing_result.get("request_id", ""),
            success=processing_result.get("success", False),
            processing_time_ms=processing_result.get("processing_time_ms", 0),
            processing_type=processing_result.get("processing_type", ""),
            filename=processing_result.get("filename", ""),
            data=data,
            metadata=processing_result.get("metadata", {}),
            error_message=processing_result.get("error_message")
        )
    
    def _fallback_ml_priority(self, extracted_data: Dict[str, Any], data: Any, decision_support: Dict[str, Any], ml_prediction: Dict[str, Any] = None):
        """Deterministic priority routing based on document facts, not generic fallback"""
        
        # Extract key facts from document
        document_type = extracted_data.get("document_type", "unknown")
        missing_fields = extracted_data.get("missing_fields", [])
        risk_flags = extracted_data.get("risk_flags", [])
        classification_confidence = extracted_data.get("classification_confidence", 0.5)
        extraction_confidence = extracted_data.get("extraction_confidence", 0.5)
        structured_data = extracted_data.get("structured_data", {})
        
        # Deterministic routing based on document facts
        # Base priority now derived dynamically from extraction confidence and completeness
        try:
            required_fields_list = self.extraction_service._compute_missing_fields(document_type, {})
            required_count = len(required_fields_list) if required_fields_list is not None else 0
            missing_count_local = len(missing_fields or [])
            base_score = extraction_confidence * (1 - (missing_count_local / max(required_count, 1)))
            base_score = max(0.0, min(1.0, base_score))
        except Exception:
            base_score = 0.5

        priority_score = base_score  # Base score (0..1 scale)
        # Persist computed score for downstream use
        try:
            extracted_data["score"] = base_score
            if isinstance(data, dict):
                data["score"] = base_score
            else:
                setattr(data, "score", base_score)
        except Exception:
            pass
        # Ensure ml_prediction is a dict for safe .get calls
        ml_prediction = self._safe_dict(ml_prediction)

        queue = "NORMAL"
        risk_level = "medium"
        review_type = "AUTO"
        
        # Document-type specific routing
        if document_type == "grievance":
            # Grievances get higher urgency
            priority_score += 0.3
            queue = "HIGH_PRIORITY" if classification_confidence > 0.7 else "NORMAL"
            risk_level = "high" if len(missing_fields) > 2 else "medium"
            
        elif document_type == "supporting_document":
            # Supporting documents get lower priority unless problematic
            priority_score -= 0.2
            queue = "LOW" if len(missing_fields) <= 1 else "NORMAL"
            risk_level = "low" if len(risk_flags) == 0 else "medium"
            
        elif document_type == "scheme_application":
            # Scheme apps based on completeness
            if len(missing_fields) == 0 and classification_confidence > 0.8:
                priority_score += 0.2
                queue = "LOW"
                risk_level = "low"
            elif len(missing_fields) > 3:
                priority_score -= 0.1
                queue = "NORMAL"
                risk_level = "medium"
            else:
                queue = "NORMAL"
                risk_level = "medium"
                
        elif document_type == "subsidy_claim":
            # Subsidy claims need financial validation
            amount_fields = ["requested_amount", "claim_amount", "subsidy_amount"]
            has_amount = any(field in structured_data for field in amount_fields)
            
            if has_amount and len(missing_fields) <= 2:
                priority_score += 0.1
                queue = "NORMAL"
                risk_level = "medium"
            else:
                priority_score -= 0.1
                queue = "NORMAL"  # Still normal for review
                risk_level = "high" if len(missing_fields) > 3 else "medium"
                
        elif document_type == "insurance_claim":
            # Insurance claims get higher review sensitivity
            priority_score += 0.1
            queue = "NORMAL"
            risk_level = "high" if len(missing_fields) > 2 else "medium"
            
        elif document_type == "farmer_record":
            # Farmer records are lower priority unless incomplete
            if len(missing_fields) > 4:
                priority_score -= 0.2
                queue = "LOW"
                risk_level = "medium"
            else:
                queue = "LOW"
                risk_level = "low"
        
        # Confidence-based adjustments
        if classification_confidence > 0.8:
            priority_score += 0.1
        elif classification_confidence < 0.5:
            priority_score -= 0.2
            queue = "NORMAL"  # At least normal review for low confidence
            risk_level = "high"
            
        # Missing fields impact
        if len(missing_fields) == 0:
            priority_score += 0.1
        elif len(missing_fields) > 5:
            priority_score -= 0.3
            queue = "LOW"
            risk_level = "high"
            review_type = "MANUAL_REVIEW"
        elif len(missing_fields) > 3:
            priority_score -= 0.1
            risk_level = "high"
            
        # Risk flags impact
        if len(risk_flags) > 2:
            priority_score -= 0.2
            queue = "LOW"
            risk_level = "high"
            review_type = "MANUAL_REVIEW"
        elif len(risk_flags) > 0:
            priority_score -= 0.1
            risk_level = "medium"
        
        # Decision support alignment - be conservative about forcing manual review
        decision_value = decision_support.get("decision") if isinstance(decision_support, dict) else None
        if decision_value == "reject":
            review_type = "MANUAL_REVIEW"
            queue = "LOW"
            risk_level = "high"
        elif decision_value == "review":
            # Escalate to manual review only when evidence warrants it
            if len(missing_fields) > 3 or len(risk_flags) > 1 or classification_confidence < 0.5:
                review_type = "MANUAL_REVIEW"
                queue = "NORMAL"
            else:
                review_type = "AUTO"
        
        # Clamp priority score to 0-100 range
        priority_score = max(0, min(100, priority_score * 100))
        
        # Override with ML prediction if available and confident
        if ml_prediction and ml_prediction.get("model_confidence", 0) > 0.7:
            priority_score = ml_prediction.get("priority_score", priority_score)
            queue = ml_prediction.get("queue", queue)
            risk_level = ml_prediction.get("risk_level", risk_level).lower()
        
        # Ensure deterministic queue mapping
        if queue not in ["LOW", "NORMAL", "HIGH_PRIORITY"]:
            queue = "NORMAL"
            
        # Ensure risk level consistency
        if risk_level not in ["low", "medium", "high"]:
            risk_level = "medium"
        
        # Ensure ML prediction has required fields
        ml_insights = {
            "priority_score": float(priority_score),
            "queue": queue,
            "review_type": review_type,
            "risk_level": risk_level,
            "processing_time": ml_prediction.get("processing_time", "2 days"),
            "approval_likelihood": ml_prediction.get("approval_likelihood", "50%"),
            "model_confidence": ml_prediction.get("model_confidence", 0.5),
            "prediction_method": ml_prediction.get("prediction_method", "rule_based_fallback")
        }
        
        extracted_data["ml_insights"] = ml_insights
        
        # Also add ML insights to main data object
        if isinstance(data, dict):
            data["ml_insights"] = ml_insights
        else:
            data.ml_insights = ml_insights
        
        # Update predictions with actual deterministic results, not generic fallback
        ml_predictions = {
            "priority_score": priority_score / 100.0,  # Convert back to 0-1 for consistency
            "queue": queue,
            "review_type": review_type,
            "risk_level": risk_level.capitalize(),  # Capitalize for UI consistency
            "model_confidence": 0.8,  # High confidence for rule-based
            "prediction_method": "deterministic_fallback"
        }
        
        # Add document-specific predictions instead of generic ones
        processing_days = 2
        if document_type == "grievance":
            processing_days = 1  # Faster for grievances
        elif document_type == "supporting_document":
            processing_days = 3  # Slower for supporting docs
        elif len(missing_fields) > 3:
            processing_days = 4  # Slower for incomplete docs
        
        # Calculate approval likelihood based on completeness and risk
        approval_likelihood = 50  # Base percentage
        if len(missing_fields) == 0 and risk_level == "low":
            approval_likelihood = 85
        elif len(missing_fields) <= 2 and risk_level == "medium":
            approval_likelihood = 65
        elif risk_level == "high" or len(missing_fields) > 5:
            approval_likelihood = 25
        
        ml_predictions.update({
            "processing_time": f"{processing_days} days",
            "approval_likelihood": f"{approval_likelihood}%",
            "risk_level": risk_level.capitalize()
        })
        
        # Update both extracted_data and main data with ML predictions
        extracted_data["predictions"] = ml_predictions
        if isinstance(data, dict):
            data["predictions"] = ml_predictions
        else:
            data.predictions = ml_predictions

        # AUTHORITATIVE FINAL EVALUATION - Ensure consistency across all fields
        self._authoritative_final_evaluation(extracted_data, data)

    def _authoritative_final_evaluation(self, extracted_data: Dict[str, Any], data: Any):
        """Single authoritative evaluation to ensure missing_fields, risk_flags, and reasoning are consistent"""
        
        document_type = extracted_data.get("document_type", "unknown")
        structured_data = extracted_data.get("structured_data", {})
        
        # Define required fields per document type
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
        
        # Authoritative missing fields evaluation
        authoritative_missing = []
        for field in required_fields:
            field_value = structured_data.get(field)
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                authoritative_missing.append(field)
        
        # Authoritative risk flags based on final missing fields
        authoritative_risk_flags = []
        
        # Add risk flags for missing required fields
        for missing_field in authoritative_missing:
            if document_type in ['scheme_application', 'subsidy_claim', 'insurance_claim'] and missing_field in ['farmer_name', 'scheme_name', 'subsidy_type', 'claim_type']:
                authoritative_risk_flags.append({
                    "code": f"missing_{missing_field}",
                    "severity": "high",
                    "message": f"Critical field {missing_field} is missing for {document_type}"
                })
            else:
                authoritative_risk_flags.append({
                    "code": f"missing_{missing_field}",
                    "severity": "medium",
                    "message": f"Required field {missing_field} is missing"
                })
        
        # Add document-specific risk flags
        classification_confidence = extracted_data.get("classification_confidence", 0.5)
        if classification_confidence < 0.5:
            authoritative_risk_flags.append({
                "code": "low_classification_confidence",
                "severity": "medium",
                "message": "Document classification confidence is low"
            })
        
        # Authoritative reasoning
        authoritative_reasoning = []
        
        if authoritative_missing:
            authoritative_reasoning.append(f"Missing required fields: {', '.join(authoritative_missing)}")
        
        # Add extraction success reasoning
        extracted_fields_count = len([k for k, v in structured_data.items() if v and str(v).strip()])
        if extracted_fields_count > 0:
            field_names = [k for k, v in structured_data.items() if v and str(v).strip()]
            authoritative_reasoning.append(f"Fields extracted: {', '.join(field_names)}")
        
        # Update all data structures with authoritative results
        extracted_data["missing_fields"] = authoritative_missing
        extracted_data["risk_flags"] = authoritative_risk_flags
        extracted_data["reasoning"] = authoritative_reasoning
        
        # Update canonical verification section
        if "canonical" not in extracted_data:
            extracted_data["canonical"] = {}
        extracted_data["canonical"]["verification"] = {
            "missing_fields": authoritative_missing,
            "risk_flags": authoritative_risk_flags,
            "completeness_score": max(0, 100 - (len(authoritative_missing) * 20))
        }
        
        # Update main data object
        if isinstance(data, dict):
            data["missing_fields"] = authoritative_missing
            data["risk_flags"] = authoritative_risk_flags
            data["reasoning"] = authoritative_reasoning
            if "canonical" not in data:
                data["canonical"] = {}
            data["canonical"]["verification"] = extracted_data["canonical"]["verification"]
        else:
            data.missing_fields = authoritative_missing
            data.risk_flags = authoritative_risk_flags
            data.reasoning = authoritative_reasoning
            if not hasattr(data, 'canonical') or data.canonical is None:
                data.canonical = {}
            data.canonical["verification"] = extracted_data["canonical"]["verification"]

    def _sanitize_supporting_document(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize supporting document data to remove financial fields and contaminated metadata
        
        Args:
            extracted_data: Raw extracted data from supporting document
            
        Returns:
            Sanitized extracted data
        """
        sanitized = extracted_data.copy()
        
        # Remove financial fields that may contain identifier-like numbers
        financial_fields_to_remove = [
            "requested_amount", "claim_amount", "subsidy_amount", 
            "loan_amount", "amount", "subsidy_amount"
        ]
        
        structured_data = sanitized.get("structured_data", {})
        extracted_fields = sanitized.get("extracted_fields", {})
        
        # Remove from structured_data
        for field in financial_fields_to_remove:
            structured_data.pop(field, None)
            extracted_fields.pop(field, None)
        
        # Remove contaminated person_name fields that are generic placeholders
        generic_name_patterns = [
            "supporting document", "document", "proof", "receipt", 
            "applicant", "beneficiary", "claimant", "holder"
        ]
        
        # Check and remove generic names
        for field_name in ["farmer_name", "applicant_name", "claimant_name", "complainant"]:
            if field_name in structured_data:
                value = str(structured_data[field_name]).lower().strip()
                if any(pattern in value for pattern in generic_name_patterns):
                    structured_data.pop(field_name, None)
                    extracted_fields.pop(field_name, None)
            
            if field_name in extracted_fields:
                value = str(extracted_fields[field_name]).lower().strip()
                if any(pattern in value for pattern in generic_name_patterns):
                    extracted_fields.pop(field_name, None)
        
        # Remove contaminated location/address fields with metadata markers
        contamination_patterns = [
            "supporting document metadata", "field value", "supporting document type",
            "reference number", "document type", "document meta"
        ]
        
        location_fields = ["location", "village", "district", "address", "place"]
        for field_name in location_fields:
            if field_name in structured_data:
                value = str(structured_data[field_name]).lower()
                if any(pattern in value for pattern in contamination_patterns):
                    structured_data.pop(field_name, None)
                    extracted_fields.pop(field_name, None)
                    
            if field_name in extracted_fields:
                value = str(extracted_fields[field_name]).lower()
                if any(pattern in value for pattern in contamination_patterns):
                    extracted_fields.pop(field_name, None)
        
        # Remove contaminated document_type_detail with multiline junk
        if "document_type_detail" in structured_data:
            value = str(structured_data["document_type_detail"])
            if "\\n" in value or any(pattern in value.lower() for pattern in contamination_patterns):
                structured_data.pop("document_type_detail", None)
                extracted_fields.pop("document_type_detail", None)
                
        if "document_type_detail" in extracted_fields:
            value = str(extracted_fields["document_type_detail"])
            if "\\n" in value or any(pattern in value.lower() for pattern in contamination_patterns):
                extracted_fields.pop("document_type_detail", None)
        
        # Update sanitized data
        sanitized["structured_data"] = structured_data
        sanitized["extracted_fields"] = extracted_fields
        
        return sanitized
