export interface Video {
  id: number
  douyin_id: string
  title: string
  author_name: string | null
  author_id: string | null
  cover_url: string | null
  video_url: string | null
  like_count: number
  comment_count: number
  share_count: number
  heat_score: number | null
  publish_time: string | null
  summary: string | null
  comment_summary?: CommentSummary
}

export interface CommentSummary {
  summary: string
  top_keywords: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  generated_at: string
  comment_count: number
}

export interface Comment {
  id: number
  video_id: number
  content: string
  author_name: string | null
  like_count: number
  created_at: string
}

export interface VideoListParams {
  keyword_id?: number
  category_id?: number
  platform?: string
  time_window?: '1d' | '3d' | '7d' | '15d' | '30d'
  sort?: 'heat_score' | 'publish_time'
  limit?: number
  offset?: number
}

export interface VideoListResponse {
  total: number
  data: Video[]
}
