/**
 * Application Constants
 * Purpose: Centralized constants used across the application
 */

// TODO: Add actual constants as features are implemented
// This is a placeholder structure

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REGISTER: '/auth/register',
  },
  APPLICATIONS: '/applications',
  GRIEVANCES: '/grievances',
  VERIFICATION: '/verification',
  ANALYTICS: '/analytics',
  FARMERS: '/farmers',
  NOTIFICATIONS: '/notifications',
} as const

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/',
  APPLICATIONS: '/applications',
  GRIEVANCES: '/grievances',
  VERIFICATION: '/verification',
  ANALYTICS: '/analytics',
  FARMER_TRACKING: '/farmer-tracking',
  NOTIFICATIONS: '/notifications',
  SETTINGS: '/settings',
} as const

export const STATUS_COLORS = {
  PENDING: 'yellow',
  APPROVED: 'green',
  REJECTED: 'red',
  IN_PROGRESS: 'blue',
  COMPLETED: 'green',
} as const

export const ROLES = {
  ADMIN: 'admin',
  OFFICER: 'officer',
  STAFF: 'staff',
} as const
