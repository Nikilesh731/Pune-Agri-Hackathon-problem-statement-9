/**
 * Applications Routes
 * Purpose: Define Express routes for application management
 */
import { Router } from 'express'
import { applicationsController } from './applications.controller'
import { upload } from '../../middlewares/upload'

const router = Router()

// Health check first (before parameterized routes)
router.get('/health', applicationsController.healthCheck)

// Farmers route (must be before /:id routes)
router.get('/farmers', applicationsController.getFarmers)
router.get('/farmers/:farmerId', applicationsController.getFarmerById)

// File URL by path route (must be before /:id routes)
router.get('/file-url-by-path', applicationsController.getFileUrlByPath)

// File upload route (must be before /:id routes)
router.post('/with-file', upload.single('file'), applicationsController.createApplicationWithFile)

// Application CRUD routes
router.post('/', applicationsController.createApplication)
router.get('/', applicationsController.getApplications)
router.get('/:id', applicationsController.getApplicationById)
router.patch('/:id', applicationsController.updateApplication)
router.delete('/:id', applicationsController.deleteApplication)
router.get('/:id/status', applicationsController.getApplicationStatus)

// Application action routes
router.patch('/:id/approve', applicationsController.approveApplication)
router.patch('/:id/reject', applicationsController.rejectApplication)
router.patch('/:id/request-clarification', applicationsController.requestClarification)
router.post('/:id/reprocess', applicationsController.reprocessWithAI)
router.get('/:id/file-url', applicationsController.getFileUrl)

// Version history routes
router.get('/:id/versions', applicationsController.getApplicationVersionHistory)

// Farmer timeline routes
router.get('/farmers/:farmerId/timeline', applicationsController.getFarmerApplicationTimeline)

// Test data cleanup route
router.post('/cleanup', applicationsController.cleanupTestData)

// Workflow and dashboard routes
router.get('/queue/verification', applicationsController.getVerificationQueue)
router.get('/dashboard/metrics', applicationsController.getDashboardMetrics)

export { router as applicationsRoutes }
