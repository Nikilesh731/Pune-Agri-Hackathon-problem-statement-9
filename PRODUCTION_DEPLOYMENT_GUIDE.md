# Production Deployment Guide: Docling + Granite Pipeline

## Overview

This guide covers the end-to-end production deployment of the AI document processing system with:
- **Docling** as primary text ingestion layer
- **Granite** as semantic extraction layer
- **Railway** for backend + ai-services
- **Vercel** for frontend

---

## Architecture Flow

```
Frontend Upload (Vercel)
    ↓
Backend API (Railway TypeScript)
    ↓
AI Services API (Railway Python - FastAPI)
    ├─ Docling (document parsing → raw text extraction)
    ├─ Classification (pre-identify document type)
    ├─ OCR Fallback (if Docling text is poor quality)
    ├─ Granite (semantic extraction & field identification)
    └─ Response Normalization
    ↓
Backend Response Processing
    ├─ Summarization
    ├─ Priority Scoring
    ├─ Fraud Detection
    └─ AI Summary
    ↓
Frontend Display (Vercel)
```

---

## Part 1: Railway Deployment - AI Services

### Environment Variables Required

```env
# Core Service
PORT=8080
NODE_ENV=production

# Document Processing
USE_DOCLING=true
USE_GRANITE=true
GRANITE_ENDPOINT=http://your-granite-endpoint:8000  # or "internal" for LLM-backed
GRANITE_API_KEY=your_api_key_if_needed

# OCR Configuration
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# CORS for Frontend
CORS_ORIGIN=https://your-vercel-frontend.vercel.app,http://localhost:3000

# Optional: LLM Configuration (if using internal Granite)
LLM_MODEL_NAME=granite-20b-code-instruct-v2
LLM_API_KEY=your_llm_api_key
```

### Deployment Steps (Railway)

1. **Connect GitHub Repository**
   ```
   Railway → Create New Project → GitHub → Select Repository → Confirm
   ```

2. **Configure Build & Start Commands**
   - Build: (automatic via Dockerfile or nixpacks.toml)
   - Start: (configured in Dockerfile/nixpacks.toml)

3. **Add Environment Variables**
   ```
   Railway → Variables → Add each env var from above
   ```

4. **Deploy**
   ```
   Git push to main branch
   Railway automatically builds and deploys
   ```

5. **Verify Deployment**
   ```bash
   curl https://railway-app-id.up.railway.app/health
   
   Expected Response:
   {
     "status": "ok",
     "service": "AI Smart Agriculture Services",
     "ocr": true,
     "granite": true
   }
   ```

---

## Part 2: Railway Deployment - Backend (TypeScript)

### Environment Variables Required

```env
# Service URLs
AI_SERVICE_URL=https://ai-services-url.railway.app  # from AI Services Railway app
DATABASE_URL=your_database_url

# All other existing backend env vars
FRONTEND_URL=https://your-vercel-frontend.vercel.app
```

### Deployment Steps (Railway)

Same as AI Services - connect, configure env vars, deploy.

---

## Part 3: Vercel Deployment - Frontend

### Environment Variables Required

```env
# API Base URL
VITE_API_BASE_URL=https://backend-url.railway.app  # Backend Railway app URL
VITE_AI_SERVICE_URL=https://ai-services-url.railway.app  # Optional: direct AI service calls
```

### Deployment Steps

1. Connect GitHub to Vercel
2. Add environment variables in Vercel dashboard
3. Deploy (automatic on push to main)

---

## API Endpoints

### Main Document Processing Endpoint

**POST** `/api/document-processing/process`

**Request:**
```json
{
  "file": "multipart/form-data",
  "processing_type": "full_process",
  "options": {}
}
```

