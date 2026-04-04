/**
 * Applications API Service
 * Purpose: Service layer for application-related API calls
 */

import { apiClient } from './api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

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
  canonical?: any

  // temporary compatibility
  missingFields?: string[]
  extractionConfidence?: number
  village?: string

  [key: string]: any
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

    return apiClient.get<ApplicationsResponse>(url, {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    })
  }

  async getApplicationById(id: string): Promise<Application> {
    return apiClient.get<Application>(`${this.endpoint}/${id}`)
  }

  async createApplication(data: CreateApplicationInput): Promise<Application> {
    try {
      return await apiClient.post<Application>(this.endpoint, data)
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
    return apiClient.get(`${this.endpoint}/${id}/status`)
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
    return apiClient.get(`${this.endpoint}/${id}/file-url`)
  }

  async getFileUrlByPath(path: string): Promise<{ fileUrl: string }> {
    return apiClient.get(`${this.endpoint}/file-url-by-path?path=${encodeURIComponent(path)}`)
  }

  async getDashboardSummary(): Promise<any> {
    return apiClient.get('/dashboard/summary')
  }

  // ✅ FIXED UPLOAD FUNCTION
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

    const response = await fetch(`${API_BASE_URL}/api${this.endpoint}/with-file`, {
      method: 'POST',
      body: formData,
    })

    const data = await response.json()

    if (!response.ok) {
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