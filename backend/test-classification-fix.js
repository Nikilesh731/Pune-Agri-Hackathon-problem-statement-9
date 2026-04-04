/**
 * Test script to verify classification field mapping fix
 * This simulates the AI service response structure and tests the canonical mapping
 */

// Simulate the actual AI service response structure
const mockAIResponse = {
  success: true,
  data: {
    request_id: "test-123",
    success: true,
    processing_time_ms: 1500,
    processing_type: "extract_structured",
    filename: "grievance_letter.pdf",
    extracted_data: {
      farmer_name: "R. MUTHUKUMAR",
      scheme_name: "PM-KISAN Support",
      aadhaar_number: "1234 5678 9012",
      land_size: "2.50 acre",
      location: "Vadugapalayam, Coimbatore"
    },
    structured_data: {
      document_type: "grievance_letter",
      classification_confidence: 1.0,
      classification_reasoning: {
        confidence_factors: ["document_content_matches_grievance_keywords", "form_structure_matches_grievance_template"]
      },
      // Other structured data fields
      farmer_name: "R. MUTHUKUMAR",
      scheme_name: "PM-KISAN Support",
      aadhaar_number: "1234 5678 9012",
      land_size: "2.50 acre",
      location: "Vadugapalayam, Coimbatore"
    },
    metadata: {
      extraction_confidence: 0.95
    },
    confidence_score: 0.95
  }
};

// Test the mapping logic
function testCanonicalMapping() {
  console.log("=== TESTING CLASSIFICATION FIELD MAPPING ===");
  
  // Simulate the AI orchestrator mapping logic
  const payload = mockAIResponse.data || {};
  console.log('[TEST] payload keys:', Object.keys(payload || {}));
  
  // Extract classification from the ACTUAL AI response structure
  const structured_data = payload?.structured_data || {};
  console.log('[TEST] structured_data source:', structured_data);
  console.log('[TEST] document_type from structured_data:', structured_data?.document_type);
  console.log('[TEST] classification_confidence from structured_data:', structured_data?.classification_confidence);
  
  const extracted = 
    payload?.extracted_data ||
    payload?.structured_data?.structured_data ||
    payload?.structured_data ||
    payload || {};
  
  console.log('[TEST] extracted source:', extracted);
  console.log('[TEST] farmer_name from source:', extracted?.farmer_name);
  console.log('[TEST] scheme_name from source:', extracted?.scheme_name);
  
  // Helper function to safely extract string values
  const safeString = (value) => value ? String(value).trim() : '';
  
  // Extract classification information with proper priority
  let documentType = safeString(structured_data.document_type);
  let classificationConfidence = typeof structured_data.classification_confidence === 'number' ? 
    structured_data.classification_confidence : 0.0;
  let classificationReasoning = structured_data.classification_reasoning || {};
  
  // Fallback: only use extracted fields if structured_data classification is missing
  if (!documentType && extracted.document_type) {
    documentType = safeString(extracted.document_type);
    console.log('[TEST] Using fallback document_type from extracted:', documentType);
  }
  if (classificationConfidence === 0.0 && typeof extracted.classification_confidence === 'number') {
    classificationConfidence = extracted.classification_confidence;
    console.log('[TEST] Using fallback classification_confidence from extracted:', classificationConfidence);
  }
  if (!classificationReasoning && extracted.classification_reasoning) {
    classificationReasoning = extracted.classification_reasoning;
    console.log('[TEST] Using fallback classification_reasoning from extracted:', classificationReasoning);
  }
  
  // Build canonical data
  const canonicalData = {
    document_type: documentType,
    document_category: 'agriculture_administration',
    applicant: {
      name: safeString(extracted.farmer_name),
      aadhaar_number: safeString(extracted.aadhaar_number),
      address: safeString(extracted.location),
      village: '',
      district: '',
      state: ''
    },
    agriculture: {
      land_size: safeString(extracted.land_size),
      land_unit: 'acres',
      location: safeString(extracted.location)
    },
    request: {
      scheme_name: safeString(extracted.scheme_name),
      request_type: 'subsidy_application'
    },
    verification: {
      classification_confidence: classificationConfidence,
      classification_reasoning: classificationReasoning.confidence_factors || []
    }
  };
  
  console.log('\n=== RESULTS ===');
  console.log('[TEST] source path used for document_type: structured_data.document_type');
  console.log('[TEST] final canonical.document_type:', canonicalData.document_type);
  console.log('[TEST] source path used for classification_confidence: structured_data.classification_confidence');
  console.log('[TEST] final canonical.verification.classification_confidence:', canonicalData.verification.classification_confidence);
  console.log('[TEST] final canonical.verification.classification_reasoning:', canonicalData.verification.classification_reasoning);
  
  // Verify the fix
  const expectedDocumentType = "grievance_letter";
  const expectedConfidence = 1.0;
  
  const success = canonicalData.document_type === expectedDocumentType && 
                  canonicalData.verification.classification_confidence === expectedConfidence;
  
  console.log('\n=== VERIFICATION ===');
  console.log('Expected document_type:', expectedDocumentType);
  console.log('Actual document_type:', canonicalData.document_type);
  console.log('Expected classification_confidence:', expectedConfidence);
  console.log('Actual classification_confidence:', canonicalData.verification.classification_confidence);
  console.log('Test result:', success ? '✅ PASS' : '❌ FAIL');
  
  return success;
}

// Run the test
testCanonicalMapping();
