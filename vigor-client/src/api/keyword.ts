import request from './index'
import type { Keyword, KeywordCreateInput, KeywordUpdateInput } from '@/types/keyword'

export const keywordApi = {
  list(params?: { category_id?: number; limit?: number; offset?: number }): Promise<Keyword[]> {
    return request.get('/api/admin/keywords', { params })
  },

  create(data: KeywordCreateInput): Promise<Keyword> {
    return request.post('/api/admin/keywords', data)
  },

  update(keywordId: number, data: KeywordUpdateInput): Promise<Keyword> {
    return request.put(`/api/admin/keywords/${keywordId}`, data)
  },

  delete(keywordId: number): Promise<Keyword> {
    return request.delete(`/api/admin/keywords/${keywordId}`)
  }
}
