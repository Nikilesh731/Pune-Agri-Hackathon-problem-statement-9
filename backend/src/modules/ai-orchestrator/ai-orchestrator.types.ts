/**
 * AI Orchestrator Types
 * Purpose: TypeScript interfaces and types for AI orchestration management
 */

export interface AIRequest {
  id: string
  serviceType: AIServiceType
  requestData: any
  userId?: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  metadata?: AIMetadata
  timestamp: Date
}

export interface AIResponse {
  success: boolean
  data?: any
  error?: string
  processingTime: number
  requestId: string
  confidence?: number
  metadata?: AIMetadata
  timestamp: Date
}

export type AIServiceType = 
  | 'ocr'
  | 'document-processing'
  | 'grievance-classification'
  | 'application-priority-scoring'
  | 'fraud-detection'
  | 'summarization'

export interface AIMetadata {
  model?: string
  version?: string
  parameters?: Record<string, any>
  cost?: number
  tokens?: number
  cacheHit?: boolean
}

export interface AIModel {
  id: string
  name: string
  serviceType: AIServiceType
  version: string
  description: string
  capabilities: string[]
  isActive: boolean
  performanceMetrics: ModelPerformance
  createdAt: Date
  updatedAt: Date
}

export interface ModelPerformance {
  accuracy?: number
  precision?: number
  recall?: number
  f1Score?: number
  averageResponseTime: number
  successRate: number
  lastUpdated: Date
}

export interface AIHealthStatus {
  serviceType: AIServiceType
  status: 'healthy' | 'degraded' | 'unhealthy'
  responseTime: number
  successRate: number
  lastCheck: Date
  activeModels: string[]
  issues?: string[]
}

export interface AIAnalytics {
  totalRequests: number
  successRequests: number
  failedRequests: number
  averageResponseTime: number
  totalCost: number
  requestsByService: Record<AIServiceType, number>
  requestsByModel: Record<string, number>
  errorRates: Record<AIServiceType, number>
  performanceTrends: PerformanceTrend[]
}

export interface PerformanceTrend {
  date: string
  serviceType: AIServiceType
  responseTime: number
  successRate: number
  requestCount: number
}

export interface AIConfig {
  serviceType: AIServiceType
  endpoint: string
  timeout: number
  retryAttempts: number
  apiKey?: string
  defaultModel?: string
  rateLimit?: {
    requestsPerMinute: number
    requestsPerHour: number
  }
  caching?: {
    enabled: boolean
    ttl: number
  }
}

export interface BatchAIRequest {
  requests: AIRequest[]
  batchId: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  callbackUrl?: string
}

export interface BatchAIResponse {
  batchId: string
  responses: AIResponse[]
  totalProcessingTime: number
  successCount: number
  failureCount: number
  timestamp: Date
}
