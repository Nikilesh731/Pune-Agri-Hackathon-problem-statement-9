/**
 * Applications Routes
 * Purpose: Define application-related API routes
 */
import { Router } from 'express'
import { applicationsController } from '../modules/applications/applications.controller'
import { upload } from '../middlewares/upload'

const router = Router()

// Health check first (before parameterized routes)
router.get('/health', applicationsController.healthCheck)
router.get('/health/check', applicationsController.healthCheck)

// Farmers route (must be before /:id routes)
router.get('/farmers', applicationsController.getFarmers)

// CANONICAL UPLOAD ENDPOINT - Single source of truth for file uploads
router.post('/upload', upload.single('file'), applicationsController.createApplicationWithFile)

// CRUD operations
router.get('/', applicationsController.getApplications)
router.post('/', applicationsController.createApplication)
router.get('/:id', applicationsController.getApplicationById)
router.patch('/:id', applicationsController.updateApplication)
router.delete('/:id', applicationsController.deleteApplication)

// Status and actions
router.get('/:id/status', applicationsController.getApplicationStatus)
router.patch('/:id/approve', applicationsController.approveApplication)
router.patch('/:id/reject', applicationsController.rejectApplication)
router.patch('/:id/request-clarification', applicationsController.requestClarification)
router.post('/:id/reprocess', applicationsController.reprocessWithAI)

export default router
