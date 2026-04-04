/**
 * AI Orchestrator Controller
 * Purpose: Handle AI orchestration-related HTTP requests
 */
import { Request, Response } from 'express'
import { asyncHandler } from '../../middlewares/asyncHandler'
import { aiOrchestratorService } from './ai-orchestrator.service'

class AIOrchestratorController {
  processDocument = asyncHandler(async (req: Request, res: Response) => {
    const { fileUrl, fileName, fileType } = req.body
    const result = await aiOrchestratorService.processDocument({ fileUrl, fileName, fileType })
    res.json(result)
  })

  classifyGrievance = asyncHandler(async (req: Request, res: Response) => {
    const { text, includeSentiment } = req.body
    const result = await aiOrchestratorService.classifyGrievance(text, includeSentiment)
    res.json(result)
  })

  scoreApplication = asyncHandler(async (req: Request, res: Response) => {
    const { applicationData, scoringModel } = req.body
    const result = await aiOrchestratorService.scoreApplication(applicationData, scoringModel)
    res.json(result)
  })

  detectFraud = asyncHandler(async (req: Request, res: Response) => {
    const { data, analysisType } = req.body
    const result = await aiOrchestratorService.detectFraud(data, analysisType)
    res.json(result)
  })

  summarizeText = asyncHandler(async (req: Request, res: Response) => {
    const { text, summaryType, maxLength } = req.body
    const result = await aiOrchestratorService.summarizeText(text, summaryType, maxLength)
    res.json(result)
  })

  getAvailableModels = asyncHandler(async (req: Request, res: Response) => {
    const models = await aiOrchestratorService.getAvailableModels()
    res.json(models)
  })

  getAIHealth = asyncHandler(async (req: Request, res: Response) => {
    const health = await aiOrchestratorService.getAIHealth()
    res.json(health)
  })

  // Service health check
  healthCheck = asyncHandler(async (req: Request, res: Response) => {
    res.json({ message: 'AI orchestrator controller working' })
  })
}

export const aiOrchestratorController = new AIOrchestratorController()
