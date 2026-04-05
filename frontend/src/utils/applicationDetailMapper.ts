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
      aiSummary: app.extractedData?.ai_summary || app.aiSummary || '',
      officerSummary: normalized.officerSummary || app.extractedData?.summary || app.extractedData?.ai_summary || app.extractedData?.llm_refinement?.refined_summary || 'Document processed. Review extracted details.',
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
 * Priority order (Part 10 - Updated for new pipeline):
 * 1. structured_data (PREFERRED) - from new unified extraction pipeline
 * 2. canonical schema (FALLBACK) - old structured format if present
 * 
 * Returns UI-friendly flat field structure for component consumption
 */
function normalizeExtractedFields(application: any): Record<string, any> {
  // PRIORITY: Use canonical schema first, structured_data only as fallback
  const canonicalData = application?.extractedData?.canonical
  if (canonicalData && typeof canonicalData === 'object' && Object.keys(canonicalData).length > 0) {
    const canonicalFields: Record<string, any> = {
      // Applicant information
      farmerName: canonicalData.applicant?.name || '',
      guardianName: canonicalData.applicant?.guardian_name || '',
      aadhaarNumber: canonicalData.applicant?.aadhaar_number || '',
      mobileNumber: canonicalData.applicant?.mobile_number || '',
      address: canonicalData.applicant?.address || '',
      village: canonicalData.applicant?.village || '',
      district: canonicalData.applicant?.district || '',
      state: canonicalData.applicant?.state || '',

      // Agriculture information
      landSize: canonicalData.agriculture?.land_size || '',
      landUnit: canonicalData.agriculture?.land_unit || '',
      surveyNumber: canonicalData.agriculture?.survey_number || '',
      cropName: canonicalData.agriculture?.crop_name || '',
      season: canonicalData.agriculture?.season || '',

      // Request information
      schemeName: canonicalData.request?.scheme_name || '',
      requestType: canonicalData.request?.request_type || '',
      requestedAmount: normalizeAmount(
        canonicalData.request?.requested_amount ||
        canonicalData.request?.claim_amount ||
        canonicalData.request?.subsidy_amount ||
        canonicalData.request?.amount ||
        canonicalData.requested_amount ||
        ''
      ),
      annualIncome: normalizeAmount(
        canonicalData.annual_income ||
        canonicalData.annualIncome ||
        canonicalData.request?.annual_income ||
        canonicalData.request?.annualIncome ||
        ''
      ),
      issueSummary: canonicalData.request?.issue_summary || '',
      claimReason: canonicalData.request?.claim_reason || '',

      // Document metadata
      documentType: canonicalData.document_meta?.supporting_doc_type || canonicalData.document_type || '',
      documentDate: canonicalData.document_meta?.document_date || '',
      referenceNumber: canonicalData.document_meta?.reference_number || '',
      sourceFileName: canonicalData.document_meta?.source_file_name || ''
    }

    return canonicalFields
  }

  // FALLBACK: structured_data from new extraction pipeline
  const structuredData = application?.extractedData?.structured_data
  if (structuredData && typeof structuredData === 'object' && Object.keys(structuredData).length > 0) {
    return {
      farmerName: structuredData.farmer_name || structuredData.applicant_name || '',
      aadhaarNumber: structuredData.aadhaar_number || '',
      mobileNumber: structuredData.mobile_number || structuredData.phone_number || '',
      address: structuredData.address || '',
      village: structuredData.village || '',
      district: structuredData.district || '',

      landSize: structuredData.land_size || structuredData.landSize || '',
      cropName: structuredData.crop_name || '',
      season: structuredData.season || '',

      schemeName: structuredData.scheme_name || '',
      requestedAmount: normalizeAmount(
        structuredData.requested_amount ||
        structuredData.claim_amount ||
        structuredData.subsidy_amount ||
        structuredData.amount ||
        ''
      ),
      annualIncome: normalizeAmount(structuredData.annual_income || structuredData.annualIncome || ''),
      claimReason: structuredData.claim_reason || structuredData.issue_description || structuredData.grievance_description || '',

      documentType: structuredData.document_type_detail || application.extractedData?.document_type || '',
      referenceNumber: structuredData.document_reference || '',

      policyNumber: structuredData.policy_number || '',
      issuesAuthority: structuredData.issuing_authority || ''
    }
  }

  // FINAL FALLBACK: Empty object if nothing available
  return {}

}

/**
 * Build structured extracted sections prioritizing canonical data.
 * Returns only validated, non-placeholder values and never returns raw backend objects.
 */
