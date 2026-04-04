/**
 * Dashboard Page Component
 * Purpose: Real government admin dashboard with live metrics
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { 
  Users, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  TrendingUp,
  Activity,
  Eye,
  Calendar,
  BarChart3
} from 'lucide-react'
import { dashboardService, DashboardStats, TodayWorkloadItem } from '@/services/dashboardService'
import { StatCard } from '@/components/ui/StatCard'
import { StatusBadge } from '@/components/ui/StatusBadge'

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [todayWorkload, setTodayWorkload] = useState<TodayWorkloadItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await dashboardService.getDashboardData({ timeframe: 'today' })
      setStats(response.stats)
      setTodayWorkload(response.todayWorkload)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority?: number) => {
    if (!priority) return 'bg-gray-100 text-gray-700'
    if (priority > 70) return 'bg-red-100 text-red-700'
    if (priority > 40) return 'bg-yellow-100 text-yellow-700'
    return 'bg-green-100 text-green-700'
  }

  const getPriorityLabel = (priority?: number) => {
    if (!priority) return 'Normal'
    if (priority > 70) return 'High Priority'
    if (priority > 40) return 'Normal'
    return 'Low'
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Loading dashboard metrics...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-red-600 mt-2">{error || 'No data available'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-2">Agricultural Administration Portal</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Activity className="w-4 h-4" />
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <StatCard
            title="Total Applications"
            value={stats.totalApplications}
            icon={<FileText />}
            color="blue"
            trend={{ value: stats.todayApplications?.toString() || "0", isPositive: true }}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <StatCard
            title="Pending Review"
            value={stats.pendingReview}
            icon={<Clock />}
            color="yellow"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <StatCard
            title="Approved"
            value={stats.approvedCount}
            icon={<CheckCircle />}
            color="green"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <StatCard
            title="Needs Action"
            value={stats.requiresActionCount}
            icon={<AlertTriangle />}
            color="red"
          />
        </motion.div>
      </div>

      {/* Risk Distribution */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            Risk Distribution
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{stats.risk_distribution?.low || 0}</div>
              <div className="text-sm text-green-600">Low Risk</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-700">{stats.risk_distribution?.medium || 0}</div>
              <div className="text-sm text-yellow-600">Medium Risk</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-700">{stats.risk_distribution?.high || 0}</div>
              <div className="text-sm text-red-600">High Risk</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Queue Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            Queue Distribution
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-700">{stats.high_priority || 0}</div>
              <div className="text-sm text-red-600">High Priority</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-700">{stats.verificationQueueCount}</div>
              <div className="text-sm text-yellow-600">Verification Queue</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-700">{stats.financialReviewCount}</div>
              <div className="text-sm text-orange-600">Financial Review</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-700">{stats.underVerification || 0}</div>
              <div className="text-sm text-gray-600">Normal Queue</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Quick Actions & Today's Workload */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="lg:col-span-1"
        >
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Quick Actions
            </h2>
            <div className="space-y-3">
              <Link
                to="/applications"
                className="block w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-center font-medium"
              >
                View All Applications
              </Link>
              <Link
                to="/verification"
                className="block w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center font-medium"
              >
                Verification Queue
              </Link>
              <Link
                to="/upload"
                className="block w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-center font-medium"
              >
                Upload Document
              </Link>
              <Link
                to="/farmer-records"
                className="block w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-center font-medium"
              >
                Farmer Records
              </Link>
            </div>
          </div>
        </motion.div>

        {/* Today's Workload */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
          className="lg:col-span-2"
        >
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-600" />
                Today's Workload
              </h2>
              <span className="text-sm text-gray-500">
                {todayWorkload.length} items
              </span>
            </div>
            
            {todayWorkload.length > 0 ? (
              <div className="space-y-3">
                {todayWorkload.slice(0, 5).map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                    className="flex items-center justify-between p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0">
                        <StatusBadge status={item.status} />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {item.applicantName || 'Unknown Applicant'}
                        </p>
                        <p className="text-sm text-gray-600">
                          {item.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      {item.priorityScore && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priorityScore)}`}>
                          {getPriorityLabel(item.priorityScore)}
                        </span>
                      )}
                      <Link
                        to={`/applications/${item.id}`}
                        className="p-1 hover:bg-gray-100 rounded transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4 text-gray-500" />
                      </Link>
                    </div>
                  </motion.div>
                ))}
                
                {todayWorkload.length > 5 && (
                  <div className="text-center pt-2">
                    <Link
                      to="/applications"
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      View all {todayWorkload.length} items →
                    </Link>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No items for today</p>
                <p className="text-sm text-gray-400 mt-1">
                  Check back later for new applications
                </p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Additional Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Farmers</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalFarmerRecords || 0}</p>
            </div>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Under Verification</p>
              <p className="text-2xl font-bold text-gray-900">{stats.verificationQueueCount}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Rejected</p>
              <p className="text-2xl font-bold text-gray-900">{stats.rejectedCount}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </motion.div>
    </div>
  )
}
