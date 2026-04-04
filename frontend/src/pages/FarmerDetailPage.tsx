import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  User, 
  Phone, 
  MapPin, 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  XCircle,
  ArrowLeft,
  Calendar,
  Eye,
  History
} from 'lucide-react'
import { farmerService } from '@/services/farmerService'

export function FarmerDetailPage() {
  const { farmerId } = useParams<{ farmerId: string }>()
  const navigate = useNavigate()
  const [farmer, setFarmer] = useState<any>(null)
  const [timeline, setTimeline] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  // Helper function to get document type display
  const getDocumentTypeDisplay = (app: any) => {
    const resolvedType = 
      app.extractedData?.canonical?.document_type ||
      app.extractedData?.document_type ||
      app.type ||
      'unknown';
    
    return resolvedType.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
  }

  // Helper function to get submission kind badge
  const getSubmissionKindBadge = (app: any) => {
    const isResubmission = app.parentApplicationId
    const kind = isResubmission ? 'resubmission' : 'initial'
    
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

  useEffect(() => {
    if (farmerId) {
      loadFarmer()
    }
  }, [farmerId])

  const loadFarmer = async () => {
    try {
      setError(null)
      setLoading(true)
      const [farmerData, timelineData] = await Promise.all([
        farmerService.getFarmerById(farmerId!),
        farmerService.getFarmerApplicationTimeline(farmerId!)
      ])
      setFarmer(farmerData)
      setTimeline(timelineData)
    } catch (e) {
      console.error(e)
      setError('Failed to load farmer details')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => navigate('/farmer-records')}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold">Loading Farmer Details...</h1>
        </div>
        <div className="text-center text-gray-500 mt-10">
          Loading farmer information...
        </div>
      </div>
    )
  }

  if (error || !farmer) {
    return (
      <div className="p-8">
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => navigate('/farmer-records')}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold">Farmer Not Found</h1>
        </div>
        <div className="text-center text-red-500 mt-10">
          {error || 'Farmer not found'}
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => navigate('/farmer-records')}
          className="p-2 hover:bg-gray-100 rounded-lg transition"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <User className="w-6 h-6 text-green-600" />
          Farmer Details
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Farmer Profile Section */}
        <div className="lg:col-span-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white border rounded-xl p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-green-600" />
              Profile Information
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Name</label>
                <p className="text-base font-medium">
                  {farmer.name || 'Unnamed Farmer'}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Aadhaar Number</label>
                <p className="text-base font-medium">
                  {farmer.aadhaarNumber || 'N/A'}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Mobile Number</label>
                <p className="text-base font-medium flex items-center gap-2">
                  <Phone className="w-4 h-4 text-gray-400" />
                  {farmer.mobileNumber || 'N/A'}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Location</label>
                <p className="text-base font-medium flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  {[farmer.village, farmer.district, farmer.state].filter(Boolean).join(', ') || 'Location not available'}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Total Applications</label>
                <p className="text-2xl font-bold text-green-600">
                  {farmer.applications?.length || 0}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Member Since</label>
                <p className="text-base font-medium flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  {new Date(farmer.createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Column - Applications and Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Applications Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white border rounded-xl p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-green-600" />
              Submitted Applications
            </h2>
            
            {farmer.applications && farmer.applications.length > 0 ? (
              <div className="space-y-4">
                {farmer.applications.map((app: any) => (
                  <motion.div
                    key={app.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                    onClick={() => navigate(`/applications/${app.id}`)}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium text-gray-900">
                            {app.fileName || 'Document'}
                          </h3>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              navigate(`/applications/${app.id}`)
                            }}
                            className="p-1 hover:bg-gray-100 rounded transition"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4 text-gray-500" />
                          </button>
                        </div>
                        
                        <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                          <span>{getDocumentTypeDisplay(app)}</span>
                          <span>•</span>
                          <span>{new Date(app.createdAt || app.submissionDate).toLocaleDateString()}</span>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {getSubmissionKindBadge(app)}
                          <span className="text-xs text-gray-400">
                            Version: {app.versionNumber || 1}
                          </span>
                        </div>
                      </div>
                      
                      <div className="ml-4">
                        {getStatusBadge(app.status)}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No applications found</p>
                <p className="text-sm text-gray-400 mt-1">
                  This farmer hasn't submitted any documents yet
                </p>
              </div>
            )}
          </motion.div>

          {/* Timeline Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white border rounded-xl p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <History className="w-5 h-5 text-green-600" />
              Application Timeline
            </h2>
            
            {timeline && timeline.length > 0 ? (
              <div className="space-y-4">
                {timeline.map((event: any, index: number) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="flex gap-4 p-4 border rounded-lg hover:bg-gray-50 transition cursor-pointer"
                    onClick={() => navigate(`/applications/${event.id}`)}
                  >
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      {getStatusBadge(event.status).props.children[0]}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {getDocumentTypeDisplay(event)}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {new Date(event.submissionDate).toLocaleDateString()} at {new Date(event.submissionDate).toLocaleTimeString()}
                          </p>
                        </div>
                        {getStatusBadge(event.status)}
                      </div>
                      
                      {event.decisionDate && (
                        <p className="text-sm text-gray-500">
                          Decision: {new Date(event.decisionDate).toLocaleDateString()}
                        </p>
                      )}
                      
                      {event.notes && (
                        <p className="text-sm text-gray-600 mt-2">
                          {event.notes}
                        </p>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <History className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No timeline events found</p>
                <p className="text-sm text-gray-400 mt-1">
                  Application history will appear here
                </p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