function buildCanonicalExtractedSections(application: any) {
  const canonical = application?.extractedData?.canonical || {}
  const structured = application?.extractedData?.structured_data || {}

  const src = (canonical && Object.keys(canonical).length > 0) ? canonical : structured || {}

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

  // Applicant
  const applicant = src.applicant || src || {}
  if (isValidString(applicant?.name || src.farmer_name || src.applicant_name)) {
    const name = applicant?.name || src.farmer_name || src.applicant_name
    if (String(name).trim().toLowerCase() !== 'supporting document') {
      sections.applicant['farmerName'] = String(name).trim()
    }
  }
  if (isValidString(applicant?.guardian_name)) sections.applicant['guardianName'] = applicant.guardian_name
  if (isValidAadhaar(applicant?.aadhaar_number || applicant?.aadhaar)) sections.applicant['aadhaarNumber'] = String(applicant?.aadhaar_number || applicant?.aadhaar).replace(/\D/g, '')
  if (isValidMobile(applicant?.mobile_number || applicant?.phone)) sections.applicant['mobileNumber'] = String(applicant?.mobile_number || applicant?.phone).trim()

  // Contact
  if (isValidString(applicant?.email || src.email)) sections.contact['email'] = applicant?.email || src.email
  if (isValidMobile(applicant?.mobile_number || src.mobile_number || src.phone_number)) sections.contact['mobile'] = applicant?.mobile_number || src.mobile_number || src.phone_number

  // Location
  if (isValidString(applicant?.address || src.address)) sections.location['address'] = applicant?.address || src.address
  if (isValidString(applicant?.village || src.village)) sections.location['village'] = applicant?.village || src.village
  if (isValidString(applicant?.district || src.district)) sections.location['district'] = applicant?.district || src.district
  if (isValidString(applicant?.state || src.state)) sections.location['state'] = applicant?.state || src.state

  // Financial
  if (isValidAmount(src.requested_amount || src.requestedAmount || (src.request && src.request.requested_amount))) sections.financial['requestedAmount'] = src.requested_amount || src.requestedAmount || (src.request && src.request.requested_amount)
  if (isValidAmount(src.annual_income || src.annualIncome)) sections.financial['annualIncome'] = src.annual_income || src.annualIncome

  // Agriculture
  if (isValidString(src.agriculture?.land_size || src.land_size || src.landSize)) sections.agriculture['landSize'] = src.agriculture?.land_size || src.land_size || src.landSize
  if (isValidString(src.agriculture?.land_unit || src.land_unit || src.landUnit)) sections.agriculture['landUnit'] = src.agriculture?.land_unit || src.land_unit || src.landUnit
  if (isValidString(src.agriculture?.crop_name || src.crop_name || src.cropName)) sections.agriculture['cropName'] = src.agriculture?.crop_name || src.crop_name || src.cropName
  if (isValidString(src.agriculture?.season || src.season)) sections.agriculture['season'] = src.agriculture?.season || src.season

  // Document
  if (isValidString(src.document_meta?.reference_number || src.reference_number || src.referenceNumber)) sections.document['referenceNumber'] = src.document_meta?.reference_number || src.reference_number || src.referenceNumber
  if (isValidString(src.document_meta?.document_date || src.documentDate)) sections.document['documentDate'] = src.document_meta?.document_date || src.documentDate
  if (isValidString(src.document_type || src.documentType)) sections.document['documentType'] = src.document_type || src.documentType

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
 * Helper function to normalize priority score to 0-100 range
 * CRITICAL FIX: Prevents 4000% display when priority_score = 40
 */
function normalizePriority(value: any): number {
  const n = Number(value || 0)
  if (!Number.isFinite(n)) return 0
  
  // If score is already in 0-100 range, return as-is
  // If score is 0-1 decimal, convert to 0-100
  // This prevents 40 -> 4000% bug
  return n <= 1 ? Math.round(n * 100) : Math.round(n)
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
    const aiSummary = application.extractedData?.ai_summary || application.aiSummary || ""
    // Officer summary: prefer explicit summary fields, then ai_summary, then llm refinement
    const officerSummaryRaw = application.extractedData?.summary || application.extractedData?.ai_summary || application.extractedData?.llm_refinement?.refined_summary
    const safeOfficerSummary = officerSummaryRaw || 'Document processed. Review extracted details.'

    // Build sanitized extracted sections (extractedFields already computed)
    const extractedSections = buildCanonicalExtractedSections(application)

    // Handle risk flags - convert string[] to object format if needed
    const rawRiskFlags = application.extractedData?.risk_flags || []
    const riskFlags = rawRiskFlags.map((flag: any) => 
      typeof flag === 'string' ? { message: flag } : flag
    )
    
    // Get decision support and intelligence data
    const decisionSupport = application.extractedData?.decision_support || null
    const summary = application.extractedData?.summary || application.extractedData?.ai_summary || ""  // Real intelligence summary
    
    // Get ML insights and predictions from backend contract
    const mlInsights = application.extractedData?.ml_insights || {}
    const predictions = application.extractedData?.predictions || {}
    
    // Frontend fail-safe defaults - prefer real intelligence summary over generic fallback
    const safeAiSummary = summary || aiSummary || ""  // Use real summary first, no generic fallback
    const safeRiskFlags = riskFlags || []
    const safeDecisionSupport = decisionSupport || null
    const safeCanonicalData = canonicalData || null

    // NEW: Single source normalization
    const displayApplicantName = getApplicantName(application)
    const displayStatus = application.status || 'unknown'
    const displayDocumentType = getDocumentTypeLabel(documentType)
    const priorityScoreNormalized = normalizePriority(application.priorityScore || mlInsights.priority_score || 0)
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
      officerSummary: safeOfficerSummary,
      priorityScore: application.priorityScore || 0,
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
      aiSummary: safeExtractedData?.ai_summary || rawApp.aiSummary || '',
      officerSummary: normalized.officerSummary || safeExtractedData?.summary || safeExtractedData?.ai_summary || 'Document processed. Review extracted details.',
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

  // Priority score normalization rule - FIXED to prevent 4000% bug
  const priorityScoreNormalized = normalizePriority(item.priorityScore || 0)

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
