"""
Example Successful API Responses

These are the EXACT response formats that the frontend expects.
All responses follow this strict schema.
"""

# ============================================================================
# EXAMPLE 1: PM KISAN SCHEME APPLICATION (PDF) - SUCCESS
# ============================================================================

EXAMPLE_1_REQUEST = """
POST /api/document-processing/process HTTP/1.1
Host: your-railway-app.up.railway.app
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="file"; filename="pm_kisan_application.pdf"
Content-Type: application/pdf

[binary PDF content]
------Boundary
Content-Disposition: form-data; name="processing_type"

full_process
------Boundary--
"""

EXAMPLE_1_RESPONSE = {
  "request_id": "req_a1b2c3d4e5f6",
  "success": True,
  "processing_time_ms": 2450,
  "processing_type": "full_process",
  "filename": "pm_kisan_application.pdf",
  "data": {
    "document_type": "scheme_application",
    "classification_confidence": 0.89,
    "classification_reasoning": {
      "keywords_found": [
        "scheme",
        "application",
        "applicant",
        "pm kisan",
        "kisan samman nidhi"
      ],
      "structural_indicators": [
        "form_layout",
        "field_names",
        "scheme_application"
      ],
      "confidence_factors": [
        "strong_keyword_match",
        "structure_match",
        "semantic_analysis"
      ]
    },
    "structured_data": {
      "farmer_name": "राज कुमार",
      "applicant_name": "राज कुमार",
      "aadhaar_number": "1234567890123",
      "bank_account_number": "123456789012",
      "ifsc_code": "SBIN0010001",
      "land_area": "2.5",
      "crop_type": "गेहूं",
      "village": "नई दिल्ली",
      "district": "दिल्ली",
      "state": "दिल्ली",
      "mobile_number": "9876543210",
      "requested_amount": "50000",
      "application_id": "APP2024001",
      "date_of_application": "2024-01-15",
      "scheme_name": "PM Kisan Samman Nidhi"
    },
    "extracted_fields": {
      "farmer_name": "राज कुमार",
      "aadhaar_number": "1234567890123",
      "bank_account_number": "123456789012",
      "ifsc_code": "SBIN0010001",
      "land_area": "2.5",
      "crop_type": "गेहूं",
      "village": "नई दिल्ली",
      "district": "दिल्ली",
      "state": "दिल्ली",
      "mobile_number": "9876543210",
      "requested_amount": "50000",
      "application_id": "APP2024001",
      "date_of_application": "2024-01-15",
      "scheme_name": "PM Kisan Samman Nidhi"
    },
    "missing_fields": [
      "land_record_number",
      "crop_insurance_id"
    ],
    "confidence": 0.87,
    "reasoning": [
      "Identified applicant: राज कुमार",
      "Financial amount detected: 50000",
      "Crop type identified: गेहूं",
      "Document classification: scheme_application",
      "Strong alignment with PM Kisan scheme keywords",
      "All critical fields present",
      "Minor fields missing but not critical"
    ],
    "risk_flags": [],
    "decision_support": {
      "decision": "approve",
      "confidence": 0.88,
      "reasoning": [
        "Document is complete",
        "All critical information present",
        "Low risk indicators"
      ]
    },
    "canonical": {
      "farmer_name": "राज कुमार",
      "requested_amount": 50000,
      "village": "नई दिल्ली",
      "crop_type": "गेहूं"
    },
    "summary": "Scheme application for PM Kisan from राज कुमार in नई दिल्ली, requesting ₹50,000.",
    "ai_summary": "PM Kisan Samman Nidhi application received from राज कुमार in नई दिल्ली requesting ₹50,000. Document contains all required information including aadhaar, bank account, land area (2.5 hectares), and crop details (wheat). Recommended for approval.",
    "parser": "docling",
    "raw_text": "[Full extracted text from Docling...]"
  },
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "docling_available": True,
    "granite_available": True,
    "file_type": "pdf",
    "docling_text_length": 2847,
    "has_tables": False,
    "has_sections": True,
    "pre_identified_type": "scheme_application",
    "pre_identification_confidence": 0.86
  },
  "error_message": None
}


# ============================================================================
# EXAMPLE 2: DRIP IRRIGATION SUBSIDY CLAIM (SCANNED IMAGE) - WITH OCR FALLBACK
# ============================================================================

EXAMPLE_2_REQUEST = """
POST /api/document-processing/process HTTP/1.1
Host: your-railway-app.up.railway.app
Content-Type: multipart/form-data

------Boundary
Content-Disposition: form-data; name="file"; filename="drip_subsidy_claim.jpg"
Content-Type: image/jpeg

[binary JPEG content]
------Boundary--
"""

