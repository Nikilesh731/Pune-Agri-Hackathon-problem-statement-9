/**
 * Shared Common Types
 * Purpose: Type definitions shared across frontend, backend, and AI services
 */

// Base entity types
export interface BaseEntity {
  id: string
  createdAt: Date
  updatedAt: Date
}

// User types
export interface User extends BaseEntity {
  email: string
  name: string
  role: UserRole
  isActive: boolean
  lastLoginAt?: Date
}

export enum UserRole {
  ADMIN = 'admin',
  OFFICER = 'officer',
  STAFF = 'staff',
}

// Application types
export interface Application extends BaseEntity {
  applicationNumber: string
  farmerId: string
  type: ApplicationType
  status: ApplicationStatus
  priority: Priority
  submittedAt: Date
  reviewedAt?: Date
  reviewedBy?: string
  documents: ApplicationDocument[]
  metadata: Record<string, any>
}

export enum ApplicationType {
  SUBSIDY = 'subsidy',
  CROP_INSURANCE = 'crop_insurance',
  LAND_RECORD = 'land_record',
  IRRIGATION = 'irrigation',
  EQUIPMENT = 'equipment',
}

export enum ApplicationStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  UNDER_REVIEW = 'under_review',
  ADDITIONAL_INFO_REQUIRED = 'additional_info_required',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  VERIFIED = 'verified',
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

export interface ApplicationDocument {
  id: string
  fileName: string
  fileType: string
  fileSize: number
  uploadedAt: Date
  extractedText?: string
  verificationStatus?: DocumentVerificationStatus
}

export enum DocumentVerificationStatus {
  PENDING = 'pending',
  VERIFIED = 'verified',
  REJECTED = 'rejected',
  SUSPICIOUS = 'suspicious',
}

// Grievance types
export interface Grievance extends BaseEntity {
  grievanceNumber: string
  farmerId: string
  title: string
  description: string
  category: GrievanceCategory
  severity: GrievanceSeverity
  status: GrievanceStatus
  submittedAt: Date
  resolvedAt?: Date
  assignedTo?: string
  attachments: GrievanceAttachment[]
}

export enum GrievanceCategory {
  CROP_DAMAGE = 'crop_damage',
  SUBSIDY_ISSUE = 'subsidy_issue',
  LAND_DISPUTE = 'land_dispute',
  INFRASTRUCTURE = 'infrastructure',
  CORRUPTION = 'corruption',
  DELAY = 'delay',
  OTHER = 'other',
}

export enum GrievanceSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum GrievanceStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
  ESCALATED = 'escalated',
  CLOSED = 'closed',
}

export interface GrievanceAttachment {
  id: string
  fileName: string
  fileType: string
  fileSize: number
  uploadedAt: Date
}

// Farmer types
export interface Farmer extends BaseEntity {
  farmerId: string
  name: string
  email: string
  phone: string
  aadhaarNumber: string
  address: FarmerAddress
  landHoldings: LandHolding[]
  bankDetails: BankDetails
  isVerified: boolean
  verificationDate?: Date
}

export interface FarmerAddress {
  village: string
  district: string
  state: string
  pincode: string
  coordinates?: {
    latitude: number
    longitude: number
  }
}

export interface LandHolding {
  id: string
  surveyNumber: string
  area: number
  unit: AreaUnit
  location: string
  cropType?: string
  ownershipType: OwnershipType
}

export enum AreaUnit {
  HECTARE = 'hectare',
  ACRE = 'acre',
  BIGHA = 'bigha',
}

export enum OwnershipType {
  OWNED = 'owned',
  LEASED = 'leased',
  SHARED = 'shared',
}

export interface BankDetails {
  accountNumber: string
  ifscCode: string
  bankName: string
  branchName: string
}

// Verification types
export interface VerificationTask extends BaseEntity {
  taskId: string
  entityType: VerificationEntityType
  entityId: string
  type: VerificationType
  status: VerificationStatus
  assignedTo?: string
  assignedAt?: Date
  completedAt?: Date
  result?: VerificationResult
  notes?: string
}

export enum VerificationEntityType {
  APPLICATION = 'application',
  FARMER = 'farmer',
  DOCUMENT = 'document',
  GRIEVANCE = 'grievance',
}

export enum VerificationType {
  IDENTITY = 'identity',
  DOCUMENT = 'document',
  FIELD_VISIT = 'field_visit',
  BACKGROUND_CHECK = 'background_check',
}

export enum VerificationStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  REJECTED = 'rejected',
  ESCALATED = 'escalated',
}

export interface VerificationResult {
  isApproved: boolean
  confidence: number
  riskScore?: number
  findings: string[]
  recommendations: string[]
}

// Notification types
export interface Notification extends BaseEntity {
  recipientId: string
  type: NotificationType
  title: string
  message: string
  data?: Record<string, any>
  isRead: boolean
  readAt?: Date
  priority: NotificationPriority
}

export enum NotificationType {
  APPLICATION_SUBMITTED = 'application_submitted',
  APPLICATION_APPROVED = 'application_approved',
  APPLICATION_REJECTED = 'application_rejected',
  GRIEVANCE_RECEIVED = 'grievance_received',
  GRIEVANCE_RESOLVED = 'grievance_resolved',
  VERIFICATION_ASSIGNED = 'verification_assigned',
  SYSTEM_ALERT = 'system_alert',
}

export enum NotificationPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error?: string
  timestamp: Date
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

export interface ErrorResponse {
  success: false
  message: string
  error: string
  errorCode?: string
  details?: Record<string, any>
  timestamp: Date
}
