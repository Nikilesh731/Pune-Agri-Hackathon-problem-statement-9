/**
 * Application Detail Page
 * Purpose: Main orchestrator for application detail view
 */
import { useParams, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { applicationsService } from '../services/applicationsService'
import { buildSafeDetailState, SafeApplicationState } from '../utils/applicationDetailMapper'
import { LoadingState } from '../components/ui/LoadingState'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { ApplicationHeader } from '../components/application/ApplicationHeader'
import { ApplicationActions } from '../components/application/ApplicationActions'
import { ApplicationSections } from '../components/application/ApplicationSections'


export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [application, setApplication] = useState<SafeApplicationState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      loadApplication(id)
    }
  }, [id])

  // Polling effect for processing status
  useEffect(() => {
    if (!application || application.aiProcessingStatus === 'completed' || application.aiProcessingStatus === 'failed') {
      return
    }

    const pollInterval = setInterval(async () => {
      if (!id) return
      try {
        const updatedApp = await applicationsService.getApplicationById(id)
        const safeState = buildSafeDetailState(updatedApp)
        
        setApplication(safeState)

        // Stop polling when processing is complete
        if (safeState.aiProcessingStatus === 'completed' || safeState.aiProcessingStatus === 'failed') {
          clearInterval(pollInterval)
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 3000) // Poll every 3 seconds

    return () => {
      clearInterval(pollInterval)
    }
  }, [id, application?.aiProcessingStatus])

  const loadApplication = async (applicationId: string) => {
    try {
      setLoading(true)
      const app = await applicationsService.getApplicationById(applicationId)
      const safeState = buildSafeDetailState(app)
      setApplication(safeState)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load application'
      setError(errorMessage)
      // Set safe fallback to prevent blank page
      const fallbackState = buildSafeDetailState({ 
        id: applicationId, 
        fileName: 'Failed to Load', 
        status: 'error',
        error: errorMessage 
      })
      setApplication(fallbackState)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!id || !application) return
    
    try {
      setActionLoading('approve')
      const updatedApp = await applicationsService.approveApplication(id)
      const safeState = buildSafeDetailState(updatedApp)
      setApplication(safeState)
    } catch (err) {
      console.error('Failed to approve application:', err)
      alert('Failed to approve application. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async () => {
    if (!id || !application) return
    
    try {
      setActionLoading('reject')
      const updatedApp = await applicationsService.rejectApplication(id)
      const safeState = buildSafeDetailState(updatedApp)
      setApplication(safeState)
    } catch (err) {
      console.error('Failed to reject application:', err)
      alert('Failed to reject application. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleRequestClarification = async () => {
    if (!id || !application) return
    
    try {
      setActionLoading('clarification')
      const updatedApp = await applicationsService.requestClarification(id)
      const safeState = buildSafeDetailState(updatedApp)
      setApplication(safeState)
    } catch (err) {
      console.error('Failed to request clarification:', err)
      alert('Failed to request clarification. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleReprocessWithAI = async () => {
    if (!id || !application) return
    
    try {
      setActionLoading('reprocess')
      const updatedApp = await applicationsService.reprocessWithAI(id)
      const safeState = buildSafeDetailState(updatedApp)
      setApplication(safeState)
    } catch (err) {
      console.error('Failed to reprocess with AI:', err)
      alert('Failed to reprocess with AI. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return <LoadingState message="Loading case file..." />
  }

  if (error || !application) {
    return (
      <ErrorBoundary>
        <div>
          <ApplicationHeader 
            application={application || {
              id: 'unknown',
              type: 'unknown',
              status: 'uploaded',
              fileName: 'Unknown File',
              fileType: 'unknown',
              personalInfo: {},
              farmInfo: {},
              documents: [],
              extractedData: {},
              aiSummary: '',
              aiProcessingStatus: 'pending',
              createdAt: null,
              reviewDate: null,
              submissionDate: new Date().toISOString(),
              applicantId: '',
              schemeId: '',
              updatedAt: new Date().toISOString(),
              normalizedData: {
                id: 'unknown',
                applicantId: '',
                status: 'uploaded',
                type: 'unknown',
                documentType: 'unknown',
                submissionDate: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                extractedFields: {},
                missingFields: [],
                completenessScore: 0,
                confidenceScore: 0,
                fraudFlags: [],
                sourceDocuments: [],
                aiSummary: '',
                priorityScore: 0,
                fraudRiskScore: 0,
                verificationRecommendation: '',
                aiProcessingStatus: 'pending',
                classificationConfidence: 0,
                classificationReasoning: [],
                canonicalData: null,
                riskFlags: [],
                decisionSupport: null,
                farmerId: null,
                farmer: null,
                caseId: null,
                case: null
              }
            }}
            showBackLink={false}
          />
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">{error || 'Application not found'}</p>
            <Link
              to="/applications"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
            >
              Back to Cases
            </Link>
          </div>
        </div>
      </ErrorBoundary>
    )
  }

  // Runtime logging for failure isolation
  if (application.id) {
    console.log('ApplicationDetailPage render check:', {
      id: application.id,
      status: application.status,
      aiProcessingStatus: application.aiProcessingStatus,
      documentType: application.type,
      normalizedDataKeys: application.normalizedData ? Object.keys(application.normalizedData) : 'none'
    })
  }

  return (
    <ErrorBoundary>
      <div>
        {/* Use only mapped/normalized data for all child components */}
        {(() => {
          const uiApplication = {
            ...application,
            // block raw nested extractedData from being used directly in UI
            extractedData: {},
            normalizedData: application.normalizedData || {}
          }

          return (
            <>
              <ApplicationHeader application={uiApplication} />

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2">
                  <ApplicationSections application={uiApplication} />
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                  <ApplicationActions
                    applicationStatus={uiApplication?.status || 'uploaded'}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onRequestClarification={handleRequestClarification}
                    onReprocessWithAI={handleReprocessWithAI}
                    actionLoading={actionLoading}
                  />
                </div>
              </div>
            </>
          )
        })()}
      </div>
    </ErrorBoundary>
  )
}
