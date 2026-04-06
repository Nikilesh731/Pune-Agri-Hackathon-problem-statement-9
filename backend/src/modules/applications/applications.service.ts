/**
 * Applications Service
 * Purpose: Business logic for application management
 */
import { applicationsRepository } from './applications.repository'
import { aiOrchestratorService } from '../ai-orchestrator/ai-orchestrator.service'
import { documentNormalizationService } from './documentNormalization.service'
import { Application, CreateApplicationInput, UpdateApplicationInput, ApplicationQuery, DuplicateCheckResult, CreateApplicationResponse, ApplicationVersionHistory } from './applications.types'
import { CaseService } from '../cases/cases.service'
import { supabase } from '../../config/supabase'

// Status mapping helper for valid Prisma enum values
// Part 9: Case-first workflow - documents go to case management first, not verification queue
function mapAiResultToApplicationStatus(
  aiResult: any,
  extractedData: any
): 'UPLOADED' | 'PROCESSING' | 'CASE_READY' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'REQUIRES_ACTION' {
  const resolvedExtractedData = extractedData || {};

  // Fields
  const missingFieldsArray: string[] = resolvedExtractedData?.missing_fields || [];
  const riskFlags: any[] = resolvedExtractedData?.risk_flags || aiResult.data?.riskFlags || [];

  // Decision support and ML insights
  const decisionSupport = resolvedExtractedData?.decision_support || aiResult.data?.decision_support || {};
  const aiDecision = (decisionSupport.decision || '').toString().toLowerCase();
  const mlQueue = (resolvedExtractedData?.ml_insights?.queue || aiResult.data?.ml_insights?.queue || resolvedExtractedData?.predictions?.queue || '').toString();

  // Fraud/risk signals
  const fraudRiskScore = Number(aiResult.data?.fraudRiskScore || 0);
  const highFraudRisk = fraudRiskScore > 0.7;
  const hasHighRisk = highFraudRisk || riskFlags.some((f: any) => (f?.severity || '').toString().toLowerCase() === 'high');

  // High priority ML tagging - FIXED: Check for VERIFICATION_QUEUE
  const needsVerificationQueue = mlQueue.toUpperCase() === 'VERIFICATION_QUEUE';

  // Resolve document type (best-effort)
  const rawDocType = (resolvedExtractedData?.canonical?.document_type || resolvedExtractedData?.document_type || '').toString().toLowerCase().trim();
  const docType = rawDocType.replace(/[-\s]+/g, '_');

  // Conservative list of critical fields (mirrors intelligence service rules)
  const GLOBAL_CRITICAL_FIELDS = new Set([
    'farmer_name', 'scheme_name', 'claim_type', 'policy_number', 'grievance_type',
    'aadhaar_number', 'mobile_number', 'requested_amount', 'claim_amount', 'subsidy_amount',
    'description', 'issue_description'
  ]);

  // Optionally extend by document-type-specific critical fields (keeps conservative default)
  const CRITICAL_BY_DOCTYPE: { [key: string]: string[] } = {
    // Add doc-type specific criticals here if needed in future
    // 'aadhaar_card': ['aadhaar_number', 'name', 'dob']
  };

  const criticalCandidates = new Set(GLOBAL_CRITICAL_FIELDS);
  if (CRITICAL_BY_DOCTYPE[docType]) {
    CRITICAL_BY_DOCTYPE[docType].forEach(f => criticalCandidates.add(f));
  }

  // hasCriticalMissing: any missing field that matches a known critical field
  const hasCriticalMissing = missingFieldsArray.some((mf: any) => {
    if (!mf) return false;
    const field = mf.toString().toLowerCase();
    if (criticalCandidates.has(field)) return true;
    // Also match when missing field contains a critical substring (e.g. canonical.applicant.aadhaar_number)
    for (const cf of criticalCandidates) {
      if (field.includes(cf)) return true;
    }
    return false;
  });

  // needsManualReview: explicit decisions that require human action
  const needsManualReview = ['review', 'manual_review', 'reject'].includes(aiDecision);

  // Routing rule: only truly problematic/high-risk/manual cases go to verification (UNDER_REVIEW)
  if (hasCriticalMissing || hasHighRisk || needsManualReview || needsVerificationQueue) {
    return 'UNDER_REVIEW';
  }

  // Otherwise: route into case-management flow (CASE_READY)
  return 'CASE_READY';
}

/**
 * Resolve display workflow state - Single source of truth for frontend status display
 * Priority logic for consistent status determination across the system
 */
export function resolveDisplayWorkflowState(application: any): {
  status: string,
  queue?: string,
  isUnderReview: boolean,
  isApproved: boolean,
  isRejected: boolean,
  isCaseReady: boolean
} {
  // Extract data with safe fallbacks
  const extractedData = application.extractedData || {}
  const mlInsights = extractedData.ml_insights || extractedData.predictions || {}
  const decisionSupport = extractedData.decision_support || {}
  const riskFlags = extractedData.risk_flags || []
  const missingFields = extractedData.missing_fields || []
  
  // Core conditions for UNDER_REVIEW status
  const isInVerificationQueue = application.queue === 'VERIFICATION_QUEUE' || mlInsights.queue === 'VERIFICATION_QUEUE'
  const needsManualReview = ['review', 'manual_review'].includes(decisionSupport.decision)
  const hasMissingFields = missingFields.length > 0
  const hasRiskFlags = riskFlags.length > 0
  
  // Priority logic as specified
  if (isInVerificationQueue || needsManualReview || hasMissingFields || hasRiskFlags) {
    return {
      status: 'UNDER_REVIEW',
      queue: application.queue || mlInsights.queue || 'NORMAL',
      isUnderReview: true,
      isApproved: false,
      isRejected: false,
      isCaseReady: false
    }
  }
  
  // Check for approved status
  if (application.status === 'APPROVED' || decisionSupport.decision === 'approve') {
    return {
      status: 'APPROVED',
      queue: application.queue || mlInsights.queue || 'NORMAL',
      isUnderReview: false,
      isApproved: true,
      isRejected: false,
      isCaseReady: false
    }
  }
  
  // Check for rejected status
  if (application.status === 'REJECTED' || decisionSupport.decision === 'reject') {
    return {
      status: 'REJECTED',
      queue: application.queue || mlInsights.queue || 'NORMAL',
      isUnderReview: false,
      isApproved: false,
      isRejected: true,
      isCaseReady: false
    }
  }
  
  // Default to CASE_READY
  return {
    status: 'CASE_READY',
    queue: application.queue || mlInsights.queue || 'NORMAL',
    isUnderReview: false,
    isApproved: false,
    isRejected: false,
    isCaseReady: true
  }
}

import crypto from 'crypto'

/**
 * Generate normalized content fingerprint from structured extracted data
 * Uses structured fields first, falls back to OCR text if needed
 */
function generateContentFingerprint(extractedData?: any): string | null {
  if (!extractedData || typeof extractedData !== 'object') {
    return null;
  }
  
  // PRIORITY 1: Use structured fields for fingerprinting
  const structured = extractedData.structured_data || {};
  const canonical = extractedData.canonical || {};
  
  // Build fingerprint from key identity and document fields
  const fingerprintFields = [];
  
  // Document type (critical for cross-format detection)
  const docType = extractedData.document_type || canonical.document_type || 'unknown';
  fingerprintFields.push(`type:${docType}`);
  
  // Identity fields (highest priority for duplicate detection)
  const aadhaar = structured.aadhaar_number || canonical.applicant?.aadhaar_number || canonical.applicant?.aadhaar || '';
  if (aadhaar) fingerprintFields.push(`aadhaar:${aadhaar.replace(/\s/g, '')}`);
  
  const name = structured.farmer_name || structured.applicant_name || canonical.applicant?.name || '';
  if (name) fingerprintFields.push(`name:${name.toLowerCase().replace(/\s+/g, ' ')}`);
  
  const mobile = structured.mobile_number || canonical.applicant?.mobile_number || canonical.applicant?.mobile || '';
  if (mobile) fingerprintFields.push(`mobile:${mobile.replace(/\D/g, '')}`);
  
  // Document-specific fields
  const scheme = structured.scheme_name || canonical.request?.scheme_name || '';
  if (scheme) fingerprintFields.push(`scheme:${scheme.toLowerCase().replace(/\s+/g, ' ')}`);
  
  const claimType = structured.claim_type || canonical.request?.request_type || '';
  if (claimType) fingerprintFields.push(`claim:${claimType.toLowerCase().replace(/\s+/g, ' ')}`);
  
  const amount = structured.requested_amount || structured.claim_amount || structured.subsidy_amount || canonical.request?.requested_amount || '';
  if (amount) {
    const cleanAmount = amount.toString().replace(/[^\d.]/g, '');
    if (cleanAmount) fingerprintFields.push(`amount:${cleanAmount}`);
  }
  
  // If we have enough structured fields, use them for fingerprint
  if (fingerprintFields.length >= 3) {
    const structuredFingerprint = fingerprintFields.join('|');
    return crypto.createHash('sha256').update(structuredFingerprint).digest('hex').substring(0, 64);
  }
  
  // PRIORITY 2: Fallback to raw OCR text if structured fields are insufficient
  const ocrText = extractedData.raw_text || extractedData.ocrText || '';
  if (ocrText && typeof ocrText === 'string') {
    // Normalize OCR text for fingerprinting
    const normalized = ocrText
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .replace(/\n\s*\n/g, '\n')
      .replace(/[^\w\s]/g, '')
      .trim();
    
    if (normalized.length >= 50) {
      return crypto.createHash('sha256').update(normalized).digest('hex').substring(0, 64);
    }
  }
  
  // PRIORITY 3: If nothing is sufficient, return null
  return null;
}

