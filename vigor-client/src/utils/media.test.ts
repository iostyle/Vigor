import { describe, expect, it } from 'vitest'
import { getOriginalVideoUrl, getPlayableVideoUrl } from './media'
import type { Video } from '@/types/video'

function video(overrides: Partial<Video>): Video {
  return {
    id: 1,
    title: '测试视频',
    author_name: null,
    cover_url: null,
    video_url: null,
    like_count: 0,
    comment_count: 0,
    share_count: 0,
    heat_score: null,
    publish_time: null,
    summary: null,
    ...overrides
  }
}

describe('getOriginalVideoUrl', () => {
  it('uses Douyin detail page instead of signed play api', () => {
    const url = getOriginalVideoUrl(
      video({
        platform: 'douyin',
        external_id: '7641610549008207002',
        video_url: 'https://www.douyin.com/aweme/v1/play/?video_id=abc'
      })
    )

    expect(url).toBe('https://www.douyin.com/video/7641610549008207002')
  })

  it('uses Bilibili detail page for BV ids', () => {
    const url = getOriginalVideoUrl(
      video({
        platform: 'bilibili',
        external_id: 'BV1xx411c7mD',
        video_url: 'https://player.bilibili.com/player.html?bvid=BV1xx411c7mD'
      })
    )

    expect(url).toBe('https://www.bilibili.com/video/BV1xx411c7mD')
  })

  it('falls back to stored video url when platform detail url cannot be built', () => {
    const url = getOriginalVideoUrl(
      video({
        platform: 'unknown',
        video_url: 'https://example.com/video'
      })
    )

    expect(url).toBe('https://example.com/video')
  })
})

describe('getPlayableVideoUrl', () => {
  it('uses Douyin signed play api for inline video attempts', () => {
    const url = getPlayableVideoUrl(
      video({
        platform: 'douyin',
        video_url: 'https://www.douyin.com/aweme/v1/play/?video_id=abc'
      })
    )

    expect(url).toBe('https://www.douyin.com/aweme/v1/play/?video_id=abc')
  })

  it('does not treat Douyin audio urls as playable videos', () => {
    const url = getPlayableVideoUrl(
      video({
        platform: 'douyin',
        video_url: 'https://lf26-music-east.douyinstatic.com/obj/music.mp3'
      })
    )

    expect(url).toBe(null)
  })
})
