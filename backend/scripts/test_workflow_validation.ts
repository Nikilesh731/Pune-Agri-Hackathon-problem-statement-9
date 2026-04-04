/**
 * Workflow Validation Test Script
 * Tests the core workflow completion with versioning, duplicate blocking, timeline consistency, and status management
 */

import { applicationsService } from '../src/modules/applications/applications.service'
import { applicationsRepository } from '../src/modules/applications/applications.repository'
import { CreateApplicationInput } from '../src/modules/applications/applications.types'

interface TestCase {
  name: string
  description: string
  setup?: () => Promise<void>
  execute: () => Promise<any>
  validate: (result: any) => boolean
  expectedVersion?: number
  expectedParentId?: string | null
  expectedStatus?: string
}

class WorkflowValidator {
  private testResults: Array<{
    case: string
    passed: boolean
    result: any
    error?: string
  }> = []

  async runAllTests(): Promise<void> {
    console.log('='.repeat(80))
    console.log('WORKFLOW VALIDATION TEST SUITE')
    console.log('='.repeat(80))

    const testCases: TestCase[] = [
      // CASE 1: First upload
      {
        name: 'CASE_1_FIRST_UPLOAD',
        description: 'First upload should create version 1 with no parent',
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application')
          return await applicationsService.createApplication(testData)
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 1 && 
                 result.application?.parentApplicationId === null &&
                 result.status === 'created'
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
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application')
          return await applicationsService.createApplication(testData)
        },
        validate: (result) => {
          return !result.success && 
                 result.status === 'duplicate' &&
                 result.message?.includes('Duplicate submission')
        },
        expectedStatus: 'duplicate'
      },

      // CASE 3: After REJECTED → upload again - should create version 2
      {
        name: 'CASE_3_RESUBMISSION_AFTER_REJECTED',
        description: 'After REJECTED status, new upload should create version 2',
        setup: async () => {
          // First, find and reject the existing application
          const apps = await applicationsRepository.findApplicationsByFarmer('farmer_001')
          const schemeApp = apps.find(app => 
            app.extractedData?.canonical?.document_type === 'scheme_application' ||
            app.type === 'scheme_application'
          )
          if (schemeApp) {
            await applicationsService.rejectApplication(schemeApp.id)
          }
        },
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application')
          return await applicationsService.createApplication(testData)
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 2 && 
                 result.application?.parentApplicationId !== null &&
                 result.status === 'resubmission'
        },
        expectedVersion: 2,
        expectedStatus: 'resubmission'
      },