/**
 * Check if application status allows resubmission
 */
function allowsResubmission(status: string): boolean {
  const normalizedStatus = status.toLowerCase().replace(/[-\s]/g, '_');
  return ['approved', 'rejected', 'requires_action', 'needs_correction'].includes(normalizedStatus);
}

/**
 * Check if application status is active (blocks duplicates)
 */
function isActiveStatus(status: string): boolean {
  const normalizedStatus = status.toLowerCase().replace(/[-\s]/g, '_');
  return ['uploaded', 'processing', 'under_review', 'case_ready', 'pending'].includes(normalizedStatus);
}

/**
 * Normalize extractedData contract before persistence
 * Ensures canonical.document_type is populated and contract structure is stable
 */
function normalizeExtractedDataContract(extractedData: any): any {
  if (!extractedData || typeof extractedData !== 'object') {
    return extractedData;
  }

  // Create a deep copy to avoid mutation
  const normalized = JSON.parse(JSON.stringify(extractedData));

  // Ensure top-level document_type is preserved
  const topLevelDocType = normalized.document_type || 'unknown';

  // Ensure canonical exists and has proper structure
  if (!normalized.canonical || typeof normalized.canonical !== 'object') {
    normalized.canonical = {};
  }

  // CRITICAL: Ensure canonical.document_type is populated when document_type is known
  if (!normalized.canonical.document_type && topLevelDocType !== 'unknown') {
    normalized.canonical.document_type = topLevelDocType;
  }

  // Ensure canonical has stable object structure
  const canonicalStructure = {
    document_type: normalized.canonical.document_type || topLevelDocType,
    document_category: normalized.canonical.document_category || 'unknown',
    applicant: {
      name: normalized.canonical.applicant?.name || '',
      guardian_name: normalized.canonical.applicant?.guardian_name || '',
      aadhaar_number: normalized.canonical.applicant?.aadhaar_number || normalized.canonical.applicant?.aadhaar || '',
      mobile_number: normalized.canonical.applicant?.mobile_number || normalized.canonical.applicant?.mobile || '',
      address: normalized.canonical.applicant?.address || '',
      village: normalized.canonical.applicant?.village || '',
      district: normalized.canonical.applicant?.district || '',
      state: normalized.canonical.applicant?.state || ''
    },
    agriculture: {
      land_size: normalized.canonical.agriculture?.land_size || '',
      land_unit: normalized.canonical.agriculture?.land_unit || '',
      survey_number: normalized.canonical.agriculture?.survey_number || '',
      crop_name: normalized.canonical.agriculture?.crop_name || '',
      season: normalized.canonical.agriculture?.season || '',
      location: normalized.canonical.agriculture?.location || ''
    },
    request: {
      scheme_name: normalized.canonical.request?.scheme_name || '',
      request_type: normalized.canonical.request?.request_type || '',
      requested_amount: normalized.canonical.request?.requested_amount || '',
      issue_summary: normalized.canonical.request?.issue_summary || '',
      claim_reason: normalized.canonical.request?.claim_reason || ''
    },
    document_meta: {
      document_date: normalized.canonical.document_meta?.document_date || '',
      reference_number: normalized.canonical.document_meta?.reference_number || '',
      supporting_doc_type: normalized.canonical.document_meta?.supporting_doc_type || '',
      source_file_name: normalized.canonical.document_meta?.source_file_name || ''
    },
    verification: {
      missing_fields: Array.isArray(normalized.canonical.verification?.missing_fields) 
        ? normalized.canonical.verification.missing_fields 
        : [],
      field_confidences: normalized.canonical.verification?.field_confidences || {},
      extraction_confidence: normalized.canonical.verification?.extraction_confidence || 0,
      validation_errors: Array.isArray(normalized.canonical.verification?.validation_errors) 
        ? normalized.canonical.verification.validation_errors 
        : [],
      recommendation: normalized.canonical.verification?.recommendation || '',
      reasoning: Array.isArray(normalized.canonical.verification?.reasoning) 
        ? normalized.canonical.verification.reasoning 
        : []
    }
  };

  // Merge with existing canonical data, preserving any additional fields
  normalized.canonical = {
    ...canonicalStructure,
    ...normalized.canonical,
    applicant: { ...canonicalStructure.applicant, ...normalized.canonical.applicant },
    agriculture: { ...canonicalStructure.agriculture, ...normalized.canonical.agriculture },
    request: { ...canonicalStructure.request, ...normalized.canonical.request },
    document_meta: { ...canonicalStructure.document_meta, ...normalized.canonical.document_meta },
    verification: { ...canonicalStructure.verification, ...normalized.canonical.verification }
  };

  // Ensure other top-level fields have proper defaults
  normalized.structured_data = normalized.structured_data || {};
  normalized.extracted_fields = normalized.extracted_fields || {};
  normalized.missing_fields = Array.isArray(normalized.missing_fields) ? normalized.missing_fields : [];
  normalized.confidence = normalized.confidence || 0;
  normalized.reasoning = Array.isArray(normalized.reasoning) ? normalized.reasoning : [];

  return normalized;
}

class ApplicationsService {
  private caseService: CaseService;

  constructor() {
    this.caseService = new CaseService();
  }

  /**
   * Helper: Normalize status to lowercase snake_case for consistent comparison
   */
  private normalizeStatus(status?: string): string {
    if (!status) return '';
    return status.toLowerCase().replace(/[-\s]/g, '_');
  }

  /**
   * Helper: Resolve actual document type from extracted data or application
   */
  private resolveActualDocumentType(appLike: any): string | undefined {
    // Helper function to normalize document type
    const normalizeDocType = (docType: string): string => {
      return docType.toLowerCase().trim().replace(/[-\s]+/g, '_');
    };

    // Try extractedData.canonical.document_type first (highest priority)
    if (appLike.extractedData?.canonical?.document_type) {
      return normalizeDocType(appLike.extractedData.canonical.document_type);
    }
    
    // Then extractedData.document_type
    if (appLike.extractedData?.document_type) {
      return normalizeDocType(appLike.extractedData.document_type);
    }
    
    // Finally app.type (fallback)
    if (appLike.type) {
      return normalizeDocType(appLike.type);
    }
    
    return undefined;
  }

  /**
   * Helper: Resolve extracted contract from AI response with strict validation
   */
  private resolveExtractedContractFromAiResponse(aiResponse: any): any {
    // Allowed candidate paths only
    const candidates = [
      aiResponse?.data?.extractedData,
      aiResponse?.data?.data?.extractedData,
      aiResponse?.data?.result?.extractedData,
      aiResponse?.data?.processedData?.extractedData,
      aiResponse?.data?.payload?.extractedData,
      aiResponse?.data?.output?.extractedData,
      aiResponse?.data?.documentProcessingResult?.extractedData,
      aiResponse?.result?.extractedData,
      aiResponse?.extractedData
    ];

    // Check each candidate for valid extracted contract shape
    for (const candidate of candidates) {
      if (candidate && typeof candidate === 'object') {
        // Valid if has at least one of these required fields
        if (
          candidate.document_type ||
          candidate.canonical ||
          candidate.structured_data ||
          candidate.extracted_fields
        ) {
          return candidate;
        }
      }
    }

    // Check direct aiResponse.data ONLY if it has valid shape
    if (aiResponse?.data && typeof aiResponse.data === 'object') {
      const directData = aiResponse.data;
      if (
        directData.document_type ||
        directData.canonical ||
        directData.structured_data ||
        directData.extracted_fields
      ) {
        return directData;
      }
    }

    // No valid extracted contract found
    return null;
  }

  /**
   * Helper: Resolve farmer identity from extracted data for preflight
   */
  private async resolveFarmerFromExtractedDataForPreflight(extractedData: any): Promise<{ id: string } | null> {
    try {
      // Canonical applicant first
      const canonical = extractedData?.canonical || {};
      const applicant = canonical.applicant || {};
      
      // Fallback to structured data
      const structuredApplicant = this.mapStructuredToApplicant(extractedData?.structured_data);
      
      // Use canonical first, then fallback
      const finalApplicant = {
        name: applicant.name || structuredApplicant?.name,
        aadhaar_number: applicant.aadhaar_number || applicant.aadhaar || structuredApplicant?.aadhaar_number,
        mobile_number: applicant.mobile_number || applicant.mobile || structuredApplicant?.mobile_number,
        address: applicant.address || structuredApplicant?.address,
        village: applicant.village || structuredApplicant?.village,
        district: applicant.district || structuredApplicant?.district,
        state: applicant.state || structuredApplicant?.state
      };
      
      // If no Aadhaar and no mobile, return null (don't create weak anonymous farmer)
      if (!finalApplicant.aadhaar_number && !finalApplicant.mobile_number) {
        console.log('[PRECHECK] No Aadhaar or mobile found in extracted data - cannot resolve farmer');
        return null;
      }
      
      // Use existing resolveFarmerFromCanonical logic
      return await this.resolveFarmerFromCanonical(finalApplicant);
      
    } catch (error) {
      console.error('[PRECHECK] Error resolving farmer from extracted data:', error);
      return null;
    }
  }

