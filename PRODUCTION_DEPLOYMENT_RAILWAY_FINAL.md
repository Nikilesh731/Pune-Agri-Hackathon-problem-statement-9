# PRODUCTION DEPLOYMENT GUIDE - RAILWAY DEPLOYMENT

## Overview

This guide provides **FINAL CRITICAL STEPS** to deploy the production-grade AI document processing system to Railway with the Docling + Granite pipeline.

---

## CRITICAL FILES MODIFIED

1. ✅ **requirements.txt** - Cleaned, Railway-safe dependencies only
2. ✅ **Dockerfile** - Single source of truth (ONLY use this, ignore nixpacks.toml)
3. ✅ **granite_extraction_service_v2.py** - Lightweight semantic extraction (NO external deps)
4. ✅ **document_processing_service.py** - Updated to use Granite V2
5. ✅ **document_processing_router.py** - Enhanced with strict pipeline

---

## PART 1: PRE-DEPLOYMENT VERIFICATION (LOCAL)

### Step 1: Test Pipeline Locally

```bash
cd ai-services

# Run test suite
python test_production_pipeline.py

# Expected output:
# ✓ PASS: Docling Ingestion
# ✓ PASS: Document Classification  
# ✓ PASS: Granite Extraction
# ✓ PASS: Full Pipeline
# Total: 4/4 tests passed
# [✓] ALL TESTS PASSED - Production ready!
```

### Step 2: Verify Requirements

```bash
# Check that all required packages are installable
pip install -r requirements.txt

# CRITICAL CHECKS:
# - docling should install successfully
# - NO torch, transformers, or sklearn
# - pytesseract + opencv-python-headless for OCR
```

### Step 3: Check Dockerfile

```bash
# Build locally first
docker build -t agri-ai-services-test .

# Expected output: "Successfully tagged agri-ai-services-test"
```

---

## PART 2: RAILWAY DEPLOYMENT

### Step 1: Connect to Railway

1. Push code to GitHub (main branch)
2. Go to Railroad → Create New Project
3. Select GitHub → Authorize → Select `agri_hackathon_clean` repository
4. Select `ai-services` as the deployment directory

### Step 2: Configure Railway Build Settings

```
Railway Dashboard → Settings:

Build command: (leave empty - uses Dockerfile)
Start command: (leave empty - uses Dockerfile)
```

### Step 3: Set Environment Variables (CRITICAL)

In Railway Dashboard → Variables:

```env
# Application
PORT=8080
NODE_ENV=production
PYTHONUNBUFFERED=1

# OCR Configuration (REQUIRED)
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Docling
USE_DOCLING=true

# Granite (lightweight V2 - internal)
USE_GRANITE=true
GRANITE_ENDPOINT=internal

# CORS (adjust to your frontend URL)
CORS_ORIGIN=https://your-frontend.vercel.app,http://localhost:3000
```

### Step 4: Deploy

```
Click "Deploy" button or push to main branch
Monitor build logs for:
- apt-get install tesseract-ocr succeeds
- pip install -r requirements.txt succeeds
- No torch/transformers errors
- App starts successfully
```

### Step 5: Test Deployment

```bash
# Get Railway app URL from Dashboard
RAILWAY_URL=https://your-railway-app.up.railway.app

# Test health endpoint
curl ${RAILWAY_URL}/health

# Expected response:
# {"status":"ok","service":"AI Smart Agriculture Services","version":"1.0.0","ocr":true,"granite":true}
```

---

## PART 3: PRODUCTION TEST (2 REAL DOCUMENTS)

### Test Case 1: PM Kisan Scheme Application (PDF)

```bash
# Sample file: test_documents/pm_kisan_application.pdf

curl -X POST ${RAILWAY_URL}/api/document-processing/process \
  -F "file=@test_documents/pm_kisan_application.pdf" \
  -F "processing_type=full_process"

# Expected response (200 OK):
{
  "success": true,
  "document_type": "scheme_application",
  "classification_confidence": 0.85,
  "parser": "docling",
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
  "ai_summary": "Scheme application received from राज कुमार in नई दिल्ली requesting ₹50,000.",
  "confidence": 0.87,
  "reasoning": [
    "Identified applicant: राज कुमार",
    "Financial amount detected: 50000",
    "Crop type identified: गेहूं",
    "Document classification: scheme_application"
  ],
  "risk_flags": [],
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "docling_available": true,
    "granite_available": true
  }
}
```

### Test Case 2: Subsidy Claim (Scanned Image - Tests OCR)

```bash
# Sample file: test_documents/drip_irrigation_claim.jpg

curl -X POST ${RAILWAY_URL}/api/document-processing/process \
  -F "file=@test_documents/drip_irrigation_claim.jpg" \
  -F "processing_type=full_process"

# Expected response (200 OK):
{
  "success": true,
  "document_type": "subsidy_claim",
  "classification_confidence": 0.78,
  "parser": "docling",
  "structured_data": {
    "farmer_name": "राहुल शर्मा",
    "land_area": "1.5",
    "crop_type": "गेहूं",
    "requested_amount": "75000",
    "village": "पंचकूला",
    "district": "हरियाणा",
    "state": "हरियाणा"
  },
  "ai_summary": "Subsidy claim received from राहुल शर्मा in पंचकूला requesting ₹75,000.",
  "confidence": 0.82,
  "metadata": {
    "pipeline": "docling_granite",
    "parser": "docling",
    "ocr_fallback_used": true
  }
}
```

