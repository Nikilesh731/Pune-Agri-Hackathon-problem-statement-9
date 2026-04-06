/**
 * Application Detail Mapper
 * Purpose: Normalizes backend response shape to frontend expectations
 * 
 * This mapper serves as the frontend adapter layer:
 * - canonical schema is PREFERRED (first priority)
 * - structured_data is FALLBACK (second priority) 
 * - returned extractedFields is a UI-friendly adapter shape
 * - No legacy fallback paths - clean data flow from backend contract
 */
import { Application } from '../services/applicationsService'

export interface MappedApplication {
  id: string
  fileName: string
  fileType: string
  status: 'uploaded' | 'processing' | 'processed' | 'needs_review' | 'pending' | 'under_review' | 'approved' | 'rejected' | 'requires_action' | 'error'
  type: string
  personalInfo: any
  farmInfo: any
  documents: any[]
  extractedData: any
  aiSummary: string
  aiProcessingStatus: string
  createdAt: string | null
  reviewDate: string | null
  submissionDate: string
  applicantId: string
  schemeId: string
  updatedAt: string
  versionNumber?: number
  parentApplicationId?: string | null
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
  error?: string
  normalizedData?: any
  officerSummary?: string
}

export function mapApplicationToUI(app: any): MappedApplication {
  // ENHANCED SAFE MAPPER GUARD: Prevent blank pages with comprehensive error handling
  try {
    // Check for missing or malformed data
    if (!app || typeof app !== 'object') {
      return {
        id: app?.id || "",
        fileName: app?.fileName || "Unknown File",
        fileType: app?.fileType || "Unknown",
        status: (app?.status as any) || "unknown",
        type: app?.type || 'unknown',
        
        personalInfo: {},
        farmInfo: {},
        documents: [],

        extractedData: {},
        aiSummary: "No application data available",
        aiProcessingStatus: "pending",
        
        createdAt: app?.createdAt || null,
        reviewDate: app?.reviewDate || null,
        submissionDate: app?.submissionDate || app?.createdAt || new Date().toISOString(),
        applicantId: app?.applicantId || '',
        schemeId: app?.schemeId || '',
        updatedAt: app?.updatedAt || app?.createdAt || new Date().toISOString(),
        
        versionNumber: 1,
        parentApplicationId: null,
        farmerId: app?.farmerId || null,
        farmer: app?.farmer || null,
        caseId: app?.caseId || null,
        case: app?.case || null,
        error: "Application data is missing or invalid"
      }
    }

    // Check for missing or invalid extractedData
    if (!app.extractedData || typeof app.extractedData !== 'object') {
      return {
        id: app.id || "",
        fileName: app.fileName || "Unknown File",
        fileType: app.fileType || "Unknown",
        status: (app.status as any) || "unknown",
        type: app?.type || 'unknown',
        
        personalInfo: app.personalInfo || {},
        farmInfo: app.farmInfo || {},
        documents: app.documents || [],
        
        extractedData: {},
        aiSummary: "No extracted data available",
        aiProcessingStatus: app.aiProcessingStatus || "pending",
        
        createdAt: app.createdAt || null,
        reviewDate: app.reviewDate || null,
        submissionDate: app.submissionDate || app.createdAt || new Date().toISOString(),
        applicantId: app.applicantId || '',
        schemeId: app.schemeId || '',
        updatedAt: app.updatedAt || app.createdAt || new Date().toISOString(),
        
        versionNumber: 1,
        parentApplicationId: null,
        farmerId: app.farmerId || null,
        farmer: app.farmer || null,
        caseId: app.caseId || null,
        case: app.case || null,
        error: "Application detail could not be mapped safely - extractedData is missing or invalid"
      }
    }

    // Set document type priority same as everywhere else
    const resolvedType =
      app.extractedData?.canonical?.document_type ||
      app.extractedData?.document_type ||
      app.type ||
      'unknown'

    const normalized = normalizeApplicationData(app)

    return {
      id: app.id || '',
      fileName: app.fileName || 'Unknown File',
      fileType: app.fileType || 'unknown',
      status: (app.status as any) || "unknown",
      type: resolvedType,
      
      personalInfo: app.personalInfo || {},
      farmInfo: app.farmInfo || {},
      documents: Array.isArray(app.documents) ? app.documents : [],
      
      extractedData: (app.extractedData && typeof app.extractedData === 'object') ? app.extractedData : {},
      // Single source of truth for summary
      officerSummary: app.extractedData?.summary || app.extractedData?.ai_summary || app.extractedData?.llm_refinement?.refined_summary || 'Document processed. Review extracted details.',
      aiSummary: app.extractedData?.summary || app.extractedData?.ai_summary || app.extractedData?.llm_refinement?.refined_summary || 'Document processed. Review extracted details.',
      aiProcessingStatus: app.aiProcessingStatus || "pending",
      
      createdAt: app.createdAt || null,
      reviewDate: app.reviewDate || null,
      submissionDate: app.submissionDate || app.createdAt || new Date().toISOString(),
      applicantId: app.applicantId || '',
      schemeId: app.schemeId || '',
      updatedAt: app.updatedAt || app.createdAt || new Date().toISOString(),
      
      versionNumber: app.versionNumber || 1,
      parentApplicationId: app.parentApplicationId || null,
      
      farmerId: app.farmerId || null,
      caseId: app.caseId || null,
      farmer: app.farmer || null,
      case: app.case || null,
      error: app.error,
      normalizedData: normalized
    }
  } catch (error) {
    // ULTIMATE FALLBACK: If anything throws, return safe fallback
    console.error('mapApplicationToUI error:', error)
    return {
      id: app?.id || "",
      fileName: app?.fileName || "Unknown File",
      fileType: app?.fileType || "Unknown",
      status: (app?.status as any) || "unknown",
      type: app?.type || 'unknown',
      
      personalInfo: {},
      farmInfo: {},
      documents: [],
      
      extractedData: {},
      aiSummary: "Application detail could not be mapped safely",
      aiProcessingStatus: "pending",
      
      createdAt: app?.createdAt || null,
      reviewDate: app?.reviewDate || null,
      submissionDate: app?.submissionDate || app?.createdAt || new Date().toISOString(),
      applicantId: app?.applicantId || '',
      schemeId: app?.schemeId || '',
      updatedAt: app?.updatedAt || app?.createdAt || new Date().toISOString(),
      
      versionNumber: 1,
      parentApplicationId: null,
      farmerId: app?.farmerId || null,
      farmer: app?.farmer || null,
      caseId: app?.caseId || null,
      case: app?.case || null,
      error: "Application detail could not be mapped safely - unexpected error"
    }
  }
}

