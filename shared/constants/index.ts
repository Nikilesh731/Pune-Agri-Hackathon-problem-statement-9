/**
 * Shared Constants
 * Purpose: Constants shared across frontend, backend, and AI services
 */

// API Endpoints
export const API_ENDPOINTS = {
  // Backend endpoints
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REGISTER: '/api/auth/register',
    PROFILE: '/api/auth/profile',
    REFRESH: '/api/auth/refresh',
  },
  APPLICATIONS: {
    LIST: '/api/applications',
    CREATE: '/api/applications',
    GET: '/api/applications/:id',
    UPDATE: '/api/applications/:id',
    DELETE: '/api/applications/:id',
    SUBMIT: '/api/applications/:id/submit',
    APPROVE: '/api/applications/:id/approve',
    REJECT: '/api/applications/:id/reject',
  },
  GRIEVANCES: {
    LIST: '/api/grievances',
    CREATE: '/api/grievances',
    GET: '/api/grievances/:id',
    UPDATE: '/api/grievances/:id',
    ASSIGN: '/api/grievances/:id/assign',
    RESOLVE: '/api/grievances/:id/resolve',
  },
  VERIFICATION: {
    LIST: '/api/verification',
    GET: '/api/verification/:id',
    ASSIGN: '/api/verification/:id/assign',
    COMPLETE: '/api/verification/:id/complete',
    ESCALATE: '/api/verification/:id/escalate',
  },
  ANALYTICS: {
    DASHBOARD: '/api/analytics/dashboard',
    REPORTS: '/api/analytics/reports',
    METRICS: '/api/analytics/metrics',
    EXPORT: '/api/analytics/export',
  },
  FARMERS: {
    LIST: '/api/farmers',
    GET: '/api/farmers/:id',
    CREATE: '/api/farmers',
    UPDATE: '/api/farmers/:id',
    VERIFY: '/api/farmers/:id/verify',
    STATUS: '/api/farmers/:id/status',
  },
  NOTIFICATIONS: {
    LIST: '/api/notifications',
    MARK_READ: '/api/notifications/:id/read',
    MARK_ALL_READ: '/api/notifications/read-all',
    SEND: '/api/notifications/send',
  },
  SETTINGS: {
    USER: '/api/settings/user',
    SYSTEM: '/api/settings/system',
    PREFERENCES: '/api/settings/preferences',
  },

  // AI Service endpoints
  AI_SERVICES: {
    OCR: {
      EXTRACT_TEXT: '/api/ocr/extract-text',
      BATCH_EXTRACT: '/api/ocr/extract-text-batch',
      LANGUAGES: '/api/ocr/languages',
    },
    CLASSIFICATION: {
      CLASSIFY: '/api/classification/classify',
      BATCH_CLASSIFY: '/api/classification/classify-batch',
      CATEGORIES: '/api/classification/categories',
      RETRAIN: '/api/classification/retrain',
    },
    SCORING: {
      SCORE: '/api/scoring/score',
      BATCH_SCORE: '/api/scoring/score-batch',
      CRITERIA: '/api/scoring/criteria',
    },
    FRAUD_DETECTION: {
      DETECT: '/api/fraud-detection/detect',
      BATCH_DETECT: '/api/fraud-detection/detect-batch',
      INDICATORS: '/api/fraud-detection/indicators',
    },
    HEALTH: '/health',
  },
} as const

// Status Colors for UI
export const STATUS_COLORS = {
  // Application status colors
  APPLICATION_STATUS: {
    DRAFT: 'gray',
    SUBMITTED: 'blue',
    UNDER_REVIEW: 'yellow',
    ADDITIONAL_INFO_REQUIRED: 'orange',
    APPROVED: 'green',
    REJECTED: 'red',
    VERIFIED: 'green',
  },
  // Grievance status colors
  GRIEVANCE_STATUS: {
    OPEN: 'blue',
    IN_PROGRESS: 'yellow',
    RESOLVED: 'green',
    ESCALATED: 'orange',
    CLOSED: 'gray',
  },
  // Verification status colors
  VERIFICATION_STATUS: {
    PENDING: 'yellow',
    IN_PROGRESS: 'blue',
    COMPLETED: 'green',
    REJECTED: 'red',
    ESCALATED: 'orange',
  },
  // Priority colors
  PRIORITY: {
    LOW: 'gray',
    MEDIUM: 'blue',
    HIGH: 'orange',
    URGENT: 'red',
  },
  // Severity colors
  SEVERITY: {
    LOW: 'green',
    MEDIUM: 'yellow',
    HIGH: 'orange',
    CRITICAL: 'red',
  },
} as const

// Application Configuration
export const APP_CONFIG = {
  // Pagination
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // File uploads
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_FILE_TYPES: [
    'image/jpeg',
    'image/png',
    'image/pdf',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ],
  
  // Session
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  TOKEN_REFRESH_THRESHOLD: 5 * 60 * 1000, // 5 minutes
  
  // Rate limiting
  RATE_LIMIT: {
    REQUESTS_PER_MINUTE: 100,
    BURST_SIZE: 20,
  },
  
  // AI Service timeouts
  AI_TIMEOUTS: {
    OCR: 30000, // 30 seconds
    CLASSIFICATION: 10000, // 10 seconds
    SCORING: 15000, // 15 seconds
    FRAUD_DETECTION: 20000, // 20 seconds
  },
} as const

