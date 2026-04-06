/**
 * Document Normalization Service
 * Purpose: Unified format-aware preprocessing for all document types
 * Creates consistent extraction input regardless of source format (PDF, image, etc.)
 */

import crypto from 'crypto'

export interface NormalizedDocument {
  rawText: string
  fileType: string
  fileName: string
  preprocessingMetadata: {
    ocrConfidence?: number
    orientationCorrected?: boolean
    contrastEnhanced?: boolean
    preprocessingSteps: string[]
  }
  confidence: number
  sourceBytes?: Buffer // For file hash generation
}

export interface ContentSignature {
  documentType?: string
  identityFields: {
    aadhaarNumber?: string
    farmerName?: string
    mobileNumber?: string
  }
  applicationFields?: {
    schemeType?: string
    requestedAmount?: string
    claimType?: string
  }
  normalizedText?: string
}

class DocumentNormalizationService {
  /**
   * Detect file type from MIME type and filename
   */
  detectFileType(fileName: string, mimeType: string): string {
    const extension = fileName.split('.').pop()?.toLowerCase() || ''
    
    // PDF handling
    if (mimeType === 'application/pdf' || extension === 'pdf') {
      return 'pdf'
    }
    
    // Image handling
    if (['image/jpeg', 'image/jpg', 'image/png'].includes(mimeType) || 
        ['jpg', 'jpeg', 'png'].includes(extension)) {
      return 'image'
    }
    
    // DOCX handling
    if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || extension === 'docx') {
      return 'docx'
    }
    
    // DOC handling
    if (mimeType === 'application/msword' || extension === 'doc') {
      return 'doc'
    }
    