export function mapApplicationsToList(applications: any[]): MappedApplication[] {
  return applications.map(app => mapApplicationToUI(app))
}

export interface NormalizedApplication {
  id: string
  applicantId: string
  status: string
  workflowStatus?: string
  type: string
  documentType?: string
  submissionDate: string
  updatedAt: string
  versionNumber?: number
  parentApplicationId?: string | null
  extractedFields: Record<string, any>
  missingFields: string[]
  completenessScore: number
  confidenceScore: number
  fraudFlags: string[]
  conflictFlags?: string[]
  recommendation?: string
  sourceDocuments: any[]
  grievanceInfo?: {
    category?: string
    urgency?: string
    routedDepartment?: string
  }
  aiSummary?: string
  priorityScore?: number
  fraudRiskScore?: number
  verificationRecommendation?: string
  aiProcessingStatus?: string
  classificationConfidence?: number
  classificationReasoning?: string[]
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
  // ML Insights fields for workflow and risk management
  mlInsights?: {
    queue?: 'HIGH_PRIORITY' | 'NORMAL' | 'LOW'
    risk_level?: 'HIGH' | 'MEDIUM' | 'LOW'
    priority_score?: number
    processing_time?: string
    approval_likelihood?: number
  }
  canonicalData?: any | null // TASK 4: PRESERVE CANONICAL DATA
  riskFlags?: Array<{
    code?: string
    severity?: string
    message?: string
  }> // TASK 5: EXPOSE RISK FLAGS
  decisionSupport?: any // TASK 5: EXPOSE DECISION SUPPORT
  officerSummary?: string
  extractedSections?: {
    applicant: Record<string, any>
    contact: Record<string, any>
    location: Record<string, any>
    financial: Record<string, any>
    agriculture: Record<string, any>
    document: Record<string, any>
  }
  // NEW: Single source normalization fields
  displayApplicantName?: string
  displayStatus?: string
  displayDocumentType?: string
  priorityScoreNormalized?: number
  riskLevel?: string
}

/**
 * Normalize monetary values for UI display.
 * Keeps original raw value when parsing fails.
 */
function normalizeAmount(value: unknown): string {
  if (value === null || value === undefined || value === "") return "";

  const raw = String(value).trim();

  // remove currency symbol and spaces only
  const cleaned = raw.replace(/₹/g, "").replace(/\s+/g, "");

  // remove commas ONLY for numeric parsing
  const numeric = Number(cleaned.replace(/,/g, ""));

  if (!Number.isFinite(numeric)) {
    return raw; // safe fallback if parsing fails
  }

  return `₹${numeric.toLocaleString("en-IN")}`;
}

/**
 * Normalizes extracted fields from backend contract
 * 
 * FIXED: Field-level fallback instead of object-level fallback
 * For each field, try canonical first, then structured_data
 * This prevents blank fields when canonical is partial
 */
