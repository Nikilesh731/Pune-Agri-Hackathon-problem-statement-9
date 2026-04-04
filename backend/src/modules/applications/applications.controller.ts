/**
 * Applications Controller
 * Purpose: Handle application-related HTTP requests
 */
import { Request, Response } from 'express'
import { asyncHandler } from '../../middlewares/asyncHandler'
import { applicationsService } from './applications.service'
import { applicationsRepository } from './applications.repository'
import { CreateApplicationInput, UpdateApplicationInput, ApplicationQuery } from './applications.types'
import { supabase } from '../../config/supabase'
import { validate as isUUID, v4 as uuidv4 } from 'uuid'
import crypto from 'crypto'

class ApplicationsController {
  createApplication = asyncHandler(async (req: Request, res: Response) => {
    try {
      const applicationData: CreateApplicationInput = req.body
      const result = await applicationsService.createApplication(applicationData)
      
      // Handle different response statuses
      if (result.status === 'resubmission') {
        return res.status(200).json({ // 200 OK - accepted resubmission
          success: result.success,
          status: result.status,
          message: result.message,
          application: result.application,
          existingApplicationId: result.existingApplicationId
        })
      }
      
      // Normal creation - 201 Created
      return res.status(201).json({
        success: result.success,
        status: result.status,
        message: result.message,
        application: result.application
      })
    } catch (error) {
      // Handle duplicate submission error
      if (error instanceof Error && error.message.includes("already in process")) {
        return res.status(409).json({
          success: false,
          message: "This document is already in process"
        })
      }
      
      // Handle other errors
      return res.status(500).json({
        success: false,
        message: "Application creation failed"
      })
    }
  })

  getApplications = asyncHandler(async (req: Request, res: Response) => {
    const { page = 1, limit = 10, status, applicantId, schemeId } = req.query
    
    const query: ApplicationQuery = {
      page: Number(page),
      limit: Number(limit),
      filters: {
        ...(status && { status: status as string }),
        ...(applicantId && { applicantId: applicantId as string }),
        ...(schemeId && { schemeId: schemeId as string })
      }
    }
    
    const result = await applicationsService.getApplications(query)
    res.json(result)
  })

  getApplicationById = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params

    if (!isUUID(id)) {
      return res.status(400).json({ error: 'Invalid application ID' })
    }

