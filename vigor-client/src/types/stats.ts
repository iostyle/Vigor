export interface KeywordStats {
  keyword_id: number
  keyword: string
  video_count: number
  avg_heat_score: number
}

export interface TrendStats {
  date: string
  video_count: number
  avg_heat_score: number
}
