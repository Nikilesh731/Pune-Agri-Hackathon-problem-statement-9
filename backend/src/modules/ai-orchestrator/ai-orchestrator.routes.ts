/**
 * AI Orchestrator Routes
 * Purpose: Define Express routes for AI orchestration management
 */
import { Router } from 'express'
import { aiOrchestratorController } from './ai-orchestrator.controller'

const router = Router()

// AI orchestrator routes
router.post('/process-document', aiOrchestratorController.processDocument)
router.post('/classify-grievance', aiOrchestratorController.classifyGrievance)
router.post('/score-application', aiOrchestratorController.scoreApplication)
router.post('/detect-fraud', aiOrchestratorController.detectFraud)
router.post('/summarize-text', aiOrchestratorController.summarizeText)
router.get('/models', aiOrchestratorController.getAvailableModels)
router.get('/health', aiOrchestratorController.getAIHealth)

// Service health check
router.get('/service-health', aiOrchestratorController.healthCheck)

export { router as aiOrchestratorRoutes }
