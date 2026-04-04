# Document Processing Code Context

Auto-generated developer context for workflow, pipeline, and file responsibilities.

# Current Source of Truth

- `app/modules/document_processing/classification_service.py` — document classification logic
- `app/modules/document_processing/document_processing_router.py` — main API router for document processing
- `app/modules/document_processing/document_processing_service.py` — orchestrates classification + extraction pipeline
- `app/modules/document_processing/extraction_service.py` — dispatches to document-specific handlers
- `app/modules/document_processing/generic_extractor.py` — common/shared field extractor used before handler-specific extraction
- `app/modules/document_processing/handlers/base_handler.py` — base contract for all document handlers
- `app/modules/document_processing/handlers/farmer_record_handler.py` — farmer_record document handler
- `app/modules/document_processing/handlers/grievance_handler.py` — grievance document handler
- `app/modules/document_processing/handlers/insurance_claim_handler.py` — insurance_claim document handler
- `app/modules/document_processing/handlers/scheme_application_handler.py` — scheme_application document handler
- `app/modules/document_processing/processors.py` — main workflow engine for classify/extract/full_process
- `app/modules/document_processing/service_schema.py` — response contract and data models
- `app/modules/document_processing/utils.py` — shared extraction utilities and helpers

# Live Pipeline

Main production workflow:

