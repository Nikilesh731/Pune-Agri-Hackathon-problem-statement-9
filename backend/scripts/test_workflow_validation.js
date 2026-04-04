/**
 * Workflow Validation Test Script
 * Tests the core workflow completion with versioning, duplicate blocking, timeline consistency, and status management
 */

const { applicationsService } = require('../src/modules/applications/applications.service');
const { applicationsRepository } = require('../src/modules/applications/applications.repository');

class WorkflowValidator {
  constructor() {
    this.testResults = [];
  }

  async runAllTests() {
    console.log('='.repeat(80));
    console.log('WORKFLOW VALIDATION TEST SUITE');
    console.log('='.repeat(80));

    const testCases = [
      // CASE 1: First upload
      {
        name: 'CASE_1_FIRST_UPLOAD',
        description: 'First upload should create version 1 with no parent',
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application');
          return await applicationsService.createApplication(testData);
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 1 && 
                 result.application?.parentApplicationId === null &&
                 result.status === 'created';
        },
        expectedVersion: 1,
        expectedParentId: null,
        expectedStatus: 'created'
      },

      // CASE 2: Upload again (still under review) - should be blocked
      {
        name: 'CASE_2_DUPLICATE_BLOCKED',
        description: 'Upload again while under review should be blocked',
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application');
          return await applicationsService.createApplication(testData);
        },
        validate: (result) => {
          return !result.success &&
                 result.message?.includes('Duplicate submission');
        },
        expectedStatus: 'duplicate'
      },

      // CASE 3: After REJECTED → upload again - should create version 2
      {
        name: 'CASE_3_RESUBMISSION_AFTER_REJECTED',
        description: 'After REJECTED status, new upload should create version 2',
        setup: async () => {
          // First, find and reject the existing application
          const apps = await applicationsRepository.findApplicationsByFarmer('farmer_001');
          const schemeApp = apps.find(app => 
            app.extractedData?.canonical?.document_type === 'scheme_application' ||
            app.type === 'scheme_application'
          );
          if (schemeApp) {
            await applicationsService.rejectApplication(schemeApp.id);
          }
        },
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application');
          return await applicationsService.createApplication(testData);
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 2 && 
                 result.application?.parentApplicationId !== null &&
                 result.status === 'resubmission';
        },
        expectedVersion: 2,
        expectedStatus: 'resubmission'
      },

      // CASE 4: Different document type should not block
      {
        name: 'CASE_4_DIFFERENT_DOCUMENT_TYPE',
        description: 'Different document type for same farmer should not be blocked',
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'grievance');
          return await applicationsService.createApplication(testData);
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 1 && 
                 result.application?.parentApplicationId === null &&
                 result.status === 'created';
        },
        expectedVersion: 1,
        expectedParentId: null,
        expectedStatus: 'created'
      }
    ];

    for (const testCase of testCases) {
      console.log(`\n${testCase.name}: ${testCase.description}`);
      console.log('-'.repeat(60));
      
      try {
        // Setup if required
        if (testCase.setup) {
          await testCase.setup();
        }

        // Execute test
        const result = await testCase.execute();
        
        // Validate result
        const passed = testCase.validate(result);
        
        // Record result
        this.testResults.push({
          case: testCase.name,
          passed,
          result,
          error: passed ? undefined : 'Validation failed'
        });

        // Log result
        console.log(`Result: ${passed ? '✅ PASSED' : '❌ FAILED'}`);
        if (!passed) {
          console.log('Expected:', {
            version: testCase.expectedVersion,
            parent: testCase.expectedParentId,
            status: testCase.expectedStatus
          });
          console.log('Actual:', {
            version: result.application?.versionNumber,
            parent: result.application?.parentApplicationId,
            status: result.status,
            success: result.success
          });
        }

      } catch (error) {
        console.log(`Result: ❌ FAILED - ${error.message || 'Unknown error'}`);
        this.testResults.push({
          case: testCase.name,
          passed: false,
          result: null,
          error: error.message || 'Unknown error'
        });
      }
    }

    this.printSummary();
  }

  createTestApplicationData(farmerId, documentType) {
    return {
      applicantId: `applicant_${farmerId}`,
      schemeId: 'scheme_001',
      type: documentType,
      fileName: `test_${documentType}_${Date.now()}.pdf`,
      fileUrl: `https://test.com/files/test_${documentType}_${Date.now()}.pdf`,
      fileSize: 1024000,
      fileType: 'application/pdf',
      personalInfo: {
        firstName: 'Test',
        lastName: 'Farmer',
        email: `${farmerId}@test.com`,
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
  }

  printSummary() {
    console.log('\n' + '='.repeat(80));
    console.log('TEST SUMMARY');
    console.log('='.repeat(80));
    
    const passed = this.testResults.filter(r => r.passed).length;
    const total = this.testResults.length;
    const failed = total - passed;
    
    console.log(`Total Tests: ${total}`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
    
    if (failed > 0) {
      console.log('\nFailed Tests:');
      this.testResults
        .filter(r => !r.passed)
        .forEach(r => {
          console.log(`  ❌ ${r.case}: ${r.error || 'Validation failed'}`);
        });
    }
    
    console.log('\n' + '='.repeat(80));
    
    if (passed === total) {
      console.log('🎉 ALL TESTS PASSED - Workflow implementation is complete!');
    } else {
      console.log('⚠️  Some tests failed - Review implementation');
    }
  }
}

// Run the validation tests
async function main() {
  const validator = new WorkflowValidator();
  await validator.runAllTests();
}

// Export for use in other modules
module.exports = { WorkflowValidator };

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}