function normalizeExtractedFields(application: any): Record<string, any> {
  // Get both canonical and structured data for field-level fallback
  const canonical = application?.extractedData?.canonical || {}
  const structured = application?.extractedData?.structured_data || {}

  // Field-level fallback: try canonical first, then structured_data for each field
  const mergedFields: Record<string, any> = {
    // Applicant information - field-level fallback
    farmerName: canonical.applicant?.name || 
                structured.farmer_name || 
                structured.applicant_name || '',
    
    guardianName: canonical.applicant?.guardian_name || 
                  structured.guardian_name || '',
    
    aadhaarNumber: canonical.applicant?.aadhaar_number || 
                   structured.aadhaar_number || '',
    
    mobileNumber: canonical.applicant?.mobile_number || 
                  structured.mobile_number || 
                  structured.phone_number || '',
    
    address: canonical.applicant?.address || 
             structured.address || '',
    
    village: canonical.applicant?.village || 
             structured.village || '',
    
    district: canonical.applicant?.district || 
              structured.district || '',
    
    state: canonical.applicant?.state || 
           structured.state || '',

    // Agriculture information - field-level fallback
    landSize: canonical.agriculture?.land_size || 
              structured.land_size || 
              structured.landSize || '',
    
    landUnit: canonical.agriculture?.land_unit || 
              structured.land_unit || 
              structured.landUnit || '',
    
    surveyNumber: canonical.agriculture?.survey_number || 
                  structured.survey_number || '',
    
    cropName: canonical.agriculture?.crop_name || 
              structured.crop_name || 
              structured.cropName || '',
    
    season: canonical.agriculture?.season || 
            structured.season || '',

    // Request information - field-level fallback
    schemeName: canonical.request?.scheme_name || 
                structured.scheme_name || '',
    
    requestType: canonical.request?.request_type || 
                 structured.request_type || '',
    
    requestedAmount: normalizeAmount(
      canonical.request?.requested_amount ||
      canonical.request?.claim_amount ||
      canonical.request?.subsidy_amount ||
      canonical.request?.amount ||
      structured.requested_amount ||
      structured.claim_amount ||
      structured.subsidy_amount ||
      structured.amount ||
      ''
    ),
    
    annualIncome: normalizeAmount(
      canonical.annual_income ||
      canonical.request?.annual_income ||
      structured.annual_income ||
      structured.annualIncome ||
      ''
    ),
    
    issueSummary: canonical.request?.issue_summary || 
                  structured.issue_description || 
                  structured.grievance_description || '',
    
    claimReason: canonical.request?.claim_reason || 
                structured.claim_reason || 
                structured.issue_description || 
                structured.grievance_description || '',

    // Document metadata - field-level fallback
    documentType: canonical.document_meta?.supporting_doc_type || 
                  canonical.document_type || 
                  structured.document_type_detail || 
                  application.extractedData?.document_type || '',
    
    documentDate: canonical.document_meta?.document_date || 
                  structured.documentDate || '',
    
    referenceNumber: canonical.document_meta?.reference_number || 
                     structured.document_reference || 
                     structured.reference_number || '',
    
    sourceFileName: canonical.document_meta?.source_file_name || 
                    structured.source_file_name || '',

    // Additional fields that may exist in structured_data
    policyNumber: structured.policy_number || '',
    issuesAuthority: structured.issuing_authority || ''
  }

  return mergedFields
}

/**
 * Build structured extracted sections with field-level fallback.
 * FIXED: Use field-level fallback instead of object-level choice
 * Returns only validated, non-placeholder values and never returns raw backend objects.
 */
function buildCanonicalExtractedSections(application: any) {
  const canonical = application?.extractedData?.canonical || {}
  const structured = application?.extractedData?.structured_data || {}

  const isValidString = (v: any) => {
    if (v === null || v === undefined) return false
    if (typeof v !== 'string') return !!String(v).trim()
    const s = v.trim()
    if (s === '' || s.toLowerCase() === 'n/a' || s === '-' || s.toLowerCase() === 'na' || s.toLowerCase() === 'unknown') return false
    if (s.toLowerCase().includes('metadata') || s.startsWith('{') || s.startsWith('[')) return false
    return true
  }

  const isValidAadhaar = (v: any) => {
    if (!isValidString(v)) return false
    const digits = String(v).replace(/\D/g, '')
    return digits.length === 12
  }

  const isValidMobile = (v: any) => {
    if (!isValidString(v)) return false
    const digits = String(v).replace(/\D/g, '')
    return digits.length >= 8 && digits.length <= 13
  }

  const isValidAmount = (v: any) => {
    if (v === null || v === undefined || v === '') return false
    const num = typeof v === 'number' ? v : parseFloat(String(v).replace(/[^0-9.]/g, ''))
    return !isNaN(num) && num > 0
  }

  const sections = {
    applicant: {} as Record<string, any>,
    contact: {} as Record<string, any>,
    location: {} as Record<string, any>,
    financial: {} as Record<string, any>,
    agriculture: {} as Record<string, any>,
    document: {} as Record<string, any>
  }

  // Applicant - field-level fallback
  const applicantName = canonical.applicant?.name || structured.farmer_name || structured.applicant_name
  if (isValidString(applicantName)) {
    if (String(applicantName).trim().toLowerCase() !== 'supporting document') {
      sections.applicant['farmerName'] = String(applicantName).trim()
    }
  }
  
  const guardianName = canonical.applicant?.guardian_name || structured.guardian_name
  if (isValidString(guardianName)) sections.applicant['guardianName'] = guardianName
  
  const aadhaarNumber = canonical.applicant?.aadhaar_number || structured.aadhaar_number
  if (isValidAadhaar(aadhaarNumber)) sections.applicant['aadhaarNumber'] = String(aadhaarNumber).replace(/\D/g, '')
  
  const mobileNumber = canonical.applicant?.mobile_number || structured.mobile_number || structured.phone_number
  if (isValidMobile(mobileNumber)) sections.applicant['mobileNumber'] = String(mobileNumber).trim()

  // Contact - field-level fallback
  const email = canonical.applicant?.email || structured.email
  if (isValidString(email)) sections.contact['email'] = email
  
  const contactMobile = canonical.applicant?.mobile_number || structured.mobile_number || structured.phone_number
  if (isValidMobile(contactMobile)) sections.contact['mobile'] = contactMobile

  // Location - field-level fallback
  const address = canonical.applicant?.address || structured.address
  if (isValidString(address)) sections.location['address'] = address
  
  const village = canonical.applicant?.village || structured.village
  if (isValidString(village)) sections.location['village'] = village
  
  const district = canonical.applicant?.district || structured.district
  if (isValidString(district)) sections.location['district'] = district
  
  const state = canonical.applicant?.state || structured.state
  if (isValidString(state)) sections.location['state'] = state

  // Financial - field-level fallback
  const requestedAmount = canonical.request?.requested_amount || 
                         canonical.request?.claim_amount || 
                         canonical.request?.subsidy_amount || 
                         canonical.request?.amount ||
                         structured.requested_amount || 
                         structured.claim_amount || 
                         structured.subsidy_amount || 
                         structured.amount
  if (isValidAmount(requestedAmount)) sections.financial['requestedAmount'] = requestedAmount
  
  const annualIncome = canonical.annual_income || 
                      canonical.request?.annual_income || 
                      structured.annual_income || 
                      structured.annualIncome
  if (isValidAmount(annualIncome)) sections.financial['annualIncome'] = annualIncome

  // Agriculture - field-level fallback
  const landSize = canonical.agriculture?.land_size || structured.land_size || structured.landSize
  if (isValidString(landSize)) sections.agriculture['landSize'] = landSize
  
  const landUnit = canonical.agriculture?.land_unit || structured.land_unit || structured.landUnit
  if (isValidString(landUnit)) sections.agriculture['landUnit'] = landUnit
  
  const cropName = canonical.agriculture?.crop_name || structured.crop_name || structured.cropName
  if (isValidString(cropName)) sections.agriculture['cropName'] = cropName
  
  const season = canonical.agriculture?.season || structured.season
  if (isValidString(season)) sections.agriculture['season'] = season

  // Document - field-level fallback
  const referenceNumber = canonical.document_meta?.reference_number || 
                         structured.document_reference || 
                         structured.reference_number
  if (isValidString(referenceNumber)) sections.document['referenceNumber'] = referenceNumber
  
  const documentDate = canonical.document_meta?.document_date || structured.documentDate
  if (isValidString(documentDate)) sections.document['documentDate'] = documentDate
  
  const documentType = canonical.document_meta?.supporting_doc_type || 
                      canonical.document_type || 
                      structured.document_type_detail
  if (isValidString(documentType)) sections.document['documentType'] = documentType

  return sections
}