**Response:**
```json
{
  "request_id": "req_123456789",
  "success": true,
  "processing_time_ms": 2500,
  "processing_type": "full_process",
  "filename": "application.pdf",
  "data": {
    "document_type": "scheme_application",
    "classification_confidence": 0.92,
    "classification_reasoning": {
      "keywords_found": ["scheme", "application", "beneficiary"],
      "structural_indicators": ["form_layout", "field_names"],
      "confidence_factors": ["strong_keyword_match", "structure_match"]
    },
    "structured_data": {
      "farmer_name": "राज कुमार",
      "aadhaar_number": "****1234",
      "bank_account_number": "****5678",
      "ifsc_code": "SBIN0010001",
      "land_area": "2.5",
      "crop_type": "गेहूं",
      "village": "नई दिल्ली",
      "district": "दिल्ली",
      "state": "दिल्ली",
      "mobile_number": "98765****",
      "requested_amount": "50000",
      "application_id": "APP2024001",
      "date_of_application": "2024-01-15",
      "scheme_name": "PM Kisan Samman Nidhi"
    },
    "extracted_fields": {
      "farmer_name": "राज कुमार",
      "aadhaar_number": "****1234",
      "requested_amount": "50000"
    },
    "missing_fields": [
      "land_record_number",
      "crop_insurance_id"
    ],
    "confidence": 0.85,
    "reasoning": [
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
      "village": "नई दिल्ली"
    },
    "summary": "Scheme application for PM Kisan from राज कुमार in नई दिल्ली, requesting ₹50,000.",
    "ai_summary": "Application for PM Kisan scheme received from farmer राज कुमार. Document contains all required information. Recommended for approval.",
    "parser": "docling",
    "raw_text": "..."
  },
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "docling_available": true,
    "granite_available": true,
    "file_type": "pdf",
    "docling_text_length": 2500,
    "has_tables": false,
    "has_sections": true,
    "pre_identified_type": "scheme_application",
    "pre_identification_confidence": 0.86
  },
  "error_message": null
}
```

### Health Check Endpoint

**GET** `/health`

Response:
```json
{
  "status": "ok",
  "service": "AI Smart Agriculture Services",
  "version": "1.0.0",
  "ocr": true,
  "granite": true
}
```

---

## Testing Production Pipeline

### 1. Test Text Extraction (Docling)

```bash
curl -X POST http://localhost:8000/api/document-processing/process \
  -F "file=@test_application.pdf" \
  -F "processing_type=full_process"
```

### 2. Test Document Classification

```bash
curl -X POST http://localhost:8000/api/document-processing/classify \
  -F "file=@test_document.pdf"
```

### 3. Test Full End-to-End

```bash
# Upload through frontend
# Check AI services logs for:
# [DOCLING] document ingestion successful
# [CLASSIFY] pre-identified as scheme_application
# [GRANITE] semantic extraction complete
# [PIPELINE] final response generated
```

---

## Sample Test Documents & Expected Responses

### Test Case 1: PM Kisan Scheme Application (English)

**Input**: PDF with scheme application form

**Expected Response**:
```json
{
  "document_type": "scheme_application",
  "classification_confidence": 0.89,
  "structured_data": {
    "farmer_name": "John Smith",
    "applicant_name": "John Smith",
    "aadhaar_number": "123456789012",
    "bank_account_number": "1234567890",
    "ifsc_code": "SBIN0001234",
    "land_area": "5",
    "crop_type": "wheat",
    "village": "Smith Village",
    "district": "Delhi",
    "state": "Delhi",
    "mobile_number": "9876543210",
    "requested_amount": "50000",
    "application_id": "PM2024001",
    "date_of_application": "2024-01-15",
    "scheme_name": "PM Kisan Samman Nidhi"
  },
  "confidence": 0.87,
  "reasoning": [
    "Contains all required PM Kisan scheme fields",
    "Application ID present and valid format",
    "Financial information complete"
  ],
  "risk_flags": []
}
```

### Test Case 2: Subsidy Claim (Hindi/Mixed Language)

**Input**: PDF with drip irrigation subsidy claim in Hindi

**Expected Response**:
```json
{
  "document_type": "subsidy_claim",
  "classification_confidence": 0.84,
  "structured_data": {
    "farmer_name": "राज कुमार",
    "applicant_name": "राज कुमार",
    "land_area": "2.5",
    "crop_type": "गेहूं",
    "requested_amount": "75000",
    "subsidy_type": "ड्रिप सिंचाई"
  },
  "confidence": 0.82,
  "reasoning": [
    "Strong subsidy-specific keywords found",
    "Irrigation-related terminology detected",
    "Financial claim details complete"
  ],
  "risk_flags": [
    {
      "code": "MISSING_LAND_RECEIPTS",
      "severity": "medium",
      "message": "Supporting land documents not included"
    }
  ]
}
```

### Test Case 3: Scanned Image (OCR Fallback)

