/**
 * API Client Service
 * Purpose: Centralized HTTP client for backend communication
 */

const RAW_API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'
const API_BASE_URL = RAW_API_BASE_URL.endsWith('/api')
  ? RAW_API_BASE_URL
  : `${RAW_API_BASE_URL}/api`

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: any,
    headers?: Record<string, string>
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    }

    if (data) {
      config.body = JSON.stringify(data)
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`)
      }

      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }

      return {} as T
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error(`API request failed: ${method} ${url}`)
    }
  }

  async get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>('GET', endpoint, undefined, headers)
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>('POST', endpoint, data)
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>('PUT', endpoint, data)
  }

  async patch<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>('PATCH', endpoint, data)
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>('DELETE', endpoint)
  }
}

export const apiClient = new ApiClient()