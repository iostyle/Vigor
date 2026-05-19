import request from './index'

export type ScheduledTaskKind = 'crawl' | 'update'
export type ScheduledTargetMode = 'category' | 'keyword' | 'video'
export type ScheduledScheduleType = 'interval' | 'daily'
export type SchedulerHealthStatus = 'healthy' | 'delayed' | 'stalled'

export interface ScheduledTask {
  id: number
  name: string
  task_kind: ScheduledTaskKind
  target_mode: ScheduledTargetMode
  target_id: number | null
  platform: string | null
  limit: number | null
  schedule_type: ScheduledScheduleType
  interval_minutes: number | null
  daily_time: string | null
  enabled: boolean
  last_run_at: string | null
  next_run_at: string | null
  last_task_ids: number[]
  created_at: string | null
  updated_at: string | null
  target_label: string | null
}

export interface ScheduledTaskInput {
  name: string
  task_kind: ScheduledTaskKind
  target_mode: ScheduledTargetMode
  target_id: number | null
  platform?: string
  limit?: number | null
  schedule_type: ScheduledScheduleType
  interval_minutes?: number | null
  daily_time?: string | null
  enabled: boolean
}

export interface ScheduledTaskListResponse {
  total: number
  data: ScheduledTask[]
}

export interface ScheduledTaskMonitor {
  server_time: string
  health: {
    status: SchedulerHealthStatus
    message: string
    seconds_since_last_run: number | null
  }
  scheduler: {
    last_run_at: string | null
    last_finished_at: string | null
    last_status: string | null
    last_due_count: number
    last_dispatched_count: number
    last_failed_count: number
  }
  tasks: {
    enabled_count: number
    disabled_count: number
    due_count: number
    last_24h_total: number
    last_24h_success: number
    last_24h_failed: number
    last_24h_running: number
    source_counts: Record<string, number>
  }
  recent_tasks: Array<{
    id: number
    task_type: string
    status: string
    source: string
    source_id: number | null
    keyword_id: number | null
    videos_crawled: number
    started_at: string | null
    completed_at: string | null
    error_message: string | null
  }>
  recent_runs: Array<{
    id: number
    status: string
    started_at: string
    finished_at: string | null
    due_count: number
    dispatched_count: number
    failed_count: number
    triggered_task_ids: number[]
    error_message: string | null
  }>
}

export const scheduledTaskApi = {
  monitor(): Promise<ScheduledTaskMonitor> {
    return request.get('/api/admin/scheduled-tasks/monitor')
  },

  list(params?: { page?: number; page_size?: number }): Promise<ScheduledTaskListResponse> {
    return request.get('/api/admin/scheduled-tasks', { params })
  },

  create(data: ScheduledTaskInput): Promise<ScheduledTask> {
    return request.post('/api/admin/scheduled-tasks', data)
  },

  update(id: number, data: Partial<ScheduledTaskInput>): Promise<ScheduledTask> {
    return request.put(`/api/admin/scheduled-tasks/${id}`, data)
  },

  toggle(id: number, enabled: boolean): Promise<ScheduledTask> {
    return request.patch(`/api/admin/scheduled-tasks/${id}/enabled`, { enabled })
  },

  delete(id: number): Promise<void> {
    return request.delete(`/api/admin/scheduled-tasks/${id}`)
  }
}
