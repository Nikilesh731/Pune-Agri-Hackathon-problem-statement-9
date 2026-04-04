/**
 * Shared Types for Frontend Components
 * Purpose: Type definitions for application processing workflow
 */

// Export types that frontend components are expecting
export interface CaseAggregate {
  id: string
  applicationNumber: string
  status: string
  documentsReceived: Array<{
    id: string
    name: string
    type: string
    status: string
  }>
  missingDocuments: Array<{
    id: string
    name: string
    type: string
    required: boolean
  }>
  completionScore: number
  sources: string[]
}

export interface VerificationFlag {
  id: string
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  sources: string[]
}

export interface DocumentType {
  id: string
  name: string
  category: string
  required: boolean
}

export interface ExtractedField {
  id: string
  name: string
  value: any
  confidence: number
  source: string
}

export interface FieldConfidence {
  score: number
  level: 'low' | 'medium' | 'high'
  issues: string[]
}

export interface ApplicationStatus {
  id: string
  name: string
  category: string
  description: string
}

export interface WorkflowRecommendation {
  action: string
  priority: 'low' | 'medium' | 'high'
  reasoning: string
  nextSteps: string[]
}
