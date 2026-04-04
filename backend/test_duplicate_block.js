/**
 * Simple test to verify strict duplicate block functionality
 */

// Test the service directly
const { applicationsService } = require('./dist/modules/applications/applications.service');

async function testStrictDuplicateBlock() {
  console.log('='.repeat(80));
  console.log('STRICT DUPLICATE BLOCK TEST');
  console.log('='.repeat(80));

  try {
    // Test data
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

    console.log('\n1. Creating first application (should succeed)...');
    const result1 = await applicationsService.createApplication(testData);
    console.log('Result 1:', {
      success: result1.success,
      status: result1.status,
      message: result1.message,
      applicationId: result1.application?.id
    });

    if (result1.success) {
      console.log('\n2. Creating duplicate application (should be blocked)...');
      
      try {
        const result2 = await applicationsService.createApplication(testData);
        console.log('ERROR: Duplicate was not blocked! Result 2:', result2);
        console.log('❌ TEST FAILED - Duplicate should have been blocked');
      } catch (error) {
        if (error.message.includes('Duplicate submission')) {
          console.log('✅ TEST PASSED - Duplicate properly blocked');
          console.log('Error message:', error.message);
        } else {
          console.log('❌ TEST FAILED - Wrong error type:', error.message);
        }
      }
    } else {
      console.log('❌ First application creation failed, cannot test duplicate blocking');
    }

  } catch (error) {
    console.error('❌ TEST ERROR:', error.message);
  }

  console.log('\n' + '='.repeat(80));
  console.log('TEST COMPLETE');
  console.log('='.repeat(80));
}

// Run the test
testStrictDuplicateBlock().catch(console.error);
