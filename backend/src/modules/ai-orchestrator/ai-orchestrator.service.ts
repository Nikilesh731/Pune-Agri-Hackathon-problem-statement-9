/**
 * AI Orchestrator Service
 * Purpose: Business logic for AI orchestration management
 */

import { aiOrchestratorRepository } from './ai-orchestrator.repository'
import { AIResponse } from './ai-orchestrator.types'

interface ProcessDocumentInput {
  fileUrl?: string
  fileName?: string
  fileType?: string
}

class AIOrchestratorService {
  async processDocument(input: ProcessDocumentInput): Promise<AIResponse> {
    const startTime = Date.now()
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const results: any = {}

    // AI ORCHESTRATOR SAFETY GUARD: Prevent calls with missing fileUrl
    // This is critical to prevent duplicate calls where first call succeeds with valid fileUrl
    // and second call fails with fileUrl = null, overwriting the success
    if (!input?.fileUrl || !String(input.fileUrl).trim()) {
      console.warn("[AI SKIP] Missing fileUrl in ai-orchestrator, returning early");
      console.warn("[AI SKIP] This prevents 'No OCR text available' errors from overwriting successful extraction");
      return {
        success: false,
        error: "Missing fileUrl for document processing",
        data: null,
        processingTime: 0,
        requestId,
        timestamp: new Date()
      };
    }

    try {
      console.log('[AI] document-processing started')

      const payload = {
        processing_type: 'full_process',
        options: {
          fileUrl: input.fileUrl,
          filename: input.fileName,
          fileType: input.fileType,
        },
      }

      console.log('[AI DEBUG] Payload:', payload)

      const documentProcessingResult = await aiOrchestratorRepository.callAIService(
        'document-processing',
        payload
      )

      console.log(
        '[AI DEBUG] document-processing response:',
        JSON.stringify(documentProcessingResult)
      )

      // IMPORTANT:
      // Repository returns { success, data, error } and does not throw for normal service failures.
      if (!documentProcessingResult?.success || !documentProcessingResult?.data) {
        console.error(
          '[AI] document-processing failed or returned empty data:',
          documentProcessingResult?.error || 'Unknown error'
        )

        return {
          success: false,
          error: documentProcessingResult?.error || 'Document processing failed',
          data: {
            aiProcessingStatus: 'failed',
            aiProcessedAt: new Date(),
          },
          processingTime: Date.now() - startTime,
          requestId,
          timestamp: new Date(),
        }
      }

      // Preserve authoritative extraction immediately
      results.extractedData = documentProcessingResult.data
      console.log('[AI] extraction SUCCESS')

      // Optional: Summarization
      try {
        const documentType =
          results.extractedData?.canonical?.document_type ||
          results.extractedData?.document_type ||
          'unknown'

        const intelligenceResult = await aiOrchestratorRepository.callAIService('summarization', {
          processing_type: 'full_process',
          options: {
            filename: input.fileName,
            extractedData: results.extractedData,
          },
        })

        if (intelligenceResult.success && intelligenceResult.data?.extractedData?.summary) {
          results.aiSummary = intelligenceResult.data.extractedData.summary
        } else if (intelligenceResult.success && intelligenceResult.data?.summary) {
          results.aiSummary = intelligenceResult.data.summary
        } else {
          results.aiSummary = `Document processed as ${documentType.replace('_', ' ')}. Review extracted fields for verification.`
        }
      } catch (intelligenceError) {
        console.warn(
          '[AI] summarization failed, continuing:',
          intelligenceError instanceof Error ? intelligenceError.message : intelligenceError
        )

        const documentType =
          results.extractedData?.canonical?.document_type ||
          results.extractedData?.document_type ||
          'unknown'

        results.aiSummary = `Document processed as ${documentType.replace('_', ' ')}. Review extracted fields for verification.`
      }

      // Optional: Priority scoring
      try {
        const hasMissingDocuments = (results.extractedData?.missing_fields?.length || 0) > 0
        const documentCompleteness = results.extractedData?.confidence || 0
        const applicationType =
          results.extractedData?.canonical?.document_type ||
          results.extractedData?.document_type ||
          'general'

        const priorityResult = await aiOrchestratorRepository.callAIService(
          'application-priority-scoring',
          {
            application_data: {
              applicationType,
              submissionDate: new Date().toISOString(),
              hasMissingDocuments,
              documentCompleteness,
              extractedData: results.extractedData,
            },
            scoring_criteria: ['urgency', 'impact', 'compliance', 'farmer_vulnerability'],
          }
        )

        if (priorityResult.success) {
          results.priorityScore = (priorityResult.data?.priority_score ?? 0.5) * 100
          // Determine queue based on priority score
          const priorityScore = (priorityResult.data?.priority_score ?? 0.5) * 100
          results.ml_insights = {
            queue: priorityScore > 80 ? 'HIGH_PRIORITY' : priorityScore > 60 ? 'NORMAL' : 'LOW',
            priority_score: priorityScore,
            risk_level: results.fraudRiskScore > 0.7 ? 'HIGH' : results.fraudRiskScore > 0.4 ? 'MEDIUM' : 'LOW'
          }
        } else {
          results.priorityScore = 50
          results.ml_insights = {
            queue: 'NORMAL',
            priority_score: 50,
            risk_level: 'MEDIUM'
          }
        }
      } catch (priorityError) {
        console.warn(
          '[AI] priority scoring failed, continuing:',
          priorityError instanceof Error ? priorityError.message : priorityError
        )
        results.priorityScore = 50
        results.ml_insights = {
          queue: 'NORMAL',
          priority_score: 50,
          risk_level: 'MEDIUM'
        }
      }

      // Optional: Fraud detection
      try {
        console.log('[AI] fraud detection started')

        const sd = results.extractedData?.structured_data || {}

        const fraudResult = await aiOrchestratorRepository.callAIService('fraud-detection', {
          farmer_name: sd.farmer_name,
          aadhaar_number: sd.aadhaar_number,
          land_size: sd.land_size,
          applicantInfo: {
            name: sd.farmer_name,
            aadhaarNumber: sd.aadhaar_number,
            location: sd.location,
          },
          applicationData: results.extractedData,
          documentMetadata: {
            fileName: input.fileName,
            fileType: input.fileType,
          },
          documents: [],
        })

        if (fraudResult.success) {
          results.fraudRiskScore = fraudResult.data?.fraud_score ?? 0.1
          results.fraudFlags = fraudResult.data?.indicators || []
        } else {
          console.warn('[AI] fraud detection failed, continuing:', fraudResult.error)
          results.fraudRiskScore = 0
          results.fraudFlags = []
        }
      } catch (fraudError) {
        console.warn(
          '[AI] fraud detection failed, continuing:',
          fraudError instanceof Error ? fraudError.message : fraudError
        )
        results.fraudRiskScore = 0
        results.fraudFlags = []
      }

      const hasMissingFields = (results.extractedData?.missing_fields?.length || 0) > 0
      const confidence = results.extractedData?.confidence || 0

      const verificationRecommendation = this.generateVerificationRecommendation({
        hasMissingFields,
        fraudRiskScore: results.fraudRiskScore || 0,
        priorityScore: results.priorityScore || 50,
        confidence,
      })

      results.verificationRecommendation = verificationRecommendation.recommendation
      results.aiProcessedAt = new Date()
      results.aiProcessingStatus = 'completed'

      console.log('[AI] returning preserved extraction result')

      return {
        success: true,
        data: results,
        processingTime: Date.now() - startTime,
        requestId,
        confidence:
          results.extractedData?.confidence ||
          results.extractedData?.decision_support?.confidence ||
          0,
        timestamp: new Date(),
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'AI processing failed',
        data: {
          aiProcessingStatus: 'failed',
          aiProcessedAt: new Date(),
        },
        processingTime: Date.now() - startTime,
        requestId,
        timestamp: new Date(),
      }
    }
  }

