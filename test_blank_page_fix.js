/**
 * Test script to verify blank application detail page fix
 */
const { mapApplicationToUI } = require('./frontend/src/utils/applicationDetailMapper');

console.log('Testing safe mapper guard...');

// Test 1: Null application
const result1 = mapApplicationToUI(null);
console.log('Test 1 - Null app:', {
  hasId: !!result1.id,
  hasError: !!result1.error,
  hasExtractedData: !!result1.extractedData,
  error: result1.error
});

// Test 2: Application without extractedData
const result2 = mapApplicationToUI({ id: 'test-app', fileName: 'test.pdf' });
console.log('Test 2 - No extractedData:', {
  hasId: !!result2.id,
  hasError: !!result2.error,
  hasExtractedData: !!result2.extractedData,
  error: result2.error
});

// Test 3: Valid application with extractedData
const result3 = mapApplicationToUI({
  id: 'valid-app',
  fileName: 'valid.pdf',
  extractedData: {
    document_type: 'scheme_application',
    structured_data: { farmer_name: 'Test Farmer' }
  }
});
console.log('Test 3 - Valid app:', {
  hasId: !!result3.id,
  hasError: !!result3.error,
  hasExtractedData: !!result3.extractedData,
  documentType: result3.type
});

console.log('\n✅ Safe mapper guard test completed');