---

## PART 4: BACKEND INTEGRATION

### Update Backend to Use New AI Service

In backend `src/services/document-processing.service.ts`:

```typescript
async processDocumentRemote(fileBuffer: Buffer, fileName: string): Promise<DocumentProcessingResponse> {
  const formData = new FormData();
  formData.append('file', new Blob([fileBuffer]), fileName);
  formData.append('processing_type', 'full_process');

  const response = await fetch(`${process.env.AI_SERVICE_URL}/api/document-processing/process`, {
    method: 'POST',
    body: formData,
  });

  const result = await response.json();

  // Expected response structure:
  return {
    request_id: result.request_id,
    success: result.success,
    document_type: result.data.document_type,
    classification_confidence: result.data.classification_confidence,
    structured_data: result.data.structured_data,
    extracted_fields: result.data.extracted_fields,
    ai_summary: result.data.ai_summary,
    confidence: result.data.confidence,
    risk_flags: result.data.risk_flags,
    metadata: result.metadata
  };
}
```

---

## PART 5: ENVIRONMENT VARIABLES CHECKLIST

### AI Services (Railway)

```env
# Required for Railway
PORT=8080
PYTHONUNBUFFERED=1

# Document Processing
USE_DOCLING=true
USE_GRANITE=true
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# CORS (allow your frontend)
CORS_ORIGIN=https://your-vercel-frontend.vercel.app

# Optional logging level
LOG_LEVEL=INFO
```

### Backend (Railway) 

```env
# AI Service URL (from Railway)
AI_SERVICE_URL=https://your-ai-services.railway.app

# Database
DATABASE_URL=your_database_url

# Frontend
FRONTEND_URL=https://your-vercel-frontend.vercel.app
```

### Frontend (Vercel)

```env
VITE_API_BASE_URL=https://your-backend.railway.app
VITE_AI_SERVICE_URL=https://your-ai-services.railway.app
```

---

## PART 6: MONITORING & TROUBLESHOOTING

### Check Logs in Railway

```
Dashboard → Deployments → Logs

Look for:
[INIT] Docling ingestion service initialized
[INIT] Granite extraction service V2 (lightweight) initialized
[EXTRACT] Using Docling+Granite pipeline
[DOCLING] Starting ingestion
[CLASSIFY] Pre-identified as scheme_application
[GRANITE] Starting semantic extraction
[PIPELINE] Final extraction complete
```

### Common Issues & Fixes

#### Issue 1: Build Timeout

**Symptom**: Build fails after 15 minutes

**Cause**: Heavy dependencies in requirements.txt

**Fix**: Verify requirements.txt has:
- ✗ NO torch
- ✗ NO transformers
- ✗ NO scipy
- ✗ NO pandas (removed)
- ✓ ONLY: fastapi, uvicorn, docling, pytesseract, opencv-headless

#### Issue 2: Tesseract Not Found

**Symptom**: OCR endpoint returns error

**Cause**: System dependencies not installed

**Fix**: Verify Dockerfile has:
```dockerfile
RUN apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar
```

#### Issue 3: Granite Service Unavailable

**Symptom**: All requests fail with "Granite unavailable"

**Cause**: Old granite_extraction_service.py still being imported

**Fix**: 
1. Verify using `granite_extraction_service_v2.py`
2. Check document_processing_service.py imports new V2
3. Restart Railway app

#### Issue 4: Poor Text Extraction

**Symptom**: Document type always "unknown"

**Cause**: Docling not working or Tesseract language packs missing

**Fix**:
1. Check logs for "[DOCLING]" entries
2. Verify TESSDATA_PREFIX environment variable
3. Re-check Dockerfile language packs installation

---

## PART 7: PRODUCTION SUCCESS CRITERIA

After deployment, verify ALL of the following:

- [ ] Railway build completes without timeout (should be < 10 minutes)
- [ ] `/health` endpoint returns status=ok
- [ ] OCR is available (health returns ocr:true)
- [ ] Granite is available (health returns granite:true)
- [ ] Docling processes PDFs without errors
- [ ] OCR fallback works for images
- [ ] Classification identifies document types correctly
- [ ] Granite extracts structured_data with fields
- [ ] AI summary is generated for all documents
- [ ] Risk flags are populated when needed
- [ ] Both Hindi and English documents process correctly
- [ ] Response time is < 5 seconds per document
- [ ] Frontend receives ai_summary in response
- [ ] No crashes on invalid/corrupted files

---

## PART 8: ROLLBACK PROCEDURE

If something breaks:

```
1. Railway → Deployments → Select Previous Version
2. Click "Redeploy"
3. Wait for build/deployment
4. Test with same test case
5. If successful, revert changes locally and retry
```

---

## FINAL CHECKLIST BEFORE GOING LIVE

- [x] requirements.txt cleaned and tested locally
- [x] Dockerfile builds successfully
- [x] granite_extraction_service_v2.py no external dependencies
- [x] document_processing_service.py uses V2
- [x] All imports updated
- [x] Test pipeline passes all checks
- [x] Environment variables documented
- [x] Backend integration tested
- [x] Monitor logs for errors
- [x] Production test documents processed successfully

---

## SUPPORT & NEXT STEPS

1. Monitor production logs for first 24 hours
2. Collect processing time metrics
3. Optimize OCR timeout if needed
4. Plan multi-document batch processing enhancement
5. Implement result caching (optional)

**You are now PRODUCTION READY!**