// Validation Rules
export const VALIDATION_RULES = {
  // User validation
  USER: {
    NAME_MIN_LENGTH: 2,
    NAME_MAX_LENGTH: 100,
    EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    PASSWORD_MIN_LENGTH: 8,
    PASSWORD_MAX_LENGTH: 128,
  },
  
  // Farmer validation
  FARMER: {
    AADHAAR_PATTERN: /^\d{12}$/,
    PHONE_PATTERN: /^\d{10}$/,
    PINCODE_PATTERN: /^\d{6}$/,
  },
  
  // Application validation
  APPLICATION: {
    TITLE_MIN_LENGTH: 5,
    TITLE_MAX_LENGTH: 200,
    DESCRIPTION_MIN_LENGTH: 10,
    DESCRIPTION_MAX_LENGTH: 2000,
  },
  
  // Grievance validation
  GRIEVANCE: {
    TITLE_MIN_LENGTH: 5,
    TITLE_MAX_LENGTH: 200,
    DESCRIPTION_MIN_LENGTH: 20,
    DESCRIPTION_MAX_LENGTH: 5000,
  },
} as const

// Error Codes
export const ERROR_CODES = {
  // Authentication errors
  AUTH: {
    INVALID_CREDENTIALS: 'AUTH_INVALID_CREDENTIALS',
    TOKEN_EXPIRED: 'AUTH_TOKEN_EXPIRED',
    TOKEN_INVALID: 'AUTH_TOKEN_INVALID',
    UNAUTHORIZED: 'AUTH_UNAUTHORIZED',
    FORBIDDEN: 'AUTH_FORBIDDEN',
  },
  
  // Validation errors
  VALIDATION: {
    REQUIRED_FIELD: 'VALIDATION_REQUIRED_FIELD',
    INVALID_FORMAT: 'VALIDATION_INVALID_FORMAT',
    INVALID_LENGTH: 'VALIDATION_INVALID_LENGTH',
    INVALID_VALUE: 'VALIDATION_INVALID_VALUE',
  },
  
  // Business logic errors
  BUSINESS: {
    DUPLICATE_APPLICATION: 'BUSINESS_DUPLICATE_APPLICATION',
    INVALID_STATUS_TRANSITION: 'BUSINESS_INVALID_STATUS_TRANSITION',
    INSUFFICIENT_PERMISSIONS: 'BUSINESS_INSUFFICIENT_PERMISSIONS',
    RESOURCE_NOT_FOUND: 'BUSINESS_RESOURCE_NOT_FOUND',
  },
  
  // System errors
  SYSTEM: {
    INTERNAL_ERROR: 'SYSTEM_INTERNAL_ERROR',
    DATABASE_ERROR: 'SYSTEM_DATABASE_ERROR',
    EXTERNAL_SERVICE_ERROR: 'SYSTEM_EXTERNAL_SERVICE_ERROR',
    RATE_LIMIT_EXCEEDED: 'SYSTEM_RATE_LIMIT_EXCEEDED',
  },
  
  // AI Service errors
  AI_SERVICE: {
    OCR_FAILED: 'AI_OCR_FAILED',
    CLASSIFICATION_FAILED: 'AI_CLASSIFICATION_FAILED',
    SCORING_FAILED: 'AI_SCORING_FAILED',
    FRAUD_DETECTION_FAILED: 'AI_FRAUD_DETECTION_FAILED',
    MODEL_NOT_LOADED: 'AI_MODEL_NOT_LOADED',
    PROCESSING_TIMEOUT: 'AI_PROCESSING_TIMEOUT',
  },
} as const

// Notification Templates
export const NOTIFICATION_TEMPLATES = {
  APPLICATION_SUBMITTED: {
    title: 'Application Submitted',
    message: 'Your application #{applicationNumber} has been submitted successfully.',
  },
  APPLICATION_APPROVED: {
    title: 'Application Approved',
    message: 'Congratulations! Your application #{applicationNumber} has been approved.',
  },
  APPLICATION_REJECTED: {
    title: 'Application Rejected',
    message: 'Your application #{applicationNumber} has been rejected. Reason: {reason}',
  },
  GRIEVANCE_RECEIVED: {
    title: 'Grievance Received',
    message: 'We have received your grievance #{grievanceNumber}. We will address it soon.',
  },
  GRIEVANCE_RESOLVED: {
    title: 'Grievance Resolved',
    message: 'Your grievance #{grievanceNumber} has been resolved. Resolution: {resolution}',
  },
  VERIFICATION_ASSIGNED: {
    title: 'Verification Task Assigned',
    message: 'A new verification task #{taskId} has been assigned to you.',
  },
} as const

// Export all constants
export * from './common'