    const result = await applicationsService.getApplicationById(id)
    res.json(result)
  })

  updateApplication = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    const updateData: UpdateApplicationInput = req.body
    const result = await applicationsService.updateApplication(id, updateData)
    res.json(result)
  })

  deleteApplication = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    await applicationsService.deleteApplication(id)
    res.json({ message: 'Application deleted successfully' })
  })

  getApplicationStatus = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    const status = await applicationsService.getApplicationStatus(id)
    res.json({ applicationId: id, status })
  })

  approveApplication = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    const result = await applicationsService.approveApplication(id)
    res.json(result)
  })

  rejectApplication = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    const result = await applicationsService.rejectApplication(id)
    res.json(result)
  })

  requestClarification = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    const result = await applicationsService.requestClarification(id)
    res.json(result)
  })

  reprocessWithAI = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params
    const result = await applicationsService.reprocessWithAI(id)
    res.json(result)
  })

  healthCheck = asyncHandler(async (req: Request, res: Response) => {
    res.json({ message: 'Applications controller working' })
  })

  getFarmers = asyncHandler(async (req: Request, res: Response) => {
    const farmers = await applicationsService.getFarmers()
    res.json(farmers)
  })

  getFarmerById = asyncHandler(async (req: Request, res: Response) => {
    const { farmerId } = req.params

    if (!isUUID(farmerId)) {
      return res.status(400).json({ error: 'Invalid farmer ID' })
    }

    try {
      const farmer = await applicationsService.getFarmerById(farmerId)
      res.json(farmer)
    } catch (error) {
      if (error instanceof Error && error.message === 'Farmer not found') {
        return res.status(404).json({ error: 'Farmer not found' })
      }
      throw error
    }
  })

  cleanupTestData = asyncHandler(async (req: Request, res: Response) => {
    console.log('[CLEANUP] Starting cleanup with mode support');
    
    const { mode } = req.body;
    
    if (mode === 'all') {
      // FULL CLEANUP - Delete all applications for local test reset
      console.log('[CLEANUP] Running FULL cleanup - deleting all applications');
      
      try {
        const result = await applicationsService.deleteAllApplications();
        
        console.log('[CLEANUP] Full cleanup completed:', result);
        res.json({
          message: 'All applications deleted successfully',
          mode: 'all',
          count: result.deletedCount,
          success: true
        });
      } catch (error) {
        console.error('[CLEANUP] Full cleanup failed:', error);
        res.status(500).json({
          message: 'Failed to delete all applications',
          mode: 'all',
          error: error instanceof Error ? error.message : 'Unknown error',
          success: false
        });
      }
    } else {
      // DEFAULT TEST-ONLY CLEANUP - Archive applications with temp-user applicantId and UPLOADED status
      console.log('[CLEANUP] Running test-only cleanup');
      
      try {
        const result = await applicationsService.cleanupTestData();
        
        console.log('[CLEANUP] Test-only cleanup completed:', result);
        res.json({
          message: 'Test data cleanup completed',
          mode: 'test_only',
          ...result
        });
      } catch (error) {
        console.error('[CLEANUP] Test-only cleanup failed:', error);
        res.status(500).json({
          message: 'Test data cleanup failed',
          mode: 'test_only',
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  })

  testUpload = asyncHandler(async (req: Request, res: Response) => {
    console.log('[TEST] Test upload endpoint reached');
    res.json({ message: 'Test upload working' });
  })

  createApplicationWithFile = asyncHandler(async (req: Request, res: Response) => {
    console.log('[UPLOAD] Starting FINAL file upload process');
    
    const file = req.file
    console.log('[UPLOAD] File received:', !!file);

    if (!file) {
      console.log('[UPLOAD] No file provided');
      return res.status(400).json({ error: 'No file uploaded' })
    }

    console.log('[UPLOAD] File details:', {
      originalname: file.originalname,
      mimetype: file.mimetype,
      size: file.size
    });

    // Use provided values or safe defaults for intake
    const applicantId = req.body.applicantId || 'temp-user';
    const documentType = req.body.documentType || 'document_upload';
    
    console.log('[UPLOAD] Creating intake application for:', { applicantId, documentType });

    // Validate file buffer exists
    if (!file || !file.buffer) {
      return res.status(400).json({ error: 'Invalid upload' })
    }

    // Upload file to Supabase storage
    const bucket = 'documents'
    const objectPath = `applications/${Date.now()}-${file.originalname}`
    console.log('[UPLOAD] Starting Supabase storage upload:', { bucket, objectPath });

    const { data: uploadData, error: uploadError } = await supabase.storage
      .from(bucket)
      .upload(objectPath, file.buffer, {
        contentType: file.mimetype,
        upsert: false
      })

    if (uploadError) {
      console.error('[UPLOAD] Supabase storage upload failed:', uploadError);
      return res.status(500).json({ 
        error: 'File upload failed', 
        details: uploadError.message 
      })
    }

    console.log('[UPLOAD] Supabase storage upload successful:', uploadData.path);

    // Store the object path (not public URL) - AI orchestrator will download from storage
    const fileUrl = uploadData.path

    // FINAL STRICT DUPLICATE DETECTION - Generate file hash
    const fileHash = crypto.createHash('sha256').update(file.buffer).digest('hex')
    console.log('[STRICT DUPLICATE] Generated file hash:', fileHash.substring(0, 16) + '...')
    console.log('[STRICT DUPLICATE] Applicant ID:', applicantId)
    console.log('[STRICT DUPLICATE] File name:', file.originalname)
    console.log('[STRICT DUPLICATE] File size:', file.size)

    // AUTHORITATIVE DUPLICATE CHECK - File hash based
    const duplicateCheck = await applicationsService.checkStrictDuplicate({
      fileHash,
      fileName: file.originalname,
      fileSize: file.size,
      applicantId
    })

    console.log('[STRICT DUPLICATE] Final result:', {
      isDuplicate: duplicateCheck.isDuplicate,
      canResubmit: duplicateCheck.canResubmit,
      existingApplicationId: duplicateCheck.existingApplicationId,
      existingStatus: duplicateCheck.existingStatus,
      blockReason: duplicateCheck.blockReason
    })

    // SCENARIO A: BLOCK ACTIVE DUPLICATE
    if (duplicateCheck.isDuplicate && !duplicateCheck.canResubmit) {
      console.log('[STRICT DUPLICATE] BLOCKING - Active duplicate found:', {
        existingApplicationId: duplicateCheck.existingApplicationId,
        existingStatus: duplicateCheck.existingStatus,
        blockReason: duplicateCheck.blockReason
      })

      // Clean up uploaded file
      try {
        await supabase.storage.from(bucket).remove([objectPath])
        console.log('[STRICT DUPLICATE] Cleaned up uploaded file for blocked duplicate')
      } catch (cleanupError) {
        console.warn('[STRICT DUPLICATE] Failed to clean up uploaded file:', cleanupError)
      }

      return res.status(409).json({
        success: false,
        status: "duplicate_blocked",
        duplicateBlocked: true,
        isReupload: false,
        existingApplicationId: duplicateCheck.existingApplicationId,
        message: "Duplicate document already under processing"
      })
    }

    // SCENARIO B: ALLOW RE-UPLOAD (completed duplicate)
    if (duplicateCheck.isDuplicate && duplicateCheck.canResubmit) {
      console.log('[STRICT DUPLICATE] ALLOWING RE-UPLOAD:', {
        existingApplicationId: duplicateCheck.existingApplicationId,
        existingStatus: duplicateCheck.existingStatus
      })

      // Create new version as re-upload
      const existingApplication = await applicationsService.getApplicationById(duplicateCheck.existingApplicationId!)
      if (!existingApplication) {
        return res.status(404).json({ error: 'Existing application not found for re-upload' })
      }

      // Calculate next version
      const nextVersion = (existingApplication.versionNumber || 1) + 1
      
      const applicationData: CreateApplicationInput = {
        applicantId: applicantId,
        schemeId: existingApplication.schemeId,
        type: existingApplication.type,
        fileName: file.originalname,
        fileUrl: fileUrl,
        fileSize: file.size,
        fileType: file.mimetype,
        fileHash: fileHash,
        farmerId: existingApplication.farmerId,
        parentApplicationId: existingApplication.id,
        versionNumber: nextVersion,
        notes: `Re-upload version ${nextVersion} of application ${existingApplication.id}`,
        personalInfo: existingApplication.personalInfo
      }

      try {
        const result = await applicationsService.createApplication(applicationData)
        console.log('[RE-UPLOAD] New version created successfully:', result.application?.id)
        
        return res.status(201).json({
          success: true,
          status: "reupload_allowed",
          isReupload: true,
          parentApplicationId: existingApplication.id,
          application: result.application,
          message: "Previous application completed. Re-upload accepted as a new version."
        })
      } catch (error) {
        console.error('[RE-UPLOAD] Failed to create new version:', error)
        return res.status(500).json({
          success: false,
          message: "Re-upload failed"
        })
      }
    }

    // SCENARIO C: NORMAL NEW UPLOAD (no duplicate)
    console.log('[STRICT DUPLICATE] Creating new application - no duplicate found');
    
    const applicationData: CreateApplicationInput = {
      applicantId: applicantId,
      schemeId: 'pending-analysis', // Will be updated by AI processing
      type: documentType,
      fileName: file.originalname,
      fileUrl: fileUrl,
      fileSize: file.size,
      fileType: file.mimetype,
      fileHash: fileHash, // Store file hash for duplicate detection
      personalInfo: {
        firstName: '', // DB-safe placeholder - AI processing will populate
        lastName: '',
        email: req.body.email || '',
        phone: req.body.phone || '',
        dateOfBirth: new Date(),
        address: {
          street: '',
          city: '',
          district: '',
          state: '',
          pincode: ''
        }
      },
      documents: [{
        type: file.mimetype,
        name: file.originalname,
        url: fileUrl,
        uploadDate: new Date(),
        verificationStatus: 'pending' as const,
        version: 1
      }]
    }

    try {
      const result = await applicationsService.createApplication(applicationData)
      console.log('[UPLOAD] Application created successfully:', result.application?.id);
      
      // Normal creation - 201 Created
      return res.status(201).json({
        success: result.success,
        status: result.status,
        message: result.message,
        application: result.application,
        isReupload: false
      });
    } catch (error) {
      console.error('[UPLOAD] Application creation failed:', error);
      return res.status(500).json({
        success: false,
        message: "Application creation failed"
      });
    }
  })
  
  getFarmerApplicationTimeline = asyncHandler(async (req: Request, res: Response) => {
    const { farmerId } = req.params

    if (!isUUID(farmerId)) {
      return res.status(400).json({ error: 'Invalid farmer ID' })
    }

    const result = await applicationsService.getFarmerApplicationTimeline(farmerId)
    res.json(result)
  })

  getApplicationVersionHistory = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params

    if (!isUUID(id)) {
      return res.status(400).json({ error: 'Invalid application ID' })
    }

    const result = await applicationsService.getApplicationVersionHistory(id)
    if (!result) {
      return res.status(404).json({ error: 'Application not found' })
    }
    
    res.json(result)
  })

  getFileUrl = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params

    if (!isUUID(id)) {
      return res.status(400).json({ error: 'Invalid application ID' })
    }

    const application = await applicationsService.getApplicationById(id)
    if (!application) {
      return res.status(404).json({ error: 'Application not found' })
    }

    if (!application.fileUrl) {
      return res.status(404).json({ error: 'File not found for application' })
    }

    // Generate real public URL using Supabase client
    const { data } = supabase.storage
      .from('documents')
      .getPublicUrl(application.fileUrl)

    if (!data?.publicUrl) {
      console.error('[FILE URL] Error generating public URL')
      return res.status(500).json({ error: 'Failed to generate file URL' })
    }

    res.json({ 
      fileUrl: data.publicUrl,
      fileName: application.fileName,
      fileType: application.fileType
    })
  })

  getFileUrlByPath = asyncHandler(async (req: Request, res: Response) => {
    const { path } = req.query

    if (!path || typeof path !== 'string' || path.trim() === '') {
      return res.status(400).json({ error: 'Path parameter is required' })
    }

    // Reject absolute URLs - only allow relative storage paths
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return res.status(400).json({ error: 'Absolute URLs not allowed' })
    }

    // Generate public URL using Supabase client for the specific storage path
    const { data } = supabase.storage
      .from('documents')
      .getPublicUrl(path)

    if (!data?.publicUrl) {
      console.error('[FILE URL BY PATH] Error generating public URL for path:', path)
      return res.status(500).json({ error: 'Failed to generate file URL' })
    }

    res.json({ 
      fileUrl: data.publicUrl
    })
  })

  getVerificationQueue = asyncHandler(async (req: Request, res: Response) => {
    const filters = {
      status: req.query.status as string,
      queue: req.query.queue as string,
      risk_level: req.query.risk_level as string,
      document_type: req.query.document_type as string,
      farmerId: req.query.farmerId as string,
      page: req.query.page ? Number(req.query.page) : undefined,
      limit: req.query.limit ? Number(req.query.limit) : undefined
    }

    const result = await applicationsService.getVerificationQueue(filters)
    res.json(result)
  })

  getDashboardMetrics = asyncHandler(async (req: Request, res: Response) => {
    const metrics = await applicationsService.getDashboardMetrics()
    res.json(metrics)
  })
}

export const applicationsController = new ApplicationsController()
