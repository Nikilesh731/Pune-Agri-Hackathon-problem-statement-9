/**
 * AI Orchestrator Repository
 * Purpose: Database interaction layer for AI orchestration management
 */
import { AIRequest, AIResponse, AIServiceType } from './ai-orchestrator.types'

class AIOrchestratorRepository {
  async callAIService(serviceType: AIServiceType, requestData: any, endpointPath?: string): Promise<AIResponse> {
    const startTime = Date.now()
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    try {
      // Get AI service endpoint from config (for now, use placeholder)
      const endpoint = this.getServiceEndpoint(serviceType, endpointPath)
      
      // Debug logging before request
      console.log(`[AI REPOSITORY] Calling ${serviceType} at ${endpoint}`)
      console.log(`[AI REPOSITORY] Request payload:`, JSON.stringify(requestData, null, 2))
      console.log(`[AI REPOSITORY] Endpoint path: ${endpointPath || 'default'}`)
      
      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error('AI service timeout')), 25000) // 25 second timeout
      )
      
      // Make HTTP call to AI service
      const fetchPromise = fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })
      
      console.log(`[AI REPOSITORY] Making HTTP request to: ${endpoint}`)
      
      const response = await Promise.race([fetchPromise, timeoutPromise])
      
      console.log(`[AI REPOSITORY] Response status: ${response.status} ${response.statusText}`)
      console.log(`[AI REPOSITORY] Response headers:`, Object.fromEntries(response.headers.entries()))
      
      if (!response.ok) {
        const errorBody = await response.text()
        console.error(`[AI REPOSITORY] ${serviceType} failed with status ${response.status}`)
        console.error(`[AI REPOSITORY] Error response body:`, errorBody)
        console.error(`[AI REPOSITORY] Full error details:`, {
          status: response.status,
          statusText: response.statusText,
          url: endpoint,
          body: errorBody
        })
        throw new Error(`AI service responded with status: ${response.status} - ${errorBody}`)
      }
      
      const responseData = await response.json() as any
      const processingTime = Date.now() - startTime
      
      console.log(`[AI REPOSITORY] ${serviceType} succeeded in ${processingTime}ms`)
      console.log(`[AI REPOSITORY] Response:`, JSON.stringify(responseData, null, 2))
      
      return {
        success: true,
        data: responseData?.data || responseData,// AI service returns data directly, not nested
        processingTime,
        requestId,
        confidence: responseData.confidence,
        timestamp: new Date()
      }
      
    } catch (error) {
      const processingTime = Date.now() - startTime
      
      console.error(`[AI REPOSITORY] ${serviceType} failed after ${processingTime}ms:`)
      console.error(`[AI REPOSITORY] ERROR TYPE:`, typeof error)
      console.error(`[AI REPOSITORY] ERROR MESSAGE:`, error instanceof Error ? error.message : error)
      console.error(`[AI REPOSITORY] ERROR STACK:`, error instanceof Error ? error.stack : 'No stack available')
      console.error(`[AI REPOSITORY] RAW ERROR OBJECT:`, error)
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        processingTime,
        requestId,
        timestamp: new Date(),
        data: null
      }
    }
  }

  private getServiceEndpoint(serviceType: string, endpointPath?: string): string {
    const baseUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000'
    
    console.log(`[AI REPOSITORY] Calling AI service at: ${baseUrl}`)
    
    const endpoints: Record<string, string> = {
      'ocr': `${baseUrl}/api/ocr/extract`,
      'classification': `${baseUrl}/api/classification/classify`,
      'extraction': `${baseUrl}/api/extraction/extract`,
      'grievance-classification': `${baseUrl}/api/grievance-classification/classify`,
      'application-priority-scoring': `${baseUrl}/api/application-priority-scoring/score`,
      'fraud-detection': `${baseUrl}/api/fraud-detection/detect`,
      'document-processing': `${baseUrl}/api/document-processing/process-from-metadata`,
      'summarization': `${baseUrl}/api/document-processing/process-from-metadata`  // Use document processing for enhanced intelligence
    }
    
    return endpoints[serviceType] || `${baseUrl}/api/default/process`
  }

  async getAvailableModels(): Promise<any> {
    return {
      'ocr': ['tesseract', 'easyocr'],
      'document-processing': ['layoutlm', 'donut'],
      'grievance-classification': ['bert', 'roberta'],
      'application-priority-scoring': ['xgboost', 'random_forest'],
      'fraud-detection': ['isolation_forest', 'neural_network']
    }
  }

  async getAIHealth(): Promise<any> {
    return {
      'ocr': { status: 'healthy', responseTime: 150 },
      'document-processing': { status: 'healthy', responseTime: 200 },
      'grievance-classification': { status: 'healthy', responseTime: 100 },
      'application-priority-scoring': { status: 'healthy', responseTime: 250 },
      'fraud-detection': { status: 'healthy', responseTime: 300 }
    }
  }

  async healthCheck(): Promise<{ message: string }> {
    return { message: 'AI orchestrator repository working' }
  }
}

export const aiOrchestratorRepository = new AIOrchestratorRepository()