**Input**: JPEG of handwritten grievance letter

**Expected Response**:
```json
{
  "document_type": "grievance",
  "classification_confidence": 0.76,
  "parser": "docling",
  "metadata": {
    "ocr_fallback_used": true,
    "ocr_language": "eng+hin+mar"
  },
  "structured_data": {
    "complainant_name": "राहुल शर्मा",
    "subject": "Delayed subsidy payment",
    "reference_number": "COMP2024567"
  },
  "confidence": 0.71,
  "reasoning": [
    "Document identified as grievance from content",
    "OCR fallback applied for scanned image",
    "Core grievance information extracted"
  ]
}
```

---

## Troubleshooting

### Issue: Docling Not Available

**Symptoms**: Error message about Docling import failing

**Solution**:
1. Verify `docling==1.30.0` in requirements.txt
2. Check Railway build logs for pip install errors
3. Rebuild with: `railway up` or redeploy

### Issue: Granite Extraction Fails

**Symptoms**: Granite service returns error or timeout

**Solution**:
1. Check `GRANITE_ENDPOINT` environment variable
2. Verify Granite service is running and accessible
3. Check logs for timeout errors
4. If using internal Granite, ensure LLM model is configured

### Issue: OCR Not Working

**Symptoms**: Image files fail to process

**Solution**:
1. Verify Tesseract is installed: `which tesseract`
2. Check language packs installed: `tesseract --list-langs`
3. Verify `TESSDATA_PREFIX` environment variable
4. In Dockerfile, confirm: `tesseract-ocr-eng`, `tesseract-ocr-hin`, `tesseract-ocr-mar`

### Issue: Poor Text Extraction Quality

**Symptoms**: Extracted text is garbled or missing

**Solution**:
1. Check if Docling is actually being used (check logs for `[DOCLING]`)
2. If images, ensure OCR fallback is enabled
3. Try alternative PDF preprocessing
4. Check file format - some PDFs require special handling

---

## Performance Optimization

### Document Processing Latency

| Component | Typical Time |
|-----------|-------------|
| Docling Text Extraction | 500-1500ms |
| OCR Fallback | 1000-3000ms |
| Classification | 50-150ms |
| Granite Extraction | 1000-2500ms |
| Backend Processing | 1000-2000ms |
| **Total E2E** | **3500-9000ms** |

### Optimization Tips

1. **Cache classification results** for similar documents
2. **Batch process** documents when possible
3. **Use OCR selectively** - only for low-quality Docling output
4. **Pre-warm** Granite model on deployment
5. **Monitor** processing times in production

---

## Monitoring & Logging

### Key Logs to Monitor

```
[DOCLING] - Document ingestion status
[CLASSIFY] - Document type identification
[OCR] - OCR fallback indication
[GRANITE] - Semantic extraction progress
[PIPELINE] - Pipeline completion status
```

### Example Production Log Sequence

```
[EXTRACT] Using Docling+Granite pipeline for application.pdf
[DOCLING] Starting ingestion for application.pdf
[DOCLING] success for application.pdf: 2500 chars
[CLASSIFY] Pre-identified as scheme_application (confidence: 0.86)
[GRANITE] Starting semantic extraction for application.pdf
[GRANITE] Extraction complete: scheme_application
[PIPELINE] Final extraction complete - document_type=scheme_application, confidence=0.85
```

---

## Rollback Procedure

If issues occur:

1. **Railroad Health Check**
   ```bash
   curl https://ai-services-url/health
   ```

2. **Revert Last Deployment**
   - Railway → Deployments → Select Previous → Redeploy

3. **Check Logs**
   - Railway → Logs → Filter by time/service

4. **Verify Connectivity**
   ```bash
   curl https://ai-services-url/api/document-processing/health
   ```

---

## Security Considerations

1. **API Keys**: Store in Railway environment variables, never in code
2. **CORS**: Restrict to specific frontend domains
3. **Rate Limiting**: Implement in production (future enhancement)
4. **Data Privacy**: Do not log PII (Aadhaar, banking details)
5. **SSL/TLS**: Enabled by default on Railway

---

## Support & Next Steps

- Monitor production logs for any issues
- Collect performance metrics and optimize
- Implement monitoring dashboard
- Plan for multi-document batch processing
- Add document validation rules

