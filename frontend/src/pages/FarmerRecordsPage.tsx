import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Users, 
  Search, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  XCircle,
  Calendar,
  FileText,
  Eye,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { farmerService } from '@/services/farmerService'

export function FarmerRecordsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [farmers, setFarmers] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [expandedFarmerId, setExpandedFarmerId] = useState<string | null>(
    searchParams.get('expanded')
  )
  const [error, setError] = useState<string | null>(null)
  const [farmerTimelines, setFarmerTimelines] = useState<Record<string, any[]>>({})

  // Helper function to get status badge
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      APPROVED: { icon: CheckCircle, color: 'text-green-600 bg-green-50', label: 'Approved' },
      UNDER_REVIEW: { icon: Clock, color: 'text-blue-600 bg-blue-50', label: 'Under Review' },
      REQUIRES_ACTION: { icon: AlertCircle, color: 'text-orange-600 bg-orange-50', label: 'Requires Action' },
      REJECTED: { icon: XCircle, color: 'text-red-600 bg-red-50', label: 'Rejected' },
      NEEDS_REVIEW: { icon: AlertCircle, color: 'text-yellow-600 bg-yellow-50', label: 'Needs Review' },
      UPLOADED: { icon: Clock, color: 'text-gray-600 bg-gray-50', label: 'Uploaded' },
      PROCESSING: { icon: Clock, color: 'text-blue-600 bg-blue-50', label: 'Processing' }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                  { icon: Clock, color: 'text-gray-600 bg-gray-50', label: status }
    
    const Icon = config.icon
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    )
  }

  // Helper function to get submission kind
  const getSubmissionKind = (app: any) => {
    if (app.parentApplicationId) {
      return 'resubmission'
    } else {
      return 'initial'
    }
  }

  // Helper function to get submission kind badge
  const getSubmissionKindBadge = (kind: string) => {
    const kindConfig = {
      initial: { color: 'text-blue-600 bg-blue-50', label: 'Initial' },
      resubmission: { color: 'text-orange-600 bg-orange-50', label: 'Resubmission' }
    }
    
    const config = kindConfig[kind as keyof typeof kindConfig] || 
                  { color: 'text-gray-600 bg-gray-50', label: kind }
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    )
  }

  // Helper function to get document type display
  const getDocumentTypeDisplay = (app: any) => {
    const resolvedType = 
      app.extractedData?.canonical?.document_type ||
      app.extractedData?.document_type ||
      app.type ||
      'unknown';
    
    return resolvedType.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
  }

  // Load farmer timeline data
  const loadFarmerTimeline = async (farmerId: string) => {
    if (farmerTimelines[farmerId]) {
      return // Already loaded
    }

    try {
      const timeline = await farmerService.getFarmerApplicationTimeline(farmerId)
      setFarmerTimelines(prev => ({
        ...prev,
        [farmerId]: timeline
      }))
    } catch (err) {
      console.error('Failed to load farmer timeline:', err)
    }
  }

  useEffect(() => {
    loadFarmers()
  }, [])

  useEffect(() => {
    const expanded = searchParams.get('expanded')
    setExpandedFarmerId(expanded)
  }, [searchParams])

  // Load timeline when farmer is expanded
  useEffect(() => {
    if (expandedFarmerId) {
      loadFarmerTimeline(expandedFarmerId)
    }
  }, [expandedFarmerId])

  const loadFarmers = async () => {
    try {
      setError(null)
      setLoading(true)
      const data = await farmerService.getFarmers()
      setFarmers(data)
    } catch (e) {
      console.error(e)
      setError('Failed to load farmers')
    } finally {
      setLoading(false)
    }
  }

  const filtered = farmers.filter(f => {
    const name = f.name?.toLowerCase() || ''
    const aadhaar = f.aadhaarNumber || ''
    const mobile = f.mobileNumber || ''

    return (
      name.includes(search.toLowerCase()) ||
      aadhaar.includes(search) ||
      mobile.includes(search)
    )
  })

  // Calculate farmer statistics
  const getFarmerStats = (farmer: any) => {
    const applications = farmer.applications || []
    const timeline = farmerTimelines[farmer.id] || []
    
    return {
      totalApplications: applications.length,
      approvedApplications: applications.filter((app: any) => app.status === 'APPROVED').length,
      pendingApplications: applications.filter((app: any) => ['PROCESSING', 'UNDER_REVIEW', 'NEEDS_REVIEW'].includes(app.status)).length,
      recentActivity: timeline.length > 0 ? new Date(timeline[0].submissionDate).toLocaleDateString() : null
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
          <Users className="w-8 h-8 text-green-600" />
          Farmer Records
        </h1>
        <p className="text-gray-600">
          Manage farmer profiles and track application timelines
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            placeholder="Search by name, Aadhaar, or mobile..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-800 rounded-full">
            <Clock className="w-4 h-4 mr-2 animate-spin" />
            Loading farmers...
          </div>
        </div>
      )}

      {/* Farmers List */}
      {!loading && (
        <div className="space-y-6">
          {filtered.map((farmer) => {
            const stats = getFarmerStats(farmer)
            const isExpanded = expandedFarmerId === farmer.id
            const timeline = farmerTimelines[farmer.id] || []
            
            return (
              <motion.div
                key={farmer.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Farmer Header */}
                <div 
                  className="p-6 cursor-pointer"
                  onClick={() => {
                    const nextId = isExpanded ? null : farmer.id
                    setExpandedFarmerId(nextId)

                    const nextParams = new URLSearchParams(searchParams)
                    if (nextId) {
                      nextParams.set('expanded', nextId)
                    } else {
                      nextParams.delete('expanded')
                    }

                    setSearchParams(nextParams, { replace: false })
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-xl font-semibold text-gray-900 hover:text-green-600 transition-colors">
                          {farmer.name || 'Unnamed Farmer'}
                        </h2>
                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">Aadhaar:</span> {farmer.aadhaarNumber || 'N/A'}
                        </div>
                        <div>
                          <span className="font-medium">Mobile:</span> {farmer.mobileNumber || 'N/A'}
                        </div>
                        <div>
                          <span className="font-medium">Location:</span> {[farmer.village, farmer.district, farmer.state].filter(Boolean).join(', ') || 'N/A'}
                        </div>
                      </div>
                      
                      {stats.recentActivity && (
                        <div className="mt-2 text-sm text-gray-500">
                          <span className="font-medium">Recent Activity:</span> {stats.recentActivity}
                        </div>
                      )}
                    </div>

                    {/* Stats Cards */}
                    <div className="flex items-center space-x-4 ml-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">{stats.totalApplications}</div>
                        <div className="text-xs text-gray-500">Total</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{stats.approvedApplications}</div>
                        <div className="text-xs text-gray-500">Approved</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{stats.pendingApplications}</div>
                        <div className="text-xs text-gray-500">Pending</div>
                      </div>
                      <Link
                        to={`/farmers/${farmer.id}`}
                        className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Eye className="w-4 h-4" />
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="border-t border-gray-200"
                  >
                    <div className="p-6 space-y-6">
                      {/* Case Timeline */}
                      {timeline.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-blue-600" />
                            Case Timeline
                          </h3>
                          <div className="space-y-3">
                            {timeline.map((event: any, index: number) => (
                              <motion.div
                                key={event.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  navigate(`/applications/${event.id}`)
                                }}
                              >
                                <div className="flex-shrink-0">
                                  {getStatusBadge(event.status)}
                                </div>
                                <div className="flex-1">
                                  <div className="font-medium text-gray-900">
                                    {getDocumentTypeDisplay(event)}
                                  </div>
                                  <div className="text-sm text-gray-600">
                                    Submitted: {new Date(event.submissionDate).toLocaleDateString()} at {new Date(event.submissionDate).toLocaleTimeString()}
                                  </div>
                                  {event.decisionDate && (
                                    <div className="text-sm text-gray-500">
                                      Decision: {new Date(event.decisionDate).toLocaleDateString()}
                                    </div>
                                  )}
                                  {event.notes && (
                                    <div className="text-sm text-gray-600 mt-1">
                                      {event.notes}
                                    </div>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  <Eye className="w-4 h-4 text-gray-400" />
                                </div>
                              </motion.div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Recent Applications */}
                      {farmer.applications && farmer.applications.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <FileText className="w-5 h-5 text-green-600" />
                            Recent Applications
                          </h3>
                          <div className="space-y-3">
                            {farmer.applications.slice(0, 5).map((app: any) => (
                              <div
                                key={app.id}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  navigate(`/applications/${app.id}`)
                                }}
                                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                              >
                                <div className="flex-1">
                                  <div className="font-medium text-gray-900 mb-1">
                                    {app.fileName || 'Document'}
                                  </div>
                                  <div className="text-sm text-gray-600">
                                    {getDocumentTypeDisplay(app)}
                                  </div>
                                  <div className="text-xs text-gray-400 mt-1">
                                    {new Date(app.createdAt || app.submissionDate).toLocaleDateString()}
                                  </div>
                                  <div className="flex items-center gap-2 mt-2">
                                    {getSubmissionKindBadge(getSubmissionKind(app))}
                                    <span className="text-xs text-gray-400">
                                      Version: {app.versionNumber || 1}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex items-center gap-3">
                                  {getStatusBadge(app.status)}
                                  <Eye className="w-4 h-4 text-gray-400" />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* No Data State */}
                      {timeline.length === 0 && (!farmer.applications || farmer.applications.length === 0) && (
                        <div className="text-center py-8">
                          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                          <p className="text-gray-500">No applications or timeline data available</p>
                          <p className="text-sm text-gray-400 mt-1">
                            Upload documents to see case history
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Empty State */}
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No farmers found</h3>
          <p className="text-gray-500">
            {farmers.length === 0 
              ? "Upload documents to generate farmer records" 
              : "No farmers match your search criteria"
            }
          </p>
        </div>
      )}
    </div>
  )
}
