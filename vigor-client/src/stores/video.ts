import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Video, VideoListParams } from '@/types/video'
import { videoApi } from '@/api/video'

export const useVideoStore = defineStore('video', () => {
  const videos = ref<Video[]>([])
  const selectedVideo = ref<Video | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const currentCategoryId = ref<number | null>(null)
  const currentPlatform = ref<string | null>(null)
  const sortBy = ref<'heat_score' | 'publish_time'>('heat_score')
  const timeWindow = ref<'1d' | '3d' | '7d' | '15d' | '30d' | null>(null)

  async function fetchVideos(params?: VideoListParams) {
    loading.value = true
    try {
      const finalParams: VideoListParams = {
        category_id:
          currentCategoryId.value && currentCategoryId.value > 0
            ? currentCategoryId.value
            : undefined,
        platform: currentPlatform.value || undefined,
        time_window: timeWindow.value || undefined,
        sort: sortBy.value,
        limit: 20,
        offset: 0,
        ...params
      }
      const res = await videoApi.list(finalParams)
      videos.value = res.data
      total.value = res.total
    } catch (error) {
      console.warn('无法连接后端,视频列表为空:', error)
      videos.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  async function selectVideo(videoId: number) {
    loading.value = true
    try {
      const video = await videoApi.getSummary(videoId)
      selectedVideo.value = video
    } catch (error) {
      console.error('Failed to fetch video detail:', error)
    } finally {
      loading.value = false
    }
  }

  function setCategoryId(id: number | null) {
    currentCategoryId.value = id
    selectedVideo.value = null
    fetchVideos()
  }

  function setSortBy(sort: 'heat_score' | 'publish_time') {
    sortBy.value = sort
    fetchVideos()
  }

  function setTimeWindow(window: '1d' | '3d' | '7d' | '15d' | '30d' | null) {
    timeWindow.value = window
    fetchVideos()
  }

  function setPlatform(platform: string | null) {
    currentPlatform.value = platform
    fetchVideos()
  }

  return {
    videos,
    selectedVideo,
    total,
    loading,
    currentCategoryId,
    currentPlatform,
    sortBy,
    timeWindow,
    fetchVideos,
    selectVideo,
    setCategoryId,
    setSortBy,
    setTimeWindow,
    setPlatform
  }
})