EXAMPLE_2_RESPONSE = {
  "request_id": "req_f6e5d4c3b2a1",
  "success": True,
  "processing_time_ms": 3200,
  "processing_type": "full_process",
  "filename": "drip_subsidy_claim.jpg",
  "data": {
    "document_type": "subsidy_claim",
    "classification_confidence": 0.82,
    "classification_reasoning": {
      "keywords_found": [
        "subsidy",
        "drip irrigation",
        "claim",
        "financial assistance",
        "requested amount"
      ],
      "structural_indicators": [
        "subsidy_claim",
        "irrigation_subsidy"
      ],
      "confidence_factors": [
        "strong_subsidy_keywords",
        "irrigation_terminology",
        "financial_claim_details"
      ]
    },
    "structured_data": {
      "farmer_name": "राहुल शर्मा",
      "applicant_name": "राहुल शर्मा",
      "land_area": "1.5",
      "crop_type": "गेहूं",
      "requested_amount": "75000",
      "subsidy_type": "ड्रिप सिंचाई",
      "village": "पंचकूला",
      "district": "हरियाणा",
      "state": "हरियाणा",
      "mobile_number": "9876543210"
    },
    "extracted_fields": {
      "farmer_name": "राहुल शर्मा",
      "land_area": "1.5",
      "crop_type": "गेहूं",
      "requested_amount": "75000",
      "subsidy_type": "ड्रिप सिंचाई",
      "village": "पंचकूला",
      "district": "हरियाणा",
      "state": "हरियाणा"
    },
    "missing_fields": [
      "bank_account_number",
      "ifsc_code",
      "aadhaar_number"
    ],
    "confidence": 0.79,
    "reasoning": [
      "Identified applicant: राहुल शर्मा",
      "Financial amount detected: 75000",
      "Crop type identified: गेहूं",
      "Document classification: subsidy_claim",
      "Strong subsidy-specific keywords found",
      "Irrigation-related terminology detected",
      "Financial claim details complete",
      "OCR fallback used - text quality medium"
    ],
    "risk_flags": [
      {
        "code": "MISSING_IDENTITY_DOCUMENTS",
        "severity": "medium",
        "message": "Aadhaar and bank details not provided in document"
      },
      {
        "code": "OCR_FALLBACK_USED",
        "severity": "info",
        "message": "Image processed using OCR - verify accuracy"
      }
    ],
    "decision_support": {
      "decision": "manual_review",
      "confidence": 0.79,
      "reasoning": [
        "Core information present but identity documents missing",
        "OCR used for image processing - recommend verification",
        "Subsidy amount within normal range"
      ]
    },
    "canonical": {
      "farmer_name": "राहुल शर्मा",
      "requested_amount": 75000,
      "village": "पंचकूला",
      "crop_type": "गेहूं",
      "subsidy_type": "ड्रिप सिंचाई"
    },
    "summary": "Drip irrigation subsidy claim from राहुल शर्मा in पंचकूला for ₹75,000.",
    "ai_summary": "Drip irrigation subsidy claim received from राहुल शर्मा in पंचकूला requesting ₹75,000. Document was processed using OCR (scanned image). Farmer details, land area (1.5 hectares), crop type (wheat), and subsidy request are clear. Supporting identity documents should be verified separately. Recommended for verification before approval.",
    "parser": "docling",
    "raw_text": "[Text extracted via Docling + OCR fallback...]"
  },
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "docling_available": True,
    "granite_available": True,
    "file_type": "image",
    "docling_text_length": 1549,
    "ocr_fallback_used": True,
    "ocr_language": "eng+hin+mar",
    "has_tables": False,
    "has_sections": False,
    "pre_identified_type": "subsidy_claim",
    "pre_identification_confidence": 0.81
  },
  "error_message": None
}


# ============================================================================
# EXAMPLE 3: FAILURE CASE - Corrupted/Unreadable Document
# ============================================================================

EXAMPLE_3_RESPONSE = {
  "request_id": "req_9z8y7x6w5v4u",
  "success": True,  # Still success=true but with failure flags
  "processing_time_ms": 500,
  "processing_type": "full_process",
  "filename": "corrupted_document.pdf",
  "data": {
    "document_type": "unknown",
    "classification_confidence": 0.0,
    "classification_reasoning": {
      "keywords_found": [],
      "structural_indicators": [],
      "confidence_factors": [
        "Text extraction failed - document may be corrupted or encrypted"
      ]
    },
    "structured_data": {},
    "extracted_fields": {},
    "missing_fields": [],
    "confidence": 0.0,
    "reasoning": [
      "Extraction failed - document may be corrupted or encrypted"
    ],
    "risk_flags": [
      {
        "code": "DOCUMENT_PROCESSING_FAILURE",
        "severity": "high",
        "message": "Unable to extract text from document - file may be corrupted, encrypted, or in unsupported format"
      }
    ],
    "decision_support": {
      "decision": "manual_review_required",
      "confidence": 0.0,
      "reasoning": [
        "Document processing failed",
        "Manual review and verification required"
      ]
    },
    "canonical": {},
    "summary": "Document processing failed. Manual review required.",
    "ai_summary": "Unable to process this document. It may be corrupted, encrypted, or in an unsupported format. Please verify the document and re-upload.",
    "parser": "docling",
    "raw_text": ""
  },
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "processing_failure": True,
    "error": "PDF parsing failed",
    "file_type": "pdf"
  },
  "error_message": None
}


