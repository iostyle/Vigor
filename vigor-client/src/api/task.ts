import request from './index'

export interface CrawlTaskTriggerRequest {
  keyword_id: number
  platform: string
}

export interface CrawlTaskResponse {
  task_id: number
  celery_task_id: string
  status: string
}

export interface Task {
  id: number
  keyword_id: number
  task_type: string
  status: string
  videos_crawled: number
  started_at: string
  completed_at: string | null
  error_message: string | null
}

export const taskApi = {
  triggerCrawl(data: CrawlTaskTriggerRequest): Promise<CrawlTaskResponse> {
    return request.post('/api/admin/tasks/crawl', data)
  },

  list(params?: { page?: number; page_size?: number }): Promise<Task[]> {
    return request.get('/api/admin/tasks', { params })
  }
}
