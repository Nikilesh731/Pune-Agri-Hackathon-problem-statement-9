"""
Document Processors - Production Workflow Engine
Contains document processing logic and workflow management for agriculture document-processing pipeline
"""
import time
import uuid
import re
from typing import Dict, Any, Optional, List

from .utils import normalize_ocr_text


class DocumentProcessor:
    """Production workflow engine for agriculture document-processing pipeline"""
    
    def __init__(self, classification_service, extraction_service):
        self.classification_service = classification_service
        self.extraction_service = extraction_service
        
        # Processing configuration
        self.min_confidence_threshold = 0.3
        self.max_processing_time_ms = 30000  # 30 seconds
        self.supported_file_types = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.txt', '.doc', '.docx']
    
    def process_document_workflow(
        self,
        file_data: bytes,
        filename: str,
        processing_type: str = "full_process",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main document processing workflow"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate input
            validation_result = self._validate_input(file_data, filename, processing_type, options or {})
            if not validation_result['valid']:
                processing_time = (time.time() - start_time) * 1000
                return self._create_error_result(request_id, validation_result['error'], processing_time, processing_type, filename)
            
            # Get OCR text
            ocr_text = self._get_ocr_text(file_data, options or {})
            ocr_text_provided = bool(options and "ocr_text" in options and options["ocr_text"])
            
            # If OCR text empty after honest extraction -> return error
            if not ocr_text.strip():
                processing_time = (time.time() - start_time) * 1000
                return self._create_error_result(request_id, "No OCR text available for processing", processing_time, processing_type, filename)
            
            # Normalize OCR text
            normalized_text = normalize_ocr_text(ocr_text)
            
            # Classify document
            classification_result = self.classification_service.classify_document(
                text=normalized_text, 
                filename=filename
            )
            document_type = classification_result['document_type']
            classification_confidence = classification_result['classification_confidence']
            classification_reasoning = classification_result['classification_reasoning']
            
            # If processing_type == "classify", return minimal data block
            if processing_type == "classify":
                processing_time = (time.time() - start_time) * 1000
                minimal_data = {
                    "document_type": document_type,
                    "classification_confidence": classification_confidence,
                    "classification_reasoning": classification_reasoning,
                    "structured_data": {},
                    "extracted_fields": {},
                    "missing_fields": [],
                    "risk_flags": [],
                    "confidence": classification_confidence,
                    "reasoning": ["Classification completed"],
                    "decision_support": {
                        "decision": "review",
                        "confidence": classification_confidence,
                        "reasoning": ["Classification-only mode"]
                    },
                    "validation_summary": {
                        "has_errors": False,
                        "error_count": 0,
                        "errors": [],
                        "missing_field_count": 0,
                        "has_required_identity": False
                    },
                    "canonical": {}  # CRITICAL: Add canonical field for backend contract consistency
                }
                metadata = self._generate_metadata(file_data, processing_time, filename, document_type, classification_confidence, ocr_text_provided)
                return self._create_success_result(request_id, processing_time, processing_type, filename, minimal_data, metadata)
            
            # Full extraction for "full_process" and "extract_structured"
            extraction_result = self.extraction_service.extract_document(
                text_content=normalized_text,
                document_type=document_type,
                metadata=options or {}
            )
            
            structured_data = extraction_result['structured_data']
            extracted_fields = extraction_result['extracted_fields']
            missing_fields = extraction_result['missing_fields']
            confidence = extraction_result['confidence']
            reasoning = extraction_result['reasoning']
            
            # Build validation summary
            validation_summary = self._build_validation_summary(document_type, structured_data, missing_fields)
            
            # Handle different processing types
            if processing_type == "extract_structured":
                # Extraction-only mode: skip risk flags and decision support
                risk_flags = []
                decision_support = {
                    "decision": "review",
                    "confidence": confidence,
                    "reasoning": ["Extraction-only mode"]
                }
            else:
                # Full process mode: include risk flags and decision support
                risk_flags = self._build_risk_flags(document_type, structured_data, confidence, missing_fields)
                # Decision support now considers document type and core-field presence
                decision_support = self._build_decision_support(document_type, confidence, missing_fields, risk_flags, structured_data)
            
            # Supporter-document-specific canonical shaping and safe-field filtering
            canonical = structured_data
            # Final document-type-specific cleanup and canonical shaping
            if document_type == 'insurance_claim':
                # Remove any subsidy-specific fields from insurance claim results
                for fld in ['subsidy_amount', 'subsidy_type']:
                    structured_data.pop(fld, None)
                    extracted_fields.pop(fld, None)

                # Tighten location fields using sanitizer; if result empty, remove
                for loc_field in ['location', 'village', 'district', 'address']:
                    if loc_field in structured_data:
                        clean_loc = self.extraction_service.sanitize_location_value(structured_data.get(loc_field)) if hasattr(self, 'extraction_service') else None
                        # Fallback to local simple sanitizer
                        if not clean_loc:
                            # Try simple normalization
                            clean_loc = structured_data.get(loc_field)
                            if isinstance(clean_loc, str) and ('\n' in clean_loc or 'field value' in clean_loc.lower() or 'claimant' in clean_loc.lower()):
                                clean_loc = None
                        if clean_loc:
                            structured_data[loc_field] = clean_loc
                        else:
                            structured_data.pop(loc_field, None)
                            extracted_fields.pop(loc_field, None)

                # Remove agricultural junk fields if they appear noisy
                for ag in ['area', 'season', 'crop_type', 'land_size']:
                    if ag in structured_data:
                        sval = str(structured_data.get(ag))
                        if '\n' in sval or '|' in sval or len(sval) > 200:
                            structured_data.pop(ag, None)
                            extracted_fields.pop(ag, None)
            if document_type == 'supporting_document':
                # Keep only safe fields in structured output
                safe_fields = [
                    'farmer_name', 'aadhaar_number', 'mobile_number', 'contact_number',
                    'document_reference', 'document_type_detail', 'bank_name', 'ifsc',
                    'account_number', 'issuing_authority'
                ]
                filtered_structured = {k: v for k, v in structured_data.items() if k in safe_fields and v}

                # Remove any non-safe extracted fields
                for k in list(extracted_fields.keys()):
                    if k not in safe_fields:
                        extracted_fields.pop(k, None)

                # Build canonical minimal object for supporting documents
                canonical = {
                    'applicant': {
                        'name': filtered_structured.get('farmer_name') or ''
                    },
                    'document_meta': {
                        'supporting_doc_type': filtered_structured.get('document_type_detail') or ''
                    },
                    'request': {
                        'request_type': 'supporting_document_linkage'
                    }
                }

                # Update structured_data to filtered view to avoid leaking claim-like fields
                structured_data = filtered_structured

                # Decision support: only add explicit linkage reasoning when linkage fields present
                linkage_fields = ['document_reference', 'account_number', 'ifsc', 'aadhaar_number']
                if any(f in structured_data for f in linkage_fields):
                    decision_support = {
                        'decision': 'review',
                        'confidence': confidence,
                        'reasoning': [
                            'Supporting document requires linkage validation to the main farmer application.'
                        ]
                    }
                else:
                    decision_support = {
                        'decision': 'review',
                        'confidence': confidence,
                        'reasoning': []
                    }

            # Ensure canonical.request.request_type for insurance claims
            if document_type == 'insurance_claim':
                if not isinstance(canonical, dict):
                    canonical = {}
                req = canonical.get('request', {})
                req['request_type'] = 'claim_request'
                canonical['request'] = req
                # FINAL DOCUMENT-TYPE FILTER: remove low-confidence header/title junk
                def _looks_like_header_title(v: Any) -> bool:
                    if v is None:
                        return False
                    try:
                        s = str(v).strip()
                    except Exception:
                        return False
                    if not s:
                        return False
                    low = s.lower()
                    title_tokens = [
                        'insurance claim form', 'insurance claim form –', 'insurance claim form -',
                        'insurance claim form – weather damage', 'insurance claim form - weather damage',
                        'field value', 'policy and farmer field value', 'policy number pmfb', 'policy number pmfby'
                    ]
                    if any(tok in low for tok in title_tokens):
                        return True
                    if '\n' in s or '|' in s or '\t' in s or re.search(r'-{3,}', s):
                        return True
                    return False

                # Remove extracted_fields entries with low confidence that match header/title
                removal_threshold = 0.5
                for fld in list(extracted_fields.keys()):
                    meta = extracted_fields.get(fld)
                    if isinstance(meta, dict):
                        conf = meta.get('confidence', 0.0)
                        val = meta.get('value')
                        if conf < removal_threshold and _looks_like_header_title(val):
                            extracted_fields.pop(fld, None)
                            structured_data.pop(fld, None)
                            canonical.pop(fld, None)

                # Also prune canonical top-level fields that are header-like and appear low-quality in structured_data
                for fld in list(canonical.keys()):
                    if fld in structured_data and fld not in extracted_fields:
                        val = structured_data.get(fld)
                        if _looks_like_header_title(val):
                            canonical.pop(fld, None)
                            structured_data.pop(fld, None)
            elif document_type == 'subsidy_claim':
                # Remove insurance-only fields from subsidy claims
                for ins_f in ['claim_amount', 'claim_type', 'loss_description', 'policy', 'requested_amount']:
                    structured_data.pop(ins_f, None)
                    extracted_fields.pop(ins_f, None)

            # Assemble full data block
            data = {
                "document_type": document_type,
                "classification_confidence": classification_confidence,
                "classification_reasoning": classification_reasoning,
                "structured_data": structured_data,
                "extracted_fields": extracted_fields,
                "missing_fields": missing_fields,
                "risk_flags": risk_flags,
                "confidence": confidence,
                "reasoning": reasoning,
                "decision_support": decision_support,
                "validation_summary": validation_summary,
                "canonical": canonical  # CRITICAL: Add canonical field for backend contract
            }

            # FINAL DOCUMENT-FAMILY SANITIZATION PASS - final authority before output/persistence
            try:
                sanitized = self.extraction_service.sanitize_by_document_family(document_type, data, normalized_text)
                if isinstance(sanitized, dict):
                    data = sanitized

                # Recompute derived structures (validation, risk, decision) from final data
                structured_data = data.get('structured_data', {}) or {}
                extracted_fields = data.get('extracted_fields', {}) or {}
                missing_fields = data.get('missing_fields', []) or []

                # Recompute validation summary and decision artifacts
                validation_summary = self._build_validation_summary(document_type, structured_data, missing_fields)

                if processing_type == "extract_structured":
                    risk_flags = []
                    decision_support = {
                        "decision": "review",
                        "confidence": data.get('confidence', confidence),
                        "reasoning": ["Extraction-only mode"]
                    }
                else:
                    risk_flags = self._build_risk_flags(document_type, structured_data, data.get('confidence', confidence), missing_fields)
                    decision_support = self._build_decision_support(document_type, data.get('confidence', confidence), missing_fields, risk_flags, structured_data)

                data['structured_data'] = structured_data
                data['extracted_fields'] = extracted_fields
                data['missing_fields'] = missing_fields
                data['validation_summary'] = validation_summary
                data['risk_flags'] = risk_flags
                data['decision_support'] = decision_support

            except Exception as e:
                # Do not fail the entire processing pipeline when sanitization has a bug.
                data.setdefault('reasoning', [])
                data['reasoning'].append(f"Sanitization step failed: {str(e)}")

            processing_time = (time.time() - start_time) * 1000
            metadata = self._generate_metadata(file_data, processing_time, filename, document_type, confidence, ocr_text_provided)

            return self._create_success_result(request_id, processing_time, processing_type, filename, data, metadata)
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return self._create_error_result(request_id, str(e), processing_time, processing_type, filename)
    
    def _validate_input(self, file_data: bytes, filename: str, processing_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input parameters"""
        if not filename:
            return {'valid': False, 'error': 'No filename provided'}
        
        if file_data and len(file_data) > 50 * 1024 * 1024:  # 50MB limit
            return {'valid': False, 'error': 'File size exceeds 50MB limit'}
        
        # Check file type
        file_extension = filename.lower().split('.')[-1]
        if f'.{file_extension}' not in self.supported_file_types:
            return {'valid': False, 'error': f'Unsupported file type: {file_extension}'}
        
        if processing_type not in ['full_process', 'classify', 'extract_structured']:
            return {'valid': False, 'error': f'Unsupported processing type: {processing_type}'}
        
        # Allow empty file_data ONLY if options contains a non-empty "ocr_text"
        if not file_data:
            ocr_text = options.get('ocr_text')
            if not ocr_text or (isinstance(ocr_text, str) and not ocr_text.strip()):
                return {'valid': False, 'error': 'No file data provided and no OCR text in options'}
        
        return {'valid': True, 'error': None}
    
    def _get_ocr_text(self, file_data: bytes, options: Dict[str, Any]) -> str:
        """Get OCR text honestly"""
        # NOTE:
        # Binary files (PDF/images) require upstream OCR service.
        # This processor does NOT perform OCR itself.
        
        # If options contains "ocr_text", normalize and return it
        if "ocr_text" in options:
            ocr_text = options["ocr_text"]
            if isinstance(ocr_text, list):
                return normalize_ocr_text(ocr_text)
            elif isinstance(ocr_text, dict):
                return normalize_ocr_text(ocr_text.get("text") or ocr_text.get("raw_text") or "")
            elif not isinstance(ocr_text, str):
                return normalize_ocr_text(str(ocr_text))
            else:
                return normalize_ocr_text(ocr_text)
        
        # If file_data appears to be plain text, decode and normalize it
        if file_data:
            try:
                decoded_text = file_data.decode('utf-8')
                # Check if it looks like text content, not binary
                if decoded_text and not decoded_text.startswith('%PDF') and len(decoded_text) > 10:
                    return normalize_ocr_text(decoded_text)
            except UnicodeDecodeError:
                # Binary files require upstream OCR service
                pass
        
        # Return empty string if no OCR text available
        return ""
    
    def _build_validation_summary(self, document_type: str, structured_data: Dict[str, Any], missing_fields: List[str]) -> Dict[str, Any]:
        """Build validation summary - OPTIMIZED: Early exit for common cases"""
        errors = []
        
        # OPTIMIZATION: Check required fields in single pass
        has_farmer_name = bool(structured_data.get('farmer_name'))
        has_scheme_name = bool(structured_data.get('scheme_name'))
        has_subsidy_type = bool(structured_data.get('subsidy_type'))
        has_requested_amount = bool(structured_data.get('requested_amount'))
        
        # Check for required identity fields
        if not has_farmer_name:
            errors.append("Farmer name is missing")
        
        # Document-specific validations (single pass)
        if document_type == 'scheme_application' and not has_scheme_name:
            errors.append("Scheme name is missing for scheme application")
        elif document_type == 'subsidy_claim':
            if not has_subsidy_type:
                errors.append("Subsidy type is missing for subsidy claim")
            if not has_requested_amount:
                errors.append("Requested amount is missing for subsidy claim")
        
        return {
            "has_errors": len(errors) > 0,
            "error_count": len(errors),
            "errors": errors,
            "missing_field_count": len(missing_fields),
            "has_required_identity": has_farmer_name
        }
    
    def _build_risk_flags(self, document_type: str, structured_data: Dict[str, Any], confidence: float, missing_fields: List[str]) -> List[Dict[str, Any]]:
        """Build risk flags - OPTIMIZED: Single pass field access"""
        risk_flags = []
        
        # OPTIMIZATION: Single pass field access for identity validation
        has_farmer_name = bool(structured_data.get('farmer_name'))
        has_aadhaar = bool(structured_data.get('aadhaar_number'))
        has_scheme_name = bool(structured_data.get('scheme_name'))
        has_subsidy_type = bool(structured_data.get('subsidy_type'))
        has_requested_amount = bool(structured_data.get('requested_amount'))
        missing_fields_count = len(missing_fields)
        
        # Identity validation per document type
        if document_type in ['scheme_application', 'subsidy_claim', 'insurance_claim']:
            if not has_farmer_name and not has_aadhaar:
                risk_flags.append({
                    "code": "missing_identity",
                    "severity": "high",
                    "message": "Missing farmer name and Aadhaar"
                })
            elif not has_farmer_name:
                risk_flags.append({
                    "code": "missing_identity",
                    "severity": "medium",
                    "message": "Missing farmer name"
                })
        else:  # grievance, supporting_document, unknown
            if not has_farmer_name:
                risk_flags.append({
                    "code": "missing_identity",
                    "severity": "medium",
                    "message": "Missing farmer name"
                })
        
        # Low confidence extraction flag
        if confidence < self.min_confidence_threshold:
            risk_flags.append({
                "code": "low_confidence_extraction",
                "severity": "medium",
                "message": f"Extraction confidence ({confidence:.2f}) below threshold ({self.min_confidence_threshold})"
            })
        
        # Incomplete application flag
        if document_type in ['scheme_application', 'subsidy_claim', 'insurance_claim'] and missing_fields_count > 0:
            risk_flags.append({
                "code": "incomplete_application",
                "severity": "medium",
                "message": f"Application missing {missing_fields_count} required fields"
            })
        
        # Missing scheme reference flag only for scheme_application
        if document_type == 'scheme_application' and not has_scheme_name:
            risk_flags.append({
                "code": "missing_scheme_reference",
                "severity": "medium",
                "message": "Scheme application missing scheme name/reference"
            })
        
        # Subsidy claim specific field flags
        if document_type == 'subsidy_claim':
            if not has_subsidy_type:
                risk_flags.append({
                    "code": "missing_subsidy_type",
                    "severity": "medium",
                    "message": "Subsidy claim missing subsidy type"
                })
            if not has_requested_amount:
                risk_flags.append({
                    "code": "missing_requested_amount",
                    "severity": "medium",
                    "message": "Subsidy claim missing requested amount"
                })
        
        return risk_flags
    
    def _build_decision_support(self, document_type: str, confidence: float, missing_fields: List[str], risk_flags: List[Dict[str, Any]], structured_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build decision support with document-type-aware rules

        For insurance claims we avoid defaulting to a vague 'review' when core
        fields are present and no major validation issues exist. We still keep
        careful checks for low confidence and high-severity risk flags.
        """
        reasoning = []

        # Reject quickly on very low confidence
        if confidence < 0.2:
            decision = "reject"
            reasoning.append(f"Very low extraction confidence: {confidence:.2f}")
            return {"decision": decision, "confidence": confidence, "reasoning": reasoning}

        # High-risk with many missing fields
        if any(flag.get("severity") == "high" for flag in risk_flags) and len(missing_fields) > 5:
            decision = "reject"
            reasoning.append("High-risk identity failure with too many missing fields")
            return {"decision": decision, "confidence": confidence, "reasoning": reasoning}

        # Document-type specific handling
        if document_type == 'insurance_claim':
            # Prioritize core insurance fields
            core_fields = [
                'farmer_name', 'aadhaar_number', 'mobile_number',
                'claim_amount', 'requested_amount', 'claim_type', 'loss_description'
            ]
            core_present = sum(1 for f in core_fields if structured_data and structured_data.get(f))
            major_missing = any(f in missing_fields for f in ['farmer_name', 'claim_type', 'loss_description'])
            high_severity_flags = any(flag.get('severity') == 'high' for flag in risk_flags)

            # If core fields are reasonably present and there are no high-severity flags,
            # avoid a vague 'Requires manual verification' and provide a document-aware reason.
            if core_present >= 4 and not high_severity_flags:
                # If extraction is strong and no flags, approve; otherwise request targeted review with meaningful reason
                if not risk_flags and confidence >= 0.75:
                    decision = 'approve'
                    reasoning = [f'High confidence insurance claim extraction: {confidence:.2f}']
                else:
                    decision = 'review'
                    reasoning = [
                        'Insurance claim appears structurally complete and is ready for officer review.'
                    ]
                    if risk_flags:
                        reasoning.append(f'Risk flags: {len(risk_flags)}')
                    if missing_fields:
                        reasoning.append(f'Missing fields: {len(missing_fields)}')

                return {"decision": decision, "confidence": confidence, "reasoning": reasoning}

        # Fallback generic decision logic for other document types
        decision = "review"
        if risk_flags:
            reasoning.append(f"Risk flags identified: {len(risk_flags)}")
        if missing_fields:
            reasoning.append(f"Missing fields: {len(missing_fields)}")

        # Only approve if no issues and high confidence
        if not risk_flags and not missing_fields and confidence >= 0.75:
            decision = "approve"
            reasoning = [f"High confidence extraction: {confidence:.2f}"]

        return {"decision": decision, "confidence": confidence, "reasoning": reasoning}
    
    def _generate_metadata(self, file_data: bytes, processing_time_ms: float, filename: str, document_type: str, confidence: float, ocr_text_provided: bool) -> Dict[str, Any]:
        """Generate processing metadata"""
        file_size = len(file_data) if file_data else 0
        
        return {
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "processing_time_ms": processing_time_ms,
            "processing_time_seconds": round(processing_time_ms / 1000, 2),
            "filename": filename,
            "document_type": document_type,
            "ocr_text_provided": ocr_text_provided,
            "extraction_confidence": confidence
        }
    
    def _create_success_result(
        self,
        request_id: str,
        processing_time_ms: float,
        processing_type: str,
        filename: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create successful processing result"""
        return {
            "request_id": request_id,
            "success": True,
            "processing_time_ms": processing_time_ms,
            "processing_type": processing_type,
            "filename": filename,
            "data": data,
            "metadata": metadata,
            "error_message": None
        }
    
    def _create_error_result(
        self,
        request_id: str,
        error_message: str,
        processing_time_ms: float,
        processing_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create error processing result"""
        return {
            "request_id": request_id,
            "success": False,
            "processing_time_ms": processing_time_ms,
            "processing_type": processing_type,
            "filename": filename,
            "data": None,
            "metadata": {},
            "error_message": error_message
        }
    
    def process_batch_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple documents in batch"""
        results = []
        
        for doc in documents:
            file_data = doc.get('file_data')
            filename = doc.get('filename', f'document_{len(results)+1}')
            processing_type = doc.get('processing_type', 'full_process')
            options = doc.get('options', {})
            
            result = self.process_document_workflow(file_data, filename, processing_type, options)
            results.append(result)
        
        return results
    
    def get_processing_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate processing statistics for batch results"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', False)]
        
        total_processing_time = sum(r.get('processing_time_ms', 0) for r in results)
        
        # Calculate average confidence from successful results
        confidences = []
        for result in successful_results:
            if result.get('data') and result['data'].get('confidence') is not None:
                confidences.append(result['data']['confidence'])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_documents": len(results),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0,
            "total_processing_time_ms": total_processing_time,
            "average_processing_time_ms": total_processing_time / len(results) if results else 0,
            "average_confidence": round(avg_confidence, 3),
            "processing_errors": [r.get('error_message', 'Unknown error') for r in failed_results]
        }
