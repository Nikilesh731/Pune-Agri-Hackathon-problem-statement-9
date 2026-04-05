/**
 * AI Orchestrator Service
 * Purpose: Business logic for AI orchestration management
 */

import { aiOrchestratorRepository } from './ai-orchestrator.repository'
import { AIResponse } from './ai-orchestrator.types'
import { CanonicalAgricultureData } from '../applications/applications.types'
import { supabase } from '../../config/supabase'
const { PDFParse } = require('pdf-parse')
import Tesseract from 'tesseract.js'

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

      const documentProcessingResult =
        await aiOrchestratorRepository.callAIService(
          'document-processing',
          payload
        )

      console.log(
        '[AI DEBUG] document-processing response:',
        JSON.stringify(documentProcessingResult)
      )

      // ✅ CRITICAL FIX: handle response properly
      if (!documentProcessingResult?.success || !documentProcessingResult?.data) {
        console.error('[AI] document-processing failed')

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

      // ✅ ALWAYS preserve AI output
      results.extractedData = documentProcessingResult.data

      console.log('[AI] extraction SUCCESS')

      // ===============================
      // OPTIONAL: Summarization
      // ===============================
      try {
        const intelligenceResult =
          await aiOrchestratorRepository.callAIService('summarization', {
            processing_type: 'full_process',
            options: {
              filename: input.fileName,
              extractedData: results.extractedData,
            },
          })

        if (intelligenceResult.success) {
          results.aiSummary =
            intelligenceResult.data?.summary ||
            intelligenceResult.data?.extractedData?.summary ||
            ''
        }
      } catch (e) {
        console.warn('[AI] summarization failed (ignored)')
      }

      // ===============================
      // OPTIONAL: Priority
      // ===============================
      try {
        const priorityResult =
          await aiOrchestratorRepository.callAIService(
            'application-priority-scoring',
            {
              application_data: {
                extractedData: results.extractedData,
              },
              scoring_criteria: ['urgency', 'impact'],
            }
          )

        if (priorityResult.success) {
          results.priorityScore =
            (priorityResult.data?.priority_score ?? 0.5) * 100
        } else {
          results.priorityScore = 50
        }
      } catch {
        results.priorityScore = 50
      }

      // ===============================
      // OPTIONAL: Fraud
      // ===============================
      try {
        const sd = results.extractedData?.structured_data || {}

        const fraudResult =
          await aiOrchestratorRepository.callAIService('fraud-detection', {
            farmer_name: sd.farmer_name,
            aadhaar_number: sd.aadhaar_number,
            extractedData: results.extractedData,
          })

        if (fraudResult.success) {
          results.fraudRiskScore = fraudResult.data?.fraud_score ?? 0
          results.fraudFlags = fraudResult.data?.indicators || []
        } else {
          results.fraudRiskScore = 0
          results.fraudFlags = []
        }
      } catch {
        results.fraudRiskScore = 0
        results.fraudFlags = []
      }

      // ===============================
      // FINAL RESPONSE
      // ===============================
      results.aiProcessingStatus = 'completed'
      results.aiProcessedAt = new Date()

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
}

export const aiOrchestratorService = new AIOrchestratorService()