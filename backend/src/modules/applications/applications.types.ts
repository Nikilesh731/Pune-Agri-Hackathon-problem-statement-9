/**
 * Applications Types
 * Purpose: TypeScript interfaces and types for application management
 */

export interface Application {
  id: string
  applicantId: string
  schemeId: string
  type: string
  status: 'UPLOADED' | 'PROCESSING' | 'PROCESSED' | 'NEEDS_REVIEW' | 'PENDING' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'REQUIRES_ACTION'
  priorityScore?: number
  fileName?: string
  fileUrl?: string
  fileSize?: number
  fileType?: string
  documents: ApplicationDocument[]
  personalInfo: PersonalInfo
  farmInfo?: FarmInfo
  extractedData?: ExtractedData
  aiSummary?: string
  fraudRiskScore?: number
  fraudFlags?: string[]
  verificationRecommendation?: string
  aiProcessingStatus?: string
  ocrProcessedAt?: Date
  aiProcessedAt?: Date
  rawExtractedText?: string
  normalizedContentHash?: string
  documentMetadata?: any
  farmerId?: string | null
  caseId?: string | null
  versionNumber: number
  parentApplicationId?: string | null
  isReupload?: boolean
  farmer?: {
    id: string
    name?: string | null
    aadhaarNumber?: string | null
    mobileNumber?: string | null
    village?: string | null
    district?: string | null
  } | null
  case?: {
    id: string
    caseType: string
    status: string
  } | null
  submissionDate: Date
  reviewDate?: Date
  decisionDate?: Date
  reviewerId?: string
  notes?: string
  createdAt: Date
  updatedAt: Date
}

export interface CreateApplicationInput {
  applicantId: string
  schemeId: string
  type: string
  fileName?: string
  fileUrl?: string
  fileSize?: number
  fileType?: string
  documents?: Omit<ApplicationDocument, 'id'>[]
  personalInfo?: PersonalInfo
  farmInfo?: FarmInfo
  aiProcessingStatus?: string
  farmerId?: string | null
  parentApplicationId?: string | null
  versionNumber?: number
  notes?: string
  fileHash?: string // File hash for strict duplicate detection
}

export interface UpdateApplicationInput {
  status?: string
  priorityScore?: number
  reviewerId?: string
  notes?: string
  reviewDate?: Date
  decisionDate?: Date
  documents?: ApplicationDocument[]
  farmInfo?: FarmInfo
  extractedData?: ExtractedData
  aiSummary?: string
  fraudRiskScore?: number
  fraudFlags?: string[]
  verificationRecommendation?: string
  aiProcessingStatus?: string
  ocrProcessedAt?: Date
  aiProcessedAt?: Date
  rawExtractedText?: string
  documentMetadata?: any
  farmerId?: string | null
  caseId?: string | null
  versionNumber?: number
  parentApplicationId?: string | null
}

export interface ApplicationDocument {
  id: string
  type: string
  name: string
  url: string
  uploadDate: Date
  verificationStatus: 'pending' | 'verified' | 'rejected'
  version: number
}

export interface PersonalInfo {
  firstName: string
  lastName: string
  email: string
  phone: string
  aadhaarNumber?: string
  dateOfBirth: Date
  address: Address
}

export interface FarmInfo {
  landArea: number
  location: Address
  cropTypes: string[]
  irrigationSource: string
  soilType?: string
  ownershipType: 'owned' | 'leased' | 'shared'
}

export interface Address {
  street: string
  city: string
  district: string
  state: string
  pincode: string
  coordinates?: {
    latitude: number
    longitude: number
  }
}

// Canonical Agriculture Administration Schema
export interface CanonicalAgricultureData {
  document_type: string
  document_category: string
  applicant: {
    name: string
    guardian_name: string
    aadhaar_number: string
    mobile_number: string
    address: string
    village: string
    district: string
    state: string
  }
  agriculture: {
    land_size: string
    land_unit: string
    survey_number: string
    crop_name: string
    season: string
    location: string
  }
  request: {
    scheme_name: string
    request_type: string
    requested_amount: string
    issue_summary: string
    claim_reason: string
  }
  document_meta: {
    document_date: string
    reference_number: string
    supporting_doc_type: string
    source_file_name: string
  }
  verification: {
    missing_fields: string[]
    field_confidences: Record<string, number>
    extraction_confidence: number
    validation_errors: string[]
    recommendation: string
    reasoning: string[]
    classification_confidence?: number
    classification_reasoning?: string[]
  }
}

export interface ExtractedData {
  // FROZEN CONTRACT - Authoritative structure from AI service
  document_type?: string
  structured_data?: Record<string, any>
  extracted_fields?: Record<string, any>
  missing_fields?: string[]
  confidence?: number
  reasoning?: string[]
  classification_confidence?: number
  classification_reasoning?: any
  risk_flags?: any[]
  decision_support?: any
  canonical?: CanonicalAgricultureData
  
  // Minimal temporary compatibility only - derived from frozen contract
  farmer_name?: string
  aadhaar_number?: string
  land_size?: string
  scheme_name?: string
  location?: string
  requested_amount?: string
  missingFields?: string[] // Legacy name for missing_fields
  
  [key: string]: any // Allow additional dynamic fields
}

export interface ApplicationFilters {
  status?: string
  applicantId?: string
  schemeId?: string
  priorityMin?: number
  priorityMax?: number
  submissionDateFrom?: Date
  submissionDateTo?: Date
}

export interface ApplicationQuery {
  page: number
  limit: number
  filters?: ApplicationFilters
  sortBy?: 'submissionDate' | 'priorityScore' | 'status'
  sortOrder?: 'asc' | 'desc'
}

export interface DuplicateCheckResult {
  isDuplicate: boolean
  canResubmit: boolean
  existingApplicationId?: string
  existingApplication?: Application
}

export interface CreateApplicationResponse {
  success: boolean
  application?: Application
  status?: 'created' | 'duplicate' | 'resubmission' | 'reupload_allowed'
  message?: string
  existingApplicationId?: string
  isReupload?: boolean
  parentApplicationId?: string
}

export interface ApplicationVersionHistory {
  applicationId: string
  documentType: string
  status: string
  currentVersion: number
  history: Array<{
    version: number
    fileUrl: string
    status: string
    createdAt: Date
    notes?: string
  }>
}
