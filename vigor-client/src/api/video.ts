import request from './index'
import type { Video, VideoListParams, VideoListResponse, Comment } from '@/types/video'

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
  }
}