      // CASE 4: Multiple resubmissions
      {
        name: 'CASE_4_MULTIPLE_RESUBMISSIONS',
        description: 'Multiple resubmissions should increment version properly',
        setup: async () => {
          // Reject the version 2 application
          const apps = await applicationsRepository.findApplicationsByFarmer('farmer_001')
          const latestApp = apps.find(app => app.versionNumber === 2)
          if (latestApp) {
            await applicationsService.rejectApplication(latestApp.id)
          }
        },
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'scheme_application')
          return await applicationsService.createApplication(testData)
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 3 && 
                 result.application?.parentApplicationId !== null &&
                 result.status === 'resubmission'
        },
        expectedVersion: 3,
        expectedStatus: 'resubmission'
      },

      // CASE 5: Timeline coherence
      {
        name: 'CASE_5_TIMELINE_COHERENCE',
        description: 'Farmer timeline should show applications sorted by createdAt DESC',
        execute: async () => {
          const timeline = await applicationsService.getFarmerApplicationTimeline('farmer_001')
          return timeline
        },
        validate: (result) => {
          if (!result.applications || result.applications.length === 0) return false
          
          // Check that applications are sorted by createdAt DESC
          const sorted = [...result.applications].sort((a, b) => 
            new Date(b.history[0]?.createdAt).getTime() - new Date(a.history[0]?.createdAt).getTime()
          )
          
          return JSON.stringify(result.applications) === JSON.stringify(sorted)
        }
      },

      // CASE 6: Status transition validation
      {
        name: 'CASE_6_STATUS_TRANSITION_VALIDATION',
        description: 'Invalid status transitions should be rejected',
        execute: async () => {
          try {
            const apps = await applicationsRepository.findApplicationsByFarmer('farmer_001')
            const approvedApp = apps.find(app => app.status === 'APPROVED')
            if (approvedApp) {
              // Try to transition from APPROVED to PROCESSING (should fail)
              await applicationsService.updateApplication(approvedApp.id, { status: 'PROCESSING' })
              return { success: true, message: 'Transition allowed (unexpected)' }
            }
            return { success: false, message: 'No approved application found' }
          } catch (error) {
            return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
          }
        },
        validate: (result) => {
          return !result.success && result.error?.includes('Invalid status transition')
        }
      },

      // CASE 7: Different document type should not block
      {
        name: 'CASE_7_DIFFERENT_DOCUMENT_TYPE',
        description: 'Different document type for same farmer should not be blocked',
        execute: async () => {
          const testData = this.createTestApplicationData('farmer_001', 'grievance')
          return await applicationsService.createApplication(testData)
        },
        validate: (result) => {
          return result.success && 
                 result.application?.versionNumber === 1 && 
                 result.application?.parentApplicationId === null &&
                 result.status === 'created'
        },
        expectedVersion: 1,
        expectedParentId: null,
        expectedStatus: 'created'
      }
    ]

    for (const testCase of testCases) {
      console.log(`\n${testCase.name}: ${testCase.description}`)
      console.log('-'.repeat(60))
      
      try {
        // Setup if required
        if (testCase.setup) {
          await testCase.setup()
        }

        // Execute test
        const result = await testCase.execute()
        
        // Validate result
        const passed = testCase.validate(result)
        
        // Record result
        this.testResults.push({
          case: testCase.name,
          passed,
          result,
          error: passed ? undefined : 'Validation failed'
        })

        // Log result
        console.log(`Result: ${passed ? '✅ PASSED' : '❌ FAILED'}`)
        if (!passed) {
          console.log('Expected:', {
            version: testCase.expectedVersion,
            parent: testCase.expectedParentId,
            status: testCase.expectedStatus
          })
          console.log('Actual:', {
            version: result.application?.versionNumber,
            parent: result.application?.parentApplicationId,
            status: result.status,
            success: result.success
          })
        }

      } catch (error) {
        console.log(`Result: ❌ FAILED - ${error instanceof Error ? error.message : 'Unknown error'}`)
        this.testResults.push({
          case: testCase.name,
          passed: false,
          result: null,
          error: error instanceof Error ? error.message : 'Unknown error'
        })
      }
    }

    this.printSummary()
  }

  private createTestApplicationData(farmerId: string, documentType: string): CreateApplicationInput {
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
    }
  }

  private printSummary(): void {
    console.log('\n' + '='.repeat(80))
    console.log('TEST SUMMARY')
    console.log('='.repeat(80))
    
    const passed = this.testResults.filter(r => r.passed).length
    const total = this.testResults.length
    const failed = total - passed
    
    console.log(`Total Tests: ${total}`)
    console.log(`Passed: ${passed}`)
    console.log(`Failed: ${failed}`)
    console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`)
    
    if (failed > 0) {
      console.log('\nFailed Tests:')
      this.testResults
        .filter(r => !r.passed)
        .forEach(r => {
          console.log(`  ❌ ${r.case}: ${r.error || 'Validation failed'}`)
        })
    }
    
    console.log('\n' + '='.repeat(80))
    
    if (passed === total) {
      console.log('🎉 ALL TESTS PASSED - Workflow implementation is complete!')
    } else {
      console.log('⚠️  Some tests failed - Review implementation')
    }
  }
}

// Run the validation tests
async function main() {
  const validator = new WorkflowValidator()
  await validator.runAllTests()
}

// Check if this file is being run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error)
}

export { WorkflowValidator }