  /**
   * REMOVED - Use checkStrictDuplicate only
   * This method is replaced by the authoritative file-hash based duplicate check
   */

  /**
   * UNIFIED DUPLICATE CHECK - Cross-format detection with content signatures
   */
  async checkUnifiedDuplicate(params: {
    fileHash: string
    contentHash?: string
    fileName: string
    fileSize: number
    applicantId: string
    normalizedDocument?: any
    extractedData?: any
  }): Promise<{
    isDuplicate: boolean
    canResubmit: boolean
    existingApplicationId?: string
    existingStatus?: string
    blockReason?: string
    duplicateType?: 'exact_file' | 'same_content'
  }> {
    const { fileHash, contentHash, fileName, fileSize, applicantId, normalizedDocument, extractedData } = params
    
    console.log('[DUP] starting unified duplicate detection')
    console.log('[DUP] file hash:', fileHash.substring(0, 16) + '...')
    if (contentHash) {
      console.log('[DUP] content hash:', contentHash.substring(0, 16) + '...')
    }

    try {
      // LEVEL 1: Exact file hash match (highest confidence)
      const exactMatches = await applicationsRepository.findApplicationsByRawFileHash(fileHash)
      
      if (exactMatches.length > 0) {
        const latestMatch = exactMatches[0]
        console.log('[DUP] exact duplicate found')
        
        const isActive = isActiveStatus(latestMatch.status)
        const canResubmit = allowsResubmission(latestMatch.status)

        if (isActive) {
          console.log('[DUP] blocked - exact duplicate active')
          return {
            isDuplicate: true,
            canResubmit: false,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status,
            blockReason: 'Duplicate document already under processing',
            duplicateType: 'exact_file'
          }
        } else if (canResubmit) {
          console.log('[DUP] resubmission allowed - exact duplicate in resubmittable state')
          return {
            isDuplicate: true,
            canResubmit: true,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status,
            duplicateType: 'exact_file'
          }
        }
      }

      // LEVEL 2: Content hash match (cross-format duplicate detection)
      // FIXED: Run content-based duplicate check whenever contentHash is available
      // Do NOT require normalizedDocument just to perform the DB lookup
      if (contentHash) {
        const contentMatches = await applicationsRepository.findApplicationsByNormalizedContentHash(contentHash)
        
        if (contentMatches.length > 0) {
          const latestMatch = contentMatches[0]
          console.log('[DUP] same-content duplicate found')
          
          const isActive = isActiveStatus(latestMatch.status)
          const canResubmit = allowsResubmission(latestMatch.status)

          if (isActive) {
            console.log('[DUP] blocked - same content duplicate active')
            return {
              isDuplicate: true,
              canResubmit: false,
              existingApplicationId: latestMatch.id,
              existingStatus: latestMatch.status,
              blockReason: 'This upload matches the content of an existing application of the same document type that is still active. Re-upload is only allowed if clarification or officer-requested changes were issued.',
              duplicateType: 'same_content'
            }
          } else if (canResubmit) {
            console.log('[DUP] resubmission allowed - same content duplicate in resubmittable state')
            return {
              isDuplicate: true,
              canResubmit: true,
              existingApplicationId: latestMatch.id,
              existingStatus: latestMatch.status,
              duplicateType: 'same_content'
            }
          }
        }
      }

      // LEVEL 3: Semantic duplicate detection (same farmer + similar data)
      // Only run if we have extracted data to analyze
      if (extractedData && (extractedData.structured_data || extractedData.canonical)) {
        const semanticMatch = await this._checkSemanticDuplicate(extractedData, applicantId)
        
        if (semanticMatch.isDuplicate) {
          const latestMatch = semanticMatch.existingApplication
          console.log('[DUP] semantic duplicate found - same farmer + similar data')
          
          const isActive = isActiveStatus(latestMatch.status)
          const canResubmit = allowsResubmission(latestMatch.status)

          if (isActive) {
            console.log('[DUP] blocked - semantic duplicate active')
            return {
              isDuplicate: true,
              canResubmit: false,
              existingApplicationId: latestMatch.id,
              existingStatus: latestMatch.status,
              blockReason: 'Similar document from the same farmer already under processing',
              duplicateType: 'same_content'
            }
          } else if (canResubmit) {
            console.log('[DUP] resubmission allowed - semantic duplicate in resubmittable state')
            return {
              isDuplicate: true,
              canResubmit: true,
              existingApplicationId: latestMatch.id,
              existingStatus: latestMatch.status,
              duplicateType: 'same_content'
            }
          }
        }
      }

      // LEVEL 4: Fallback filename+size check (legacy compatibility)
      const filenameMatches = await applicationsRepository.findApplicationsByFileNameAndSize(
        fileName,
        fileSize,
        applicantId
      )
      
      if (filenameMatches.length > 0) {
        const latestMatch = filenameMatches[0]
        console.log('[DUP] filename+size fallback match:', latestMatch.id)

        const isActive = isActiveStatus(latestMatch.status)
        const canResubmit = allowsResubmission(latestMatch.status)

        if (isActive) {
          console.log('[DUP] blocked - filename+size duplicate active')
          return {
            isDuplicate: true,
            canResubmit: false,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status,
            blockReason: 'Same filename and size with active application',
            duplicateType: 'exact_file'
          }
        } else if (canResubmit) {
          console.log('[DUP] resubmission allowed - filename+size duplicate in resubmittable state')
          return {
            isDuplicate: true,
            canResubmit: true,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status,
            duplicateType: 'exact_file'
          }
        }
      }

      console.log('[DUP] no duplicates found - allowing new upload')
      return {
        isDuplicate: false,
        canResubmit: false,
        duplicateType: undefined
      }

    } catch (error) {
      console.error('[DUP] error during unified duplicate check:', error)
      // On error, allow upload but don't block
      return {
        isDuplicate: false,
        canResubmit: false,
        duplicateType: undefined
      }
    }
  }

  /**
   * REMOVED - Preflight duplicate checking is deprecated
   * Use checkStrictDuplicate before file upload instead
   */
  async preflightUploadCheck(params: {
    fileUrl: string
    fileName?: string
    fileType?: string
    applicantId?: string
  }) {
    console.log('[PRECHECK] DEPRECATED - Use checkStrictDuplicate instead');
    
    // Return neutral result - this method should not be used
    return {
      extractedData: null,
      resolvedDocumentType: undefined,
      resolvedFarmerId: null,
      duplicate: {
        isDuplicate: false,
        canResubmit: false
      }
    };
  }

