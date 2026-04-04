/**
 * Applications Page Component
 * Purpose: Advanced case management with ML indicators and filters
 */
import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { applicationsService } from '../services/applicationsService'
import { mapApplicationsToList } from '../utils/applicationDetailMapper'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { LoadingState } from '../components/ui/LoadingState'
import { EmptyState } from '../components/ui/EmptyState'
import { SectionCard } from '../components/ui/SectionCard'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { AnimatedPageWrapper, AnimatedSection } from '../components/ui/AnimatedPageWrapper'
import { 
  Search, 
  Filter, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Eye,
  ChevronDown,
  Zap,
  TrendingUp,
  Upload,
  Calendar
} from 'lucide-react'

export function ApplicationsPage() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [sortBy, setSortBy] = useState('submissionDate')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Add ref to prevent duplicate requests in development
  const isLoadingRef = useRef(false)

  useEffect(() => {
    loadApplications()
  }, [])

  const loadApplications = async () => {
    // Prevent duplicate requests
    if (isLoadingRef.current) {
      return
    }

    try {
      isLoadingRef.current = true
      setLoading(true)
      const response = await applicationsService.getApplications({ page: 1, limit: 50 })
      
      // Map the response using the central mapper
      const mappedApplications = mapApplicationsToList(response.applications)
      setApplications(mappedApplications)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications')
    } finally {
      setLoading(false)
      isLoadingRef.current = false
    }
  }

  const getPriorityLevel = (app: any) => {
    const mlInsights = app.extractedData?.ml_insights
    if (!mlInsights?.priority_score) return 'normal'
    
    const score = mlInsights.priority_score
    if (score > 0.7) return 'high'
    if (score > 0.4) return 'medium'
    return 'low'
  }

  const getPriorityColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-700 border-green-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getPriorityIcon = (level: string) => {
    switch (level) {
      case 'high': return AlertTriangle
      case 'medium': return Clock
      case 'low': return CheckCircle
      default: return FileText
    }
  }

  const getRiskLevel = (app: any) => {
    const riskLevel = app.extractedData?.predictions?.risk_level?.toLowerCase()
    return riskLevel || 'low'
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const sortApplications = (apps: any[]) => {
    return [...apps].sort((a, b) => {
      let aValue: any, bValue: any

      switch (sortBy) {
        case 'priority':
          aValue = a.extractedData?.ml_insights?.priority_score || 0
          bValue = b.extractedData?.ml_insights?.priority_score || 0
          break
        case 'submissionDate':
          aValue = new Date(a.submissionDate).getTime()
          bValue = new Date(b.submissionDate).getTime()
          break
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        case 'type':
          aValue = a.type
          bValue = b.type
          break
        default:
          aValue = a.submissionDate
          bValue = b.submissionDate
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })
  }

  const filteredApplications = sortApplications(
    applications.filter(app => {
      const matchesSearch = searchTerm === '' || 
        app.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.fileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.extractedData?.canonical?.applicant?.name?.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStatus = statusFilter === 'all' || app.status === statusFilter
      const matchesType = typeFilter === 'all' || app.type === typeFilter
      const priorityLevel = getPriorityLevel(app)
      const matchesPriority = priorityFilter === 'all' || priorityLevel === priorityFilter
      
      return matchesSearch && matchesStatus && matchesType && matchesPriority
    })
  )
  
  if (loading && applications.length === 0) {
    return <LoadingState message="Loading applications..." />
  }

  return (
    <AnimatedPageWrapper variant="slide">
      <PageHeader 
        title="Case Management"
        subtitle="Manage farmer cases with AI-powered prioritization"
      >
        <Link to="/upload">
          <Button variant="success" className="group">
            <Upload className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" />
            Intake New Case
          </Button>
        </Link>
      </PageHeader>

      {error && (
        <AnimatedSection delay={0.1}>
          <Card variant="danger" className="mb-6">
            <div className="flex items-center">
              <span className="text-red-700">{error}</span>
            </div>
          </Card>
        </AnimatedSection>
      )}

      {/* Advanced Filters Section */}
      <AnimatedSection delay={0.2}>
        <SectionCard title="Advanced Filters" className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search cases..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
              />
            </div>
            
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all appearance-none bg-white"
              >
                <option value="all">All Statuses</option>
                <option value="uploaded">Uploaded</option>
                <option value="processing">Under Verification</option>
                <option value="under_review">Under Review</option>
                <option value="needs_review">Needs Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            
            <div className="relative">
              <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all appearance-none bg-white"
              >
                <option value="all">All Types</option>
                <option value="scheme_application">Scheme Applications</option>
                <option value="subsidy_claim">Subsidy Claims</option>
                <option value="insurance_claim">Insurance Claims</option>
                <option value="grievance">Grievances</option>
                <option value="farmer_record">Farmer Records</option>
                <option value="supporting_document">Supporting Documents</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            
            <div className="relative">
              <Zap className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all appearance-none bg-white"
              >
                <option value="all">All Priorities</option>
                <option value="high">High Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="low">Low Priority</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>

            <div className="relative">
              <TrendingUp className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-')
                  setSortBy(sort)
                  setSortOrder(order as 'asc' | 'desc')
                }}
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all appearance-none bg-white"
              >
                <option value="submissionDate-desc">Newest First</option>
                <option value="submissionDate-asc">Oldest First</option>
                <option value="priority-desc">High Priority First</option>
                <option value="priority-asc">Low Priority First</option>
                <option value="status-asc">Status A-Z</option>
                <option value="status-desc">Status Z-A</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </SectionCard>
      </AnimatedSection>

      {/* Cases List */}
      <AnimatedSection delay={0.3}>
        <SectionCard title={`Cases (${filteredApplications.length})`}>
          {filteredApplications.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <EmptyState
                  title="No cases found"
                  description={applications.length === 0 ? "No cases in the system. Start by intaking farmer documents." : "No cases match your current filters."}
                  action={
                    applications.length === 0 && (
                      <Link to="/upload">
                        <Button variant="success">
                          <Upload className="w-4 h-4 mr-2" />
                          Intake First Case
                        </Button>
                      </Link>
                    )
                  }
                />
              </motion.div>
          ) : (
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Case Details
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ML Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Level
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredApplications.map((application, index) => {
                    const priorityLevel = getPriorityLevel(application)
                    const PriorityIcon = getPriorityIcon(priorityLevel)
                    const riskLevel = getRiskLevel(application)
                    
                    return (
                      <motion.tr 
                        key={application.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                        className="hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => navigate(`/applications/${application.id}`)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              CASE-{application.id.slice(0, 8)}...
                            </div>
                            <div className="text-sm text-gray-500">
                              {application.extractedData?.canonical?.applicant?.name || 'Unknown Farmer'}
                            </div>
                            {application.fileName && (
                              <div className="text-xs text-gray-400">
                                {application.fileName}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {application.type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={application.status} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(priorityLevel)}`}>
                              <PriorityIcon className="w-3 h-3 mr-1" />
                              {priorityLevel.charAt(0).toUpperCase() + priorityLevel.slice(1)}
                            </span>
                            {application.extractedData?.ml_insights?.priority_score && (
                              <span className="text-xs text-gray-500">
                                {Math.round(application.extractedData.ml_insights.priority_score * 100)}%
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(riskLevel)}`}>
                            {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(application.submissionDate).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link
                            to={`/applications/${application.id}`}
                            className="inline-flex items-center text-green-600 hover:text-green-900 font-medium group"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Eye className="w-4 h-4 mr-1 group-hover:scale-110 transition-transform" />
                            Review
                          </Link>
                        </td>
                      </motion.tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </AnimatedSection>

      {total > applications.length && (
        <AnimatedSection delay={0.4}>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              Showing {filteredApplications.length} of {total} cases
            </p>
          </div>
        </AnimatedSection>
      )}
    </AnimatedPageWrapper>
  )
}
