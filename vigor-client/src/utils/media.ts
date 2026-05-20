import type { Video } from '@/types/video'

/**
 * 规范化封面 URL,处理 HTTP/HTTPS 和空值
 */
export function normalizeCover(url?: string | null): string {
  if (!url) {
    // 返回占位 SVG Data URL
    return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23f0f0f0" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%23999" font-size="18"%3E暂无封面%3C/text%3E%3C/svg%3E'
  }

  if (url.startsWith('//')) {
    return `https:${url}`
  }

  // HTTP 转 HTTPS(B 站图片服务器支持 HTTPS)
  if (url.startsWith('http://')) {
    return url.replace('http://', 'https://')
  }

  return url
}

export function getOriginalVideoUrl(video?: Pick<Video, 'platform' | 'external_id' | 'video_url'> | null): string {
  if (!video) return '#'
  const externalId = video.external_id?.trim()
  if (video.platform === 'douyin' && externalId) {
    return `https://www.douyin.com/video/${externalId}`
  }
  if (video.platform === 'bilibili' && externalId) {
    return `https://www.bilibili.com/video/${externalId}`
  }
  return video.video_url || '#'
}

export function getPlayableVideoUrl(video?: Pick<Video, 'platform' | 'video_url'> | null): string | null {
  if (!video?.video_url) return null
  if (video.video_url.toLowerCase().includes('.mp3')) return null
  if (video.platform === 'douyin' && video.video_url.includes('/aweme/v1/play/')) {
    return video.video_url
  }
  if (video.platform !== 'bilibili') {
    return video.video_url
  }
  return null
}
