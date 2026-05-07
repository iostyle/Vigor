import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage, THEME_KEY } from '@/utils/storage'

export type ThemeMode = 'light' | 'dark'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('light')

  function init() {
    const savedTheme = storage.get<ThemeMode>(THEME_KEY)
    if (savedTheme) {
      mode.value = savedTheme
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      mode.value = prefersDark ? 'dark' : 'light'
    }
    applyTheme()
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', mode.value)
  }

  function toggleTheme() {
    mode.value = mode.value === 'light' ? 'dark' : 'light'
    storage.set(THEME_KEY, mode.value)
    applyTheme()
  }

  function setTheme(newMode: ThemeMode) {
    mode.value = newMode
    storage.set(THEME_KEY, newMode)
    applyTheme()
  }

  init()

  return {
    mode,
    toggleTheme,
    setTheme
  }
})
