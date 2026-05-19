import request from './index'

export interface CrawlTaskTriggerRequest {
  keyword_id: number
  platform: string
}

export interface CrawlByCategoryTriggerRequest {
  category_id: number
  platform: string
}

export interface UpdateTaskTriggerRequest {
  video_id?: number
  keyword_id?: number
  limit?: number
}

export interface UpdateByCategoryTriggerRequest {
  category_id: number
  limit?: number
}

export interface CrawlTaskResponse {
  task_id: number
  celery_task_id: string
  status: string
}

export interface CrawlByCategoryResponse {
  category_id: number
  keyword_count: number
  task_ids: number[]
  celery_task_ids: string[]
  status: string
}

export interface UpdateByCategoryResponse {
  category_id: number
  video_count: number
  limit: number
  task_ids: number[]
  celery_task_ids: string[]
  status: string
}

export interface UpdateTaskResponse {
  keyword_id?: number
  video_count?: number
  limit?: number
  task_id?: number
  celery_task_id?: string
  celery_task_ids?: string[]
  status: string
}

export interface Task {
  id: number
  keyword_id: number
  task_type: string
  source: 'manual' | 'scheduled' | 'system' | 'legacy'
  source_id: number | null
  status: string
  videos_crawled: number
  started_at: string
  completed_at: string | null
  error_message: string | null
  summary?: string | null
}

export interface TaskListResponse {
  data: Task[]
  total: number
}

export const taskApi = {
  triggerCrawl(data: CrawlTaskTriggerRequest): Promise<CrawlTaskResponse> {
    return request.post('/api/admin/tasks/crawl', data)
  },

  triggerCrawlByCategory(data: CrawlByCategoryTriggerRequest): Promise<CrawlByCategoryResponse> {
    return request.post('/api/admin/tasks/crawl-by-category', data)
  },

  triggerUpdate(data: UpdateTaskTriggerRequest): Promise<UpdateTaskResponse> {
    return request.post('/api/admin/tasks/update', data)
  },

  triggerUpdateByCategory(data: UpdateByCategoryTriggerRequest): Promise<UpdateByCategoryResponse> {
    return request.post('/api/admin/tasks/update-by-category', data)
  },

  list(params?: { page?: number; page_size?: number }): Promise<TaskListResponse> {
    return request.get('/api/admin/tasks', { params })
  }
}
