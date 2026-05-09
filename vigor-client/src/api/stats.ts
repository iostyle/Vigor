import request from './index'

export interface TodayStats {
  date: string
  total: number
  by_platform: Record<string, number>
}

export const statsApi = {
  today(): Promise<TodayStats> {
    return request.get('/api/internal/stats/today')
  }
}