/**
 * Helper function to get applicant display name with priority order
 * FIXED: Use canonical.applicant.name as first priority to fix "Unknown Farmer" issue
 */
function getApplicantName(application: any): string {
  // 1. extractedData.canonical.applicant.name (FIXED: First priority for "Unknown Farmer" issue)
  if (application.extractedData?.canonical?.applicant?.name) {
    return application.extractedData.canonical.applicant.name
  }
  // 2. extractedData.structured_data.farmer_name (new pipeline)
  if (application.extractedData?.structured_data?.farmer_name) {
    return application.extractedData.structured_data.farmer_name
  }
  // 3. extractedData.farmer_name (direct extraction)
  if (application.extractedData?.farmer_name) {
    return application.extractedData.farmer_name
  }
  // 4. personalInfo.firstName + lastName
  if (application.personalInfo?.firstName && application.personalInfo?.lastName) {
    return `${application.personalInfo.firstName} ${application.personalInfo.lastName}`
  }
  // 5. applicantId as last safe fallback
  if (application.applicantId) {
    return application.applicantId
  }
  // 6. Unknown only if truly no value exists
  return 'Unknown Applicant'
}

/**
 * SHARED HELPER: Normalize priority score to 0-100 range
 * CRITICAL FIX: Prevents 6000% display when priority_score = 60
 * USAGE: `${normalizePriorityScore(priority_score)}%`
 */
export function normalizePriorityScore(value: any): number {
  if (typeof value !== 'number' || isNaN(value)) return 0
  if (value <= 1) return Math.round(value * 100)
  if (value <= 100) return Math.round(value)
  return 100
}

/**
 * Helper function to normalize risk level
 */
function normalizeRiskLevel(riskLevel: string): string {
  if (!riskLevel) return 'medium'
  const normalized = riskLevel.toLowerCase().trim()
  switch (normalized) {
    case 'high':
    case 'high_priority':
      return 'high'
    case 'low':
    case 'low_priority':
      return 'low'
    case 'medium':
    case 'normal':
    default:
      return 'medium'
  }
}

/**
 * Normalizes raw application data from backend to frontend-friendly format
 */
