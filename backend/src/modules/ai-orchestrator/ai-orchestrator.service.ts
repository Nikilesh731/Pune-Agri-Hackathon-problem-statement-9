/**
 * AI Orchestrator Service
 * Purpose: Business logic for AI orchestration management
 */
import { aiOrchestratorRepository } from './ai-orchestrator.repository'
import { AIResponse, AIServiceType } from './ai-orchestrator.types'
import { CanonicalAgricultureData } from '../applications/applications.types'
import * as fs from 'fs'
import * as path from 'path'
import { supabase } from '../../config/supabase'
const { PDFParse } = require('pdf-parse')
import Tesseract from 'tesseract.js'

interface ProcessDocumentInput {
  fileUrl?: string
  fileName?: string
  fileType?: string
}

interface AIProcessingResult {
  success: boolean
  data?: {
    applicantName?: string
    applicationType?: string
    village?: string
    submittedDocuments?: string[]
    missingFields?: string[]
    confidence?: number
    summary?: string
    priorityScore?: number
    fraudRiskScore?: number
    fraudFlags?: string[]
    verificationRecommendation?: string
  }
  error?: string
  confidence?: number
}

class AIOrchestratorService {
  
  /**
   * Validate if extracted data contains meaningful information
   */
  private hasValidExtractedData(extractedData: any): boolean {
    if (!extractedData || typeof extractedData !== 'object') {
      return false;
    }
    
    // Check document_type exists and is not unknown
    const docType = extractedData.document_type;
    if (docType && docType !== 'unknown' && docType.trim() !== '') {
      return true;
    }
    
    // Check structured_data has at least 1 key
    const structuredData = extractedData.structured_data;
    if (structuredData && typeof structuredData === 'object' && Object.keys(structuredData).length > 0) {
      return true;
    }
    
    // Check extracted_fields has at least 1 key
    const extractedFields = extractedData.extracted_fields;
    if (extractedFields && typeof extractedFields === 'object' && Object.keys(extractedFields).length > 0) {
      return true;
    }
    
    // Check canonical exists and has meaningful nested data
    const canonical = extractedData.canonical;
    if (canonical && typeof canonical === 'object') {
      // Check if canonical has any meaningful nested properties
      const meaningfulKeys = ['applicant', 'agriculture', 'request', 'document_meta'];
      for (const key of meaningfulKeys) {
        if (canonical[key] && typeof canonical[key] === 'object' && Object.keys(canonical[key]).length > 0) {
          return true;
        }
      }
    }
    
    return false;
  }

