import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Category } from '@/api/category'
import { categoryApi } from '@/api/category'

const DEFAULT_CATEGORIES: Category[] = [
  { category: '财经', keyword_count: 0 },
  { category: '科技', keyword_count: 0 },
  { category: '美食', keyword_count: 0 },
  { category: '教育', keyword_count: 0 },
  { category: '娱乐', keyword_count: 0 }
]

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>(DEFAULT_CATEGORIES)
  const activeCategory = ref<string | null>(DEFAULT_CATEGORIES[0].category)
  const loading = ref(false)
  const isUsingDefaults = ref(true)

  async function fetchCategories() {
    loading.value = true
    try {
      const result = await categoryApi.list()
      if (result && result.length > 0) {
        categories.value = result
        isUsingDefaults.value = false
        if (!result.find((c) => c.category === activeCategory.value)) {
          activeCategory.value = result[0].category
        }
      }
    } catch (error) {
      console.warn('无法连接后端,使用默认领域:', error)
    } finally {
      loading.value = false
    }
  }

  function setActiveCategory(category: string) {
    activeCategory.value = category
  }

  return {
    categories,
    activeCategory,
    loading,
    isUsingDefaults,
    fetchCategories,
    setActiveCategory
  }
})