export function normalizeApplicationData(application: Application): NormalizedApplication {
  try {
    // Use the simplified normalization function
    const extractedFields = normalizeExtractedFields(application)
    const canonicalData = application?.extractedData?.canonical

    // Extract missing fields and confidence directly from backend contract
    const missingFields = application.extractedData?.missing_fields || []
    const confidenceScore = application.extractedData?.confidence || 0
    
    // Extract classification information from backend contract
    const classificationConfidence = application.extractedData?.classification_confidence || 0
    const classificationReasoning = application.extractedData?.classification_reasoning || []
    
    const completenessScore = confidenceScore * (1 - (missingFields.length / 10)) // Assume 10 expected fields max

    // Extract document type with correct priority order
    const documentType = 
      canonicalData?.document_type ||
      application.extractedData?.document_type ||
      application.type ||
      'unknown'

    // Normalize fraud flags from backend contract with fail-safe defaults
    const fraudFlags = application.fraudFlags || application.extractedData?.risk_flags || []

    // TASK 5: FAIL-SAFE UI DATA - Ensure AI fields have safe defaults
    // Single summary source: prefer backend summary, then ai_summary (same value), then refinement
    const officerSummary = application.extractedData?.summary || application.extractedData?.ai_summary || ""  // Real intelligence summary

    // Build sanitized extracted sections (extractedFields already computed)
    const extractedSections = buildCanonicalExtractedSections(application)

    // Handle risk flags - preserve object format for OCR failure, convert strings to objects
    const rawRiskFlags = application.extractedData?.risk_flags || []
    const riskFlags = rawRiskFlags.map((flag: any) => {
      if (typeof flag === 'string') {
        return { message: flag }
      }
      if (flag && typeof flag === 'object') {
        // Preserve OCR failure objects as-is to maintain code/severity/message structure
        return flag
      }
      return { message: String(flag) }
    })
    
    // Get decision support and intelligence data
    const decisionSupport = application.extractedData?.decision_support || null
    
    // Get ML insights and predictions from backend contract
    const mlInsights = application.extractedData?.ml_insights || {}
    const predictions = application.extractedData?.predictions || {}
    
    // Frontend fail-safe defaults - prefer real intelligence summary over generic fallback
    const safeAiSummary = officerSummary || ""  
    const safeRiskFlags = riskFlags || []
    const safeDecisionSupport = decisionSupport || {
      decision: "manual_review_required",
      confidence: 0.0,
      reasoning: [],
      recommendation: "manual_review_required"
    }
    const safeCanonicalData = canonicalData || null

    // NEW: Single source normalization
    const displayApplicantName = getApplicantName(application)
    const displayStatus = application.status || 'unknown'
    const displayDocumentType = getDocumentTypeLabel(documentType)
    const priorityScoreNormalized = normalizePriorityScore(
      mlInsights.priority_score ?? predictions.priority_score ?? application.priorityScore ?? 0
    )
    const riskLevel = normalizeRiskLevel(mlInsights.risk_level || predictions.risk_level || 'medium')

    return {
      id: application.id,
      applicantId: application.applicantId,
      status: application.status,
      workflowStatus: application.aiProcessingStatus,
      type: documentType,
      documentType,
      submissionDate: application.submissionDate || application.createdAt,
      updatedAt: application.updatedAt,
      
      // Add version fields
      versionNumber: application.versionNumber || 1,
      parentApplicationId: application.parentApplicationId || null,
      
      extractedFields,
      extractedSections,
      missingFields,
      completenessScore: Math.max(0, Math.min(100, completenessScore * 100)),
      confidenceScore: Math.max(0, Math.min(100, confidenceScore * 100)),
      fraudFlags,
      recommendation: application.verificationRecommendation || application.extractedData?.decision_support?.recommendation,
      sourceDocuments: application.documents || [],
      
      // TASK 4: FAIL-SAFE UI DATA - Always provide AI fields with safe defaults
      aiSummary: safeAiSummary,
      officerSummary: officerSummary,
      priorityScore: priorityScoreNormalized,
      fraudRiskScore: application.fraudRiskScore || 0,
      verificationRecommendation: application.verificationRecommendation || safeDecisionSupport?.recommendation || "",
      aiProcessingStatus: application.aiProcessingStatus || "pending",
      classificationConfidence: Math.max(0, Math.min(100, classificationConfidence * 100)),
      classificationReasoning,
      
      // TASK 4: PRESERVE CANONICAL DATA - Ensure canonical.document_type is always accessible
      canonicalData: safeCanonicalData,
      
      // TASK 5: EXPOSE AI FIELDS - Ensure risk_flags and decision_support are available
      riskFlags: safeRiskFlags,
      decisionSupport: safeDecisionSupport,
      
      // Add ML insights for workflow and risk management
      mlInsights: mlInsights,
      
      // Add farmer fields if available (backward compatible)
      farmerId: application.farmerId || null,
      farmer: application.farmer || null,
      // Add case fields if available (non-breaking)
      caseId: application.caseId || null,
      case: application.case || null,
      
      // NEW: Single source normalization fields
      displayApplicantName,
      displayStatus,
      displayDocumentType,
      priorityScoreNormalized,
      riskLevel
    }
  } catch (error) {
    // SAFE FALLBACK: Return minimal normalized object if normalization fails
    console.error('normalizeApplicationData error:', error)
    return {
      id: application?.id || '',
      applicantId: application?.applicantId || '',
      status: application?.status || 'unknown',
      workflowStatus: application?.aiProcessingStatus || 'pending',
      type: application?.type || 'unknown',
      documentType: application?.type || 'unknown',
      submissionDate: application?.submissionDate || application?.createdAt || new Date().toISOString(),
      updatedAt: application?.updatedAt || application?.createdAt || new Date().toISOString(),
      
      versionNumber: application?.versionNumber || 1,
      parentApplicationId: application?.parentApplicationId || null,
      
      extractedFields: {},
      missingFields: [],
      completenessScore: 0,
      confidenceScore: 0,
      fraudFlags: [],
      recommendation: '',
      sourceDocuments: application?.documents || [],
      
      aiSummary: 'Application data could not be processed safely',
      priorityScore: 0,
      fraudRiskScore: 0,
      verificationRecommendation: '',
      aiProcessingStatus: application?.aiProcessingStatus || 'pending',
      classificationConfidence: 0,
      classificationReasoning: [],
      
      canonicalData: null,
      riskFlags: [],
      decisionSupport: null,
      
      farmerId: application?.farmerId || null,
      farmer: application?.farmer || null,
      caseId: application?.caseId || null,
      case: application?.case || null
    }
  }
}

