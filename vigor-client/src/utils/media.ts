/**
 * 规范化封面 URL,处理 HTTP/HTTPS 和空值
 */
export function normalizeCover(url?: string | null): string {
  if (!url) {
    // 返回占位 SVG Data URL
    return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23f0f0f0" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%23999" font-size="18"%3E暂无封面%3C/text%3E%3C/svg%3E'
  }

  // HTTP 转 HTTPS(B 站图片服务器支持 HTTPS)
  if (url.startsWith('http://')) {
    return url.replace('http://', 'https://')
  }

  return url
}
