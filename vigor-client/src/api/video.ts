import request from './index'
import type { Video, VideoListParams, VideoListResponse, Comment } from '@/types/video'

export interface GenerateSummaryResponse {
  task_id: number
  celery_task_id: string
  status: string
}

export interface SummaryTaskStatusResponse {
  task_id: number | null
  status: string | null
  is_running: boolean
}

export type VideoStatus = 'active' | 'hidden' | 'archived'

export const videoApi = {
  list(params: VideoListParams): Promise<VideoListResponse> {
    return request.get('/api/internal/videos', { params })
  },

  get(videoId: number): Promise<Video> {
    return request.get(`/api/internal/videos/${videoId}`)
  },

  getComments(videoId: number, params: { limit?: number; offset?: number }): Promise<Comment[]> {
    return request.get(`/api/internal/videos/${videoId}/comments`, { params })
  },

  getSummary(videoId: number): Promise<Video> {
    return request.get(`/api/internal/videos/${videoId}/summary`)
  },

  generateSummary(videoId: number): Promise<GenerateSummaryResponse> {
    return request.post(`/api/admin/videos/${videoId}/generate-summary`)
  },

  getSummaryTaskStatus(videoId: number): Promise<SummaryTaskStatusResponse> {
    return request.get(`/api/admin/videos/${videoId}/summary-task`)
  },

  adminList(params: VideoListParams): Promise<VideoListResponse> {
    return request.get('/api/admin/videos', { params })
  },

  updateStatus(videoId: number, status: VideoStatus): Promise<Video> {
    return request.patch(`/api/admin/videos/${videoId}/status`, { status })
  }
}