# ============================================================================
# EXAMPLE 4: HEALTH CHECK ENDPOINT
# ============================================================================

EXAMPLE_4_HEALTH_CHECK = """
GET /health HTTP/1.1
Host: your-railway-app.up.railway.app
"""

EXAMPLE_4_HEALTH_RESPONSE = {
  "status": "ok",
  "service": "AI Smart Agriculture Services",
  "version": "1.0.0",
  "ocr": True,
  "granite": True
}


# ============================================================================
# EXAMPLE 5: CLASSIFICATION-ONLY ENDPOINT
# ============================================================================

EXAMPLE_5_CLASSIFY = """
POST /api/document-processing/classify HTTP/1.1
Host: your-railway-app.up.railway.app
Content-Type: multipart/form-data

------Boundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

[binary PDF content]
------Boundary--
"""

EXAMPLE_5_CLASSIFY_RESPONSE = {
  "document_type": "scheme_application",
  "confidence": 0.89,
  "classification_reasoning": {
    "keywords_found": ["scheme", "application", "applicant", "pm kisan"],
    "structural_indicators": ["form_layout", "field_names"],
    "confidence_factors": ["strong_keyword_match"]
  }
}


# ============================================================================
# KEY RESPONSE FIELDS DOCUMENTATION
# ============================================================================

RESPONSE_SCHEMA_DOCUMENTATION = """
{
  "request_id": "Unique identifier for this processing request",
  "success": "Always true if document was attempted (check risk_flags for errors)",
  "processing_time_ms": "Time taken in milliseconds",
  "processing_type": "Type of processing requested (full_process, etc)",
  "filename": "Original filename",
  "data": {
    "document_type": "Classification result: scheme_application, subsidy_claim, insurance_claim, grievance, farmer_record, supporting_document, unknown",
    
    "classification_confidence": "0.0-1.0, confidence in document type classification",
    
    "structured_data": {
      "farmer_name": "Extracted farmer/applicant name",
      "aadhaar_number": "Extracted Aadhaar (masked or full)",
      "bank_account_number": "Extracted bank account",
      "ifsc_code": "Extracted IFSC code",
      "land_area": "Extracted land area with units",
      "crop_type": "Extracted crop type",
      "village": "Extracted village/location",
      "district": "Extracted district",
      "state": "Extracted state",
      "mobile_number": "Extracted mobile number",
      "requested_amount": "Extracted financial amount",
      "application_id": "Extracted application/reference ID",
      "date_of_application": "Extracted date",
      "scheme_name": "Extracted scheme name if applicable"
    },
    
    "extracted_fields": "Subset of structured_data with high-confidence fields",
    "missing_fields": "List of expected fields not found in document",
    
    "confidence": "0.0-1.0, overall confidence in extraction",
    "reasoning": "List of reasons for classification and extraction decisions",
    
    "ai_summary": "Human-readable summary of document for officer review",
    
    "risk_flags": [
      {
        "code": "Flag code for specific risk",
        "severity": "info|medium|high",
        "message": "Human-readable description"
      }
    ],
    
    "decision_support": {
      "decision": "approve|reject|manual_review",
      "confidence": "0.0-1.0",
      "reasoning": ["List of reasons for decision"]
    },
    
    "canonical": "Normalized version of structured_data with cleaned values",
    "summary": "Brief summary of document",
    "parser": "docling (always Docling for this pipeline)",
    "raw_text": "Full extracted text from document"
  },
  
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "docling_available": "true/false",
    "granite_available": "true/false",
    "file_type": "pdf|image|docx|txt",
    "ocr_fallback_used": "true/false (if image processed via OCR)",
    "processing_failure": "true/false (if extraction failed)"
  },
  
  "error_message": "null if successful, error string if failed"
}
"""

if __name__ == "__main__":
    print("Example API Response Formats")
    print("\nFor successful PM Kisan application:")
    print(json.dumps(EXAMPLE_1_RESPONSE, ensure_ascii=False, indent=2)[:500] + "...")