/**
 * Gets a human-readable label for document types
 */
export function getDocumentTypeLabel(type: string): string {
  switch (type) {
    case 'scheme_application':
      return 'Scheme Application'
    case 'subsidy_claim':
      return 'Subsidy Claim'
    case 'insurance_claim':
      return 'Insurance Claim'
    case 'grievance':
    case 'grievance_letter':
      return 'Grievance Letter'
    case 'farmer_record':
      return 'Farmer Record'
    case 'supporting_document':
      return 'Supporting Document'
    case 'land_record':
      return 'Land Record'
    case 'bank_passbook':
      return 'Bank Passbook'
    case 'id_proof':
      return 'ID Proof'
    default:
      return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
}

/**
 * Formats confidence score for display
 */
export function formatConfidenceScore(score: number): string {
  if (score >= 80) return `${Math.round(score)}% (High)`
  if (score >= 60) return `${Math.round(score)}% (Medium)`
  return `${Math.round(score)}% (Low)`
}

/**
 * Formats completeness score for display
 */
export function formatCompletenessScore(score: number): string {
  if (score >= 90) return `${Math.round(score)}% (Complete)`
  if (score >= 70) return `${Math.round(score)}% (Mostly Complete)`
  if (score >= 50) return `${Math.round(score)}% (Partially Complete)`
  return `${Math.round(score)}% (Incomplete)`
}

/**
 * Unified Frontend Normalization Function
 * Purpose: Create ONE shared safe state builder for all frontend usage
 * - Normalizes backend status to lowercase UI-safe values
 * - Normalizes aiProcessingStatus to lowercase UI-safe values
 * - Resolves document type with proper priority order
 * - Always guarantees required object structure
 * - Never throws - provides safe fallbacks
 */
export interface SafeApplicationState {
  id: string
  fileName: string
  fileType: string
  status: 'uploaded' | 'processing' | 'processed' | 'needs_review' | 'pending' | 'under_review' | 'approved' | 'rejected' | 'requires_action' | 'error'
  type: string
  personalInfo: Record<string, any>
  farmInfo: Record<string, any>
  documents: any[]
  extractedData: Record<string, any>
  aiSummary: string
  officerSummary?: string
  aiProcessingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string | null
  reviewDate: string | null
  submissionDate: string
  applicantId: string
  schemeId: string
  updatedAt: string
  versionNumber?: number
  parentApplicationId?: string | null
  farmerId?: string | null
  caseId?: string | null
  farmer?: any
  case?: any
  error?: string
  normalizedData: any
}

/**
 * Resolve display workflow state - SINGLE SOURCE OF TRUTH for status display
 * Prevents contradictory CASE_READY + Under review + VERIFICATION_QUEUE combinations
 */
export interface DisplayWorkflowState {
  displayStatusText: string
  displayBadgeLabel: string
  displayQueueLabel: string
  isUnderReview: boolean
}

export function resolveDisplayWorkflowState(application: any): DisplayWorkflowState {
  const normalizedData = application.normalizedData || {}
  const mlInsights = normalizedData.mlInsights || {}
  const decisionSupport = normalizedData.decisionSupport || {}
  const missingFields = normalizedData.missingFields || []
  const riskFlags = normalizedData.riskFlags || []
  
  // Check if application should be marked as UNDER_REVIEW
  const needsReview = (
    mlInsights.queue === 'VERIFICATION_QUEUE' ||
    ['review', 'manual_review'].includes(decisionSupport?.decision) ||
    missingFields.length > 0 ||
    riskFlags.some((flag: any) => flag.severity && ['medium', 'high'].includes(flag.severity))
  )
  
  if (needsReview) {
    return {
      displayStatusText: 'UNDER_REVIEW',
      displayBadgeLabel: 'Under review',
      displayQueueLabel: mlInsights.queue || 'VERIFICATION_QUEUE',
      isUnderReview: true
    }
  }
  
  // Use explicit application status if available
  if (application.status && ['approved', 'rejected', 'requires_action'].includes(application.status)) {
    return {
      displayStatusText: application.status.toUpperCase(),
      displayBadgeLabel: application.status.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
      displayQueueLabel: mlInsights.queue || 'NORMAL',
      isUnderReview: false
    }
  }
  
  // Default to CASE_READY
  return {
    displayStatusText: 'CASE_READY',
    displayBadgeLabel: 'Case ready',
    displayQueueLabel: mlInsights.queue || 'NORMAL',
    isUnderReview: false
  }
}

export function buildSafeDetailState(rawApp: any): SafeApplicationState {
  try {
    if (!rawApp || typeof rawApp !== 'object') {
      return {
        id: rawApp?.id || '',
        fileName: 'Unknown File',
        fileType: 'unknown',
        status: 'uploaded',
        type: 'unknown',
        personalInfo: {},
        farmInfo: {},
        documents: [],
        extractedData: {},
        aiSummary: 'No application data available',
        aiProcessingStatus: 'pending',
        createdAt: rawApp?.createdAt || null,
        reviewDate: rawApp?.reviewDate || null,
        submissionDate: rawApp?.submissionDate || rawApp?.createdAt || new Date().toISOString(),
        applicantId: rawApp?.applicantId || '',
        schemeId: rawApp?.schemeId || '',
        updatedAt: rawApp?.updatedAt || rawApp?.createdAt || new Date().toISOString(),
        versionNumber: 1,
        parentApplicationId: null,
        farmerId: rawApp?.farmerId || null,
        caseId: rawApp?.caseId || null,
        farmer: rawApp?.farmer || null,
        case: rawApp?.case || null,
        error: 'Application data is missing or invalid',
        normalizedData: {
          id: rawApp?.id || '',
          applicantId: rawApp?.applicantId || '',
          status: 'uploaded',
          type: 'unknown',
          documentType: 'unknown',
          submissionDate: rawApp?.submissionDate || rawApp?.createdAt || new Date().toISOString(),
          updatedAt: rawApp?.updatedAt || rawApp?.createdAt || new Date().toISOString(),
          extractedFields: {},
          missingFields: [],
          completenessScore: 0,
          confidenceScore: 0,
          fraudFlags: [],
          sourceDocuments: [],
          aiSummary: 'No application data available',
          priorityScore: 0,
          fraudRiskScore: 0,
          verificationRecommendation: '',
          aiProcessingStatus: 'pending',
          classificationConfidence: 0,
          classificationReasoning: [],
          canonicalData: null,
          riskFlags: [],
          decisionSupport: null,
          farmerId: rawApp?.farmerId || null,
          farmer: rawApp?.farmer || null,
          caseId: rawApp?.caseId || null,
          case: rawApp?.case || null
        }
      }
    }

    // Backend status normalization mapping: UPPERCASE -> lowercase
    const normalizeStatus = (status: any): SafeApplicationState['status'] => {
      if (!status) return 'uploaded'
      const s = status.toString().toLowerCase()
      switch (s) {
        case 'uploaded': return 'uploaded'
        case 'processing': return 'processing'
        case 'processed': return 'processed'
        case 'needs_review': return 'needs_review'
        case 'pending': return 'pending'
        case 'under_review': return 'under_review'
        case 'approved': return 'approved'
        case 'rejected': return 'rejected'
        case 'requires_action': return 'requires_action'
        case 'error': return 'error'
        default: return 'uploaded'
      }
    }

    // Normalize AI processing status: various cases -> lowercase
    const normalizeAIStatus = (status: any): SafeApplicationState['aiProcessingStatus'] => {
      if (!status) return 'pending'
      const s = status.toString().toLowerCase()
      switch (s) {
        case 'pending': return 'pending'
        case 'processing': return 'processing'
        case 'completed': return 'completed'
        case 'failed': return 'failed'
        default: return 'pending'
      }
    }

    // Resolve document type with priority: canonical.document_type -> extractedData.document_type -> type
    const resolveDocumentType = (app: any): string => {
      return app?.extractedData?.canonical?.document_type ||
             app?.extractedData?.document_type ||
             app?.type ||
             'unknown'
    }

    // Always guarantee required objects
    const safeExtractedData = (rawApp.extractedData && typeof rawApp.extractedData === 'object') ? rawApp.extractedData : {}

    const normalized = normalizeApplicationData(rawApp)

    return {
      id: rawApp.id || '',
      fileName: rawApp.fileName || 'Unknown File',
      fileType: rawApp.fileType || 'unknown',
      status: normalizeStatus(rawApp.status),
      type: resolveDocumentType(rawApp),
      personalInfo: rawApp.personalInfo || {},
      farmInfo: rawApp.farmInfo || {},
      documents: Array.isArray(rawApp.documents) ? rawApp.documents : [],
      extractedData: safeExtractedData,
      // Single source for summary to prevent duplication
      officerSummary: safeExtractedData?.summary || safeExtractedData?.ai_summary || 'Document processed. Review extracted details.',
      aiSummary: safeExtractedData?.summary || safeExtractedData?.ai_summary || 'Document processed. Review extracted details.',
      aiProcessingStatus: normalizeAIStatus(rawApp.aiProcessingStatus),
      createdAt: rawApp.createdAt || null,
      reviewDate: rawApp.reviewDate || null,
      submissionDate: rawApp.submissionDate || rawApp.createdAt || new Date().toISOString(),
      applicantId: rawApp.applicantId || '',
      schemeId: rawApp.schemeId || '',
      updatedAt: rawApp.updatedAt || rawApp.createdAt || new Date().toISOString(),
      versionNumber: rawApp.versionNumber || 1,
      parentApplicationId: rawApp.parentApplicationId || null,
      farmerId: rawApp.farmerId || null,
      caseId: rawApp.caseId || null,
      farmer: rawApp.farmer || null,
      case: rawApp.case || null,
      error: rawApp.error,
      normalizedData: normalized
    }
  } catch (error) {
    console.error('buildSafeDetailState error:', error)
    return {
      id: rawApp?.id || '',
      fileName: 'Error Loading',
      fileType: 'unknown',
      status: 'error',
      type: 'unknown',
      personalInfo: {},
      farmInfo: {},
      documents: [],
      extractedData: {},
      aiSummary: 'Failed to process application data',
      aiProcessingStatus: 'failed',
      createdAt: rawApp?.createdAt || null,
      reviewDate: rawApp?.reviewDate || null,
      submissionDate: rawApp?.submissionDate || rawApp?.createdAt || new Date().toISOString(),
      applicantId: rawApp?.applicantId || '',
      schemeId: rawApp?.schemeId || '',
      updatedAt: rawApp?.updatedAt || rawApp?.createdAt || new Date().toISOString(),
      versionNumber: 1,
      parentApplicationId: null,
      farmerId: rawApp?.farmerId || null,
      caseId: rawApp?.caseId || null,
      farmer: rawApp?.farmer || null,
      case: rawApp?.case || null,
      error: 'Application data could not be processed safely',
      normalizedData: {
        id: rawApp?.id || '',
        applicantId: rawApp?.applicantId || '',
        status: 'error',
        type: 'unknown',
        documentType: 'unknown',
        submissionDate: rawApp?.submissionDate || rawApp?.createdAt || new Date().toISOString(),
        updatedAt: rawApp?.updatedAt || rawApp?.createdAt || new Date().toISOString(),
        extractedFields: {},
        missingFields: [],
        completenessScore: 0,
        confidenceScore: 0,
        fraudFlags: [],
        sourceDocuments: [],
        aiSummary: 'Failed to process application data',
        priorityScore: 0,
        fraudRiskScore: 0,
        verificationRecommendation: '',
        aiProcessingStatus: 'failed',
        classificationConfidence: 0,
        classificationReasoning: [],
        canonicalData: null,
        riskFlags: [],
        decisionSupport: null,
        farmerId: rawApp?.farmerId || null,
        farmer: rawApp?.farmer || null,
        caseId: rawApp?.caseId || null,
        case: rawApp?.case || null
      }
    }
  }
}

// Queue normalization helper for verification page
export interface NormalizedQueueItem {
  id: string
  fileName: string
  documentType: string
  displayDocumentType: string
  displayApplicantName: string
  status: string
  displayStatus: string
  priorityScoreNormalized: number
  riskLevel: string
  submittedAt: string
}

export function normalizeQueueItem(item: any): NormalizedQueueItem {
  // Applicant name priority order - FIXED: Use canonical.applicant.name first
  const applicantName = 
    item.extractedData?.canonical?.applicant?.name ||
    item.extractedData?.structured_data?.farmer_name ||
    item.extractedData?.farmer_name ||
    item.farmer?.name ||
    item.applicantId ||
    "Unknown Applicant"

  // Priority score normalization rule - FIXED to prevent 6000% bug
  const priorityScoreNormalized = normalizePriorityScore(item.priorityScore || 0)

  // Display document type
  const displayDocumentType = item.documentType?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) || 'Unknown'

  // Display status
  const displayStatus = item.status?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) || 'Unknown'

  return {
    id: item.id,
    fileName: item.fileName || item.fileName || 'Unknown File',
    documentType: item.documentType || item.type || 'unknown',
    displayDocumentType,
    displayApplicantName: applicantName,
    status: item.status || 'unknown',
    displayStatus,
    priorityScoreNormalized,
    riskLevel: item.riskLevel || 'medium',
    submittedAt: item.submittedAt || item.submissionDate || new Date().toISOString()
  }
}

