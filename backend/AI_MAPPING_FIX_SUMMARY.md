# Backend AI Response Mapping Fix - Summary

## Problem
The backend was saving empty extracted fields into `applications.extracted_data` even though the AI service was returning real extracted values successfully.

## Root Cause
The AI response normalization logic was using incorrect paths to access the extracted data from the AI service response.

## Files Changed

### 1. `backend/src/modules/ai-orchestrator/ai-orchestrator.service.ts`

**Old wrong response path:**
```typescript
const extractionData = aiServiceOutput.structured_data || aiServiceOutput
```

**New correct response path:**
```typescript
const payload = aiServiceOutput?.data || aiServiceOutput || {};
const extracted = 
  payload?.extracted_data ||
  payload?.structured_data?.structured_data ||
  payload?.structured_data ||
  payload || {};
```

**Changes made:**
- Fixed `normalizeToCanonicalSchema` method to use correct AI response paths
- Added comprehensive logging to track data flow
- Updated data extraction in `processDocument` method
- Ensured canonical schema is built from real extracted values

### 2. `backend/src/modules/applications/applications.service.ts`

**Old wrong response path:**
```typescript
const aiResult = aiResponse.data?.extractedData || {};
const normalizedData = 
  rawData?.structured_data ||
  rawData ||
  aiResult?.extracted_data ||
  aiResult ||
  {};
```

**New correct response path:**
```typescript
const payload = aiResponse.data || {};
const extracted = 
  payload?.extracted_data ||
  payload?.structured_data?.structured_data ||
  payload?.structured_data ||
  {};
```

**Changes made:**
- Fixed `triggerAIProcessing` method to use correct AI response paths
- Added logging for verification after database save
- Simplified extraction logic to use real extracted data directly
- Added verification logging to confirm values were saved correctly

## AI Response Structure Fixed

The fix now properly handles the AI service response shape:
```
aiResponse.data.extracted_data (primary)
aiResponse.data.structured_data.structured_data (fallback 1)
aiResponse.data.structured_data (fallback 2)
aiResponse.data (fallback 3)
```

## Example Saved extractedData After Fix

```json
{
  "farmer_name": "Rajesh Kumar",
  "aadhaar_number": "234567890123",
  "land_size": "2.5",
  "scheme_name": "Pradhan Mantri Krishi Sinchai Yojana",
  "annual_income": "45000",
  "location": "Village: Rampur, District: Varanasi",
  "requested_amount": "25000",
  "document_type": "scheme_application",
  "confidence": 0.85,
  "field_confidences": {
    "farmer_name": 0.9,
    "aadhaar_number": 0.95,
    "land_size": 0.8,
    "scheme_name": 0.85
  },
  "extraction_confidence": 0.85,
  "missing_fields": [],
  "canonical": {
    "document_type": "scheme_application",
    "document_category": "agriculture_administration",
    "applicant": {
      "name": "Rajesh Kumar",
      "aadhaar_number": "234567890123",
      "address": "Village: Rampur, District: Varanasi",
      "village": "Village: Rampur, District: Varanasi",
      "district": "Village: Rampur, District: Varanasi"
    },
    "agriculture": {
      "land_size": "2.5",
      "land_unit": "acres",
      "location": "Village: Rampur, District: Varanasi"
    },
    "request": {
      "scheme_name": "Pradhan Mantri Krishi Sinchai Yojana",
      "requested_amount": "25000"
    },
    "verification": {
      "extraction_confidence": 0.85,
      "field_confidences": {
        "farmer_name": 0.9,
        "aadhaar_number": 0.95,
        "land_size": 0.8,
        "scheme_name": 0.85
      }
    }
  }
}
```

## How to Test After Fix

### 1. Restart Backend
```bash
cd backend
npm run dev
```

### 2. Upload a Fresh Document
- Upload a new agricultural subsidy application PDF
- Wait for AI processing to complete

### 3. Verify Database Contents
```sql
select id, extracted_data, ai_processing_status
from applications
order by created_at desc
limit 3;
```

### 4. Check Specific Fields
```sql
select 
  id,
  extracted_data->>'farmer_name' as farmer_name,
  extracted_data->>'scheme_name' as scheme_name,
  extracted_data->>'location' as location,
  extracted_data->>'aadhaar_number' as aadhaar_number,
  extracted_data->>'land_size' as land_size,
  ai_processing_status
from applications
order by created_at desc
limit 1;
```

### 5. Run Test Script
```bash
cd backend
npm run build
node test-ai-mapping.js
```

## Expected Results After Fix

✅ `applications.extracted_data` contains real extracted values
✅ `farmer_name` is not empty
✅ `scheme_name` is not empty  
✅ `location` is not empty
✅ `aadhaar_number` is not empty
✅ Frontend shows real extracted information instead of empty canonical defaults
✅ Logs show `[AI MAP]` messages confirming correct data paths
✅ Verification logs confirm values were saved to database

## Logging Added

The fix includes comprehensive logging:
- `[AI MAP] payload keys:` - Shows what keys are available in AI response
- `[AI MAP] extracted source:` - Shows which path provided the data
- `[AI MAP] farmer_name from source:` - Shows specific field values
- `[VERIFY SAVE]` - Confirms values were actually saved to database

## Done When

- applications.extracted_data contains real extracted values
- farmer_name is not empty
- scheme_name is not empty
- location is not empty
- aadhaar_number is not empty
- frontend shows real extracted information instead of only empty canonical defaults
