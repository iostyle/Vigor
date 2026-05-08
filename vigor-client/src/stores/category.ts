import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Category } from '@/api/category'
import { categoryApi } from '@/api/category'

const DEFAULT_CATEGORIES: Category[] = [
  {
    id: -1,
    name: '财经',
    description: null,
    icon: null,
    sort_order: 0,
    status: 'active',
    keyword_count: 0,
    created_at: null,
    updated_at: null
  }
]

const STORAGE_KEY = 'vigor:home:activeCategoryId'

function loadActiveCategoryId(): number | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? Number(stored) : DEFAULT_CATEGORIES[0].id
  } catch {
    return DEFAULT_CATEGORIES[0].id
  }
}

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>(DEFAULT_CATEGORIES)
  const activeCategoryId = ref<number | null>(loadActiveCategoryId())
  const loading = ref(false)
  const isUsingDefaults = ref(true)

  async function fetchCategories() {
    loading.value = true
    try {
      const result = await categoryApi.list()
      if (result && result.length > 0) {
        categories.value = result
        isUsingDefaults.value = false
        if (!result.find((c) => c.id === activeCategoryId.value)) {
          activeCategoryId.value = result[0].id
        }
      }
    } catch (error) {
      console.warn('无法连接后端,使用默认领域:', error)
    } finally {
      loading.value = false
    }
  }

  function setActiveCategory(id: number) {
    activeCategoryId.value = id
    try {
      localStorage.setItem(STORAGE_KEY, String(id))
    } catch {
      // localStorage 不可用时静默失败
    }
  }

  return {
    categories,
    activeCategoryId,
    loading,
    isUsingDefaults,
    fetchCategories,
    setActiveCategory
  }
})
