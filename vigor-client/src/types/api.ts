export interface ApiResponse<T = any> {
  data: T
  message?: string
  code?: number
}

export interface ApiError {
  message: string
  code: number
  details?: any
}

export interface PaginationParams {
  limit?: number
  offset?: number
}

export interface PaginationResponse<T> {
  total: number
  data: T[]
}
