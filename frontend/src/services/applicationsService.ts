/**
 * Applications API Service
 * Purpose: Service layer for application-related API calls
 */
import { apiClient } from './api'

export interface Application {
  id: string
  applicantId: string
  schemeId: string
  type: string
  status: 'uploaded' | 'processing' | 'processed' | 'needs_review' | 'pending' | 'under_review' | 'approved' | 'rejected' | 'requires_action'
  priorityScore?: number
  fileName?: string
  fileUrl?: string
  fileSize?: number
  fileType?: string
  versionNumber?: number
  parentApplicationId?: string | null
  documents: ApplicationDocument[]
  personalInfo: PersonalInfo
  farmInfo?: FarmInfo
  extractedData?: ExtractedData
  aiSummary?: string
  fraudRiskScore?: number
  fraudFlags?: string[]
  verificationRecommendation?: string
  aiProcessingStatus?: string
  ocrProcessedAt?: string
  aiProcessedAt?: string
  rawExtractedText?: string
  documentMetadata?: any
  submissionDate: string
  reviewDate?: string
  decisionDate?: string
  reviewerId?: string
  notes?: string
  createdAt: string
  updatedAt: string
  farmerId?: string | null
  caseId?: string | null
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
}

export interface ApplicationDocument {
  id: string
  type: string
  name: string
  url: string
  uploadDate: string
  verificationStatus: 'pending' | 'verified' | 'rejected'
}

export interface PersonalInfo {
  firstName?: string
  lastName?: string
  email?: string
  phone?: string
  aadhaarNumber?: string
  dateOfBirth?: string
  address?: Partial<Address>
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

export interface FarmInfo {
  landArea: number
  location: Address
  cropTypes: string[]
  irrigationSource: string
  soilType?: string
  ownershipType: 'owned' | 'leased' | 'shared'
}

export interface ExtractedData {
  // Backend frozen contract fields
  document_type?: string
  structured_data?: Record<string, any>
  extracted_fields?: Record<string, any>
  missing_fields?: string[]
  confidence?: number
  reasoning?: string[]
  classification_confidence?: number
  classification_reasoning?: string[]
  risk_flags?: string[]
  decision_support?: {
    recommendation?: string
    confidence?: number
    reasoning?: string[]
  }
  canonical?: {
    applicant?: {
      name?: string
      guardian_name?: string
      aadhaar_number?: string
      mobile_number?: string
      address?: string
      village?: string
      district?: string
      state?: string
    }
    agriculture?: {
      land_size?: string
      land_unit?: string
      survey_number?: string
      crop_name?: string
      season?: string
    }
    request?: {
      scheme_name?: string
      request_type?: string
      requested_amount?: string
      issue_summary?: string
      claim_reason?: string
    }
    document_meta?: {
      supporting_doc_type?: string
      document_date?: string
      reference_number?: string
      source_file_name?: string
    }
    document_type?: string
  }
  
  // Temporary compatibility fields (marked for removal) - only actively used fields retained
  missingFields?: string[]     // @deprecated - use missing_fields (still used by ApplicationSections)
  extractionConfidence?: number // @deprecated - use confidence (still used by ApplicationSections)
  village?: string        // @deprecated - use canonical.applicant.village (still used by ApplicationSections)
  [key: string]: any // Allow additional dynamic fields
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
  personalInfo?: Partial<PersonalInfo>
  farmInfo?: FarmInfo
}

export interface ApplicationsResponse {
  applications: Application[]
  total: number
}

export interface ApplicationQuery {
  page?: number
  limit?: number
  status?: string
  applicantId?: string
  schemeId?: string
}

class ApplicationsService {
  private endpoint = '/applications'

  async getApplications(query: ApplicationQuery = {}): Promise<ApplicationsResponse> {
    const params = new URLSearchParams()
    
    if (query.page) params.append('page', query.page.toString())
    if (query.limit) params.append('limit', query.limit.toString())
    if (query.status) params.append('status', query.status)
    if (query.applicantId) params.append('applicantId', query.applicantId)
    if (query.schemeId) params.append('schemeId', query.schemeId)

    const queryString = params.toString()
    const url = queryString ? `${this.endpoint}?${queryString}` : this.endpoint

    // Add cache-busting headers for applications list to prevent 304 stale responses
    return apiClient.get<ApplicationsResponse>(url, {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    })
  }

  async getApplicationById(id: string): Promise<Application> {
    const response = await apiClient.get<Application>(`${this.endpoint}/${id}`)
    // apiClient already returns parsed data, return response directly
    return response
  }

  async createApplication(data: CreateApplicationInput): Promise<Application> {
    try {
      const res = await apiClient.post<Application>(this.endpoint, data)
      return res
    } catch (error: any) {
      throw error.response?.data || error
    }
  }

  async updateApplication(id: string, data: Partial<Application>): Promise<Application> {
    return apiClient.patch<Application>(`${this.endpoint}/${id}`, data)
  }

  async deleteApplication(id: string): Promise<void> {
    return apiClient.delete<void>(`${this.endpoint}/${id}`)
  }

  async getApplicationStatus(id: string): Promise<{ applicationId: string; status: string }> {
    return apiClient.get<{ applicationId: string; status: string }>(`${this.endpoint}/${id}/status`)
  }

  async approveApplication(id: string): Promise<Application> {
    return apiClient.patch<Application>(`${this.endpoint}/${id}/approve`, {})
  }

  async rejectApplication(id: string): Promise<Application> {
    return apiClient.patch<Application>(`${this.endpoint}/${id}/reject`, {})
  }

  async requestClarification(id: string): Promise<Application> {
    return apiClient.patch<Application>(`${this.endpoint}/${id}/request-clarification`, {})
  }

  async reprocessWithAI(id: string): Promise<Application> {
    return apiClient.post<Application>(`${this.endpoint}/${id}/reprocess`, {})
  }

  async getFileUrl(id: string): Promise<{ fileUrl: string; fileName: string; fileType: string }> {
    return apiClient.get<{ fileUrl: string; fileName: string; fileType: string }>(`${this.endpoint}/${id}/file-url`)
  }

  async getFileUrlByPath(path: string): Promise<{ fileUrl: string }> {
    return apiClient.get<{ fileUrl: string }>(
      `${this.endpoint}/file-url-by-path?path=${encodeURIComponent(path)}` 
    )
  }

  async getDashboardSummary(): Promise<{
    total_applications: number
    pending: number
    approved: number
    rejected: number
    high_priority: number
    risk_distribution: { low: number; medium: number; high: number }
    last_updated: string
  }> {
    return apiClient.get<{
      total_applications: number
      pending: number
      approved: number
      rejected: number
      high_priority: number
      risk_distribution: { low: number; medium: number; high: number }
      last_updated: string
    }>('/dashboard/summary')
  }

  async uploadApplicationFile(file: File): Promise<{
    success: boolean
    status: string
    message: string
    application?: Application
    existingApplicationId?: string
    isReupload: boolean
  }> {
    const formData = new FormData()
    formData.append('file', file)

    // Use fetch directly for FormData to avoid JSON.stringify
    const response = await fetch(`/api${this.endpoint}/with-file`, {
      method: 'POST',
      body: formData,
    })

    const data = await response.json()

    if (!response.ok) {
      // For duplicate submissions (409), return the response data instead of throwing
      if (response.status === 409) {
        return data
      }
      const errorText = data.message || data.error || 'Upload failed'
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    return data
  }
}

export const applicationsService = new ApplicationsService()
