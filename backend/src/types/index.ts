/**
 * Global Type Definitions
 * Purpose: Shared TypeScript interfaces and types used across the backend
 */

// TODO: Add actual type definitions as features are implemented
// This is a placeholder structure

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'officer' | 'staff'
  password: string
  createdAt: Date
  updatedAt: Date
}

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error?: string
}

export interface PaginationParams {
  page: number
  limit: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
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

// Feature-specific types
export enum ApplicationStatus {
  UPLOADED = 'UPLOADED',
  PROCESSING = 'PROCESSING', 
  PROCESSED = 'PROCESSED',
  NEEDS_REVIEW = 'NEEDS_REVIEW',
  PENDING = 'PENDING',
  UNDER_REVIEW = 'UNDER_REVIEW',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  REQUIRES_ACTION = 'REQUIRES_ACTION'
}

export enum ApplicationType {
  SUBSIDY = 'subsidy',
  LOAN = 'loan',
  EQUIPMENT = 'equipment',
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export interface Application {
  id: string;
  applicationNumber: string;
  applicantId: string;
  schemeId: string;
  type: ApplicationType;
  status: ApplicationStatus;
  priority: Priority;
  submittedAt: Date;
  reviewedAt?: Date;
  approvedAt?: Date;
  rejectedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface DocumentType {
  id: string;
  name: string;
  type: string;
  required: boolean;
}

export interface CaseAssemblyResult {
  id: string;
  applicationId: string;
  documents: any[];
  isComplete: boolean;
  confidence?: number;
  primaryCaseType?: string;
  assembledAt: Date;
}

export interface Grievance {
  id: string;
  // Add grievance properties as needed
}

export interface VerificationTask {
  id: string;
  // Add verification task properties as needed
}

export interface Farmer {
  id: string;
  // Add farmer properties as needed
}