// Helper to build extracted sections from normalized fields
export interface ExtractedSections {
  applicantInfo: Record<string, any>
  contactInfo: Record<string, any>
  locationInfo: Record<string, any>
  financialInfo: Record<string, any>
  agricultureInfo: Record<string, any>
  documentMeta: Record<string, any>
}

export function buildExtractedSections(extractedFields: Record<string, any>): ExtractedSections {
  const sections: ExtractedSections = {
    applicantInfo: {},
    contactInfo: {},
    locationInfo: {},
    financialInfo: {},
    agricultureInfo: {},
    documentMeta: {}
  }

  // Group fields by category
  Object.entries(extractedFields).forEach(([key, value]) => {
    const lowerKey = key.toLowerCase()
    
    // Applicant information
    if (lowerKey.includes('name') || lowerKey.includes('applicant') || lowerKey.includes('beneficiary') || lowerKey.includes('claimant')) {
      sections.applicantInfo[key] = value
    }
    
    // Contact information
    else if (lowerKey.includes('phone') || lowerKey.includes('mobile') || lowerKey.includes('contact') || lowerKey.includes('email')) {
      sections.contactInfo[key] = value
    }
    
    // Location information
    else if (lowerKey.includes('address') || lowerKey.includes('village') || lowerKey.includes('district') || lowerKey.includes('location') || lowerKey.includes('place')) {
      sections.locationInfo[key] = value
    }
    
    // Financial information
    else if (lowerKey.includes('amount') || lowerKey.includes('loan') || lowerKey.includes('subsidy') || lowerKey.includes('claim') || lowerKey.includes('financial')) {
      sections.financialInfo[key] = value
    }
    
    // Agriculture information
    else if (lowerKey.includes('land') || lowerKey.includes('crop') || lowerKey.includes('farm') || lowerKey.includes('area') || lowerKey.includes('season')) {
      sections.agricultureInfo[key] = value
    }
    
    // Document metadata
    else if (lowerKey.includes('document') || lowerKey.includes('type') || lowerKey.includes('reference') || lowerKey.includes('authority') || lowerKey.includes('issue') || lowerKey.includes('date')) {
      sections.documentMeta[key] = value
    }
    
    // Default to document metadata for uncategorized fields
    else {
      sections.documentMeta[key] = value
    }
  })

  return sections
}
