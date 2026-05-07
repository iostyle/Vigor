import request from './index'
import type { Keyword, KeywordCreateInput, KeywordUpdateInput } from '@/types/keyword'

export const keywordApi = {
  list(): Promise<Keyword[]> {
    return request.get('/api/admin/keywords')
  },

  get(keywordId: number): Promise<Keyword> {
    return request.get(`/api/admin/keywords/${keywordId}`)
  },

  create(data: KeywordCreateInput): Promise<Keyword> {
    return request.post('/api/admin/keywords', data)
  },

  update(keywordId: number, data: KeywordUpdateInput): Promise<Keyword> {
    return request.put(`/api/admin/keywords/${keywordId}`, data)
  },

  delete(keywordId: number): Promise<void> {
    return request.delete(`/api/admin/keywords/${keywordId}`)
  }
}
