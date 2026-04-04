/**
 * Verification Queue Page
 * Purpose: Real verification queue with ML-prioritized applications
 */
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  FileText,
  Search,
  Filter,
  Eye,
  Zap,
  TrendingUp,
  ChevronDown
} from 'lucide-react'
import { StatusBadge } from '../components/ui/StatusBadge'
import { LoadingState } from '../components/ui/LoadingState'
import { EmptyState } from '../components/ui/EmptyState'
import { SectionCard } from '../components/ui/SectionCard'
import { Button } from '../components/ui/Button'
import { normalizeQueueItem, NormalizedQueueItem } from '../utils/applicationDetailMapper'

export function VerificationPage() {
  const navigate = useNavigate()
  const [queue, setQueue] = useState<NormalizedQueueItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [sortBy, setSortBy] = useState('priority')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  useEffect(() => {
    loadVerificationQueue()
  }, [])

  const loadVerificationQueue = async () => {
    try {
      setLoading(true)
      // Use the real verification queue endpoint
      const response = await fetch('/api/applications/queue/verification')
      if (!response.ok) {
        throw new Error('Failed to load verification queue')
      }
      const data = await response.json()
      
      // Use the normalized queue mapper
      const verificationItems = data.items.map((item: any) => normalizeQueueItem(item))
      
      setQueue(verificationItems)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load verification queue')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityLevel = (priorityScore?: number) => {
    if (!priorityScore) return 'normal'
    if (priorityScore > 70) return 'high'
    if (priorityScore > 40) return 'medium'
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

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const sortQueue = (items: NormalizedQueueItem[]) => {
    return [...items].sort((a, b) => {
      let aValue: any, bValue: any

      switch (sortBy) {
        case 'priority':
          aValue = a.priorityScoreNormalized || 0
          bValue = b.priorityScoreNormalized || 0
          break
        case 'submissionDate':
          aValue = new Date(a.submittedAt).getTime()
          bValue = new Date(b.submittedAt).getTime()
          break
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        case 'risk':
          aValue = a.riskLevel || 'low'
          bValue = b.riskLevel || 'low'
          break
        default:
          aValue = a.priorityScoreNormalized || 0
          bValue = b.priorityScoreNormalized || 0
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })
  }

  const filteredQueue = sortQueue(
    queue.filter(item => {
      const matchesSearch = searchTerm === '' || 
        item.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.fileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.documentType.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.displayApplicantName?.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStatus = statusFilter === 'all' || item.status === statusFilter
      const priorityLevel = getPriorityLevel(item.priorityScoreNormalized)
      const matchesPriority = priorityFilter === 'all' || priorityLevel === priorityFilter
      
      return matchesSearch && matchesStatus && matchesPriority
    })
  )

  const queueStats = {
    pending: queue.filter(item => item.status === 'processing').length,
    inProgress: queue.filter(item => item.status === 'under_review').length,
    needsAttention: queue.filter(item => item.status === 'needs_review').length,
    highPriority: queue.filter(item => getPriorityLevel(item.priorityScoreNormalized) === 'high').length,
  }

  if (loading) {
    return <LoadingState message="Loading verification queue..." />
  }

  return (
    <div className="p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-green-600" />
              Verification Queue
            </h1>
            <p className="text-gray-600 mt-2">
              AI-prioritized verification queue for document review
            </p>
          </div>
          <Button onClick={loadVerificationQueue} variant="secondary">
            Refresh Queue
          </Button>
        </div>
      </motion.div>

      {/* Status Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
      >
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending Review</p>
              <p className="text-2xl font-bold text-gray-900">{queueStats.pending}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">In Progress</p>
              <p className="text-2xl font-bold text-gray-900">{queueStats.inProgress}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Needs Attention</p>
              <p className="text-2xl font-bold text-gray-900">{queueStats.needsAttention}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Priority</p>
              <p className="text-2xl font-bold text-gray-900">{queueStats.highPriority}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <SectionCard title="Queue Filters">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search queue..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none bg-white"
              >
                <option value="all">All Statuses</option>
                <option value="processing">Pending Review</option>
                <option value="under_review">In Progress</option>
                <option value="needs_review">Needs Attention</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            
            <div className="relative">
              <Zap className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none bg-white"
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
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none bg-white"
              >
                <option value="priority-desc">High Priority First</option>
                <option value="priority-asc">Low Priority First</option>
                <option value="submissionDate-desc">Newest First</option>
                <option value="submissionDate-asc">Oldest First</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </SectionCard>
      </motion.div>

      {/* Queue Items */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <SectionCard title={`Verification Queue (${filteredQueue.length})`}>
          {error ? (
            <div className="text-center py-8">
              <p className="text-red-600">{error}</p>
              <Button onClick={loadVerificationQueue} className="mt-4">
                Retry
              </Button>
            </div>
          ) : filteredQueue.length === 0 ? (
            <EmptyState
              title="Queue is empty"
              description={queue.length === 0 ? "No items in verification queue" : "No items match your current filters"}
            />
          ) : (
            <div className="space-y-3">
              {filteredQueue.map((item, index) => {
                const priorityLevel = getPriorityLevel(item.priorityScoreNormalized)
                const riskLevel = item.riskLevel?.toLowerCase() || 'low'
                
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => navigate(`/applications/${item.id}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="font-medium text-gray-900">
                            CASE-{item.id.slice(0, 8)}...
                          </div>
                          <StatusBadge status={item.status} />
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(priorityLevel)}`}>
                            {priorityLevel.charAt(0).toUpperCase() + priorityLevel.slice(1)} Priority
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(riskLevel)}`}>
                            {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk
                          </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 space-y-1">
                          <div>
                            <span className="font-medium">Applicant:</span> {item.displayApplicantName || 'Unknown'}
                          </div>
                          <div>
                            <span className="font-medium">Document:</span> {item.fileName}
                          </div>
                          <div>
                            <span className="font-medium">Type:</span> {item.displayDocumentType}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {item.priorityScoreNormalized && (
                          <div className="text-right">
                            <div className="text-xs text-gray-500">Priority Score</div>
                            <div className="text-lg font-bold text-gray-900">
                              {Math.round(item.priorityScoreNormalized)}%
                            </div>
                          </div>
                        )}
                        <Link
                          to={`/applications/${item.id}`}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Eye className="w-5 h-5 text-gray-500" />
                        </Link>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </SectionCard>
      </motion.div>
    </div>
  )
}
