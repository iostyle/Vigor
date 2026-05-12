import type { SelectOption } from 'naive-ui'
import type { Keyword } from '@/types/keyword'

const KEYWORD_STATUS_TEXT: Record<Keyword['status'], string> = {
  active: '启用',
  paused: '暂停',
  archived: '归档'
}

export function keywordStatusText(status: Keyword['status']) {
  return KEYWORD_STATUS_TEXT[status] || status
}

export function buildKeywordOption(keyword: Keyword, options?: { disableInactive?: boolean }): SelectOption {
  const statusText = keywordStatusText(keyword.status)
  const inactive = keyword.status !== 'active'
  return {
    label: inactive ? `${keyword.keyword} (${statusText}, ID: ${keyword.id})` : `${keyword.keyword} (ID: ${keyword.id})`,
    value: keyword.id,
    disabled: Boolean(options?.disableInactive && inactive)
  }
}
