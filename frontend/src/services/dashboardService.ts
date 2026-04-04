/**
 * Dashboard API Service
 * Purpose: Service layer for dashboard-related API calls
 */
import { apiClient } from './api'

export interface DashboardStats {
  totalApplications: number
  pendingReview: number
  approvedCount: number
  rejectedCount: number
  requiresActionCount: number
  highPriorityCount: number
  financialReviewCount: number
  verificationQueueCount: number
  duplicateBlocksPrevented: number
  totalFarmerRecords?: number
  underVerification?: number
  processedApplications?: number
  todayApplications?: number
  todayWorkload?: number
  needsOfficerAction?: number
  // New fields for production-grade dashboard
  pending: number
  approved: number
  rejected: number
  high_priority: number
  risk_distribution: { low: number; medium: number; high: number }
}

export interface DocumentTypeDistribution {
  type: string
  count: number
}

export interface RiskDistribution {
  level: string
  count: number
}

export interface RecentActivity {
  id: string
  type: string
  description: string
  timestamp: string
  applicantId: string
  documentType: string
}

export interface DashboardMetrics {
  totalApplications: number
  pendingReview: number
  approvedCount: number
  rejectedCount: number
  requiresActionCount: number
  highPriorityCount: number
  financialReviewCount: number
  verificationQueueCount: number
  duplicateBlocksPrevented: number
  documentTypeDistribution: DocumentTypeDistribution[]
  riskDistribution: RiskDistribution[]
  recentActivity: RecentActivity[]
}

export interface TodayWorkloadItem {
  id: string
  type: string
  status: string
  submissionDate: string
  priorityScore?: number
  applicantName?: string
}

export interface DashboardResponse {
  stats: DashboardStats
  todayWorkload: TodayWorkloadItem[]
  recentWorkload: TodayWorkloadItem[]
  lastUpdated: string
}

export interface DashboardQuery {
  timeframe?: 'today' | 'week' | 'month'
  status?: string
}

class DashboardService {
  private endpoint = '/applications'

  async getDashboardData(_query: DashboardQuery = {}): Promise<DashboardResponse> {
    try {
      console.log('[Dashboard] fetching dashboard data...')
      
      // Get the summary data from the correct endpoint
      const summary = await this.getDashboardSummary()
      
      // Normalize backend snake_case to frontend camelCase in one place
      const stats: DashboardStats = {
        totalApplications: summary.total_applications,
        pendingReview: summary.pending,
        approvedCount: summary.approved,
        rejectedCount: summary.rejected,
        requiresActionCount: summary.requires_action || 0,
        highPriorityCount: summary.high_priority,
        financialReviewCount: 0,
        verificationQueueCount: summary.pending,
        duplicateBlocksPrevented: 0,
        totalFarmerRecords: 0,
        underVerification: summary.pending,
        processedApplications: summary.approved + summary.rejected,
        todayApplications: 0,
        todayWorkload: 0,
        needsOfficerAction: summary.requires_action || 0,
        // Raw backend fields for compatibility
        pending: summary.pending,
        approved: summary.approved,
        rejected: summary.rejected,
        high_priority: summary.high_priority,
        risk_distribution: summary.risk_distribution
      }

      // Empty workload for now since backend doesn't provide it
      const todayWorkload: TodayWorkloadItem[] = []

      return {
        stats,
        todayWorkload,
        recentWorkload: todayWorkload,
        lastUpdated: summary.last_updated
      }
    } catch (error) {
      console.error('Dashboard service error:', error)
      throw error
    }
  }

  async getDashboardSummary(): Promise<{
    total_applications: number
    pending: number
    approved: number
    rejected: number
    requires_action: number
    high_priority: number
    risk_distribution: { low: number; medium: number; high: number }
    last_updated: string
  }> {
    return apiClient.get<{
      total_applications: number
      pending: number
      approved: number
      rejected: number
      requires_action: number
      high_priority: number
      risk_distribution: { low: number; medium: number; high: number }
      last_updated: string
    }>('/dashboard/summary')
  }

  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const url = `${this.endpoint}/dashboard/metrics`
    return apiClient.get<DashboardMetrics>(url)
  }

  async getDashboardStats(query: DashboardQuery = {}): Promise<DashboardStats> {
    const response = await this.getDashboardData(query)
    return response.stats
  }

  async getTodayWorkload(): Promise<TodayWorkloadItem[]> {
    const response = await this.getDashboardData({ timeframe: 'today' })
    return response.todayWorkload
  }

  async refreshDashboard(): Promise<DashboardResponse> {
    return apiClient.post<DashboardResponse>(`${this.endpoint}/dashboard/refresh`, {})
  }
}

export const dashboardService = new DashboardService()