  /**
   * Normalize AI service output to canonical agriculture schema
   */
  private normalizeToCanonicalSchema(aiServiceOutput: any, fileName?: string): CanonicalAgricultureData {
    // USE THE FROZEN AI RESPONSE CONTRACT
    const payload = aiServiceOutput?.data || aiServiceOutput || {};
    
    // Extract from the FROZEN CONTRACT structure only
    const structured_data = payload?.structured_data || {};
    const extracted_fields = payload?.extracted_fields || {};
    const missing_fields = payload?.missing_fields || [];
    const confidence = payload?.confidence || payload?.decision_support?.confidence || 0;
    const reasoning = payload?.reasoning || [];
    const classification_confidence = payload?.classification_confidence || 0;
    const classification_reasoning = payload?.classification_reasoning || {};
    const risk_flags = payload?.risk_flags || [];
    const decision_support = payload?.decision_support || {};
    
    // Helper function to safely extract string values
    const safeString = (value: any): string => value ? String(value).trim() : ''
    
    // Helper function to safely extract array values
    const safeArray = (value: any): string[] => {
      if (Array.isArray(value)) return value.map(v => String(v)).filter(v => v.trim())
      if (value && typeof value === 'string') return [value.trim()].filter(v => v)
      return []
    }
    
    // Extract classification information from FROZEN CONTRACT
    const documentType = safeString(payload?.document_type || structured_data?.document_type);
    const classificationConfidence = typeof classification_confidence === 'number' ? classification_confidence : 0.0;
    const classificationReasoning = classification_reasoning || {};
    
    // Parse location from STRUCTURED_DATA
    const location = safeString(structured_data?.location)
    let village = safeString(structured_data?.village)
    let district = safeString(structured_data?.district)
    
    // If we have a combined location but no individual village/district, split it
    if (location && !village && !district) {
      const locationParts = location.split(',').map(part => part.trim())
      if (locationParts.length >= 2) {
        village = locationParts[0]
        district = locationParts[1]
      }
    }
    
    // Extract request information based on document type
    let requestType = 'subsidy_application'; // Default
    if (documentType === 'insurance_claim') {
      requestType = 'claim_request';
    } else if (documentType === 'grievance') {
      requestType = 'grievance_filing';
    } else if (structured_data?.document_type === 'insurance_claim') {
      requestType = 'claim_request';
    }

    return {
      document_category: documentType === 'grievance' ? 'grievance' : 'application',
      document_type: documentType,
      applicant: {
        name: safeString(structured_data?.farmer_name),
        guardian_name: '', // Not currently extracted
        aadhaar_number: safeString(structured_data?.aadhaar_number),
        mobile_number: safeString(structured_data?.phone_number),
        address: safeString(structured_data?.address),
        village: village,
        district: district,
        state: '' // Not currently extracted
      },
      agriculture: {
        land_size: safeString(structured_data?.land_size),
        land_unit: 'acres', // Default unit, could be enhanced in future
        survey_number: '', // Not currently extracted
        crop_name: '', // Not currently extracted
        season: '', // Not currently extracted
        location: safeString(location)
      },
      request: {
        scheme_name: safeString(structured_data?.scheme_name),
        request_type: requestType,
        requested_amount: safeString(structured_data?.requested_amount),
        issue_summary: '', // Not currently extracted
        claim_reason: '' // Not currently extracted
      },
      document_meta: {
        document_date: '', // Not currently extracted
        reference_number: '', // Not currently extracted
        supporting_doc_type: documentType,
        source_file_name: safeString(fileName)
      },
      verification: {
        missing_fields: safeArray(missing_fields),
        field_confidences: extracted_fields,
        extraction_confidence: confidence,
        validation_errors: safeArray(decision_support?.validation_errors || []),
        recommendation: safeString(decision_support?.recommendation),
        reasoning: safeArray(reasoning),
        classification_confidence: classificationConfidence,
        classification_reasoning: safeArray(classificationReasoning?.keywords_found || [])
      }
    }
  }

  async extractTextFile(objectPath: string): Promise<string> {
    try {
      // DOWNLOAD FILE FROM SUPABASE
      const bucket = 'documents'
      
      const { data, error } = await supabase.storage.from(bucket).download(objectPath)
      
      if (error || !data) {
        console.error('SUPABASE DOWNLOAD FAILED:', error)
        return ""
      }
      
      // CONVERT DOWNLOADED FILE TO BUFFER
      const arrayBuffer = await data.arrayBuffer()
      const buffer = Buffer.from(arrayBuffer)
      
      if (buffer.length === 0) {
        console.error("DOWNLOADED FILE IS EMPTY")
        return ""
      }
      
      // CONVERT BUFFER TO TEXT
      const text = buffer.toString('utf-8')
      console.log("Text file extracted successfully, length:", text.length)
      
      return text
    } catch (error) {
      console.error("Text file extraction failed:", error)
      return ""
    }
  }

