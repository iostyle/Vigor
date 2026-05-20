import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Video, VideoListParams } from '@/types/video'
import { videoApi } from '@/api/video'

const STORAGE_KEYS = {
  platform: 'vigor:home:platform',
  sortBy: 'vigor:home:sortBy',
  timeWindow: 'vigor:home:timeWindow'
}

const PAGE_SIZE = 20

function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(key)
    return stored ? (JSON.parse(stored) as T) : defaultValue
  } catch {
    return defaultValue
  }
}

function saveToStorage(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // localStorage 不可用时静默失败
  }
}

export const useVideoStore = defineStore('video', () => {
  const videos = ref<Video[]>([])
  const selectedVideo = ref<Video | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const loadingMore = ref(false)
  const currentCategoryId = ref<number | null>(null)
  const currentPlatform = ref<string | null>(loadFromStorage(STORAGE_KEYS.platform, null))
  const sortBy = ref<'heat_score' | 'publish_time'>(
    loadFromStorage(STORAGE_KEYS.sortBy, 'heat_score')
  )
  const timeWindow = ref<'1d' | '3d' | '7d' | '15d' | '30d' | null>(
    loadFromStorage(STORAGE_KEYS.timeWindow, null)
  )
  let selectRequestId = 0

  function buildListParams(params?: VideoListParams): VideoListParams {
    return {
      category_id:
        currentCategoryId.value && currentCategoryId.value > 0
          ? currentCategoryId.value
          : undefined,
      platform: currentPlatform.value || undefined,
      time_window: timeWindow.value || undefined,
      sort: sortBy.value,
      limit: PAGE_SIZE,
      offset: 0,
      ...params
    }
  }

  async function fetchVideos(params?: VideoListParams) {
    loading.value = true
    try {
      const finalParams = buildListParams(params)
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

  async function loadMoreVideos() {
    if (loading.value || loadingMore.value || videos.value.length >= total.value) return
    loadingMore.value = true
    try {
      const res = await videoApi.list(
        buildListParams({
          offset: videos.value.length,
          limit: PAGE_SIZE
        })
      )
      videos.value = [...videos.value, ...res.data]
      total.value = res.total
    } catch (error) {
      console.warn('加载更多视频失败:', error)
    } finally {
      loadingMore.value = false
    }
  }

  async function selectVideo(videoId: number) {
    const requestId = ++selectRequestId
    const listVideo = videos.value.find((video) => video.id === videoId)
    if (listVideo) {
      selectedVideo.value = listVideo
    }
    loading.value = true
    try {
      const video = await videoApi.getSummary(videoId)
      if (requestId === selectRequestId) {
        selectedVideo.value = video
      }
    } catch (error) {
      console.error('Failed to fetch video detail:', error)
    } finally {
      if (requestId === selectRequestId) {
        loading.value = false
      }
    }
  }

  // 重新拉取当前选中视频的详情(用于摘要生成后刷新等场景)
  async function fetchVideoDetail(videoId: number) {
    try {
      const video = await videoApi.getSummary(videoId)
      selectedVideo.value = video
    } catch (error) {
      console.error('Failed to refresh video detail:', error)
    }
  }

  function setCategoryId(id: number | null) {
    currentCategoryId.value = id
    selectedVideo.value = null
    fetchVideos()
  }

  function setSortBy(sort: 'heat_score' | 'publish_time') {
    sortBy.value = sort
    saveToStorage(STORAGE_KEYS.sortBy, sort)
    fetchVideos()
  }

  function setTimeWindow(window: '1d' | '3d' | '7d' | '15d' | '30d' | null) {
    timeWindow.value = window
    saveToStorage(STORAGE_KEYS.timeWindow, window)
    fetchVideos()
  }

  function setPlatform(platform: string | null) {
    currentPlatform.value = platform
    saveToStorage(STORAGE_KEYS.platform, platform)
    fetchVideos()
  }

  return {
    videos,
    selectedVideo,
    total,
    loading,
    loadingMore,
    hasMore: computed(() => videos.value.length < total.value),
    currentCategoryId,
    currentPlatform,
    sortBy,
    timeWindow,
    fetchVideos,
    loadMoreVideos,
    selectVideo,
    fetchVideoDetail,
    setCategoryId,
    setSortBy,
    setTimeWindow,
    setPlatform
  }
})
