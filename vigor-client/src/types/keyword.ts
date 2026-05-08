export interface Keyword {
  id: number
  category_id: number
  keyword: string
  status: 'active' | 'paused' | 'archived'
  crawl_threshold: number
  priority: number
  created_at: string | null
  updated_at: string | null
}

export interface KeywordCreateInput {
  category_id: number
  keyword: string
  crawl_threshold?: number
  priority?: number
}

export interface KeywordUpdateInput {
  category_id?: number
  keyword?: string
  status?: 'active' | 'paused' | 'archived'
  crawl_threshold?: number
  priority?: number
}
