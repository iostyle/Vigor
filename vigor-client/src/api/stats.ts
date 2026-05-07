import request from './index'
import type { KeywordStats, TrendStats } from '@/types/stats'

export const statsApi = {
  getKeywordStats(): Promise<KeywordStats[]> {
    return request.get('/api/internal/stats/keywords')
  },

  getTrends(): Promise<TrendStats[]> {
    return request.get('/api/internal/stats/trends')
  }
}
