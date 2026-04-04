/**
 * Application Actions Component
 * Purpose: Handles application action buttons and loading states
 */
import { Button } from '../ui/Button'

interface ApplicationActionsProps {
  applicationStatus: string
  onApprove: () => void
  onReject: () => void
  onRequestClarification: () => void
  onReprocessWithAI: () => void
  actionLoading: string | null
  disabled?: boolean
}

export function ApplicationActions({
  applicationStatus,
  onApprove,
  onReject,
  onRequestClarification,
  onReprocessWithAI,
  actionLoading,
  disabled = false
}: ApplicationActionsProps) {
  const getAvailableActions = () => {
    const actions = []

    if (applicationStatus === 'needs_review' || applicationStatus === 'under_review') {
      actions.push({
        id: 'approve',
        label: 'Approve',
        variant: 'success' as const,
        onClick: onApprove,
        loading: actionLoading === 'approve'
      })
      
      actions.push({
        id: 'reject',
        label: 'Reject',
        variant: 'destructive' as const,
        onClick: onReject,
        loading: actionLoading === 'reject'
      })
    }

    if (applicationStatus === 'needs_review' || applicationStatus === 'under_review') {
      actions.push({
        id: 'clarification',
        label: 'Request Clarification',
        variant: 'warning' as const,
        onClick: onRequestClarification,
        loading: actionLoading === 'clarification'
      })
    }

    if (applicationStatus === 'processing' || applicationStatus === 'processed') {
      actions.push({
        id: 'reprocess',
        label: 'Reprocess with AI',
        variant: 'secondary' as const,
        onClick: onReprocessWithAI,
        loading: actionLoading === 'reprocess'
      })
    }

    return actions
  }

  const actions = getAvailableActions()

  if (actions.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        No actions available for this application status
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-medium text-gray-900">Actions</h3>
      
      <div className="flex flex-wrap gap-3">
        {actions.map(action => (
          <Button
            key={action.id}
            variant={action.variant}
            onClick={action.onClick}
            disabled={disabled || action.loading}
            className="min-w-[120px]"
          >
            {action.loading ? 'Loading...' : action.label}
          </Button>
        ))}
      </div>

      {applicationStatus === 'approved' && (
        <div className="text-sm text-green-600 font-medium">
          ✓ This application has been approved
        </div>
      )}

      {applicationStatus === 'rejected' && (
        <div className="text-sm text-red-600 font-medium">
          ✗ This application has been rejected
        </div>
      )}

      {applicationStatus === 'requires_action' && (
        <div className="text-sm text-yellow-600 font-medium">
          ⚠ This application requires additional information
        </div>
      )}
    </div>
  )
}
