import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useVideoStore } from './video'
import { videoApi } from '@/api/video'
import type { Video } from '@/types/video'

vi.mock('@/api/video', () => ({
  videoApi: {
    list: vi.fn(),
    getSummary: vi.fn()
  }
}))

const baseVideo: Video = {
  id: 1,
  external_id: '7123456789',
  platform: 'douyin',
  title: '列表视频',
  author_name: '作者',
  cover_url: 'https://example.com/cover.jpg',
  video_url: 'https://example.com/video.mp4',
  like_count: 1,
  comment_count: 2,
  share_count: 3,
  heat_score: 12,
  publish_time: '2026-05-20T00:00:00Z',
  summary: null
}

function detailVideo(id: number, title: string): Video {
  return {
    ...baseVideo,
    id,
    external_id: String(id),
    title
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((res) => {
    resolve = res
  })
  return { promise, resolve }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useVideoStore.selectVideo', () => {
  it('点击列表视频后立即切换详情,再用接口详情补齐', async () => {
    const pendingDetail = deferred<Video>()
    vi.mocked(videoApi.getSummary).mockReturnValue(pendingDetail.promise)

    const store = useVideoStore()
    store.videos = [baseVideo]

    const selecting = store.selectVideo(baseVideo.id)

    expect(store.selectedVideo?.id).toBe(baseVideo.id)
    expect(store.selectedVideo?.title).toBe('列表视频')
    expect(store.loading).toBe(true)

    pendingDetail.resolve(detailVideo(baseVideo.id, '接口详情'))
    await selecting

    expect(store.selectedVideo?.title).toBe('接口详情')
    expect(store.loading).toBe(false)
  })

  it('快速切换视频时忽略较慢返回的旧详情', async () => {
    const firstDetail = deferred<Video>()
    const secondDetail = deferred<Video>()
    vi.mocked(videoApi.getSummary)
      .mockReturnValueOnce(firstDetail.promise)
      .mockReturnValueOnce(secondDetail.promise)

    const store = useVideoStore()
    store.videos = [detailVideo(1, '第一个列表视频'), detailVideo(2, '第二个列表视频')]

    const firstSelecting = store.selectVideo(1)
    const secondSelecting = store.selectVideo(2)

    firstDetail.resolve(detailVideo(1, '较慢的第一个详情'))
    secondDetail.resolve(detailVideo(2, '第二个详情'))
    await Promise.all([firstSelecting, secondSelecting])

    expect(store.selectedVideo?.id).toBe(2)
    expect(store.selectedVideo?.title).toBe('第二个详情')
    expect(store.loading).toBe(false)
  })
})
