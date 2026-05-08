import request from './index'

export interface Category {
  id: number
  name: string
  description: string | null
  icon: string | null
  sort_order: number
  status: 'active' | 'inactive'
  keyword_count: number
  created_at: string | null
  updated_at: string | null
}

export interface CategoryCreateInput {
  name: string
  description?: string
  icon?: string
  sort_order?: number
  status?: 'active' | 'inactive'
}

export interface CategoryUpdateInput {
  name?: string
  description?: string
  icon?: string
  sort_order?: number
  status?: 'active' | 'inactive'
}

export const categoryApi = {
  list(): Promise<Category[]> {
    return request.get('/api/internal/categories')
  },

  adminList(): Promise<Category[]> {
    return request.get('/api/admin/categories')
  },

  create(data: CategoryCreateInput): Promise<Category> {
    return request.post('/api/admin/categories', data)
  },

  update(id: number, data: CategoryUpdateInput): Promise<Category> {
    return request.put(`/api/admin/categories/${id}`, data)
  },

  delete(id: number): Promise<void> {
    return request.delete(`/api/admin/categories/${id}`)
  }
}
