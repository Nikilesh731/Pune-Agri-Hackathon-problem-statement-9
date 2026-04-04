/**
 * Dashboard Routes
 * Purpose: Define Express routes for dashboard data
 */
import express from 'express'
import { asyncHandler } from '../middlewares/asyncHandler'
import { applicationsRepository } from '../modules/applications/applications.repository'

const router = express.Router()

router.get('/summary', asyncHandler(async (req: express.Request, res: express.Response) => {
  try {
    console.log('[Dashboard Summary] fetching REAL summary data...')
    
    // Get applications for summary statistics
    const allApplications = await applicationsRepository.getApplications({ page: 1, limit: 1000 })
    const applications = allApplications.applications
    
    // Calculate summary statistics from REAL data using STRICT status mapping
    const totalApplications = allApplications.total
    let pending = 0
    let approved = 0
    let rejected = 0
    let requiresAction = 0
    let highPriority = 0
    let riskDistribution = { low: 0, medium: 0, high: 0 }
    
    applications.forEach(app => {
      // Normalize status to lowercase with underscore for consistent comparison
      const status = (app.status || 'UPLOADED').toLowerCase().replace(/[-\s]/g, '_')
      
      // PENDING = uploaded + processing + under_review
      if (['uploaded', 'processing', 'under_review'].includes(status)) {
        pending++
      } else if (status === 'approved') {
        approved++
      } else if (status === 'rejected') {
        rejected++
      } else if (status === 'requires_action') {
        requiresAction++
      }
      
      // Count high priority using REAL ml_insights data
      const isHighPriority = app.extractedData?.ml_insights?.queue === 'HIGH_PRIORITY' ||
                           (app.priorityScore && app.priorityScore > 0.8)
      if (isHighPriority) {
        highPriority++
      }
      
      // Count risk distribution using REAL ml_insights data
      const riskLevel = app.extractedData?.ml_insights?.risk_level?.toLowerCase() || 
                       app.extractedData?.predictions?.risk_level?.toLowerCase() ||
                       'medium'
      if (['low', 'medium', 'high'].includes(riskLevel)) {
        (riskDistribution as any)[riskLevel]++
      } else {
        riskDistribution['medium']++ // Default to medium
      }
    })
    
    console.log('[Dashboard Summary] REAL metrics calculated:', {
      totalApplications,
      pending,
      approved,
      rejected,
      requiresAction,
      highPriority,
      riskDistribution
    })
    
    res.json({
      total_applications: totalApplications,
      pending: pending,
      approved: approved,
      rejected: rejected,
      requires_action: requiresAction,
      high_priority: highPriority,
      risk_distribution: riskDistribution,
      last_updated: new Date().toISOString()
    })
  } catch (error) {
    console.error('[Dashboard Summary] error:', error)
    // Only fallback to zeros on actual backend failure
    res.json({
      total_applications: 0,
      pending: 0,
      approved: 0,
      rejected: 0,
      requires_action: 0,
      high_priority: 0,
      risk_distribution: { low: 0, medium: 0, high: 0 },
      last_updated: new Date().toISOString()
    })
  }
}))

router.get('/', asyncHandler(async (req: express.Request, res: express.Response) => {
  try {
    console.log('[Dashboard] fetching dashboard data sequentially...')
    
    // SEQUENTIAL execution to avoid connection pool timeout with limit 1
    console.log('[Dashboard] fetching total records...')
    const totalRecords = await applicationsRepository.getApplications({ page: 1, limit: 1 })
    
    console.log('[Dashboard] fetching pending records...')
    const pendingRecords = await applicationsRepository.getApplications({ 
      page: 1,
      limit: 1,
      filters: { status: 'uploaded' }
    })
    
    console.log('[Dashboard] fetching under verification records...')
    const underVerificationRecords = await applicationsRepository.getApplications({
      page: 1,
      limit: 1,
      filters: { status: 'processing' }
    })
    
    console.log('[Dashboard] fetching needs action records...')
    const needsActionRecords = await applicationsRepository.getApplications({
      page: 1,
      limit: 1, 
      filters: { status: 'needs_review' }
    })
    
    console.log('[Dashboard] fetching today records...')
    const todayRecords = await applicationsRepository.getApplications({
      page: 1,
      limit: 1,
      filters: { submissionDateFrom: new Date(new Date().setHours(0, 0, 0, 0)) }
    })
    
    console.log('[Dashboard] fetching today workload data...')
    const todayWorkloadData = await applicationsRepository.getApplications({
      page: 1,
      limit: 10,
      sortBy: 'submissionDate',
      sortOrder: 'desc',
      filters: { submissionDateFrom: new Date(new Date().setHours(0, 0, 0, 0)) }
    })
    
    // Get detailed counts for each status - SEQUENTIAL execution
    console.log('[Dashboard] fetching detailed counts sequentially...')
    const allApplications = await applicationsRepository.getApplications({ page: 1, limit: 1000 })
    const pendingApps = await applicationsRepository.getApplications({ page: 1, limit: 1000, filters: { status: 'uploaded' } })
    const processingApps = await applicationsRepository.getApplications({ page: 1, limit: 1000, filters: { status: 'processing' } })
    const needsReviewApps = await applicationsRepository.getApplications({ page: 1, limit: 1000, filters: { status: 'needs_review' } })
    
    // Map today's workload to expected format
    const todayWorkload = todayWorkloadData.applications.map(app => ({
      id: app.id,
      type: app.type || 'Unknown Scheme',
      status: app.status,
      submissionDate: app.createdAt?.toISOString() || app.submissionDate?.toISOString() || new Date().toISOString(),
      priorityScore: app.priorityScore,
      applicantName: app.personalInfo?.firstName && app.personalInfo?.lastName 
        ? `${app.personalInfo.firstName} ${app.personalInfo.lastName}`
        : app.extractedData?.applicantName || 'Unknown Applicant'
    }))
    
    console.log('[Dashboard] completed fetching without pool timeout')
    
    res.json({
      stats: {
        totalFarmerRecords: allApplications.total,
        pendingApplications: pendingApps.total,
        underVerification: processingApps.total, 
        needsOfficerAction: needsReviewApps.total,
        totalApplications: allApplications.total,
        processedApplications: 0, // TODO: Add processed status filter
        approvedApplications: 0, // TODO: Add approved status filter
        rejectedApplications: 0, // TODO: Add rejected status filter
        todayApplications: todayRecords.total,
        todayWorkload: todayRecords.total
      },
      todayWorkload,
      lastUpdated: new Date().toISOString()
    })
  } catch (error) {
    console.error('[Dashboard] error:', error)
    // Fallback to zeros if database fails
    res.json({
      stats: {
        totalFarmerRecords: 0,
        pendingApplications: 0,
        underVerification: 0,
        needsOfficerAction: 0,
        totalApplications: 0,
        processedApplications: 0,
        approvedApplications: 0,
        rejectedApplications: 0,
        todayApplications: 0,
        todayWorkload: 0
      },
      todayWorkload: [],
      lastUpdated: new Date().toISOString()
    })
  }
}))

export default router
