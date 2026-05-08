import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Keyword } from '@/types/keyword'
import { keywordApi } from '@/api/keyword'

const DEFAULT_KEYWORDS: Keyword[] = [
  {
    id: -1,
    keyword: '财经',
    category: '财经',
    status: 'active',
    crawl_threshold: 1000,
    priority: 10,
    created_at: '',
    updated_at: ''
  },
  {
    id: -2,
    keyword: '科技',
    category: '科技',
    status: 'active',
    crawl_threshold: 1000,
    priority: 9,
    created_at: '',
    updated_at: ''
  },
  {
    id: -3,
    keyword: '美食',
    category: '美食',
    status: 'active',
    crawl_threshold: 1000,
    priority: 8,
    created_at: '',
    updated_at: ''
  },
  {
    id: -4,
    keyword: '教育',
    category: '教育',
    status: 'active',
    crawl_threshold: 1000,
    priority: 7,
    created_at: '',
    updated_at: ''
  },
  {
    id: -5,
    keyword: '娱乐',
    category: '娱乐',
    status: 'active',
    crawl_threshold: 1000,
    priority: 6,
    created_at: '',
    updated_at: ''
  }
]

export const useKeywordStore = defineStore('keyword', () => {
  const keywords = ref<Keyword[]>(DEFAULT_KEYWORDS)
  const activeKeywordId = ref<number | null>(DEFAULT_KEYWORDS[0].id)
  const loading = ref(false)
  const isUsingDefaults = ref(true)

  async function fetchKeywords() {
    loading.value = true
    try {
      const result = await keywordApi.list()
      if (result && result.length > 0) {
        keywords.value = result
        isUsingDefaults.value = false
        if (!keywords.value.find((k) => k.id === activeKeywordId.value)) {
          activeKeywordId.value = keywords.value[0].id
        }
      }
    } catch (error) {
      console.warn('无法连接后端,使用默认领域:', error)
    } finally {
      loading.value = false
    }
  }

  function setActiveKeyword(keywordId: number) {
    activeKeywordId.value = keywordId
  }

  return {
    keywords,
    activeKeywordId,
    loading,
    isUsingDefaults,
    fetchKeywords,
    setActiveKeyword
  }
})