  async extractPdfText(objectPath: string): Promise<string> {
    try {
      // DOWNLOAD FILE FROM SUPABASE
      const bucket = 'documents'
      
      const { data, error } = await supabase.storage.from(bucket).download(objectPath)
      
      if (error || !data) {
        console.error('SUPABASE DOWNLOAD FAILED:', error)
        return ""
      }
      
      // CONVERT DOWNLOADED FILE TO BUFFER
      const arrayBuffer = await data.arrayBuffer()
      const buffer = Buffer.from(arrayBuffer)
      
      if (buffer.length === 0) {
        console.error("DOWNLOADED FILE IS EMPTY")
        return ""
      }
      
      // ADD SAFE CLEANUP WITH TRY/FINALLY
      let parser
      try {
        parser = new PDFParse({ data: buffer })
        const result = await parser.getText()
        const extractedText = result?.text || ''
        
        console.log("PDF text extracted successfully, length:", extractedText.length)
        
        // If PDF text extraction fails or returns very little text, try OCR fallback
        if (!extractedText || extractedText.trim().length < 10) {
          console.warn("PDF text extraction failed or returned minimal text - attempting OCR fallback")
          return ""
        }
        
        return extractedText
      } finally {
        if (parser) await parser.destroy()
      }
    } catch (error) {
      console.error("PDF text extraction failed:", error)
      return ""
    }
  }

  private async extractImageText(fileBuffer: Buffer): Promise<string> {
    try {
      const result = await Tesseract.recognize(fileBuffer, 'eng')
      const extractedText = result.data.text || ''
      
      console.log("Image OCR completed, text length:", extractedText.length)
      
      return extractedText
    } catch (error) {
      console.error("Image OCR extraction failed:", error)
      return ""
    }
  }

