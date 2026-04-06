# 🚀 QUICK START - RAILWAY DEPLOYMENT (5 STEPS)

**Time to Production**: ~15 minutes

---

## ✅ STEP 1: VERIFY LOCALLY (5 minutes)

```bash
cd ai-services

# Test everything works
python test_production_pipeline.py

# Expected output:
# ✓ PASS: Docling Ingestion
# ✓ PASS: Document Classification
# ✓ PASS: Granite Extraction
# ✓ PASS: Full Pipeline
# Total: 4/4 tests passed
```

**If all pass** → Go to Step 2
**If any fail** → Check logs and fix before proceeding

---

## ✅ STEP 2: PUSH TO GITHUB (2 minutes)

```bash
cd ../..  # Go to repo root

git add ai-services/
git add PRODUCTION_READY_SUMMARY.md
git add PRODUCTION_DEPLOYMENT_RAILWAY_FINAL.md

git commit -m "Production deployment: Docling+Granite lightweight pipeline"

git push origin main
```

---

## ✅ STEP 3: CONFIGURE RAILWAY (5 minutes)

1. Go to **Railway Dashboard** → Create New Project
2. Select **GitHub** → Authorize → Select `agri_hackathon_clean` repo
3. Railway auto-detects → Click **ai-services** folder
4. Railway creates deployment

### Configure Environment Variables:

In Railway Dashboard → **Variables** (add these):

```env
PORT=8080
NODE_ENV=production
PYTHONUNBUFFERED=1

USE_DOCLING=true
USE_GRANITE=true
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

CORS_ORIGIN=https://your-vercel-frontend.vercel.app,http://localhost:3000
```

Click **Deploy** button

---

## ✅ STEP 4: WAIT FOR BUILD (3 minutes)

Watch logs in Railway Dashboard:

**Look for these SUCCESS messages:**
```
✓ apt-get install tesseract-ocr
✓ pip install -r requirements.txt
✓ [INIT] Docling ingestion service initialized
✓ [INIT] Granite extraction service V2 initialized
✓ Uvicorn running on 0.0.0.0:8080
```

---

## ✅ STEP 5: TEST IN PRODUCTION (1 minute)

Get your Railway URL from Dashboard (looks like: `https://xxx-production.up.railway.app`)

### Test Health:

```bash
curl https://your-railway-url/health

# Expected:
# {"status":"ok","service":"AI Smart Agriculture Services","version":"1.0.0","ocr":true,"granite":true}
```

### Test Document Processing:

```bash
curl -X POST https://your-railway-url/api/document-processing/process \
  -F "file=@test_document.pdf"

# Expected: 200 OK with structured data
```

---

## 🎯 EXPECTED RESPONSE FORMAT

```json
{
  "success": true,
  "data": {
    "document_type": "scheme_application",
    "classification_confidence": 0.87,
    "structured_data": {
      "farmer_name": "राज कुमार",
      "requested_amount": "50000",
      ...
    },
    "ai_summary": "PM Kisan application from राज कुमार...",
    "confidence": 0.87,
    "risk_flags": []
  }
}
```

---

## ⚠️ COMMON ERRORS & FIXES

| Error | Fix |
|-------|-----|
| Build timeout > 15min | Check requirements.txt has NO torch/sklearn/pandas |
| Tesseract not found | Verify Dockerfile has OCR install commands |
| Granite unavailable | Check new `granite_extraction_service_v2.py` is imported |
| Module not found | Verify file paths in document_processing_service.py |
| CORS errors | Set CORS_ORIGIN env var to your frontend URL |

---

## ✅ SUCCESS CHECKLIST

- [ ] Local test passes
- [ ] Code pushed to GitHub
- [ ] Railway build completes in < 10 min
- [ ] Health endpoint returns ok
- [ ] Document processes and returns ai_summary
- [ ] Classification works (scheme_application, subsidy_claim, etc)
- [ ] Frontend receives response

---

## 🔗 INTEGRATION WITH BACKEND

Update backend `src/services/document-processing.service.ts`:

```typescript
async processDocumentRemote(fileBuffer: Buffer, fileName: string) {
  const formData = new FormData();
  formData.append('file', new Blob([fileBuffer]), fileName);
  
  const response = await fetch(
    `${process.env.AI_SERVICE_URL}/api/document-processing/process`,
    { method: 'POST', body: formData }
  );
  
  return response.json(); // Contains ai_summary, structured_data, etc
}
```

---

## 📊 PERFORMANCE

Target: < 5 seconds per document

Typical:
- PDF scheme application: 2-3 seconds
- Scanned image (OCR): 3-4 seconds
- Text classification: 0.1 seconds
- Granite extraction: 0.2-0.5 seconds

---

## 🚨 IMMEDIATE ACTIONS

1. **Right Now**: Run `python test_production_pipeline.py`
2. **Next**: Commit and push to GitHub
3. **Then**: Deploy on Railway (takes ~5 minutes)
4. **Finally**: Test with real document

---

**You're all set for production! 🎉**

Questions? See `PRODUCTION_DEPLOYMENT_RAILWAY_FINAL.md` for detailed guide.
