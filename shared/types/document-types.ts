/**
 * Document Types
 * Purpose: Type definitions for document processing and extraction
 */

// Document Types
export enum DocumentType {
  SCHEME_APPLICATION = 'scheme_application',
  SUBSIDY_CLAIM = 'subsidy_claim',
  INSURANCE_CLAIM = 'insurance_claim',
  GRIEVANCE_LETTER = 'grievance_letter',
  LAND_RECORD = 'land_record',
  BANK_PASSBOOK = 'bank_passbook',
  ID_PROOF = 'id_proof',
  FARMER_RECORD = 'farmer_record',
  UNKNOWN = 'unknown'
}

// Field Confidence Types
export enum FieldConfidence {
  VERY_LOW = 'very_low',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  VERY_HIGH = 'very_high'
}

// Extracted Field Types
export interface ExtractedField {
  name: string
  value: any
  confidence: FieldConfidence
  sourceText?: string
  extractionMethod: string
}

// Document Processing Types
export interface DocumentProcessingRequest {
  processingType: string
  options?: Record<string, any>
  extractMetadata?: boolean
}

export interface DocumentExtractionRequest {
  textContent: string
  documentType: DocumentType
  fileName?: string
  metadata?: Record<string, any>
}

export interface DocumentExtractionResponse {
  success: boolean
  result?: ExtractionResult
  error?: string
  processingTimeMs: number
}

export interface ExtractionResult {
  documentType: DocumentType
  extractedFields: Record<string, ExtractedField>
  missingFields: string[]
  confidence: number
  extractionStatus: string
  fieldConfidences: Record<string, number>
  processingTimeMs: number
  warnings: string[]
}

export interface DocumentClassificationRequest {
  textContent: string
  fileName?: string
  fileType?: string
  metadata?: Record<string, any>
}

export interface DocumentClassificationResponse {
  documentType: DocumentType
  confidence: number
  reasoning: ClassificationReasoning
  processingTimeMs?: number
  suggestions?: DocumentType[]
}

export interface ClassificationReasoning {
  keywordsFound: string[]
  structuralIndicators: string[]
  confidenceFactors: string[]
}

export interface FarmerDataExtraction {
  farmer_name?: string
  aadhaar_number?: string
  land_size?: string
  scheme_name?: string
  annual_income?: string
  location?: string
  confidence: number
  status: 'success' | 'partial' | 'failed'
  extractedAt: number
}

export interface DocumentProcessingResult {
  requestId: string
  success: boolean
  processingTimeMs: number
  processingType?: string
  filename?: string
  extractedData?: string
  structuredData?: FarmerDataExtraction | any
  metadata?: Record<string, any>
  confidenceScore?: number
  errorMessage?: string
}

// Document Validation Types
export interface DocumentValidationRequest {
  documentType: DocumentType
  extractedFields: Record<string, ExtractedField>
  validationRules?: string[]
}

export interface DocumentValidationResponse {
  isValid: boolean
  validationResult: ValidationResult
  confidence: number
  errors: ValidationError[]
  warnings: ValidationWarning[]
}

export interface ValidationResult {
  fieldValidations: Record<string, FieldValidation>
  overallScore: number
  missingRequiredFields: string[]
  dataQuality: DataQualityMetrics
}

export interface FieldValidation {
  isValid: boolean
  confidence: number
  errors: string[]
  warnings: string[]
  suggestions: string[]
}

export interface ValidationError {
  field: string
  type: 'format' | 'required' | 'consistency' | 'business_rule'
  message: string
  severity: 'error' | 'warning' | 'info'
}

export interface ValidationWarning {
  field: string
  type: 'format' | 'consistency' | 'quality'
  message: string
  recommendation: string
}

export interface DataQualityMetrics {
  completeness: number
  accuracy: number
  consistency: number
  timeliness: number
  overall: number
}

// Document Metadata Types
export interface DocumentMetadata {
  documentId: string
  documentType: DocumentType
  fileName: string
  fileSize: number
  uploadedAt: Date
  processedAt?: Date
  processingStatus: ProcessingStatus
  extractionConfidence?: number
  validationResults?: DocumentValidationResponse
}

export enum ProcessingStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  PROCESSED = 'processed',
  VALIDATED = 'validated',
  FAILED = 'failed',
  RETRY = 'retry'
}

// Document Analysis Types
export interface DocumentAnalysisRequest {
  documentId: string
  analysisTypes: AnalysisType[]
  options?: Record<string, any>
}

export enum AnalysisType {
  EXTRACTION = 'extraction',
  CLASSIFICATION = 'classification',
  VALIDATION = 'validation',
  QUALITY_CHECK = 'quality_check',
  FRAUD_DETECTION = 'fraud_detection'
}

export interface DocumentAnalysisResponse {
  documentId: string
  analysisResults: Record<AnalysisType, AnalysisResult>
  overallConfidence: number
  processingTimeMs: number
  recommendations: string[]
}

export interface AnalysisResult {
  success: boolean
  confidence: number
  data?: any
  errors: string[]
  warnings: string[]
  metadata?: Record<string, any>
}
