"""
Granite Extraction Service
Purpose: Semantic extraction and reasoning layer using Granite model
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List
import uuid
import requests
import time


class GraniteExtractionService:
    """
    Granite-based semantic extraction service
    
    Responsibilities:
    - Take Docling structured output
    - Prepare Granite prompt
    - Request strict JSON output
    - Return schema-compliant extraction results
    """
    
    def __init__(self, granite_endpoint: Optional[str] = None, model_name: str = "granite"):
        self.logger = logging.getLogger(__name__)
        self.granite_endpoint = granite_endpoint or os.getenv("GRANITE_ENDPOINT")
        self.model_name = model_name
        self._granite_available = None
        self._granite_import_error = None
        self._session = None
        if not self.granite_endpoint:
            self._granite_available = False
            self._granite_import_error = "GRANITE_ENDPOINT not configured"

    def _build_schema_safe_payload(self, raw_text_length: int = 0, reasoning: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "document_type": "unknown",
            "structured_data": {},
            "extracted_fields": {},
            "missing_fields": [],
            "confidence": 0.0,
            "reasoning": reasoning or [],
            "classification_confidence": 0.0,
            "classification_reasoning": {
                "keywords_found": [],
                "structural_indicators": [],
                "confidence_factors": reasoning or [],
            },
            "risk_flags": [
                {
                    "code": "GRANITE_UNAVAILABLE",
                    "severity": "medium",
                    "message": "Granite is unavailable or returned an invalid response",
                }
            ],
            "decision_support": {
                "decision": "manual_review",
                "confidence": 0.0,
                "reasoning": reasoning or ["Granite is unavailable or returned an invalid response"],
            },
            "canonical": {},
            "summary": "Document processed without Granite enrichment",
            "processing_metadata": {
                "processing_method": "granite",
                "model_name": self.model_name,
                "input_text_length": raw_text_length,
                "processing_timestamp": time.time(),
                "granite_unavailable": True,
            },
        }

    def _ensure_schema_compliance(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        defaults = self._build_schema_safe_payload()
        normalized = dict(defaults)
        normalized.update(parsed_response if isinstance(parsed_response, dict) else {})

        if not isinstance(normalized.get("structured_data"), dict):
            normalized["structured_data"] = {}
        if not isinstance(normalized.get("extracted_fields"), dict):
            normalized["extracted_fields"] = {}
        if not isinstance(normalized.get("risk_flags"), list):
            normalized["risk_flags"] = []
        if not isinstance(normalized.get("reasoning"), list):
            normalized["reasoning"] = []
        if not isinstance(normalized.get("missing_fields"), list):
            normalized["missing_fields"] = []
        if not isinstance(normalized.get("canonical"), dict):
            normalized["canonical"] = {}
        if not isinstance(normalized.get("classification_reasoning"), dict):
            normalized["classification_reasoning"] = {
                "keywords_found": [],
                "structural_indicators": [],
                "confidence_factors": [],
            }
        if not isinstance(normalized.get("decision_support"), dict):
            normalized["decision_support"] = {
                "decision": "manual_review",
                "confidence": 0.0,
                "reasoning": ["Schema validation failed"],
            }

        for confidence_field in ["confidence", "classification_confidence"]:
            try:
                normalized[confidence_field] = max(0.0, min(1.0, float(normalized.get(confidence_field, 0.0))))
            except (TypeError, ValueError):
                normalized[confidence_field] = 0.0

        for required_field in ["document_type", "structured_data", "extracted_fields", "confidence", "reasoning"]:
            if required_field not in normalized:
                normalized[required_field] = defaults[required_field]

        return normalized
        
    def _check_granite_availability(self) -> bool:
        """
        Check if Granite service is available with lazy initialization
        """
        if self._granite_available is None:
            try:
                # Test connection to Granite endpoint
                response = requests.get(f"{self.granite_endpoint}/health", timeout=5)
                if response.status_code == 200:
                    self._granite_available = True
                    self.logger.info("[GRANITE] Granite service is available")
                else:
                    self._granite_available = False
                    self._granite_import_error = f"Service returned status {response.status_code}"
                    self.logger.warning(f"[GRANITE] Granite service not healthy: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self._granite_available = False
                self._granite_import_error = str(e)
                self.logger.warning(f"[GRANITE] Granite service not available: {e}")
                
        return self._granite_available
    
    def _get_session(self):
        """
        Get HTTP session for Granite requests
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.timeout = 30  # 30 second timeout
        return self._session
    
    def _prepare_granite_prompt(self, docling_output: Dict[str, Any]) -> str:
        """
        Prepare prompt for Granite extraction
        
        Args:
            docling_output: Structured output from Docling
            
        Returns:
            Formatted prompt string
        """
        raw_text = docling_output.get('raw_text', '')
        sections = docling_output.get('sections', [])
        tables = docling_output.get('tables', [])
        metadata = docling_output.get('metadata', {})
        file_type = metadata.get('file_type', 'unknown')

        input_payload = {
            "raw_text": raw_text,
            "tables": tables,
            "metadata": metadata,
        }
        
        # Build context from Docling output
        context_parts = []
        
        # Add raw text (truncated if too long)
        if raw_text:
            max_text_length = 8000  # Limit context size
            if len(raw_text) > max_text_length:
                raw_text = raw_text[:max_text_length] + "...[truncated]"
            context_parts.append(f"DOCUMENT TEXT:\n{raw_text}")
        
        # Add sections if available
        if sections:
            context_parts.append("\nDOCUMENT STRUCTURE:")
            for i, section in enumerate(sections[:10]):  # Limit sections
                section_text = section.get('text', '')[:200]  # Limit section text
                context_parts.append(f"Section {i+1} ({section.get('type', 'unknown')}): {section_text}")
        
        # Add tables if available
        if tables:
            context_parts.append("\nTABLES:")
            for i, table in enumerate(tables[:5]):  # Limit tables
                context_parts.append(f"Table {i+1}:")
                for j, row in enumerate(table.get('rows', [])[:10]):  # Limit rows
                    context_parts.append(f"  Row {j+1}: {row}")
        
        # Add file type context
        context_parts.append(f"\nFILE TYPE: {file_type}")
        
        # Build the complete prompt
        prompt = f"""
You are an expert agricultural document processor for Indian government schemes and subsidies.

CONTEXT:
{''.join(context_parts)}

INPUT JSON:
{json.dumps(input_payload, ensure_ascii=False, default=str)}

TASK:
Extract structured information from this agricultural document and respond with ONLY valid JSON.

DOCUMENT TYPES TO IDENTIFY:
- pm_kisan_scheme (PM Kisan Samman Nidhi scheme applications)
- subsidy_claim_drip_irrigation (Drip irrigation subsidy claims)
- insurance_claim_crop_loss (Crop insurance claims)
- grievance_delayed_subsidy_payment (Grievances about delayed payments)
- farmer_record_profile (Farmer profile documents)
- supporting_document_land_receipt (Land ownership/receipt documents)
- other_agricultural_document (Other agricultural documents)

EXTRACTED FIELDS TO LOOK FOR:
- farmer_name/applicant_name
- aadhaar_number
- bank_account_number
- ifsc_code
- land_area/hectares/acres
- crop_type
- village/location
- district
- state
- mobile_number
- requested_amount/claim_amount/subsidy_amount
- application_id/reference_number
- date_of_application
- scheme_name

RESPONSE FORMAT (STRICT JSON ONLY):
{{
    "document_type": "detected_document_type",
    "structured_data": {{
        "farmer_name": "extracted_name_or_null",
        "aadhaar_number": "extracted_aadhaar_or_null",
        "bank_account_number": "extracted_account_or_null",
        "ifsc_code": "extracted_ifsc_or_null",
        "land_area": "extracted_area_or_null",
        "crop_type": "extracted_crop_or_null",
        "village": "extracted_village_or_null",
        "district": "extracted_district_or_null",
        "state": "extracted_state_or_null",
        "mobile_number": "extracted_mobile_or_null",
        "requested_amount": "extracted_amount_or_null",
        "application_id": "extracted_id_or_null",
        "date_of_application": "extracted_date_or_null",
        "scheme_name": "extracted_scheme_or_null"
    }},
    "extracted_fields": {{
        "farmer_name": "extracted_name_or_null",
        "aadhaar_number": "extracted_aadhaar_or_null",
        "bank_account_number": "extracted_account_or_null",
        "ifsc_code": "extracted_ifsc_or_null",
        "land_area": "extracted_area_or_null",
        "crop_type": "extracted_crop_or_null",
        "village": "extracted_village_or_null",
        "district": "extracted_district_or_null",
        "state": "extracted_state_or_null",
        "mobile_number": "extracted_mobile_or_null",
        "requested_amount": "extracted_amount_or_null",
        "application_id": "extracted_id_or_null",
        "date_of_application": "extracted_date_or_null",
        "scheme_name": "extracted_scheme_or_null"
    }},
    "missing_fields": ["field1", "field2"],
    "confidence": 0.85,
    "reasoning": ["reason1", "reason2"],
    "classification_confidence": 0.90,
    "classification_reasoning": {{
        "keywords_found": ["keyword1", "keyword2"],
        "structural_indicators": ["indicator1"],
        "confidence_factors": ["factor1", "factor2"]
    }},
    "risk_flags": [],
    "decision_support": {{
        "decision": "approve/review/manual_review",
        "confidence": 0.80,
        "reasoning": ["decision_reason1", "decision_reason2"]
    }},
    "canonical": {{}},
    "summary": "Brief summary of the document"
}}

RULES:
1. Respond with ONLY valid JSON, no markdown formatting
2. Use null for missing/unclear values
3. confidence should be between 0.0 and 1.0
4. classification_confidence should be between 0.0 and 1.0
5. Include specific reasoning for classification decisions
6. summary should be concise and factual
7. risk_flags array should contain objects with code, severity, message fields
8. decision_support.decision should be one of: approve, review, manual_review
"""
        return prompt
    
    def _call_granite_api(self, prompt: str) -> str:
        """
        Call Granite API with prompt
        
        Args:
            prompt: Formatted prompt for Granite
            
        Returns:
            Raw response text from Granite
        """
        if not self._check_granite_availability():
            raise ValueError(f"Granite service not available: {self._granite_import_error}")
        
        try:
            session = self._get_session()
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.1,  # Low temperature for consistent output
                "stop": ["```", "```json", "```markdown"]  # Stop at markdown blocks
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            self.logger.info(f"[GRANITE] Sending request to {self.granite_endpoint}")
            start_time = time.time()
            
            response = session.post(
                self.granite_endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"[GRANITE] Response received in {elapsed_time:.2f}s")
            
            # Extract response text
            response_data = response.json()
            if isinstance(response_data, dict):
                # Handle different response formats
                if 'text' in response_data:
                    return response_data['text']
                elif 'generated_text' in response_data:
                    return response_data['generated_text']
                elif 'output' in response_data:
                    return response_data['output']
                else:
                    return str(response_data)
            else:
                return str(response_data)
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"[GRANITE] API request failed: {e}")
            raise ValueError(f"Granite API request failed: {e}")
        except Exception as e:
            self.logger.error(f"[GRANITE] Unexpected error: {e}")
            raise ValueError(f"Granite extraction failed: {e}")
    
    def _parse_granite_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Granite response and validate schema
        
        Args:
            response_text: Raw response from Granite
            
        Returns:
            Parsed and validated JSON response
            
        Raises:
            ValueError: If response cannot be parsed or doesn't match schema
        """
        try:
            # Clean response text - remove markdown formatting if present
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            parsed_response = json.loads(cleaned_text)
            
            # Validate required fields
            required_fields = [
                'document_type', 'structured_data', 'extracted_fields',
                'missing_fields', 'confidence', 'reasoning',
                'classification_confidence', 'classification_reasoning',
                'risk_flags', 'decision_support', 'canonical', 'summary'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in parsed_response:
                    missing_fields.append(field)
            
            if missing_fields:
                self.logger.warning(f"[GRANITE] Response missing required fields: {missing_fields}")
                # Add missing fields with default values
                for field in missing_fields:
                    if field in ['structured_data', 'extracted_fields', 'canonical']:
                        parsed_response[field] = {}
                    elif field in ['missing_fields', 'reasoning', 'risk_flags']:
                        parsed_response[field] = []
                    elif field in ['confidence', 'classification_confidence']:
                        parsed_response[field] = 0.0
                    elif field == 'classification_reasoning':
                        parsed_response[field] = {
                            'keywords_found': [],
                            'structural_indicators': [],
                            'confidence_factors': []
                        }
                    elif field == 'decision_support':
                        parsed_response[field] = {
                            'decision': 'manual_review',
                            'confidence': 0.0,
                            'reasoning': ['Schema validation failed']
                        }
                    elif field == 'summary':
                        parsed_response[field] = 'Document processed with schema validation issues'
                    else:
                        parsed_response[field] = None
            
            # Validate data types
            if not isinstance(parsed_response.get('missing_fields'), list):
                parsed_response['missing_fields'] = []
            
            if not isinstance(parsed_response.get('reasoning'), list):
                parsed_response['reasoning'] = []
            
            if not isinstance(parsed_response.get('risk_flags'), list):
                parsed_response['risk_flags'] = []
            
            # Validate confidence values
            for confidence_field in ['confidence', 'classification_confidence']:
                if confidence_field in parsed_response:
                    try:
                        value = float(parsed_response[confidence_field])
                        parsed_response[confidence_field] = max(0.0, min(1.0, value))
                    except (ValueError, TypeError):
                        parsed_response[confidence_field] = 0.0
            
            return self._ensure_schema_compliance(parsed_response)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"[GRANITE] Failed to parse JSON response: {e}")
            self.logger.error(f"[GRANITE] Response text: {response_text[:500]}...")
            raise ValueError(f"Granite response is not valid JSON: {e}")
        except Exception as e:
            self.logger.error(f"[GRANITE] Response parsing failed: {e}")
            raise ValueError(f"Failed to parse Granite response: {e}")
    
    def extract_with_granite(self, docling_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured information using Granite
        
        Args:
            docling_output: Structured output from Docling ingestion
            
        Returns:
            Schema-compliant extraction result:
            {
                "document_type": str,
                "structured_data": dict,
                "extracted_fields": dict,
                "missing_fields": list,
                "confidence": float,
                "reasoning": list,
                "classification_confidence": float,
                "classification_reasoning": dict,
                "risk_flags": list,
                "decision_support": dict,
                "canonical": dict,
                "summary": str
            }
            
        Raises:
            ValueError: If Granite extraction fails
        """
        if not docling_output:
            raise ValueError("No Docling output provided")
        
        # Check if we have any content to process
        raw_text = docling_output.get('raw_text', '')
        if not raw_text.strip():
            raise ValueError("No text content available for extraction")
        
        try:
            # Prepare prompt
            prompt = self._prepare_granite_prompt(docling_output)
            
            # Call Granite API
            response_text = self._call_granite_api(prompt)
            
            # Parse and validate response
            extraction_result = self._parse_granite_response(response_text)
            
            # Add processing metadata
            extraction_result['processing_metadata'] = {
                'processing_method': 'granite',
                'model_name': self.model_name,
                'input_text_length': len(raw_text),
                'processing_timestamp': time.time()
            }
            
            self.logger.info(f"[GRANITE] Successfully extracted: {extraction_result.get('document_type', 'unknown')}")
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"[GRANITE] Extraction failed: {e}")
            raw_text_length = len(docling_output.get('raw_text', '')) if isinstance(docling_output, dict) else 0
            return self._build_schema_safe_payload(
                raw_text_length=raw_text_length,
                reasoning=[f"Granite extraction failed: {e}"],
            )
    
    def is_available(self) -> bool:
        """
        Check if Granite service is available
        """
        return self._check_granite_availability()
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get service information
        """
        return {
            'service_name': 'GraniteExtractionService',
            'endpoint': self.granite_endpoint,
            'model_name': self.model_name,
            'available': self.is_available(),
            'error': self._granite_import_error if not self._granite_available else None
        }