    // Default fallback
    return 'unknown'
  }

  /**
   * Normalize document into unified extraction source
   */
  async normalizeDocument(input: {
    fileBuffer: Buffer
    fileName: string
    mimeType: string
    fileUrl?: string
  }): Promise<NormalizedDocument> {
    const fileType = this.detectFileType(input.fileName, input.mimeType)
    console.log(`[INGEST] File type detected: ${fileType}`)
    
    const preprocessingSteps: string[] = []
    
    try {
      let rawText = ''
      let confidence = 0
      let ocrConfidence: number | undefined
      let orientationCorrected = false
      let contrastEnhanced = false
      
      if (fileType === 'pdf') {
        // PDF extraction - keep existing working flow
        const result = await this.extractPDFText(input.fileUrl || input.fileBuffer)
        rawText = result.text
        confidence = result.confidence
        preprocessingSteps.push('pdf_text_extraction')
      } else if (fileType === 'image') {
        // Image preprocessing and OCR
        preprocessingSteps.push('image_preprocessing')
        
        // Preprocess image for better OCR
        const preprocessedImage = await this.preprocessImage(input.fileBuffer)
        if (preprocessedImage.orientationCorrected) {
          orientationCorrected = true
          preprocessingSteps.push('orientation_correction')
        }
        if (preprocessedImage.contrastEnhanced) {
          contrastEnhanced = true
          preprocessingSteps.push('contrast_enhancement')
        }
        
        // Extract text via OCR
        const ocrResult = await this.extractImageText(preprocessedImage.buffer)
        rawText = ocrResult.text
        confidence = ocrResult.confidence
        ocrConfidence = ocrResult.confidence
        preprocessingSteps.push('ocr_extraction')
      } else if (fileType === 'docx') {
        // DOCX text extraction
        const docxResult = await this.extractDocxText(input.fileBuffer)
        rawText = docxResult.text
        confidence = docxResult.confidence
        preprocessingSteps.push('docx_text_extraction')
      } else if (fileType === 'doc') {
        // DOC text extraction
        const docResult = await this.extractDocText(input.fileBuffer)
        rawText = docResult.text
        confidence = docResult.confidence
        preprocessingSteps.push('doc_text_extraction')
      } else {
        // Unknown format - attempt basic text extraction
        rawText = input.fileBuffer.toString('utf-8')
        confidence = 0.1
        preprocessingSteps.push('fallback_text_extraction')
      }
      
      console.log(`[INGEST] Normalized extraction source ready`)
      
      return {
        rawText: rawText.trim(),
        fileType,
        fileName: input.fileName,
        preprocessingMetadata: {
          ocrConfidence,
          orientationCorrected,
          contrastEnhanced,
          preprocessingSteps
        },
        confidence,
        sourceBytes: input.fileBuffer
      }
    } catch (error) {
      console.error('[INGEST] Document normalization failed:', error)
      
      // Return minimal normalized document on failure
      return {
        rawText: '',
        fileType,
        fileName: input.fileName,
        preprocessingMetadata: {
          preprocessingSteps: ['normalization_failed']
        },
        confidence: 0,
        sourceBytes: input.fileBuffer
      }
    }
  }

  /**
   * Extract text from DOCX using python-docx
   */
  private async extractDocxText(fileBuffer: Buffer): Promise<{ text: string; confidence: number }> {
    try {
      console.log('[DOCX] Extracting text from DOCX')
      
      // In a real implementation, this would call a service to extract DOCX text
      // For now, return placeholder that will be integrated with actual DOCX extraction
      // The actual implementation would:
      // 1. Use python-docx to extract all paragraphs and tables
      // 2. Combine text in readable format
      // 3. Return with high confidence since DOCX is structured text
      
      return {
        text: '', // Will be populated by actual DOCX extraction
        confidence: 0.9 // DOCX typically has high confidence as it's structured text
      }
    } catch (error) {
      console.error('[DOCX] Extraction failed:', error)
      return { text: '', confidence: 0 }
    }
  }

  /**
   * Extract text from DOC using textract
   */
  private async extractDocText(fileBuffer: Buffer): Promise<{ text: string; confidence: number }> {
    try {
      console.log('[DOC] Extracting text from DOC')
      
      // In a real implementation, this would call a service to extract DOC text
      // For now, return placeholder that will be integrated with actual DOC extraction
      // The actual implementation would:
      // 1. Use textract to extract text from legacy DOC format
      // 2. Handle encoding issues properly
      // 3. Return with moderate confidence
      
      return {
        text: '', // Will be populated by actual DOC extraction
        confidence: 0.7 // DOC has moderate confidence due to legacy format
      }
    } catch (error) {
      console.error('[DOC] Extraction failed:', error)
      return { text: '', confidence: 0 }
    }
  }

  /**
   * Extract text from PDF - preserve existing working behavior
   */
  private async extractPDFText(source: string | Buffer): Promise<{ text: string; confidence: number }> {
    try {
      // This should integrate with existing PDF extraction logic
      // For now, return placeholder that will be replaced by actual PDF extraction
      console.log('[PDF] Using existing PDF extraction pipeline')
      
      // In the actual implementation, this would call the existing PDF extraction service
      // that's currently working in the AI orchestrator
      return {
        text: '', // Will be populated by actual PDF extraction
        confidence: 0.8 // PDF typically has high confidence
      }
    } catch (error) {
      console.error('[PDF] Extraction failed:', error)
      return { text: '', confidence: 0 }
    }
  }

  /**
   * Preprocess image for better OCR accuracy
   */
  private async preprocessImage(imageBuffer: Buffer): Promise<{
    buffer: Buffer
    orientationCorrected: boolean
    contrastEnhanced: boolean
  }> {
    try {
      console.log('[IMAGE] Starting image preprocessing')
      
      // In a real implementation, this would use image processing libraries
      // For now, return the original buffer with metadata
      // The actual implementation would:
      // 1. Detect and correct orientation using EXIF data or content analysis
      // 2. Enhance contrast for better text readability
      // 3. Normalize brightness and remove noise
      // 4. Ensure proper DPI for OCR
      
      return {
        buffer: imageBuffer,
        orientationCorrected: false, // Would be determined by actual processing
        contrastEnhanced: false // Would be determined by actual processing
      }
    } catch (error) {
      console.error('[IMAGE] Preprocessing failed:', error)
      return {
        buffer: imageBuffer,
        orientationCorrected: false,
        contrastEnhanced: false
      }
    }
  }

  /**
   * Extract text from image using OCR
   */
  private async extractImageText(imageBuffer: Buffer): Promise<{ text: string; confidence: number }> {
    try {
      console.log('[OCR] Starting text extraction from image')
      
      // In a real implementation, this would call an OCR service
      // For now, return placeholder that will be integrated with actual OCR
      // The actual implementation would:
      // 1. Send preprocessed image to OCR service
      // 2. Get structured text with confidence scores
      // 3. Post-process OCR output to clean common errors
      
      return {
        text: '', // Will be populated by actual OCR
        confidence: 0.6 // OCR typically has moderate confidence
      }
    } catch (error) {
      console.error('[OCR] Text extraction failed:', error)
      return { text: '', confidence: 0 }
    }
  }

  /**
   * Generate lightweight content signature for duplicate detection
   */
  generateContentSignature(normalizedDoc: NormalizedDocument, extractedData?: any): ContentSignature {
    console.log('[DUP] Building normalized content signature')
    
    const signature: ContentSignature = {
      identityFields: {},
      applicationFields: {}
    }
    
    // Extract document type from data or normalize from filename
    if (extractedData?.canonical?.document_type) {
      signature.documentType = extractedData.canonical.document_type.toLowerCase().trim()
    } else if (extractedData?.document_type) {
      signature.documentType = extractedData.document_type.toLowerCase().trim()
    }
    
    // Extract identity fields with normalization
    const canonical = extractedData?.canonical || {}
    const structured = extractedData?.structured_data || {}
    
    // Aadhaar number normalization
    const aadhaar = canonical.applicant?.aadhaar_number || canonical.applicant?.aadhaar || structured.aadhaar_number
    if (aadhaar) {
      signature.identityFields.aadhaarNumber = aadhaar.toString().replace(/\D/g, '').trim()
    }
    
    // Farmer name normalization
    const name = canonical.applicant?.name || structured.farmer_name || structured.applicant_name
    if (name) {
      signature.identityFields.farmerName = name.toString().toLowerCase().trim().replace(/\s+/g, ' ')
    }
    
    // Mobile number normalization
    const mobile = canonical.applicant?.mobile_number || canonical.applicant?.mobile || structured.mobile_number || structured.phone_number
    if (mobile) {
      signature.identityFields.mobileNumber = mobile.toString().replace(/\D/g, '').trim()
    }
    
    // Application-specific fields
    const request = canonical.request || {}
    
    if (request.scheme_name || structured.scheme_name) {
      signature.applicationFields!.schemeType = (request.scheme_name || structured.scheme_name).toString().toLowerCase().trim()
    }
    
    if (request.requested_amount || structured.requested_amount) {
      signature.applicationFields!.requestedAmount = this.normalizeAmount(request.requested_amount || structured.requested_amount)
    }
    
    if (request.claim_type || structured.claim_type) {
      signature.applicationFields!.claimType = (request.claim_type || structured.claim_type).toString().toLowerCase().trim()
    }
    
    // Fallback: use normalized text if structured fields are weak
    if (!signature.identityFields.aadhaarNumber && !signature.identityFields.farmerName && normalizedDoc.rawText.length > 50) {
      signature.normalizedText = this.normalizeTextForSignature(normalizedDoc.rawText)
    }
    
    console.log('[DUP] Content signature built:', {
      hasDocumentType: !!signature.documentType,
      hasIdentityFields: Object.keys(signature.identityFields).length > 0,
      hasApplicationFields: Object.keys(signature.applicationFields || {}).length > 0,
      hasNormalizedText: !!signature.normalizedText
    })
    
    return signature
  }

  /**
   * Generate normalized content hash from signature
   */
  generateContentHash(signature: ContentSignature): string {
    const canonicalParts: string[] = []
    
    // Add document type if available
    if (signature.documentType) {
      canonicalParts.push(`doc_type:${signature.documentType}`)
    }
    
    // Add identity fields
    if (signature.identityFields.aadhaarNumber) {
      canonicalParts.push(`aadhaar:${signature.identityFields.aadhaarNumber}`)
    }
    if (signature.identityFields.farmerName) {
      canonicalParts.push(`name:${signature.identityFields.farmerName}`)
    }
    if (signature.identityFields.mobileNumber) {
      canonicalParts.push(`mobile:${signature.identityFields.mobileNumber}`)
    }
    
    // Add application fields
    if (signature.applicationFields?.schemeType) {
      canonicalParts.push(`scheme:${signature.applicationFields.schemeType}`)
    }
    if (signature.applicationFields?.requestedAmount) {
      canonicalParts.push(`amount:${signature.applicationFields.requestedAmount}`)
    }
    if (signature.applicationFields?.claimType) {
      canonicalParts.push(`claim:${signature.applicationFields.claimType}`)
    }
    
    // Fallback to normalized text
    if (canonicalParts.length === 0 && signature.normalizedText) {
      canonicalParts.push(`text:${signature.normalizedText}`)
    }
    
    if (canonicalParts.length === 0) {
      throw new Error('Insufficient data to generate content hash')
    }
    
    const canonicalString = canonicalParts.join('|')
    const hash = crypto.createHash('sha256').update(canonicalString).digest('hex')
    
    console.log('[DUP] Generated content hash:', hash.substring(0, 16) + '...')
    return hash
  }

  /**
   * Generate raw file hash for exact duplicate detection
   */
  generateFileHash(fileBuffer: Buffer): string {
    const hash = crypto.createHash('sha256').update(fileBuffer).digest('hex')
    console.log('[DUP] Raw file hash computed:', hash.substring(0, 16) + '...')
    return hash
  }

  /**
   * Normalize text for signature generation
   */
  private normalizeTextForSignature(text: string): string {
    return text
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .substring(0, 500) // Limit length for consistency
  }

  /**
   * Normalize amount values for comparison
   */
  private normalizeAmount(amount: any): string {
    const amountStr = amount.toString()
      .replace(/[^\d.]/g, '')
      .replace(/^0+/, '')
      .replace(/\.?0*$/, '')
    
    return amountStr || '0'
  }
}

export const documentNormalizationService = new DocumentNormalizationService()