document_processing_router.py
→ document_processing_service.py
→ processors.py
→ classification_service.py
→ extraction_service.py
→ generic_extractor.py + handlers/*
→ service_schema.py output

Separate testing workflow:
- extraction_router.py — internal/testing extraction router, not main production workflow

# Locked / Rebuilt Files

- `app/modules/document_processing/classification_service.py` — core pipeline file
- `app/modules/document_processing/document_processing_router.py` — core pipeline file
- `app/modules/document_processing/document_processing_service.py` — core pipeline file
- `app/modules/document_processing/extraction_service.py` — core pipeline file
- `app/modules/document_processing/generic_extractor.py` — core pipeline file
- `app/modules/document_processing/handlers/base_handler.py` — uses BaseHandler, build_result
- `app/modules/document_processing/handlers/farmer_record_handler.py` — uses BaseHandler, build_result
- `app/modules/document_processing/handlers/grievance_handler.py` — uses BaseHandler, build_result
- `app/modules/document_processing/handlers/insurance_claim_handler.py` — uses BaseHandler, build_result
- `app/modules/document_processing/handlers/scheme_application_handler.py` — uses BaseHandler, build_result
- `app/modules/document_processing/processors.py` — core pipeline file
- `app/modules/document_processing/service_schema.py` — core pipeline file
- `app/modules/document_processing/utils.py` — core pipeline file

# Legacy / Stale / Review Carefully

- `app/modules/document_processing/handlers/__init__.py` — uses old BaseDocumentHandler import, needs cleanup to BaseHandler
- `app/modules/document_processing/schema/__init__.py` — old enum/model-based extraction schema
- `app/modules/document_processing/schema/document_classification.py` — old enum/model-based extraction schema
- `app/modules/document_processing/schema/extraction.py` — old enum/model-based extraction schema

# Auxiliary / Not in Main Live Path

- `app/modules/document_processing/__init__.py` — present in module inventory but not currently marked as source-of-truth or legacy
- `app/modules/document_processing/decision_service.py` — auxiliary decision/recommendation logic, not part of main rebuilt live pipeline
- `app/modules/document_processing/extraction_router.py` — present in module inventory but not currently marked as source-of-truth or legacy

# Next Work Items

- create subsidy_claim_handler.py
- create supporting_document_handler.py
- end-to-end testing with OCR text samples
- validate extraction_service handler dispatch
- verify processors.py output shape against frontend/backend usage

# Handler Contract

All document handlers must follow this standard:

- All document handlers inherit from `BaseHandler`
- All handlers should return only through `build_result(...)`
- All field writes should use `safe_set_field(...)`
- Standard handler output shape:
  - document_type
  - structured_data
  - extracted_fields
  - missing_fields
  - confidence
  - reasoning

Preferred extraction philosophy:
- labeled regex primary
- boundary-aware optional
- keyword fallback where helpful
- no fake/sample data
- no one-template logic

# Handler Field Contract (Strict)

--------------------------------------------------
scheme_application
--------------------------------------------------
REQUIRED:
- farmer_name
- scheme_name

OPTIONAL:
- aadhaar_number
- location
- village
- district
- land_size
- requested_amount
- crop_type
- season
- phone_number
- application_id

--------------------------------------------------
farmer_record
--------------------------------------------------
REQUIRED:
- farmer_id
- farmer_name

OPTIONAL:
- land_holding
- land_size
- location
- crops
- village
- district
- benefit_history
- aadhaar_number
- phone_number
- email
- bank_details
- registration_date

--------------------------------------------------
grievance
--------------------------------------------------
REQUIRED:
- complaint_subject

OPTIONAL:
- applicant_name
- grievance_text
- department
- urgency
- location
- contact_number
- aadhaar_number
- reference_number
- submission_date
- expected_resolution

--------------------------------------------------
insurance_claim
--------------------------------------------------
REQUIRED:
- farmer_name
- policy_number
- claim_amount

OPTIONAL:
- aadhaar_number
- location
- village
- district
- crop_type
- season
- incident_date
- claim_reason
- insurer_name
- contact_number
- application_id

--------------------------------------------------
subsidy_claim
--------------------------------------------------
REQUIRED:
- farmer_name
- subsidy_type
- requested_amount

OPTIONAL:
- aadhaar_number
- location
- village
- district
- land_size
- crop_type
- season
- department
- subsidy_reason
- contact_number
- application_id
- submission_date

--------------------------------------------------
supporting_document
--------------------------------------------------
REQUIRED:
- document_reference

OPTIONAL:
- farmer_name
- aadhaar_number
- location
- document_type_detail
- issuing_authority
- issue_date
- contact_number
- application_id

❗ RULES:
- DO NOT rename required fields
- DO NOT replace required fields with similar-looking fields
- DO NOT introduce new primary fields unless explicitly requested
- DO NOT copy field contracts from other handlers
- If a handler example conflicts with this section, this section wins

# Reasoning Contract (Locked Style)

Handlers MUST use summary-style reasoning only.

Allowed reasoning patterns:
- Missing required fields: ...
- Fields extracted: ...
- Core fields identified successfully

Reasoning must be:
- minimal
- summary-only
- consistent across all handlers

NOT ALLOWED:
- per-field logs
- extraction-step narration
- regex explanations
- verbose debugging text
- one reasoning line per extracted field

If a future handler prompt suggests per-field reasoning, ignore that and follow this section.

# Anti-Drift Rules

When generating or editing handlers:

- DO NOT mix document domains
  - insurance_claim ≠ subsidy_claim ≠ scheme_application ≠ grievance

- DO NOT reuse primary fields from another handler unless they are explicitly part of the field contract

Examples of forbidden drift:
- using scheme_name as the required field in subsidy_claim
- using claim_amount instead of requested_amount in subsidy_claim
- using grievance_type instead of complaint_subject in grievance
- using policy_number in scheme_application

Priority order when generating handlers:
1. Handler Field Contract (Strict)
2. BaseHandler contract
3. Locked handler coding style
4. Existing handler examples

If any example conflicts with the strict field contract:
- ignore the example
- follow the strict field contract

Future chats should treat this section as binding guidance, not optional commentary.


---

## `app/modules/document_processing/__init__.py`

**Role:** module

**Purpose:** Document Processing Module

**Likely pipeline connections:**
- service orchestration

**Imports:**
- `.document_processing_router: router`
- `.document_processing_service: DocumentProcessingService`

## `app/modules/document_processing/classification_service.py`

**Role:** service/orchestration layer

**Purpose:** Document Classification Service

**Imports:**
- `re`
- `typing: Dict, List, Any, Optional, Tuple`

**Classes:**
- `DocumentClassificationService` (bases: -) — Service for classifying agricultural office documents
  - `__init__(self)` — -
  - `classify_document(self, text, filename)` — Classify document based on text content and optional filename
  - `_detect_grievance_intent(self, text_lower)` — Detect grievance intent with priority override
  - `_calculate_type_score(self, text_lower, doc_type, rules)` — Calculate classification score for a specific document type
  - `_analyze_filename(self, filename)` — Analyze filename for classification indicators
  - `_is_keyword_match_safe(self, keyword, text_lower)` — Safer keyword matching that avoids noisy substring matches for short words
  - `_calculate_filename_boost(self, filename, doc_type)` — Calculate modest filename-based score boost
  - `_get_pattern_description(self, pattern)` — Convert regex pattern to human-friendly description
  - `_count_keyword_occurrences(self, keyword, text_lower)` — Count keyword occurrences consistently with safer matching logic
  - `_is_filename_token_safe(self, token, filename_lower)` — Safer filename token matching that avoids noisy matches

## `app/modules/document_processing/decision_service.py`

**Role:** service/orchestration layer

**Purpose:** Decision Service

**Imports:**
- `enum: Enum`
- `re`
- `typing: Dict, List, Any, Optional`

**Classes:**
- `RecommendationType` (bases: Enum) — -
- `DecisionService` (bases: -) — Service for making confidence-based decisions on extracted data
  - `__init__(self)` — -
  - `make_decision(self, extraction_result)` — Make a decision based on extraction results
  - `_calculate_completeness_score(self, structured_data, missing_fields)` — Calculate completeness score based on which fields are present
  - `_validate_fields(self, structured_data, field_confidences)` — Validate field formats and values
  - `_validate_single_field(self, field_name, field_value)` — Validate a single field
  - `_calculate_decision_score(self, extraction_confidence, completeness_score, validation_results)` — Calculate overall decision score
  - `_determine_recommendation(self, decision_score, validation_results, missing_fields)` — Determine recommendation based on decision score and other factors
  - `_generate_reasoning(self, recommendation, extraction_confidence, completeness_score, validation_results, missing_fields)` — Generate human-readable reasoning for the decision

## `app/modules/document_processing/document_processing_router.py`

**Role:** API/router layer

**Purpose:** Document Processing Router

**Likely pipeline connections:**
- API layer
- response/schema contract
- service orchestration

**Imports:**
- `.document_processing_service: DocumentProcessingService`
- `.service_schema: DocumentProcessingRequest, DocumentProcessingResult`
- `fastapi: APIRouter, UploadFile, File, HTTPException`
- `typing: Optional, List, Dict, Any`

**Top-level functions:**
- `process_document(file, processing_type, options)` — Process uploaded document
- `process_document_from_metadata(request)` — Process document from metadata
- `process_documents_batch(files, processing_type, options)` — Process multiple documents in batch
- `get_processing_types()` — Get available document processing types
- `health_check()` — Health check endpoint

## `app/modules/document_processing/document_processing_service.py`

**Role:** service/orchestration layer

**Purpose:** Document Processing Service

**Likely pipeline connections:**
- classification stage
- extraction stage
- response/schema contract
- workflow engine

**Imports:**
- `.classification_service: DocumentClassificationService`
- `.extraction_service: DocumentExtractionService`
- `.processors: DocumentProcessor`
- `.service_schema: DocumentProcessingRequest, DocumentProcessingResult`
- `typing: Optional, Dict, Any, List`
- `uuid`

**Classes:**
- `DocumentProcessingService` (bases: -) — Clean orchestration service for document processing operations
  - `__init__(self)` — -
  - `process_document(self, file_data, filename, processing_type, options)` — Process document based on specified type
  - `process_batch(self, documents, processing_type)` — Process multiple documents in batch
  - `classify_document(self, file_data, filename, options)` — Classify document type
  - `get_supported_processing_types(self)` — Get supported document processing types
  - `get_processing_statistics(self, results)` — Get processing statistics for batch results
  - `validate_request(self, request)` — Validate document processing request
  - `process_request(self, request)` — Process document processing request (main API method)
  - `_convert_to_result_format(self, processing_result)` — Convert processor result to DocumentProcessingResult format

## `app/modules/document_processing/extraction_router.py`

**Role:** API/router layer

**Purpose:** Document Extraction Router

**Likely pipeline connections:**
- API layer
- extraction stage

**Imports:**
- `.extraction_service: DocumentExtractionService`
- `fastapi: APIRouter, HTTPException, Form`
- `json`
- `typing: Optional, Dict, Any`

**Top-level functions:**
- `extract_document(text_content, document_type, file_name, metadata)` — Extract fields from document text based on document type
- `auto_classify_and_extract(text_content, file_name, metadata)` — Automatically classify document and extract fields
- `get_supported_document_types()` — Get list of supported document types
- `health_check()` — Health check endpoint for document extraction service

## `app/modules/document_processing/extraction_service.py`

**Role:** service/orchestration layer

**Purpose:** Document Extraction Service

**Likely pipeline connections:**
- classification stage
- shared extraction utilities

**Imports:**
- `.classification_service: DocumentClassificationService`
- `.generic_extractor: GenericFieldExtractor`
- `.handlers.supporting_document_handler: SupportingDocumentHandler`
- `.utils: normalize_ocr_text`
- `importlib`
- `typing: Dict, List, Optional, Any`

**Classes:**
- `DocumentExtractionService` (bases: -) — Main handler-dispatch service for document extraction
  - `__init__(self)` — -
  - `_initialize_handlers(self)` — Initialize handler mapping for document types
  - `_get_handler(self, document_type)` — Get or instantiate handler for document type
  - `_import_handler(self, document_type)` — Import handler with safer importlib approach
  - `_create_fallback_handler(self)` — Create minimal fallback handler with useful debugging info
  - `_is_metadata_shaped(self, value)` — Check if value has proper field metadata shape
  - `extract_document(self, text_content, document_type, metadata)` — Extract fields from a document based on its type
  - `auto_classify_and_extract(self, text_content, file_name, metadata)` — Automatically classify document and extract fields
  - `get_supported_document_types(self)` — Get list of supported document types
  - `_merge_extraction_results(self, generic_result, handler_fields)` — Merge generic and handler-specific results correctly
  - `_compute_missing_fields(self, document_type, structured_data)` — Compute missing required fields for document type
  - `_compute_confidence_from_fields(self, extracted_fields)` — Compute confidence from merged extracted fields

## `app/modules/document_processing/generic_extractor.py`

**Role:** module

**Purpose:** Generic Field Extractor

**Likely pipeline connections:**
- shared extraction utilities

**Imports:**
- `.utils: normalize_ocr_text, BoundaryAwareExtractor, FieldValidators, FieldNormalizers`
- `re`
- `typing: Dict, Any, Optional, List`

**Classes:**
- `GenericFieldExtractor` (bases: -) — Generic field extractor for agricultural documents - focuses on common/shared fields only
  - `__init__(self)` — -
  - `extract_fields(self, text)` — Extract common fields from agricultural document text.
  - `_extract_single_field(self, text, field_name)` — Extract a single field using multiple strategies with confidence scoring.
  - `_normalize_field_value(self, value, field_name)` — Normalize field value using appropriate normalizer.
  - `_validate_field_value(self, value, field_name)` — Validate field value using appropriate validator.
  - `_extract_location_field(self, text)` — Extract location by combining village and district separately
  - `_extract_annual_income_field(self, text)` — Extract annual income with field-aware patterns
  - `_extract_application_id_field(self, text)` — Extract application ID with field-aware patterns

## `app/modules/document_processing/handlers/__init__.py`

**Role:** module

**Purpose:** module

**Likely pipeline connections:**
- handler base contract

**Imports:**
- `.base_handler: BaseDocumentHandler`
- `.farmer_record_handler: FarmerRecordHandler`
- `.grievance_handler: GrievanceHandler`
- `.scheme_application_handler: SchemeApplicationHandler`

## `app/modules/document_processing/handlers/base_handler.py`

**Role:** document-type-specific extraction handler

**Purpose:** Base Document Handler

**Imports:**
- `abc: ABC, abstractmethod`
- `typing: Dict, List, Optional, Any`

**Classes:**
- `BaseHandler` (bases: ABC) — Abstract base class for document type handlers
  - `__init__(self)` — -
  - `get_document_type(self)` — Return the standardized document type string this handler handles
  - `extract_fields(self, text, metadata)` — Extract fields from document text
  - `build_field(self, field_name, value, confidence, source)` — Build a standardized field metadata dictionary
  - `build_result(self, document_type, structured_data, extracted_fields, reasoning)` — Build a standardized handler result dictionary
  - `get_field_synonyms(self, field_name)` — Get synonyms for a field name
  - `is_missing(self, value)` — Check if a value should be considered missing
  - `safe_set_field(self, structured_data, extracted_fields, field_name, value, confidence, source)` — Safely set a field in both structured_data and extracted_fields
  - `normalize_confidence(self, confidence)` — Normalize confidence to [0.0, 1.0] range
  - `combine_reasoning(self)` — Combine reasoning parts into a flat list

## `app/modules/document_processing/handlers/farmer_record_handler.py`

**Role:** document-type-specific extraction handler

**Purpose:** Farmer Record Handler

**Likely pipeline connections:**
- handler base contract
- shared extraction utilities

**Imports:**
- `..utils: normalize_ocr_text, BoundaryAwareExtractor, FieldValidators, FieldNormalizers`
- `.base_handler: BaseHandler`
- `re`
- `typing: Dict, Optional, Any, Tuple`

**Classes:**
- `FarmerRecordHandler` (bases: BaseHandler) — Handler for farmer registration and profile documents
  - `__init__(self)` — -
  - `get_document_type(self)` — -
  - `extract_fields(self, text, metadata)` — Extract fields from farmer record text
  - `_extract_farmer_id(self, text)` — Extract farmer ID using regex-primary extraction
  - `_extract_farmer_name(self, text)` — Extract farmer name using boundary-aware extraction
  - `_extract_land_holding(self, text)` — Extract land holding using regex-primary extraction
  - `_extract_crops(self, text)` — Extract crops using label-based regex primary
  - `_extract_location_fields(self, text)` — Extract village and district using boundary-aware extraction
  - `_extract_benefit_history(self, text)` — Extract benefit history using keyword scanning
  - `_extract_aadhaar_number(self, text)` — Extract Aadhaar number using boundary-aware extraction
  - `_extract_phone_number(self, text)` — Extract phone number using boundary-aware extraction
  - `_extract_email(self, text)` — Extract email using regex primary extraction
  - `_extract_bank_details(self, text)` — Extract bank details keeping it practical and compact
  - `_extract_registration_date(self, text)` — Extract registration date using labeled regex patterns

## `app/modules/document_processing/handlers/grievance_handler.py`

**Role:** document-type-specific extraction handler

**Purpose:** Grievance Handler

**Likely pipeline connections:**
- handler base contract
- shared extraction utilities

**Imports:**
- `..utils: normalize_ocr_text, BoundaryAwareExtractor, FieldValidators, FieldNormalizers`
- `.base_handler: BaseHandler`
- `re`
- `typing: Dict, Optional, Any, Tuple`

**Classes:**
- `GrievanceHandler` (bases: BaseHandler) — Handler for grievance letters and complaints
  - `__init__(self)` — -
  - `get_document_type(self)` — -
  - `extract_fields(self, text, metadata)` — Extract fields from grievance text
  - `_extract_complaint_subject(self, text)` — Extract complaint subject using labeled regex primary
  - `_infer_complaint_subject_from_keywords(self, text)` — Infer complaint subject from keywords
  - `_extract_applicant_name(self, text)` — Extract applicant name using boundary-aware extraction
  - `_extract_grievance_text(self, text)` — Extract the main grievance description
  - `_extract_department(self, text)` — Extract target department
  - `_extract_urgency(self, text)` — Extract urgency level
  - `_extract_location(self, text)` — Extract location information
  - `_extract_contact_number(self, text)` — Extract contact number
  - `_extract_aadhaar_number(self, text)` — Extract Aadhaar number
  - `_extract_reference_number(self, text)` — Extract reference number
  - `_extract_submission_date(self, text)` — Extract submission date
  - `_extract_expected_resolution(self, text)` — Extract expected resolution timeline

## `app/modules/document_processing/handlers/insurance_claim_handler.py`

**Role:** document-type-specific extraction handler

**Purpose:** Handler for agricultural insurance claim documents.

**Likely pipeline connections:**
- handler base contract
- shared extraction utilities

**Imports:**
- `..utils: normalize_ocr_text, BoundaryAwareExtractor, FieldValidators, FieldNormalizers`
- `.base_handler: BaseHandler`
- `re`
- `typing: Dict, Optional, Any, Tuple`

**Classes:**
- `InsuranceClaimHandler` (bases: BaseHandler) — Handler for agricultural insurance claim documents.
  - `__init__(self)` — -
  - `get_document_type(self)` — -
  - `extract_fields(self, text, metadata)` — Extract fields from insurance claim document text.
  - `_extract_farmer_name(self, text)` — Extract farmer name using boundary-aware and labeled regex.
  - `_extract_policy_number(self, text)` — Extract policy number using regex-primary approach.
  - `_extract_claim_amount(self, text)` — Extract claim amount using boundary-aware and labeled regex.
  - `_extract_aadhaar_number(self, text)` — Extract Aadhaar number using boundary-aware and regex fallback.
  - `_extract_location_fields(self, text)` — Extract village and district using boundary-aware and regex fallback.
  - `_extract_crop_type(self, text)` — Extract crop type using label-based regex and keyword fallback.
  - `_extract_season(self, text)` — Extract season using controlled vocabulary.
  - `_extract_incident_date(self, text)` — Extract incident date using labeled regex.
  - `_extract_claim_reason(self, text)` — Extract claim reason from keywords or labeled line.
  - `_extract_insurer_name(self, text)` — Extract insurer name using labeled regex.
  - `_extract_contact_number(self, text)` — Extract contact number using boundary-aware and labeled regex.
  - `_extract_application_id(self, text)` — Extract application ID using regex-primary approach.

## `app/modules/document_processing/handlers/scheme_application_handler.py`

**Role:** document-type-specific extraction handler

**Purpose:** Scheme Application Handler

**Likely pipeline connections:**
- handler base contract
- shared extraction utilities

**Imports:**
- `..utils: normalize_ocr_text, BoundaryAwareExtractor, FieldValidators, FieldNormalizers`
- `.base_handler: BaseHandler`
- `re`
- `typing: Dict, Optional, Any, Tuple`

**Classes:**
- `SchemeApplicationHandler` (bases: BaseHandler) — Handler for scheme application documents
  - `__init__(self)` — -
  - `get_document_type(self)` — -
  - `extract_fields(self, text, metadata)` — Extract fields from scheme application text
  - `_extract_farmer_name(self, text)` — Extract farmer name using boundary-aware extraction
  - `_extract_scheme_name(self, text)` — Extract scheme name using boundary-aware extraction
  - `_extract_aadhaar_number(self, text)` — Extract Aadhaar number using boundary-aware extraction
  - `_extract_location_fields(self, text)` — Extract village and district using boundary-aware extraction
  - `_extract_land_size(self, text)` — Extract land size using boundary-aware extraction
  - `_extract_requested_amount(self, text)` — Extract requested amount using boundary-aware extraction
  - `_extract_crop_type(self, text)` — Extract crop type using fallback-driven extraction
  - `_extract_season(self, text)` — Extract season using controlled vocabulary
  - `_extract_phone_number(self, text)` — Extract phone number using boundary-aware extraction
  - `_extract_application_id(self, text)` — Extract application ID using regex-primary extraction

## `app/modules/document_processing/processors.py`

**Role:** workflow engine / pipeline execution layer

**Purpose:** Document Processors - Production Workflow Engine

**Likely pipeline connections:**
- shared extraction utilities

**Imports:**
- `.utils: normalize_ocr_text`
- `time`
- `typing: Dict, Any, Optional, List`
- `uuid`

**Classes:**
- `DocumentProcessor` (bases: -) — Production workflow engine for agriculture document-processing pipeline
  - `__init__(self, classification_service, extraction_service)` — -
  - `process_document_workflow(self, file_data, filename, processing_type, options)` — Main document processing workflow
  - `_validate_input(self, file_data, filename, processing_type, options)` — Validate input parameters
  - `_get_ocr_text(self, file_data, options)` — Get OCR text honestly
  - `_build_validation_summary(self, document_type, structured_data, missing_fields)` — Build validation summary
  - `_build_risk_flags(self, document_type, structured_data, confidence, missing_fields)` — Build risk flags
  - `_build_decision_support(self, confidence, missing_fields, risk_flags)` — Build decision support
  - `_generate_metadata(self, file_data, processing_time_ms, filename, document_type, confidence, ocr_text_provided)` — Generate processing metadata
  - `_create_success_result(self, request_id, processing_time_ms, processing_type, filename, data, metadata)` — Create successful processing result
  - `_create_error_result(self, request_id, error_message, processing_time_ms, processing_type, filename)` — Create error processing result
  - `process_batch_documents(self, documents)` — Process multiple documents in batch
  - `get_processing_statistics(self, results)` — Generate processing statistics for batch results

## `app/modules/document_processing/schema/__init__.py`

**Role:** module

**Purpose:** Document Processing Schemas

**Imports:**
- `.document_classification: DocumentType, ClassificationReasoning, DocumentClassificationRequest, DocumentClassificationResponse`
- `.extraction: FieldConfidence, ExtractedField, ExtractionResult, DocumentExtractionRequest, DocumentExtractionResponse, BatchExtractionRequest, BatchExtractionResponse`

## `app/modules/document_processing/schema/document_classification.py`

**Role:** module

**Purpose:** Document Classification Schemas

**Imports:**
- `enum: Enum`
- `pydantic: BaseModel, Field`
- `typing: List, Optional`

**Classes:**
- `DocumentType` (bases: str, Enum) — -
- `ClassificationReasoning` (bases: BaseModel) — Reasoning behind document classification
- `DocumentClassificationRequest` (bases: BaseModel) — Request model for document classification
- `DocumentClassificationResponse` (bases: BaseModel) — Response model for document classification

## `app/modules/document_processing/schema/extraction.py`

**Role:** module

**Purpose:** Document Extraction Schemas

**Imports:**
- `.document_classification: DocumentType`
- `enum: Enum`
- `pydantic: BaseModel, Field`
- `typing: Dict, List, Optional, Any`

**Classes:**
- `FieldConfidence` (bases: str, Enum) — -
- `ExtractedField` (bases: BaseModel) — Represents an extracted field with confidence
- `ExtractionResult` (bases: BaseModel) — Result of document extraction
- `DocumentExtractionRequest` (bases: BaseModel) — Request for document extraction
- `DocumentExtractionResponse` (bases: BaseModel) — Response from document extraction
- `BatchExtractionRequest` (bases: BaseModel) — Request for batch document extraction
- `BatchExtractionResponse` (bases: BaseModel) — Response from batch document extraction

## `app/modules/document_processing/service_schema.py`

**Role:** service/orchestration layer

**Purpose:** Document processing request

**Imports:**
- `pydantic: BaseModel, Field`
- `typing: Optional, List, Dict, Any`

**Classes:**
- `DocumentProcessingRequest` (bases: BaseModel) — Document processing request
- `ExtractedFieldData` (bases: BaseModel) — Individual extracted field with metadata
- `RiskFlag` (bases: BaseModel) — Risk flag for document processing
- `DecisionSupport` (bases: BaseModel) — Decision support information
- `ProcessedDocumentData` (bases: BaseModel) — Canonical processed document data structure
- `DocumentProcessingResult` (bases: BaseModel) — Canonical document processing result

## `app/modules/document_processing/utils.py`

**Role:** shared utility/helper layer

**Purpose:** Document Processing Utilities

**Imports:**
- `re`
- `typing: Dict, List, Optional, Any, Union`

**Classes:**
- `BoundaryAwareExtractor` (bases: -) — Reusable boundary-aware field extraction framework for agricultural documents.
  - `__init__(self)` — -
  - `extract_field_by_boundary(self, text, field_type, candidate_labels)` — Extract field value using boundary-aware parsing.
  - `_guard_against_contamination(self, value, field_type)` — Guard against field contamination from neighboring labels.
- `FieldValidators` (bases: -) — Reusable field-type validators for agricultural document extraction
  - `validate_person_name(value)` — Validate person name field
  - `validate_aadhaar_number(value)` — Validate Aadhaar number (12 digits)
  - `validate_mobile_number(value)` — Validate Indian mobile number
  - `validate_money_amount(value)` — Validate money amount field
  - `validate_land_size(value)` — Validate land size with units
  - `validate_location(value)` — Validate village/district/location field
  - `validate_scheme_name(value)` — Validate scheme name field
- `FieldNormalizers` (bases: -) — Reusable field normalizers for consistent data formatting
  - `normalize_person_name(value)` — Normalize person name field
  - `normalize_aadhaar(value)` — Normalize Aadhaar number to readable format
  - `normalize_mobile(value)` — Normalize mobile number to 10-digit format
  - `normalize_amount(value)` — Normalize money amount to clean number
  - `normalize_land_size(value)` — Normalize land size to standard format
  - `normalize_location(value)` — Normalize location (village/district) field
  - `normalize_scheme_name(value)` — Normalize scheme name field

**Top-level functions:**
- `normalize_ocr_text(value)` — Normalize OCR text input to consistent string format.
- `is_missing_value(value)` — Check if a value should be considered missing/empty.
- `safe_float(value, default)` — Safely convert value to float with default fallback.
