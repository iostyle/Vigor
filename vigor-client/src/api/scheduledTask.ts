import request from './index'

export type ScheduledTaskKind = 'crawl' | 'update'
export type ScheduledTargetMode = 'category' | 'keyword' | 'video'
export type ScheduledScheduleType = 'interval' | 'daily'

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

export const scheduledTaskApi = {
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
