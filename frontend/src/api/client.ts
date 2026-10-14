import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

class ApiClient {
  private client: AxiosInstance
  private refreshPromise: Promise<string> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            if (!this.refreshPromise) {
              this.refreshPromise = this.refreshAccessToken()
            }
            await this.refreshPromise
            return this.client(originalRequest)
          } catch {
            this.clearAuth()
            window.location.href = '/login'
            return Promise.reject(error)
          } finally {
            this.refreshPromise = null
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private async refreshAccessToken(): Promise<string> {
    const response = await this.client.post<{ access_token: string }>('/auth/refresh')
    return response.data.access_token
  }

  private clearAuth(): void {
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  async patch<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url)
    return response.data
  }

  // Auth endpoints
  async login(): Promise<void> {
    await this.client.get('/auth/login')
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout')
  }

  async getMe(): Promise<UserInfo> {
    return this.get<UserInfo>('/auth/me')
  }

  async demoLogin(): Promise<void> {
    await this.client.get('/auth/demo-login')
  }

  // Health endpoints
  async healthCheck(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health')
  }

  async healthDb(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health/db')
  }

  async readinessCheck(): Promise<ReadinessResponse> {
    return this.get<ReadinessResponse>('/health/ready')
  }
}

export interface HealthResponse {
  status: string
  app?: string
  version?: string
  debug?: boolean
  demo_mode?: boolean
  database?: string
  error?: string
}

export interface ReadinessResponse {
  status: string
  checks: Record<string, string>
}

export interface UserInfo {
  id: number
  subject: string
  email: string | null
  username: string | null
  full_name: string | null
  avatar_url: string | null
  role: 'viewer' | 'operator' | 'admin'
  is_active: boolean
}

export interface Skill {
  id: number
  source_type: string
  source_url: string
  source_ref: string | null
  owner: string
  repo: string
  skill_folder: string
  skill_name: string
  display_name: string | null
  description: string | null
  version: string | null
  author: string | null
  license: string | null
  homepage: string | null
  tags: string | null
  readme_content: string | null
  skill_md_content: string | null
  skill_folder_hash: string | null
  status: string
  discovered_at: string
  indexed_at: string | null
  last_checked_at: string | null
  error_message: string | null
}

export interface Installation {
  id: number
  user_id: number
  skill_id: number
  scope: 'project' | 'global'
  target_path: string
  installed_hash: string
  installed_at: string
  updated_at: string | null
  is_active: boolean
  metadata: string | null
  skill?: Skill
}

export interface LockfileEntry {
  id: number
  user_id: number
  skill_id: number
  scope: 'project' | 'global'
  source_url: string
  skill_folder: string
  skill_folder_hash: string
  target_path: string
  installed_at: string
  updated_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const api = new ApiClient()