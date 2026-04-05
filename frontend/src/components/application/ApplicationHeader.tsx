/**
 * Application Header Component
 * Purpose: Displays application header with navigation and status
 */
import { Link } from 'react-router-dom'
import { MappedApplication } from '../../utils/applicationDetailMapper'
import { PageHeader } from '../ui/PageHeader'
import { StatusBadge } from '../ui/StatusBadge'
import { getDocumentTypeLabel } from '../../utils/applicationDetailMapper'
import { AlertTriangle, Clock, CheckCircle, XCircle } from 'lucide-react'

interface ApplicationHeaderProps {
  application: MappedApplication
  showBackLink?: boolean
  backLinkTo?: string
}

export function ApplicationHeader({ 
  application, 
  showBackLink = true, 
  backLinkTo = '/applications' 
}: ApplicationHeaderProps) {
  // Get document type with correct priority order
  const getDocumentType = (app: MappedApplication) => {
    const normalizedData = (app as any).normalizedData
    if (normalizedData?.documentType) return normalizedData.documentType
    // Fallback to application.type only (avoid raw extractedData usage)
    return app.type || 'document_upload'
  }

  const documentType = getDocumentType(application)

  // Get workflow information
  const getWorkflowInfo = (app: MappedApplication) => {
    const normalized = (app as any).normalizedData || {}
    const mlInsights = normalized.mlInsights || normalized.ml_insights || {}

    return {
      status: (normalized.aiProcessingStatus || app.aiProcessingStatus || 'pending').toString(),
      priority: mlInsights.queue || 'NORMAL',
      riskLevel: mlInsights.risk_level || normalized.riskLevel || 'Medium',
      estimatedTime: mlInsights.processing_time || '2 days'
    }
  }

  const workflow = getWorkflowInfo(application)

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'auto_approved':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'pending_verification':
        return <Clock className="w-4 h-4 text-yellow-600" />
      case 'manual_review_required':
        return <AlertTriangle className="w-4 h-4 text-orange-600" />
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-600" />
      default:
        return <Clock className="w-4 h-4 text-blue-600" />
    }
  }

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high_priority':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'normal':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Get risk color
  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Get applicant display name from normalized data only
  const getApplicantName = (app: MappedApplication) => {
    const normalizedData = (app as any).normalizedData || {}
    return normalizedData.displayApplicantName || normalizedData.extractedFields?.farmerName || app.farmer?.name || app.applicantId || 'Unknown Applicant'
  }

  const applicantName = getApplicantName(application)

  return (
    <PageHeader 
      title={`${getDocumentTypeLabel(documentType)} - ${applicantName}`}
      subtitle={`${application.caseId || `CASE-${String(application.id).slice(0,8)}`} | ${(application.aiProcessingStatus?.toString().toLowerCase() === 'completed' || application.status?.toString().toLowerCase() === 'processed' || application.status?.toString().toLowerCase() === 'approved') ? 'CASE_READY' : 'UNDER_REVIEW'}`}
    >
      <div className="flex items-center justify-between">
        {showBackLink && (
          <Link
            to={backLinkTo}
            className="text-green-600 hover:text-green-900"
          >
            ← Back to Cases
          </Link>
        )}
        
        <div className="flex items-center space-x-4">
          {/* Application Status */}
          <StatusBadge status={application.status} />
          
          {/* Workflow Status */}
          <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 rounded-full border border-gray-200">
            {getStatusIcon(workflow.status)}
            <span className="text-sm font-medium text-gray-700">
              {workflow.status.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
          
          {/* Priority */}
          <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getPriorityColor(workflow.priority)}`}>
            Priority: {workflow.priority.replace(/_/g, ' ').toUpperCase()}
          </div>
          
          {/* Risk Level */}
          <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getRiskColor(workflow.riskLevel)}`}>
            Risk: {workflow.riskLevel.toUpperCase()}
          </div>
          
          {/* Document Type */}
          <div className="text-sm text-gray-500">
            Type: {getDocumentTypeLabel(documentType)}
          </div>
        </div>
      </div>
    </PageHeader>
  )
}
