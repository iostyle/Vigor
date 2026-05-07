export function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return '-'

  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 60) {
    return `${minutes}分钟前`
  }
  if (hours < 24) {
    return `${hours}小时前`
  }
  if (days < 7) {
    return `${days}天前`
  }

  return date.toLocaleDateString('zh-CN')
}

export function formatHeatScore(score: number | null): {
  text: string
  color: string
} {
  if (score === null) {
    return { text: '-', color: 'gray' }
  }

  if (score >= 80) {
    return { text: score.toFixed(1), color: 'red' }
  }
  if (score >= 60) {
    return { text: score.toFixed(1), color: 'orange' }
  }
  return { text: score.toFixed(1), color: 'gray' }
}

export function formatSentiment(sentiment: string): {
  text: string
  color: string
} {
  const map: Record<string, { text: string; color: string }> = {
    positive: { text: '正面', color: 'green' },
    neutral: { text: '中性', color: 'gray' },
    negative: { text: '负面', color: 'red' }
  }
  return map[sentiment] || { text: '未知', color: 'gray' }
}