  private generateVerificationRecommendation(context: {
    hasMissingFields: boolean
    fraudRiskScore: number
    priorityScore: number
    confidence: number
  }): { recommendation: string } {
    const { hasMissingFields, fraudRiskScore, priorityScore, confidence } = context

    if (fraudRiskScore > 0.7) {
      return { recommendation: 'HIGH_RISK_MANUAL_REVIEW' }
    }

    if (hasMissingFields || confidence < 0.6) {
      return { recommendation: 'NEEDS_CLARIFICATION' }
    }

    if (fraudRiskScore > 0.4) {
      return { recommendation: 'MANUAL_VERIFICATION_REQUIRED' }
    }

    if (priorityScore > 80) {
      return { recommendation: 'EXPEDITED_REVIEW' }
    }

    return { recommendation: 'APPROVE_FOR_REVIEW' }
  }

  async classifyGrievance(text: string, includeSentiment?: boolean): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('grievance-classification', {
      text,
      includeSentiment,
    })
  }

  async scoreApplication(applicationData: any, scoringModel?: string): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('application-priority-scoring', {
      application_data: applicationData,
      scoring_criteria: ['urgency', 'impact', 'compliance', 'farmer_vulnerability'],
    })
  }

  async detectFraud(data: any, analysisType?: string): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('fraud-detection', {
      application_data: data,
      documents: [],
    })
  }

  async summarizeText(text: string, summaryType?: string, maxLength?: number): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('summarization', {
      text,
      summaryType,
      maxLength,
    })
  }

  async getAvailableModels(): Promise<any> {
    return await aiOrchestratorRepository.getAvailableModels()
  }

  async getAIHealth(): Promise<any> {
    return await aiOrchestratorRepository.getAIHealth()
  }

  async healthCheck(): Promise<{ message: string }> {
    return { message: 'AI orchestrator service working' }
  }
}

export const aiOrchestratorService = new AIOrchestratorService()