  /**
   * Delete all applications for local test reset
   */
  async deleteAllApplications(): Promise<{ deletedCount: number; errors?: string[] }> {
    console.log('[DELETE ALL] Starting complete application cleanup');
    
    try {
      const result = await applicationsRepository.deleteAllApplications();
      
      console.log('[DELETE ALL] Cleanup completed:', {
        deletedCount: result.deletedCount,
        errors: result.errors
      });
      
      return result;
    } catch (error) {
      console.error('[DELETE ALL] Critical error during cleanup:', error);
      throw new Error(`Failed to delete all applications: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async createApplication(applicationData: CreateApplicationInput): Promise<CreateApplicationResponse> {
    console.log(`[CREATE APP] Starting application creation`);
    
    // PART 1: RESOLVE HASHES FOR DUPLICATE DETECTION
    const rawFileHash = (applicationData as any).rawFileHash || (applicationData as any).fileHash;
    
    if (!rawFileHash) {
      throw new Error('Raw file hash is required for duplicate detection');
    }
    
    // PART 2: GENERATE PRE-CREATE CONTENT HASH WHEN POSSIBLE
    // PRIORITY A: Use existing normalizedContentHash if available
    let preCreateContentHash = (applicationData as any).normalizedContentHash;
    
    // PRIORITY B: Generate from extractedData if available and no existing hash
    if (!preCreateContentHash && (applicationData as any).extractedData) {
      const extractedData = (applicationData as any).extractedData;
      
      // Normalize contract first to ensure stable structure
      const normalizedExtractedData = normalizeExtractedDataContract(extractedData);
      
      // Generate content fingerprint from normalized data
      preCreateContentHash = generateContentFingerprint(normalizedExtractedData);
      
      if (preCreateContentHash) {
        console.log('[NORMALIZATION] content hash generated from pre-create extractedData');
      }
    }
    
    // PRIORITY C: If no structured data available, keep preCreateContentHash as null
    // Exact file duplicate detection will still work
    
    // PART 3: UNIFIED DUPLICATE DETECTION WITH AVAILABLE HASHES
    const duplicateCheck = await this.checkUnifiedDuplicate({
      fileHash: rawFileHash,
      contentHash: preCreateContentHash,
      fileName: applicationData.fileName || 'unknown',
      fileSize: applicationData.fileSize || 0,
      applicantId: applicationData.applicantId,
      extractedData: (applicationData as any).extractedData
    });
    
    // Handle duplicate blocking
    if (duplicateCheck.isDuplicate && !duplicateCheck.canResubmit) {
      console.log('[DUP] BLOCKED -', duplicateCheck.blockReason, {
        existingApplicationId: duplicateCheck.existingApplicationId,
        existingStatus: duplicateCheck.existingStatus,
        duplicateType: duplicateCheck.duplicateType
      });
      
      const error = new Error(duplicateCheck.blockReason || 'Duplicate document detected');
      (error as any).statusCode = 409;
      (error as any).code = 'DUPLICATE_BLOCKED';
      (error as any).existingApplicationId = duplicateCheck.existingApplicationId;
      (error as any).existingStatus = duplicateCheck.existingStatus;
      (error as any).duplicateType = duplicateCheck.duplicateType;
      throw error;
    }
    
    // Handle allowed resubmission
    if (duplicateCheck.isDuplicate && duplicateCheck.canResubmit && duplicateCheck.existingApplicationId) {
      const existingApp = await applicationsRepository.getApplicationById(duplicateCheck.existingApplicationId);
      if (existingApp) {
        console.log('[RE-UPLOAD] ALLOWED -', {
          existingApplicationId: existingApp.id,
          existingStatus: existingApp.status,
          existingVersion: existingApp.versionNumber,
          duplicateType: duplicateCheck.duplicateType
        });
        
        // Create NEW application with version chain
        const reuploadData = {
          ...applicationData,
          versionNumber: existingApp.versionNumber + 1,
          parentApplicationId: existingApp.id,
          isReupload: true
        };
        
        const application = await applicationsRepository.createApplication({
          ...reuploadData,
          aiProcessingStatus: 'pending',
          farmerId: applicationData.farmerId ?? null,
          rawFileHash: rawFileHash,
          normalizedContentHash: preCreateContentHash,
          notes: `Re-upload version ${reuploadData.versionNumber} of application ${existingApp.id} (${duplicateCheck.duplicateType})`,
          personalInfo: applicationData.personalInfo || {
            firstName: '',
            lastName: '',
            email: '',
            phone: '',
            dateOfBirth: new Date(),
            address: {
              street: '',
              city: '',
              district: '',
              state: '',
              pincode: ''
            }
          }
        });
        
        console.log(`[RE-UPLOAD] Created version ${reuploadData.versionNumber}: ${application.id}`);
        
        // Trigger AI processing ASYNCHRONOUSLY
        this.triggerAIProcessingAsync(application.id)
          .then(() => {
            console.log(`[ASYNC AI] Background processing completed for re-upload: ${application.id}`);
          })
          .catch((error: any) => {
            console.error(`[ASYNC AI] Background processing failed for re-upload: ${application.id}`, error);
          });
        
        return {
          success: true,
          application: application,
          status: 'reupload_allowed',
          message: `Re-upload detected (Version ${reuploadData.versionNumber})`,
          isReupload: true,
          parentApplicationId: existingApp.id
        };
      }
    }
    
    // NORMAL NEW APPLICATION (no duplicates found)
    console.log('[NEW] No duplicates found - creating new application');
    
    const application = await applicationsRepository.createApplication({
      ...applicationData,
      aiProcessingStatus: 'pending',
      versionNumber: applicationData.versionNumber ?? 1,
      parentApplicationId: applicationData.parentApplicationId ?? null,
      farmerId: applicationData.farmerId ?? null,
      rawFileHash: rawFileHash,
      normalizedContentHash: preCreateContentHash,
      notes: 'Application submitted - processing in background',
      personalInfo: applicationData.personalInfo || {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        dateOfBirth: new Date(),
        address: {
          street: '',
          city: '',
          district: '',
          state: '',
          pincode: ''
        }
      }
    });
    
    console.log(`[CREATE APP] Initial application created: ${application.id}`);
    
    // Trigger AI processing ASYNCHRONOUSLY
    this.triggerAIProcessingAsync(application.id)
      .then(() => {
        console.log(`[ASYNC AI] Background processing completed for application: ${application.id}`);
      })
      .catch((error: any) => {
        console.error(`[ASYNC AI] Background processing failed for application: ${application.id}`, error);
      });
    
    // Return immediately
    return {
      success: true,
      application: application,
      status: 'created',
      message: 'Application submitted successfully - processing in background'
    };
  }

  async getApplications(query: ApplicationQuery): Promise<{ applications: Application[], total: number }> {
    return await applicationsRepository.getApplications(query)
  }

  async getApplicationById(id: string): Promise<Application> {
    const response = await applicationsRepository.getApplicationById(id)
    if (!response) {
      throw new Error(`Application with id ${id} not found`);
    }
    
    // Include case metadata if available
    if (response.caseId) {
      try {
        const caseSummary = await this.caseService.getCaseSummary(response.caseId);
        if (caseSummary) {
          (response as any).case = caseSummary;
        }

        // Add case history (NEW)
        const caseHistory = await this.caseService.getCaseHistoryForApplication(id);
        (response as any).case_history = caseHistory;
        
      } catch (error) {
        console.error(`Error fetching case metadata:`, error);
      }
    }
    return response
  }

  async approveApplication(id: string): Promise<Application> {
    const application = await this.getApplicationById(id)
    
    // Validate status transition
    this.validateStatusTransition(id, 'APPROVED');
    
    return await applicationsRepository.updateApplication(id, {
      status: 'APPROVED',
      decisionDate: new Date(),
      reviewDate: new Date(),
      aiProcessingStatus: 'completed'
    })
  }

  async rejectApplication(id: string): Promise<Application> {
    const application = await this.getApplicationById(id)
    
    // Validate status transition
    this.validateStatusTransition(id, 'REJECTED');
    
    return await applicationsRepository.updateApplication(id, {
      status: 'REJECTED',
      decisionDate: new Date(),
      reviewDate: new Date(),
      aiProcessingStatus: 'completed'
    })
  }

  async requestClarification(id: string): Promise<Application> {
    const application = await this.getApplicationById(id)
    
    // Validate status transition
    this.validateStatusTransition(id, 'REQUIRES_ACTION');
    
    return await applicationsRepository.updateApplication(id, {
      status: 'REQUIRES_ACTION',
      reviewDate: new Date()
    })
  }

  async reprocessWithAI(id: string): Promise<Application> {
    console.log(`[REPROCESS] Starting AI reprocess for application: ${id}`)
    
    const application = await this.getApplicationById(id)
    
    // Update status to processing
    await applicationsRepository.updateApplication(id, {
      aiProcessingStatus: 'processing'
    })
    
    // Trigger AI processing and WAIT for completion
    try {
      await this.triggerAIProcessing(id)
      console.log(`[REPROCESS] AI processing completed successfully`)
    } catch (error) {
      console.error(`[REPROCESS] AI processing failed:`, error)
      // If AI processing fails, update status
      await applicationsRepository.updateApplication(id, {
        aiProcessingStatus: 'failed',
        status: 'CASE_READY',
        notes: error instanceof Error ? error.message : 'AI reprocessing failed'
      })
    }
    
    // Return the fully updated application
    return await this.getApplicationById(id)
  }

  private async triggerAIProcessingAsync(applicationId: string): Promise<void> {
    console.log("[AI] Started:", applicationId);
    
    try {
      // Get application details
      const application = await applicationsRepository.getApplicationById(applicationId);
      if (!application?.fileUrl) {
        console.warn("[AI SKIP] No fileUrl found for application, skipping AI processing");
        return;
      }
      
      // Convert stored file path to public Supabase URL
      const filePath = application.fileUrl;
      console.log("[AI FILE URL] object path:", filePath);
      
      const { data: publicUrlData } = supabase.storage
        .from('documents')
        .getPublicUrl(filePath);
      
      const publicUrl = publicUrlData.publicUrl;
      console.log("[AI FILE URL] public url:", publicUrl);
      
      // CRITICAL GUARD: Validate fileUrl before AI processing
      // This prevents the duplicate call issue where fileUrl = null
      if (!publicUrl || typeof publicUrl !== "string" || !publicUrl.trim()) {
        console.warn("[AI SKIP] Missing or invalid fileUrl, skipping AI document-processing call");
        console.warn("[AI SKIP] This prevents 'No OCR text available' errors from overwriting success");
        return;
      }
      
      // DEBUG LOGGING: Log AI call details
      console.log("[AI CALL] applicationId:", applicationId);
      console.log("[AI CALL] fileUrl:", publicUrl);
      console.log("[AI CALL] fileName:", application.fileName);
      console.log("[AI CALL] fileType:", application.fileType);
      
      // Call AI orchestrator with public URL
      const aiResponse = await aiOrchestratorService.processDocument({
        fileUrl: publicUrl,
        fileName: application.fileName,
        fileType: application.fileType
      });
      
      if (!aiResponse?.success) {
        throw new Error(aiResponse?.error || 'AI processing failed');
      }
      
      // Extract data using SAFE resolver
      const extractedContract = this.resolveExtractedContractFromAiResponse(aiResponse);
      
      // Ensure extractedData is never null
      let extractedData = extractedContract;
      
      if (!extractedData) {
        extractedData = {
          document_type: "unknown",
          structured_data: {},
          extracted_fields: {},
          missing_fields: [],
          confidence: 0,
          reasoning: ["AI processing failed"],
          canonical: {
            document_type: "unknown",
            document_category: "unknown",
            applicant: {
              name: "",
              guardian_name: "",
              aadhaar_number: "",
              mobile_number: "",
              address: "",
              village: "",
              district: "",
              state: ""
            },
            agriculture: {
              land_size: "",
              land_unit: "",
              survey_number: "",
              crop_name: "",
              season: "",
              location: ""
            },
            request: {
              scheme_name: "",
              request_type: "",
              requested_amount: "",
              issue_summary: "",
              claim_reason: ""
            },
            document_meta: {
              document_date: "",
              reference_number: "",
              supporting_doc_type: "",
              source_file_name: ""
            },
            verification: {
              missing_fields: [],
              field_confidences: {},
              extraction_confidence: 0,
              validation_errors: [],
              recommendation: "",
              reasoning: ["AI processing failed"]
            }
          }
        }
      }

      // Resolve farmer (same as sync path)
      let farmerId = null;
      const applicant = extractedData?.canonical?.applicant || this.mapStructuredToApplicant(extractedData?.structured_data);
      
      if (applicant && (applicant.name || applicant.aadhaar_number || applicant.mobile_number)) {
        try {
          const resolvedFarmer = await this.resolveFarmerFromCanonical(applicant);
          if (resolvedFarmer) {
            farmerId = resolvedFarmer.id;
          }
        } catch (error) {
          console.error(`[ASYNC AI] Error resolving farmer:`, error);
        }
      }
      
      // Determine final status (same as sync path)
      const finalStatus = mapAiResultToApplicationStatus(aiResponse, extractedData);
      
      // Update application with results (including farmerId)
      const updateData: UpdateApplicationInput = {
        extractedData,
        farmerId: farmerId || undefined,
        status: finalStatus,
        aiProcessingStatus: extractedData.document_type === "unknown" ? "failed" : "completed",
        aiProcessedAt: new Date(),
        priorityScore: aiResponse.data?.priorityScore || 0,
        fraudRiskScore: aiResponse.data?.fraudRiskScore || 0,
        fraudFlags: aiResponse.data?.fraudFlags || [],
        verificationRecommendation: aiResponse.data?.verificationRecommendation,
        aiSummary: aiResponse.data?.aiSummary || aiResponse.data?.extractedData?.ai_summary || aiResponse.data?.extractedData?.summary || `Document processed as ${extractedData?.document_type || 'unknown'}. Review extracted fields for verification.`
      };
      
      // FAULT TOLERANCE: Preserve successful extraction even if optional downstream fails
      // Only update fields that succeeded, never overwrite with failure data
      const faultTolerantUpdate: any = {
        extractedData, // Always preserve if we have it
        farmerId: farmerId || undefined,
        status: finalStatus,
        aiProcessedAt: new Date()
      };

      // CRITICAL: Include normalizedContentHash in fault-tolerant update
      const fingerprint = generateContentFingerprint(extractedData);
      if (fingerprint) {
        faultTolerantUpdate.normalizedContentHash = fingerprint;
        console.log('[NORMALIZATION] Generated and persisted content hash:', fingerprint.substring(0, 16) + '...');
      }

      // Only add optional fields if they succeeded
      if (aiResponse.data?.priorityScore !== undefined) {
        faultTolerantUpdate.priorityScore = aiResponse.data.priorityScore;
      }
      if (aiResponse.data?.fraudRiskScore !== undefined) {
        faultTolerantUpdate.fraudRiskScore = aiResponse.data.fraudRiskScore;
      }
      if (aiResponse.data?.fraudFlags) {
        faultTolerantUpdate.fraudFlags = aiResponse.data.fraudFlags;
      }
      if (aiResponse.data?.verificationRecommendation) {
        faultTolerantUpdate.verificationRecommendation = aiResponse.data.verificationRecommendation;
      }
      if (aiResponse.data?.aiSummary || aiResponse.data?.extractedData?.ai_summary || aiResponse.data?.extractedData?.summary) {
        faultTolerantUpdate.aiSummary = aiResponse.data.aiSummary || aiResponse.data.extractedData?.ai_summary || aiResponse.data.extractedData?.summary || `Document processed as ${extractedData?.document_type || 'unknown'}. Review extracted fields for verification.`;
      }

      // Set AI processing status based on extraction success, not optional downstream
      faultTolerantUpdate.aiProcessingStatus = extractedData.document_type === "unknown" ? "failed" : "completed";
      
      await this.updateApplication(applicationId, faultTolerantUpdate);
      
      console.log('[AI FAULT TOLERANCE] Applied fault-tolerant update:', {
        hasExtractedData: !!extractedData,
        hasPriorityScore: aiResponse.data?.priorityScore !== undefined,
        hasFraudData: aiResponse.data?.fraudRiskScore !== undefined,
        hasSummary: !!faultTolerantUpdate.aiSummary,
        finalStatus: faultTolerantUpdate.aiProcessingStatus
      });
      
      // Resolve case if needed using shared resolved document type (same as sync path)
      if (farmerId) {
        try {
          const resolvedDocumentType = this.resolveActualDocumentType({ extractedData, type: application.type });
          if (resolvedDocumentType) {
            await this.caseService.resolveCase({
              applicationId,
              farmerId,
              documentType: resolvedDocumentType
            });
          }
        } catch (caseError) {
          console.error(`[ASYNC AI] Error resolving case:`, caseError);
        }
      }
      
      console.log("[AI] Completed:", applicationId);
      
    } catch (error) {
      console.error("[AI] Failed:", applicationId, error);
      
      // CRITICAL PROTECTION: Check if we already have valid extractedData
      // If so, DO NOT overwrite it with failure data
      const existingApplication = await applicationsRepository.getApplicationById(applicationId);
      const existingExtractedData = existingApplication?.extractedData;
      
      // Check if existing data is valid (has meaningful content)
      const hasValidExistingData = existingExtractedData && (
        (existingExtractedData.canonical && Object.keys(existingExtractedData.canonical).length > 0) ||
        (existingExtractedData.structured_data && Object.keys(existingExtractedData.structured_data).length > 0) ||
        (existingExtractedData.document_type && existingExtractedData.document_type !== "unknown")
      );
      
      if (hasValidExistingData) {
        console.warn("[AI PROTECTION] Valid extractedData exists, NOT overwriting with failure");
        console.warn("[AI PROTECTION] This prevents successful extraction from being lost");
        
        // Only update status, not the extractedData
        await this.updateApplication(applicationId, {
          aiProcessingStatus: "failed",
          aiProcessedAt: new Date()
        });
      } else {
        console.log("[AI PROTECTION] No valid existing data, setting failure state");
        
        // Only set failure data if no valid data exists
        await this.updateApplication(applicationId, {
          extractedData: {
            document_type: "unknown",
            structured_data: {},
            extracted_fields: {},
            missing_fields: [],
            confidence: 0,
            reasoning: ["AI processing failed"],
            canonical: {
              document_type: "unknown",
              document_category: "unknown",
              applicant: {
                name: "",
                guardian_name: "",
                aadhaar_number: "",
                mobile_number: "",
                address: "",
                village: "",
                district: "",
                state: ""
              },
              agriculture: {
                land_size: "",
                land_unit: "",
                survey_number: "",
                crop_name: "",
                season: "",
                location: ""
              },
              request: {
                scheme_name: "",
                request_type: "",
                requested_amount: "",
                issue_summary: "",
                claim_reason: ""
              },
              document_meta: {
                document_date: "",
                reference_number: "",
                supporting_doc_type: "",
                source_file_name: ""
              },
              verification: {
                missing_fields: [],
                field_confidences: {},
                extraction_confidence: 0,
                validation_errors: [],
                recommendation: "",
                reasoning: ["AI processing failed"]
              }
            }
          },
          aiProcessingStatus: "failed",
          aiProcessedAt: new Date()
        });
      }
    }
  }

  private async triggerAIProcessing(applicationId: string): Promise<void> {
    console.log(`[SYNC AI] Starting synchronous AI processing for application: ${applicationId}`);
    
    const application = await applicationsRepository.getApplicationById(applicationId);
    if (!application?.fileUrl) {
      throw new Error('No file URL found for processing');
    }
    
    // Convert stored file path to public Supabase URL
    const filePath = application.fileUrl;
    console.log("[AI FILE URL] object path:", filePath);
    
    const { data: publicUrlData } = supabase.storage
      .from('documents')
      .getPublicUrl(filePath);
    
    const publicUrl = publicUrlData.publicUrl;
    console.log("[AI FILE URL] public url:", publicUrl);
    
    // HARD GUARD: Validate fileUrl before AI processing
    if (!publicUrl || typeof publicUrl !== "string" || !publicUrl.trim()) {
      console.warn("[AI SKIP] Missing fileUrl, skipping AI document-processing call");
      throw new Error('No file URL found for processing');
    }
    
    // DEBUG LOGGING: Log AI call details
    console.log("[AI CALL] applicationId:", applicationId);
    console.log("[AI CALL] fileUrl:", publicUrl);
    console.log("[AI CALL] fileName:", application.fileName);
    console.log("[AI CALL] fileType:", application.fileType);
    
    // Call AI orchestrator with public URL
    const aiPromise = aiOrchestratorService.processDocument({
      fileUrl: publicUrl,
      fileName: application.fileName,
      fileType: application.fileType
    });
    
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('AI processing timeout')), 60000)
    );
    
    const aiResponse = await Promise.race([aiPromise, timeoutPromise]) as any;
    
    if (!aiResponse?.success) {
      throw new Error(aiResponse?.error || 'AI processing failed');
    }
    
    // Extract data using strict contract resolution
    const extractedData = this.resolveExtractedContractFromAiResponse(aiResponse) || {};
    
    // Resolve farmer
    let farmerId = null;
    const applicant = extractedData?.canonical?.applicant || this.mapStructuredToApplicant(extractedData?.structured_data);
    
    if (applicant && (applicant.name || applicant.aadhaar_number || applicant.mobile_number)) {
      try {
        const resolvedFarmer = await this.resolveFarmerFromCanonical(applicant);
        if (resolvedFarmer) {
          farmerId = resolvedFarmer.id;
        }
      } catch (error) {
        console.error(`[SYNC AI] Error resolving farmer:`, error);
      }
    }
    
    // Determine final status
    const finalStatus = mapAiResultToApplicationStatus(aiResponse, extractedData);
    
    // Update application with results
    const updateData: UpdateApplicationInput = {
      extractedData,
      farmerId: farmerId || undefined,
      status: finalStatus,
      aiProcessingStatus: 'completed',
      aiProcessedAt: new Date(),
      priorityScore: aiResponse.data?.priorityScore || 0,
      fraudRiskScore: aiResponse.data?.fraudRiskScore || 0,
      fraudFlags: aiResponse.data?.fraudFlags || [],
      verificationRecommendation: aiResponse.data?.verificationRecommendation,
      aiSummary: aiResponse.data?.aiSummary || aiResponse.data?.extractedData?.ai_summary || aiResponse.data?.extractedData?.summary || `Document processed as ${extractedData?.document_type || 'unknown'}. Review extracted fields for verification.`
    };
    
    // Add normalized content hash based on extracted data
    const fingerprint = generateContentFingerprint(extractedData);
    if (fingerprint) {
      (updateData as any).normalizedContentHash = fingerprint;
    }

    // FAULT TOLERANCE: Preserve successful extraction even if optional downstream fails
    // Only update fields that succeeded, never overwrite with failure data
    const faultTolerantUpdate: any = {
      extractedData, // Always preserve if we have it
      farmerId: farmerId || undefined,
      status: finalStatus,
      aiProcessedAt: new Date()
    };

    // CRITICAL: Include normalizedContentHash in fault-tolerant update
    if (fingerprint) {
      faultTolerantUpdate.normalizedContentHash = fingerprint;
      console.log('[NORMALIZATION] Generated and persisted content hash:', fingerprint.substring(0, 16) + '...');
    }

    // Only add optional fields if they succeeded
    if (aiResponse.data?.priorityScore !== undefined) {
      faultTolerantUpdate.priorityScore = aiResponse.data.priorityScore;
    }
    if (aiResponse.data?.fraudRiskScore !== undefined) {
      faultTolerantUpdate.fraudRiskScore = aiResponse.data.fraudRiskScore;
    }
    if (aiResponse.data?.fraudFlags) {
      faultTolerantUpdate.fraudFlags = aiResponse.data.fraudFlags;
    }
    if (aiResponse.data?.verificationRecommendation) {
      faultTolerantUpdate.verificationRecommendation = aiResponse.data.verificationRecommendation;
    }
    if (aiResponse.data?.aiSummary || aiResponse.data?.extractedData?.ai_summary || aiResponse.data?.extractedData?.summary) {
      faultTolerantUpdate.aiSummary = aiResponse.data.aiSummary || aiResponse.data.extractedData?.ai_summary || aiResponse.data.extractedData?.summary || `Document processed as ${extractedData?.document_type || 'unknown'}. Review extracted fields for verification.`;
    }

    // Set AI processing status based on extraction success, not optional downstream
    faultTolerantUpdate.aiProcessingStatus = extractedData.document_type === "unknown" ? "failed" : "completed";
    
    await applicationsRepository.updateApplication(applicationId, faultTolerantUpdate);
    
    console.log('[SYNC AI FAULT TOLERANCE] Applied fault-tolerant update:', {
      hasExtractedData: !!extractedData,
      hasPriorityScore: aiResponse.data?.priorityScore !== undefined,
      hasFraudData: aiResponse.data?.fraudRiskScore !== undefined,
      hasSummary: !!faultTolerantUpdate.aiSummary,
      finalStatus: faultTolerantUpdate.aiProcessingStatus
    });
    
    // Resolve case if needed using shared resolved document type
    if (farmerId) {
      try {
        const resolvedDocumentType = this.resolveActualDocumentType({ extractedData, type: application.type });
        if (resolvedDocumentType) {
          await this.caseService.resolveCase({
            applicationId,
            farmerId,
            documentType: resolvedDocumentType
          });
        }
      } catch (caseError) {
        console.error(`[SYNC AI] Error resolving case:`, caseError);
      }
    }
    
    console.log(`[SYNC AI] Completed processing for application: ${applicationId}`);

    // Safety fallback persist: ensure extractedData and completed status are saved
    try {
      const aiResult = aiResponse?.data?.extractedData || aiResponse?.data || extractedData;
      if (aiResult) {
        try { (application as any).extractedData = aiResult; (application as any).aiProcessingStatus = 'completed'; (application as any).updatedAt = new Date(); } catch (_) {}

        await applicationsRepository.updateApplication(applicationId, {
          extractedData: aiResult,
          aiProcessingStatus: 'completed'
        });
      }
    } catch (e) {
      console.error('[SYNC AI] Error persisting aiResult fallback:', e);
    }
  }

  private extractDataFromAIResponse(aiResponse: any): any {
    // Thin wrapper that delegates to the strict contract resolver
    return this.resolveExtractedContractFromAiResponse(aiResponse) || {};
  }

  /**
   * Map structured_data to applicant shape for fallback
   */
  private mapStructuredToApplicant(data: any) {
    if (!data) return null

    return {
      name: data.farmer_name || data.applicant_name,
      aadhaar_number: data.aadhaar_number,
      mobile_number: data.phone_number || data.mobile_number,
      address: data.location || data.address,
      village: data.village,
      district: data.district,
      state: data.state
    }
  }

  /**
   * Resolve farmer from canonical applicant data
   */
  private async resolveFarmerFromCanonical(applicant: any): Promise<{ id: string } | null> {
    try {
      // Extract fields from canonical applicant shape
      const aadhaarNumber = applicant?.aadhaar_number?.trim();
      const mobileNumber = applicant?.mobile_number?.trim();
      const name = applicant?.name?.trim();
      const address = applicant?.address?.trim();
      const village = applicant?.village?.trim();
      const district = applicant?.district?.trim();
      const state = applicant?.state?.trim() || null;
      
      console.log(`[FARMER] Resolving farmer with canonical applicant data:`, {
        aadhaarNumber,
        mobileNumber,
        name,
        village,
        district,
        state
      });
      
      // 1. If Aadhaar exists, try to find by Aadhaar
      if (aadhaarNumber) {
        let existingFarmer = await applicationsRepository.findFarmerByAadhaar(aadhaarNumber);
        if (existingFarmer) {
          console.log(`[FARMER] Found existing farmer by Aadhaar: ${existingFarmer.id}`);
          
          // Update empty fields only
          const updateData: any = {};
          if (!existingFarmer.name && name) updateData.name = name;
          if (!existingFarmer.mobileNumber && mobileNumber) updateData.mobileNumber = mobileNumber;
          if (!existingFarmer.address && address) updateData.address = address;
          if (!existingFarmer.village && village) updateData.village = village;
          if (!existingFarmer.district && district) updateData.district = district;
          if (!existingFarmer.state && state) updateData.state = state;
          
          if (Object.keys(updateData).length > 0) {
            await applicationsRepository.updateFarmer(existingFarmer.id, updateData);
            console.log(`[FARMER] Updated existing farmer with additional data`);
          }
          
          return { id: existingFarmer.id };
        }
      }
      
      // 2. Else if mobile exists, try to find by mobile
      if (mobileNumber && !aadhaarNumber) {
        let existingFarmer = await applicationsRepository.findFarmerByMobile(mobileNumber);
        if (existingFarmer) {
          console.log(`[FARMER] Found existing farmer by mobile: ${existingFarmer.id}`);
          
          // Update empty fields only
          const updateData: any = {};
          if (!existingFarmer.name && name) updateData.name = name;
          if (!existingFarmer.aadhaarNumber && aadhaarNumber) updateData.aadhaarNumber = aadhaarNumber;
          if (!existingFarmer.address && address) updateData.address = address;
          if (!existingFarmer.village && village) updateData.village = village;
          if (!existingFarmer.district && district) updateData.district = district;
          if (!existingFarmer.state && state) updateData.state = state;
          
          if (Object.keys(updateData).length > 0) {
            await applicationsRepository.updateFarmer(existingFarmer.id, updateData);
            console.log(`[FARMER] Updated existing farmer with additional data`);
          }
          
          return { id: existingFarmer.id };
        }
      }
      
      // 3. If no Aadhaar and no mobile, return null (don't create weak anonymous farmer)
      if (!aadhaarNumber && !mobileNumber) {
        console.log(`[FARMER] No Aadhaar or mobile number, skipping farmer creation`);
        return null;
      }
      
      // 4. If not found, create new farmer
      const newFarmerData = {
        name,
        aadhaarNumber,
        mobileNumber,
        address,
        village,
        district,
        state
      };
      
      console.log(`[FARMER] Creating new farmer with data:`, newFarmerData);
      const newFarmer = await applicationsRepository.createFarmer(newFarmerData);
      console.log(`[FARMER] Created new farmer: ${newFarmer.id}`);
      
      return { id: newFarmer.id };
      
    } catch (error) {
      console.error(`[FARMER] Error in resolveFarmerFromCanonical:`, error);
      return null;
    }
  }

  /**
   * Validate status transitions
   */
  private validateStatusTransition(applicationId: string, newStatus: string): void {
    // Add validation logic if needed
    console.log(`[STATUS] Validating transition for application ${applicationId} to ${newStatus}`);
  }

  async healthCheck(): Promise<{ message: string }> {
    return { message: 'Applications service working' }
  }

  async getFarmers() {
    return await applicationsRepository.getAllFarmersWithApplications()
  }

  async getFarmerById(farmerId: string) {
    return await applicationsRepository.getFarmerByIdWithApplications(farmerId)
  }

  async updateApplication(id: string, updateData: UpdateApplicationInput): Promise<Application> {
    // CRITICAL: Normalize extractedData contract before persistence
    if (updateData.extractedData) {
      updateData.extractedData = normalizeExtractedDataContract(updateData.extractedData);
      console.log('[NORMALIZATION] Applied extractedData contract normalization for application:', id);
    }
    
    return await applicationsRepository.updateApplication(id, updateData)
  }

  async deleteApplication(id: string): Promise<void> {
    await applicationsRepository.deleteApplication(id)
  }

  async getApplicationStatus(id: string): Promise<string> {
    const application = await this.getApplicationById(id)
    return application.status
  }

  async getFarmerApplicationTimeline(farmerId: string): Promise<any> {
    // Get all applications for this farmer using farmerId, not applicantId
    const applications = await applicationsRepository.findApplicationsByFarmerForTimeline(farmerId);
    
    return applications.map((app: any) => ({
      id: app.id,
      status: app.status,
      type: this.resolveActualDocumentType(app) || app.type,
      submissionDate: app.createdAt,
      decisionDate: app.decisionDate,
      notes: app.notes,
      extractedData: app.extractedData
    }));
  }

  async getApplicationVersionHistory(id: string): Promise<ApplicationVersionHistory[]> {
    const versions = await applicationsRepository.getApplicationVersions(id)
    
    // Group by application and create version history
    const versionMap = new Map<string, ApplicationVersionHistory>()
    
    versions.forEach(app => {
      const existing = versionMap.get(app.id)
      if (!existing) {
        versionMap.set(app.id, {
          applicationId: app.id,
          documentType: app.type,
          status: app.status,
          currentVersion: app.versionNumber,
          history: [{
            version: app.versionNumber,
            fileUrl: app.fileUrl || '',
            status: app.status,
            createdAt: app.createdAt,
            notes: app.notes
          }]
        })
      } else {
        existing.history.push({
          version: app.versionNumber,
          fileUrl: app.fileUrl || '',
          status: app.status,
          createdAt: app.createdAt,
          notes: app.notes
        })
      }
    })
    
    return Array.from(versionMap.values())
  }

  async cleanupTestData() {
    try {
      console.log('[CLEANUP] Starting test data cleanup service');
      
      // Delete applications with temp-user applicantId and UPLOADED status
      const result = await applicationsRepository.archiveTestData({
        applicantId: 'temp-user',
        status: 'UPLOADED',
        olderThanDays: 7 // Only delete records older than 7 days
      });
      
      console.log('[CLEANUP] Test data cleanup service completed:', result);
      return result;
    } catch (error) {
      console.error('[CLEANUP] Error in cleanupTestData:', error);
      throw error;
    }
  }

  /**
   * Get verification queue with filtering options - STRICT: ONLY under_review status
   */
  async getVerificationQueue(filters?: {
    status?: string;
    queue?: string;
    risk_level?: string;
    document_type?: string;
    farmerId?: string;
    page?: number;
    limit?: number;
  }) {
    console.log('[QUEUE] Getting verification queue with filters:', filters);
    
    try {
      // STRICT: ONLY get applications with under_review status
      const query: ApplicationQuery = {
        page: filters?.page || 1,
        limit: filters?.limit || 50,
        filters: {
          status: 'UNDER_REVIEW', // STRICT: Only under_review applications
          ...(filters?.farmerId && { applicantId: filters.farmerId })
        }
      };
      
      const result = await applicationsRepository.getApplications(query);
      let applications = result.applications;
      
      // Filter by ML insights queue if specified
      if (filters?.queue) {
        applications = applications.filter(app => {
          const queue = app.extractedData?.ml_insights?.queue || 
                      app.extractedData?.predictions?.queue || 
                      'NORMAL';
          return queue.toLowerCase() === filters.queue!.toLowerCase();
        });
      }
      
      // Filter by risk level if specified
      if (filters?.risk_level) {
        applications = applications.filter(app => {
          const riskLevel = app.extractedData?.ml_insights?.risk_level || 
                           app.extractedData?.predictions?.risk_level || 
                           'Medium';
          return riskLevel.toLowerCase() === filters.risk_level!.toLowerCase();
        });
      }
      
      // Filter by document type if specified
      if (filters?.document_type) {
        applications = applications.filter(app => {
          const docType = app.extractedData?.document_type || 
                         app.extractedData?.canonical?.document_type || 
                         app.type;
          return docType?.toLowerCase() === filters.document_type!.toLowerCase();
        });
      }
      
      // Transform to queue format
      const queueItems = applications.map(app => {
        const mlInsights = app.extractedData?.ml_insights || {};
        const predictions = app.extractedData?.predictions || {};
        const decisionSupport = app.extractedData?.decision_support || {};
        
        // Derive applicant name from extracted data in priority order
        const getApplicantName = () => {
          // 1. extractedData.canonical.applicant.name
          if (app.extractedData?.canonical?.applicant?.name) {
            return app.extractedData.canonical.applicant.name;
          }
          // 2. extractedData.farmer_name
          if (app.extractedData?.farmer_name) {
            return app.extractedData.farmer_name;
          }
          // 3. extractedData.structured_data.farmer_name
          if (app.extractedData?.structured_data?.farmer_name) {
            return app.extractedData.structured_data.farmer_name;
          }
          // 4. personalInfo.firstName + lastName
          if (app.personalInfo?.firstName && app.personalInfo?.lastName) {
            return `${app.personalInfo.firstName} ${app.personalInfo.lastName}`;
          }
          // 5. applicantId as last safe fallback
          if (app.applicantId) {
            return app.applicantId;
          }
          // 6. Unknown only if truly no value exists
          return 'Unknown Applicant';
        };
        
        return {
          id: app.id,
          applicantId: app.applicantId,
          farmerId: app.farmerId,
          fileName: app.fileName,
          documentType: app.extractedData?.document_type || app.type,
          status: app.status,
          queue: mlInsights.queue || predictions.queue || 'NORMAL',
          riskLevel: mlInsights.risk_level || predictions.risk_level || 'Medium',
          priorityScore: mlInsights.priority_score || predictions.priority_score || 50,
          decision: decisionSupport.decision || 'review',
          confidence: decisionSupport.confidence || 0.5,
          submittedAt: app.createdAt,
          lastActivity: app.updatedAt,
          missingFields: app.extractedData?.missing_fields || [],
          riskFlags: app.extractedData?.risk_flags || [],
          applicantName: getApplicantName()
        };
      });
      
      // SORT: High risk first, then by priority score, then latest first
      queueItems.sort((a, b) => {
        // Primary sort: Risk level (high > medium > low)
        const riskOrder: { [key: string]: number } = { 'high': 3, 'medium': 2, 'low': 1 };
        const aRiskLevel = (a.riskLevel || '').toLowerCase();
        const bRiskLevel = (b.riskLevel || '').toLowerCase();
        const aRiskPriority = riskOrder[aRiskLevel] || 1;
        const bRiskPriority = riskOrder[bRiskLevel] || 1;
        
        if (aRiskPriority !== bRiskPriority) {
          return bRiskPriority - aRiskPriority; // Higher risk first
        }
        
        // Secondary sort: Priority score (high to low)
        if (b.priorityScore !== a.priorityScore) {
          return b.priorityScore - a.priorityScore;
        }
        
        // Tertiary sort: Latest first
        return new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime();
      });
      
      console.log(`[QUEUE] Returning ${queueItems.length} under_review applications (sorted by risk priority)`);
      
      return {
        items: queueItems,
        total: queueItems.length,
        filters: filters || {},
        queueStatus: 'under_review_only' // Indicate strict filtering
      };
      
    } catch (error) {
      console.error('[QUEUE] Error getting verification queue:', error);
      throw error;
    }
  }

  /**
   * Get dashboard metrics - REAL COUNTS with proper status mapping
   */
  async getDashboardMetrics() {
    console.log('[DASHBOARD] Getting dashboard metrics');
    
    try {
      // Get all applications for metrics calculation
      const allAppsResult = await applicationsRepository.getApplications({
        page: 1,
        limit: 10000 // Get all for metrics
      });
      const applications = allAppsResult.applications;
      
      // Calculate basic metrics using STRICT status mapping
      const totalApplications = applications.length;
      
      // PENDING = uploaded + processing + under_review
      const pendingCount = applications.filter(app => {
        const status = (app.status || 'UPLOADED').toLowerCase().replace(/[-\s]/g, '_');
        return ['uploaded', 'processing', 'under_review'].includes(status);
      }).length;
      
      // APPROVED = approved only
      const approvedCount = applications.filter(app => {
        const status = (app.status || 'UPLOADED').toLowerCase().replace(/[-\s]/g, '_');
        return status === 'approved';
      }).length;
      
      // REJECTED = rejected only  
      const rejectedCount = applications.filter(app => {
        const status = (app.status || 'UPLOADED').toLowerCase().replace(/[-\s]/g, '_');
        return status === 'rejected';
      }).length;
      
      // REQUIRES_ACTION = requires_action only
      const requiresActionCount = applications.filter(app => {
        const status = (app.status || 'UPLOADED').toLowerCase().replace(/[-\s]/g, '_');
        return status === 'requires_action';
      }).length;
      
      // Risk distribution from ML insights
      const riskDistribution: { [key: string]: number } = { low: 0, medium: 0, high: 0 };
      applications.forEach(app => {
        const riskLevel = app.extractedData?.ml_insights?.risk_level || 
                         app.extractedData?.predictions?.risk_level || 
                         'medium';
        const normalizedRisk = riskLevel.toLowerCase();
        if (['low', 'medium', 'high'].includes(normalizedRisk)) {
          riskDistribution[normalizedRisk]++;
        } else {
          riskDistribution['medium']++; // Default to medium
        }
      });
      
      // Document type distribution
      const documentTypeDistribution: { [key: string]: number } = {};
      applications.forEach(app => {
        const docType = app.extractedData?.document_type || 
                       app.extractedData?.canonical?.document_type || 
                       app.type || 
                       'unknown';
        documentTypeDistribution[docType] = (documentTypeDistribution[docType] || 0) + 1;
      });
      
      // Recent activity (last 10 significant events)
      const recentActivity = applications
        .filter(app => app.updatedAt)
        .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
        .slice(0, 10)
        .map(app => {
          const status = (app.status || 'UPLOADED').toLowerCase().replace(/[-\s]/g, '_');
          const activity = {
            id: app.id,
            type: 'application_updated',
            description: `Application ${status.replace('_', ' ')}`,
            timestamp: app.updatedAt,
            applicantId: app.applicantId,
            documentType: app.extractedData?.document_type || app.type
          };
          
          // More specific activity descriptions
          if (status === 'approved') {
            activity.description = 'Application approved';
            activity.type = 'application_approved';
          } else if (status === 'rejected') {
            activity.description = 'Application rejected';
            activity.type = 'application_rejected';
          } else if (status === 'requires_action') {
            activity.description = 'Clarification requested';
            activity.type = 'clarification_requested';
          } else if (app.extractedData?.ml_insights?.queue === 'HIGH_PRIORITY') {
            activity.description = 'High priority application detected';
            activity.type = 'high_priority_detected';
          }
          
          return activity;
        });
      
      const metrics = {
        totalApplications,
        pending: pendingCount, // Use correct field name
        approved: approvedCount,
        rejected: rejectedCount,
        requires_action: requiresActionCount, // Use correct field name
        riskDistribution: Object.entries(riskDistribution).map(([level, count]) => ({
          level,
          count
        })),
        documentTypeDistribution: Object.entries(documentTypeDistribution).map(([type, count]) => ({
          type,
          count
        })),
        recentActivity,
        lastUpdated: new Date().toISOString()
      };
      
      console.log('[DASHBOARD] Real metrics calculated:', {
        totalApplications,
        pending: pendingCount,
        approved: approvedCount,
        rejected: rejectedCount,
        requires_action: requiresActionCount
      });
      
      return metrics;
      
    } catch (error) {
      console.error('[DASHBOARD] Error getting dashboard metrics:', error);
      throw error;
    }
  }

  /**
   * LEVEL 3: Semantic duplicate detection - same farmer + similar data
   */
  private async _checkSemanticDuplicate(
    extractedData: any,
    applicantId: string
  ): Promise<{
    isDuplicate: boolean
    existingApplication?: any
    confidence?: number
  }> {
    try {
      console.log('[SEMANTIC DUP] Starting semantic duplicate analysis')
      
      // Extract key identity fields from current document
      const structured = (extractedData.structured_data || {}) as any
      const canonical = (extractedData.canonical || {}) as any
      
      // Build identity signature from multiple fields
      const currentSignature = {
        farmer_name: this._normalizeText(structured.farmer_name || canonical.applicant?.name || ''),
        aadhaar_number: this._normalizeText(structured.aadhaar_number || canonical.applicant?.aadhaar_number || ''),
        mobile_number: this._normalizeText(structured.mobile_number || structured.contact_number || canonical.applicant?.contact?.mobile || ''),
        village: this._normalizeText(structured.village || structured.location || ''),
        district: this._normalizeText(structured.district || ''),
        document_type: this._normalizeText((extractedData as any).document_type || '')
      }
      
      console.log('[SEMANTIC DUP] Current signature:', {
        ...currentSignature,
        aadhaar_number: currentSignature.aadhaar_number ? currentSignature.aadhaar_number.substring(0, 4) + '...' : 'none'
      })
      
      // Get recent applications from the same applicant (last 30 days)
      const thirtyDaysAgo = new Date()
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
      
      const recentApplications = await applicationsRepository.findRecentApplicationsByApplicant(
        applicantId,
        thirtyDaysAgo.toISOString()
      )
      
      console.log(`[SEMANTIC DUP] Found ${recentApplications.length} recent applications for analysis`)
      
      for (const existingApp of recentApplications) {
        const existingExtracted = (existingApp.extractedData || {}) as any
        const existingStructured = (existingExtracted.structured_data || {}) as any
        const existingCanonical = (existingExtracted.canonical || {}) as any
        
        // Build signature for existing application
        const existingSignature = {
          farmer_name: this._normalizeText(existingStructured.farmer_name || existingCanonical.applicant?.name || ''),
          aadhaar_number: this._normalizeText(existingStructured.aadhaar_number || existingCanonical.applicant?.aadhaar_number || ''),
          mobile_number: this._normalizeText(existingStructured.mobile_number || existingStructured.contact_number || existingCanonical.applicant?.contact?.mobile || ''),
          village: this._normalizeText(existingStructured.village || existingStructured.location || ''),
          district: this._normalizeText(existingStructured.district || ''),
          document_type: this._normalizeText(existingExtracted.document_type || '')
        }
        
        // Calculate similarity score
        const similarity = this._calculateSemanticSimilarity(currentSignature, existingSignature)
        
        console.log(`[SEMANTIC DUP] Similarity with app ${existingApp.id}: ${similarity.toFixed(2)}`)
        
        // High similarity threshold (0.8) for semantic duplicate
        if (similarity >= 0.8) {
          console.log(`[SEMANTIC DUP] Semantic duplicate detected with app ${existingApp.id}`)
          return {
            isDuplicate: true,
            existingApplication: existingApp,
            confidence: similarity
          }
        }
      }
      
      console.log('[SEMANTIC DUP] No semantic duplicates found')
      return { isDuplicate: false }
      
    } catch (error) {
      console.error('[SEMANTIC DUP] Error in semantic duplicate check:', error)
      return { isDuplicate: false }
    }
  }

  /**
   * Calculate semantic similarity between two document signatures
   */
  private _calculateSemanticSimilarity(sig1: any, sig2: any): number {
    let totalScore = 0
    let fieldCount = 0
    
    // Field weights based on importance for identity matching
    const fieldWeights = {
      farmer_name: 0.3,
      aadhaar_number: 0.35,
      mobile_number: 0.2,
      village: 0.1,
      district: 0.05
    }
    
    for (const [field, weight] of Object.entries(fieldWeights)) {
      const value1 = sig1[field] || ''
      const value2 = sig2[field] || ''
      
      if (value1 && value2) {
        // Exact match gets full weight
        if (value1 === value2) {
          totalScore += weight
        } else {
          // Partial match for names (fuzzy matching)
          if (field === 'farmer_name') {
            const nameSimilarity = this._calculateStringSimilarity(value1, value2)
            totalScore += weight * nameSimilarity
          } else if (field === 'village' || field === 'district') {
            // Location similarity - check if one contains the other
            const locationSimilarity = value1.includes(value2) || value2.includes(value1) ? 0.8 : 0
            totalScore += weight * locationSimilarity
          }
        }
        fieldCount++
      }
    }
    
    // Normalize by total weight of compared fields
    const totalWeight = fieldCount > 0 ? 
      Object.values(fieldWeights).reduce((sum, w, idx) => idx < fieldCount ? sum + w : sum, 0) : 1
    
    return totalScore / totalWeight
  }

  /**
   * Calculate string similarity using simple character-based approach
   */
  private _calculateStringSimilarity(str1: string, str2: string): number {
    if (str1 === str2) return 1.0
    
    // Remove spaces and convert to lowercase for comparison
    const s1 = str1.replace(/\s/g, '').toLowerCase()
    const s2 = str2.replace(/\s/g, '').toLowerCase()
    
    if (s1 === s2) return 1.0
    if (s1.length === 0 || s2.length === 0) return 0.0
    
    // Simple Levenshtein distance approximation
    const longer = s1.length > s2.length ? s1 : s2
    const shorter = s1.length > s2.length ? s2 : s1
    
    if (longer.length === 0) return 1.0
    
    const editDistance = this._levenshteinDistance(longer, shorter)
    return (longer.length - editDistance) / longer.length
  }

  /**
   * Simple Levenshtein distance implementation
   */
  private _levenshteinDistance(str1: string, str2: string): number {
    const matrix = []
    
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i]
    }
    
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j
    }
    
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1]
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          )
        }
      }
    }
    
    return matrix[str2.length][str1.length]
  }

  /**
   * Normalize text for comparison
   */
  private _normalizeText(text: string): string {
    if (!text) return ''
    return text.toString().trim().toLowerCase().replace(/\s+/g, ' ')
  }
}

export const applicationsService = new ApplicationsService()
