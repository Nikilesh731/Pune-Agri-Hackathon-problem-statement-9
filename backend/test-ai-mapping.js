#!/usr/bin/env node

/**
 * Test script to verify AI response mapping fix
 * This script simulates the AI response structure and tests the normalization
 */

const { aiOrchestratorService } = require('./dist/modules/ai-orchestrator/ai-orchestrator.service');

// Mock AI response structure that matches what the AI service actually returns
const mockAIResponse = {
  success: true,
  data: {
    extracted_data: {
      farmer_name: "Rajesh Kumar",
      aadhaar_number: "234567890123",
      land_size: "2.5",
      scheme_name: "Pradhan Mantri Krishi Sinchai Yojana",
      annual_income: "45000",
      location: "Village: Rampur, District: Varanasi",
      requested_amount: "25000",
      document_type: "scheme_application",
      confidence: 0.85,
      field_confidences: {
        farmer_name: 0.9,
        aadhaar_number: 0.95,
        land_size: 0.8,
        scheme_name: 0.85
      },
      extraction_confidence: 0.85,
      missing_fields: [],
      validation_summary: {
        has_errors: false,
        errors: []
      }
    },
    structured_data: {
      recommendation: "APPROVE_FOR_REVIEW",
      reasoning: ["All required fields present", "Confidence scores above threshold"]
    }
  },
  processingTime: 1500,
  requestId: "test_req_123",
  timestamp: new Date()
};

async function testAIMapping() {
  console.log('=== Testing AI Response Mapping Fix ===\n');
  
  try {
    // Test the normalizeToCanonicalSchema method directly
    const canonicalData = aiOrchestratorService.normalizeToCanonicalSchema(mockAIResponse, 'test_document.pdf');
    
    console.log('✅ Canonical mapping successful:');
    console.log('- Applicant name:', canonicalData.applicant.name);
    console.log('- Aadhaar number:', canonicalData.applicant.aadhaar_number);
    console.log('- Land size:', canonicalData.agriculture.land_size);
    console.log('- Scheme name:', canonicalData.request.scheme_name);
    console.log('- Location:', canonicalData.agriculture.location);
    console.log('- Extraction confidence:', canonicalData.verification.extraction_confidence);
    
    // Verify no empty values
    const hasEmptyValues = !canonicalData.applicant.name || 
                          !canonicalData.applicant.aadhaar_number ||
                          !canonicalData.agriculture.land_size ||
                          !canonicalData.request.scheme_name;
    
    if (hasEmptyValues) {
      console.log('\n❌ FAILED: Empty values found in canonical data');
      return false;
    } else {
      console.log('\n✅ SUCCESS: All fields contain real extracted values');
      return true;
    }
    
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    return false;
  }
}

// Run the test
testAIMapping().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});
