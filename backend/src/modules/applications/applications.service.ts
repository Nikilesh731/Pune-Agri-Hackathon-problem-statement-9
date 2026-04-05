/**
 * Applications Service
 * Purpose: Business logic for application management
 */
import { applicationsRepository } from './applications.repository'
import { aiOrchestratorService } from '../ai-orchestrator/ai-orchestrator.service'
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

  // High priority ML tagging
  const highPriorityReview = mlQueue.toUpperCase() === 'HIGH_PRIORITY';

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
  if (hasCriticalMissing || hasHighRisk || needsManualReview || highPriorityReview) {
    return 'UNDER_REVIEW';
  }

  // Otherwise: route into case-management flow (CASE_READY)
  return 'CASE_READY';
}

import crypto from 'crypto'

/**
 * Generate normalized content fingerprint from OCR text
 */
function generateContentFingerprint(ocrText?: string): string | null {
  if (!ocrText || typeof ocrText !== 'string') {
    return null;
  }
  
  // Normalize OCR text for fingerprinting
  const normalized = ocrText
    .toLowerCase()                           // lowercase
    .replace(/\s+/g, ' ')                  // collapse whitespace
    .replace(/\n\s*\n/g, '\n')             // remove repeated line breaks
    .replace(/[^\w\s]/g, '')               // remove punctuation noise
    .trim();
  
  if (normalized.length < 50) {
    return null; // Too short to be reliable
  }
  
  return crypto.createHash('sha256').update(normalized).digest('hex').substring(0, 64);
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
   * FINAL STRICT DUPLICATE CHECK - File hash based pre-save duplicate logic
   * This is the ONLY authoritative duplicate check method
   */
  async checkStrictDuplicate(params: {
    fileHash: string
    fileName: string
    fileSize: number
    applicantId: string
  }): Promise<{
    isDuplicate: boolean
    canResubmit: boolean
    existingApplicationId?: string
    existingStatus?: string
    blockReason?: string
  }> {
    const { fileHash, fileName, fileSize, applicantId } = params
    
    console.log("[DUP CHECK] Start")
    console.log('[STRICT DUPLICATE] Final authoritative check:', {
      fileHash: fileHash.substring(0, 16) + '...',
      fileName,
      fileSize,
      applicantId
    })

    try {
      // PRIMARY KEY: File hash exact match (most reliable)
      const hashMatches = await applicationsRepository.findApplicationsByFileHash(fileHash)
      
      console.log("[DUP CHECK] Query result:", hashMatches.length, "hash matches found")
      
      if (hashMatches.length > 0) {
        const latestMatch = hashMatches[0] // Already ordered by desc createdAt
        
        console.log('[STRICT DUPLICATE] File hash match found:', {
          existingApplicationId: latestMatch.id,
          existingStatus: latestMatch.status,
          fileName: latestMatch.fileName
        })

        // Use unified status helper
        const isActive = isActiveStatus(latestMatch.status)
        const canResubmit = allowsResubmission(latestMatch.status)

        if (isActive) {
          console.log('[STRICT DUPLICATE] BLOCKED - Active duplicate found')
          const blockResult = {
            isDuplicate: true,
            canResubmit: false,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status,
            blockReason: 'Duplicate document already under processing'
          }
          console.log("[DUP CHECK] Returning:", blockResult)
          return blockResult
        } else if (canResubmit) {
          console.log('[STRICT DUPLICATE] ALLOWED - Completed duplicate, re-upload permitted')
          const resubmitResult = {
            isDuplicate: true,
            canResubmit: true,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status
          }
          console.log("[DUP CHECK] Returning:", resubmitResult)
          return resubmitResult
        }
      }

      // FALLBACK: Same applicant + filename + size (only when hash not found)
      const filenameMatches = await applicationsRepository.findApplicationsByFileNameAndSize(
        fileName,
        fileSize,
        applicantId
      )
      
      if (filenameMatches.length > 0) {
        const latestMatch = filenameMatches[0]
        
        console.log('[STRICT DUPLICATE] Filename+size fallback match:', {
          existingApplicationId: latestMatch.id,
          existingStatus: latestMatch.status
        })

        const isActive = isActiveStatus(latestMatch.status)
        const canResubmit = allowsResubmission(latestMatch.status)

        if (isActive) {
          return {
            isDuplicate: true,
            canResubmit: false,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status,
            blockReason: 'Same filename and size with active application'
          }
        } else if (canResubmit) {
          return {
            isDuplicate: true,
            canResubmit: true,
            existingApplicationId: latestMatch.id,
            existingStatus: latestMatch.status
          }
        }
      }

      console.log('[STRICT DUPLICATE] No duplicates found - allowing new upload')
      const finalResult = {
        isDuplicate: false,
        canResubmit: false,
        existingApplicationId: undefined,
        existingStatus: undefined,
        blockReason: undefined
      }
      console.log("[DUP CHECK] Returning:", finalResult)
      return finalResult

    } catch (error) {
      console.error('[STRICT DUPLICATE] Error during duplicate check:', error)
      // On error, allow upload but don't block
      return {
        isDuplicate: false,
        canResubmit: false,
        existingApplicationId: undefined,
        existingStatus: undefined,
        blockReason: undefined
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
    
    // PART 1: STRICT DUPLICATE DETECTION BEFORE SAVING
    const fileHash = (applicationData as any).fileHash;
    if (!fileHash) {
      throw new Error('File hash is required for duplicate detection');
    }
    
    // Find existing applications with same fileHash and farmerId
    const existingApps = await applicationsRepository.findApplicationsByFileHash(fileHash);
    const sameFarmerApps = existingApps.filter(app => app.applicantId === applicationData.applicantId);
    
    if (sameFarmerApps.length > 0) {
      const existing = sameFarmerApps[0]; // Latest one
      const normalizedStatus = existing.status.toLowerCase().replace(/[-\s]/g, '_');
      
      // BLOCK if status is active: uploaded, processing, under_review, pending
      if (['uploaded', 'processing', 'under_review', 'pending'].includes(normalizedStatus)) {
        console.log('[DUPLICATE] BLOCKED - Active duplicate found:', {
          existingApplicationId: existing.id,
          existingStatus: existing.status
        });
        
        // THROW 409 - DO NOT SAVE, DO NOT SEND TO AI
        const error = new Error('Duplicate document already under processing');
        (error as any).statusCode = 409;
        (error as any).code = 'DUPLICATE_BLOCKED';
        (error as any).existingApplicationId = existing.id;
        (error as any).existingStatus = existing.status;
        throw error;
      }
      
      // ALLOW re-upload if status is completed: approved, rejected, requires_action
      if (['approved', 'rejected', 'requires_action'].includes(normalizedStatus)) {
        console.log('[RE-UPLOAD] ALLOWED - Completed duplicate found:', {
          existingApplicationId: existing.id,
          existingStatus: existing.status,
          existingVersion: existing.versionNumber
        });
        
        // Create NEW application with version chain
        const reuploadData = {
          ...applicationData,
          versionNumber: existing.versionNumber + 1,
          parentApplicationId: existing.id,
          isReupload: true
        };
        
        const application = await applicationsRepository.createApplication({
          ...reuploadData,
          aiProcessingStatus: 'pending',
          farmerId: applicationData.farmerId ?? null,
          notes: `Re-upload version ${reuploadData.versionNumber} of application ${existing.id}`,
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
          parentApplicationId: existing.id
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
      fileHash: fileHash || null,
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
      
      // Add normalized content hash if available from AI response
      if (aiResponse.data?.rawExtractedText) {
        const fingerprint = generateContentFingerprint(aiResponse.data.rawExtractedText);
        if (fingerprint) {
          (updateData as any).normalizedContentHash = fingerprint;
        }
      }
      
      await this.updateApplication(applicationId, updateData);
      
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
    
    // Add normalized content hash if available from AI response
    if (aiResponse.data?.rawExtractedText) {
      const fingerprint = generateContentFingerprint(aiResponse.data.rawExtractedText);
      if (fingerprint) {
        (updateData as any).normalizedContentHash = fingerprint;
      }
    }
    
    await applicationsRepository.updateApplication(applicationId, updateData);
    
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
      name: data.farmer_name,
      aadhaar_number: data.aadhaar_number,
      mobile_number: data.phone_number,
      address: data.location,
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
}

export const applicationsService = new ApplicationsService()
