<template>
  <nav class="top-nav">
    <div class="nav-left">
      <div class="logo">
        <span class="logo-icon">V</span>
        <span class="logo-text">Vigor</span>
      </div>
      <button
        v-if="showSidebarToggle"
        class="sidebar-toggle"
        :title="sidebarCollapsed ? '展开列表' : '收起列表'"
        @click="emit('toggle-sidebar')"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <line x1="9" y1="3" x2="9" y2="21" />
        </svg>
      </button>
    </div>

    <div class="nav-center">
      <button
        v-for="item in categories"
        :key="item.id"
        class="category-btn"
        :class="{ active: item.id === activeCategoryId }"
        @click="handleCategoryClick(item.id)"
      >
        <span v-if="item.icon" class="category-icon">{{ item.icon }}</span>
        {{ item.name }}
      </button>
    </div>

    <div class="nav-right">
      <button
        class="theme-toggle"
        :title="themeStore.mode === 'light' ? '切换到深色' : '切换到浅色'"
        @click="themeStore.toggleTheme"
      >
        <svg v-if="themeStore.mode === 'light'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z" />
        </svg>
        <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 0 0 0-1.41l-1.06-1.06zm1.06-10.96a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z" />
        </svg>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import type { Category } from '@/api/category'

defineProps<{
  categories: Category[]
  activeCategoryId: number | null
  showSidebarToggle?: boolean
  sidebarCollapsed?: boolean
}>()

const emit = defineEmits<{
  (e: 'change-category', id: number): void
  (e: 'toggle-sidebar'): void
}>()

const themeStore = useThemeStore()

function handleCategoryClick(id: number) {
  emit('change-category', id)
}
</script>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 var(--spacing-xl);
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  backdrop-filter: blur(20px);
}

.nav-left,
.nav-right {
  flex: 0 0 auto;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.sidebar-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.sidebar-toggle:hover {
  background-color: var(--bg-secondary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: var(--spacing-sm);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.nav-center::-webkit-scrollbar {
  display: none;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #007aff, #5856d6);
  color: white;
  font-weight: 700;
  font-size: 18px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.category-btn {
  padding: 6px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.category-icon {
  font-size: 16px;
}

.category-btn:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.category-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-toggle:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .top-nav {
    padding: 0 var(--spacing-md);
  }

  .logo-text {
    display: none;
  }

  .nav-center {
    justify-content: flex-start;
  }
}
</style>
