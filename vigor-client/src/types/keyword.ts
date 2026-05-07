export interface Keyword {
  id: number
  keyword: string
  category: string | null
  status: 'active' | 'inactive'
  crawl_threshold: number
  priority: number
  created_at: string
  updated_at: string
}

export interface KeywordCreateInput {
  keyword: string
  category?: string
  crawl_threshold?: number
  priority?: number
}

export interface KeywordUpdateInput {
  keyword?: string
  category?: string
  status?: 'active' | 'inactive'
  crawl_threshold?: number
  priority?: number
}
