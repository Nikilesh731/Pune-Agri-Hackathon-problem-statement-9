/**
 * Global Type Definitions
 * Purpose: Shared TypeScript interfaces and types used across the application
 */

// TODO: Add actual type definitions as features are implemented
// This is a placeholder structure

export interface User {
  id: string
  email: string
  name: string
  role: string
}

export interface ApiResponse<T> {
  data: T
  message: string
  status: 'success' | 'error'
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

// Feature-specific types will be added here as needed
// export interface Application { ... }
// export interface Grievance { ... }
// export interface VerificationTask { ... }
