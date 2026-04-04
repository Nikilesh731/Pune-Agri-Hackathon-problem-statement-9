/**
 * Test duplicate error message alignment
 */

const axios = require('axios');

async function testDuplicateErrorMessage() {
  console.log('='.repeat(80));
  console.log('DUPLICATE ERROR MESSAGE ALIGNMENT TEST');
  console.log('='.repeat(80));

  const testData = {
    applicantId: 'test_user_001',
    schemeId: 'scheme_001',
    type: 'scheme_application',
    fileName: 'test_document.pdf',
    fileUrl: 'https://test.com/files/test_document.pdf',
    fileSize: 1024000,
    fileType: 'application/pdf',
    personalInfo: {
      firstName: 'Test',
      lastName: 'User',
      email: 'test@example.com',
      phone: '1234567890',
      dateOfBirth: new Date('1990-01-01'),
      address: {
        street: 'Test Street',
        city: 'Test City',
        district: 'Test District',
        state: 'Test State',
        pincode: '123456'
      }
    }
  };

  try {
    console.log('\n1. Creating first application (should succeed)...');
    const response1 = await axios.post('http://localhost:3001/api/applications', testData);
    console.log('✅ First application created:', response1.data.success);
    console.log('   Message:', response1.data.message);

    if (response1.data.success) {
      console.log('\n2. Creating duplicate application (should show clear error)...');
      
      try {
        const response2 = await axios.post('http://localhost:3001/api/applications', testData);
        console.log('❌ ERROR: Duplicate was not blocked!');
        console.log('   Response:', response2.data);
      } catch (error) {
        if (error.response?.status === 409) {
          console.log('✅ DUPLICATE PROPERLY BLOCKED');
          console.log('   Status Code:', error.response.status);
          console.log('   Error Message:', error.response.data.message);
          
          if (error.response.data.message === 'This document is already in process') {
            console.log('✅ ERROR MESSAGE ALIGNED: "This document is already in process"');
          } else {
            console.log('❌ ERROR MESSAGE NOT ALIGNED');
            console.log('   Expected: "This document is already in process"');
            console.log('   Actual:', error.response.data.message);
          }
        } else {
          console.log('❌ UNEXPECTED ERROR:', error.message);
        }
      }
    }

  } catch (error) {
    console.error('❌ TEST FAILED:', error.message);
    if (error.response) {
      console.error('   Response:', error.response.data);
    }
  }

  console.log('\n' + '='.repeat(80));
  console.log('TEST COMPLETE');
  console.log('='.repeat(80));
}

// Run test
testDuplicateErrorMessage().catch(console.error);
