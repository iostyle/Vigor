import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Keyword } from '@/types/keyword'
import { keywordApi } from '@/api/keyword'

export const useKeywordStore = defineStore('keyword', () => {
  const keywords = ref<Keyword[]>([])
  const activeKeywordId = ref<number | null>(null)
  const loading = ref(false)

  async function fetchKeywords() {
    loading.value = true
    try {
      keywords.value = await keywordApi.list()
      if (keywords.value.length > 0 && !activeKeywordId.value) {
        activeKeywordId.value = keywords.value[0].id
      }
    } catch (error) {
      console.error('Failed to fetch keywords:', error)
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
    fetchKeywords,
    setActiveKeyword
  }
})