  async processDocument(input: ProcessDocumentInput): Promise<AIResponse> {
    const startTime = Date.now()
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const results: any = {}
    let hasValidExtraction = false;
    
    try {
      // STEP 1: AUTHORITATIVE DOCUMENT PROCESSING
      console.log('[AI] document-processing started');
      
      let documentProcessingResult: any;
      try {
        // Use correct payload format for metadata processing
        const payload = {
          processing_type: "full_process",
          options: {
            fileUrl: input.fileUrl,
            filename: input.fileName,
            fileType: input.fileType
          }
        };
        
        console.log('[AI] Payload:', payload);
        
        documentProcessingResult = await aiOrchestratorRepository.callAIService('document-processing', payload)
        
      } catch (aiServiceError) {
        console.error('[AI] document-processing failed:', aiServiceError instanceof Error ? aiServiceError.message : aiServiceError);
        
        // Document processing itself failed - return failure immediately
        return {
          success: false,
          error: aiServiceError instanceof Error ? aiServiceError.message : 'Document processing failed',
          data: {
            aiProcessingStatus: 'failed',
            aiProcessedAt: new Date()
          },
          processingTime: Date.now() - startTime,
          requestId,
          timestamp: new Date()
        };
      }
      
      // STEP 2: BUILD AND PRESERVE EXTRACTED DATA IMMEDIATELY AFTER DOCUMENT-PROCESSING
      if (documentProcessingResult.success && documentProcessingResult.data) {
        console.log('[AI] document-processing success');
        
        try {
          // USE THE FROZEN AI RESPONSE CONTRACT
          const payload = documentProcessingResult.data || {};
          
          // Extract from FROZEN CONTRACT structure only
          const structured_data = payload?.structured_data || {};
          const extracted_fields = payload?.extracted_fields || {};
          const missing_fields = payload?.missing_fields || [];
          const confidence = payload?.confidence || payload?.decision_support?.confidence || 0;
          const reasoning = payload?.reasoning || [];
          const classification_confidence = payload?.classification_confidence || 0;
          const classification_reasoning = payload?.classification_reasoning || {};
          const risk_flags = payload?.risk_flags || [];
          const decision_support = payload?.decision_support || {};
          
          // CLEAN NULL VALUES FROM STRUCTURED_DATA
          const cleanedStructuredData = JSON.parse(JSON.stringify(structured_data, (key, value) => {
            if (value === null || value === undefined) return '';
            return value;
          }));
          
          // Normalize to canonical schema using frozen contract
          const canonicalData = this.normalizeToCanonicalSchema(documentProcessingResult.data, input.fileName);
          
          // BUILD FINAL EXTRACTED DATA FROM FROZEN CONTRACT - AUTHORITATIVE
          results.extractedData = {
            // Frozen contract fields - authoritative structure
            document_type: payload?.document_type || structured_data?.document_type,
            structured_data: structured_data,
            extracted_fields: extracted_fields,
            missing_fields: missing_fields,
            confidence: confidence,
            reasoning: reasoning,
            classification_confidence: classification_confidence,
            classification_reasoning: classification_reasoning,
            risk_flags: risk_flags,
            decision_support: decision_support,
            canonical: canonicalData,
            
            // Minimal compatibility fields derived from structured_data only
            farmer_name: cleanedStructuredData.farmer_name,
            aadhaar_number: cleanedStructuredData.aadhaar_number,
            land_size: cleanedStructuredData.land_size,
            scheme_name: cleanedStructuredData.scheme_name,
            location: cleanedStructuredData.location,
            requested_amount: cleanedStructuredData.requested_amount,
            missingFields: missing_fields, // Map frozen contract to legacy name
            extractionConfidence: payload?.confidence || payload?.decision_support?.confidence || 0 // Map frozen contract to legacy name with fallback
          };
          
          // VALIDITY CHECK: Is this a real extraction result?
          hasValidExtraction = this.hasValidExtractedData(results.extractedData);
          
          if (hasValidExtraction) {
            console.log('[AI] extractedData valid - preservation successful');
          } else {
            console.log('[AI] extractedData invalid - using fallback');
            results.extractedData = {
              document_type: 'unknown',
              structured_data: {},
              extracted_fields: {},
              missing_fields: ['Document processing returned invalid data'],
              confidence: 0,
              reasoning: ['Document processing returned invalid data'],
              classification_confidence: 0,
              classification_reasoning: {},
              risk_flags: [],
              decision_support: {},
              canonical: null
            };
          }
          
        } catch (extractionError) {
          console.error('[AI] data extraction failed:', extractionError instanceof Error ? extractionError.message : extractionError);
          hasValidExtraction = false;
          results.extractedData = {
            document_type: 'unknown',
            structured_data: {},
            extracted_fields: {},
            missing_fields: ['Data extraction failed'],
            confidence: 0,
            reasoning: ['Data extraction failed'],
            classification_confidence: 0,
            classification_reasoning: {},
            risk_flags: [],
            decision_support: {},
            canonical: null
          };
        }
      } else {
        console.log('[AI] document-processing returned no data or failed');
        hasValidExtraction = false;
        results.extractedData = {
          document_type: 'unknown',
          structured_data: {},
          extracted_fields: {},
          missing_fields: ['Document processing failed'],
          confidence: 0,
          reasoning: ['Document processing failed'],
          classification_confidence: 0,
          classification_reasoning: {},
          risk_flags: [],
          decision_support: {},
          canonical: null
        };
      }
      
      // STEP 3: OPTIONAL DOWNSTREAM SERVICES - ISOLATED FAILURES
      
      // Step 3.1: Enhanced Intelligence Summary - ISOLATED
      try {
        const documentType = results.extractedData?.canonical?.document_type || results.extractedData?.document_type || 'unknown';
        
        // Use document processing service with intelligence service for enhanced summary
        const intelligenceResult = await aiOrchestratorRepository.callAIService('summarization', {
          processing_type: 'full_process',
          options: {
            filename: input.fileName,
            extractedData: results.extractedData  // Pass extracted data for context
          }
        })
        
        if (intelligenceResult.success && intelligenceResult.data?.extractedData?.summary) {
          results.aiSummary = intelligenceResult.data.extractedData.summary
        } else if (intelligenceResult.success && intelligenceResult.data?.summary) {
          results.aiSummary = intelligenceResult.data.summary
        }
        
      } catch (intelligenceError) {
        console.warn('[AI] summarization failed, continuing:', intelligenceError instanceof Error ? intelligenceError.message : intelligenceError);
        // Use safe fallback summary format
        const documentType = results.extractedData?.canonical?.document_type || results.extractedData?.document_type || 'unknown';
        results.aiSummary = `Document processed as ${documentType.replace('_', ' ')}. Review extracted fields for verification.`;
      }
      
      // Step 3.2: Priority Scoring - ISOLATED
      try {
        const hasMissingDocuments = (results.extractedData?.missing_fields?.length || 0) > 0;
        const documentCompleteness = results.extractedData?.confidence || 0;
        const applicationType = 
          results.extractedData?.canonical?.document_type ||
          results.extractedData?.document_type || 
          'general';
        
        const priorityResult = await aiOrchestratorRepository.callAIService('application-priority-scoring', {
          application_data: {
            applicationType: applicationType,
            submissionDate: new Date().toISOString(),
            hasMissingDocuments: hasMissingDocuments,
            documentCompleteness: documentCompleteness,
            extractedData: results.extractedData
          },
          scoring_criteria: ['urgency', 'impact', 'compliance', 'farmer_vulnerability']
        })
        
        if (priorityResult.success) {
          results.priorityScore = ((priorityResult.data?.priority_score ?? 0.5) * 100)
        }
        
      } catch (priorityError) {
        console.warn('[AI] priority scoring failed, continuing:', priorityError instanceof Error ? priorityError.message : priorityError);
        results.priorityScore = 50; // Safe default
      }
      
      // Step 3.3: Fraud Detection - ISOLATED
      console.log('[AI] fraud detection started');
      try {
        const sd = results.extractedData?.structured_data || {};
        
        const fraudResult = await aiOrchestratorRepository.callAIService('fraud-detection', {
          farmer_name: sd.farmer_name,
          aadhaar_number: sd.aadhaar_number,
          land_size: sd.land_size,
          applicantInfo: {
            name: sd.farmer_name,
            aadhaarNumber: sd.aadhaar_number,
            location: sd.location
          },
          applicationData: results.extractedData,
          documentMetadata: {
            fileName: input.fileName,
            fileType: input.fileType
          },
          documents: []
        })
        
        if (fraudResult.success) {
          results.fraudRiskScore = fraudResult.data?.fraud_score ?? 0.1
          results.fraudFlags = fraudResult.data?.indicators || []
        }
        
      } catch (fraudError) {
        console.log('[AI] fraud detection failed, continuing');
        results.fraudRiskScore = 0; // Safe default
        results.fraudFlags = []; // Safe default
      }
      
      // STEP 4: FINAL VERIFICATION AND RESPONSE
      const hasMissingFields = (results.extractedData?.missing_fields?.length || 0) > 0;
      const confidence = results.extractedData?.confidence || 0;
      
      const verificationRecommendation = this.generateVerificationRecommendation({
        hasMissingFields: hasMissingFields,
        fraudRiskScore: results.fraudRiskScore || 0,
        priorityScore: results.priorityScore || 50,
        confidence: confidence
      })
      
      results.verificationRecommendation = verificationRecommendation.recommendation
      results.aiProcessedAt = new Date()
      results.aiProcessingStatus = 'completed'
      
      // FINAL SUCCESS RULE: Return success only when document-processing succeeded and extractedData is valid
      const overallSuccess = hasValidExtraction;
      
      if (overallSuccess) {
        console.log('[AI] returning preserved extraction result');
      }
      
      return {
        success: overallSuccess,
        data: results,
        processingTime: Date.now() - startTime,
        requestId,
        confidence: results.extractedData?.confidence || results.extractedData?.decision_support?.confidence || 0,
        timestamp: new Date()
      }
      
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'AI processing failed',
        data: {
          aiProcessingStatus: 'failed',
          aiProcessedAt: new Date()
        },
        processingTime: Date.now() - startTime,
        requestId,
        timestamp: new Date()
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
      includeSentiment 
    })
  }

  async scoreApplication(applicationData: any, scoringModel?: string): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('application-priority-scoring', { 
      application_data: applicationData,
      scoring_criteria: ['urgency', 'impact', 'compliance', 'farmer_vulnerability']
    })
  }

  async detectFraud(data: any, analysisType?: string): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('fraud-detection', { 
      application_data: data,
      documents: []
    })
  }

  async summarizeText(text: string, summaryType?: string, maxLength?: number): Promise<AIResponse> {
    return await aiOrchestratorRepository.callAIService('summarization', { 
      text, 
      summaryType, 
      maxLength 
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
