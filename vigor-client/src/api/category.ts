import request from './index'

export interface Category {
  category: string
  keyword_count: number
}

export const categoryApi = {
  list(): Promise<Category[]> {
    return request.get('/api/internal/categories')
  }
}
