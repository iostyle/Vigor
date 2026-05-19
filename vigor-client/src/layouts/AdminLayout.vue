<template>
  <n-config-provider :theme="naiveTheme">
    <div class="admin-layout" :data-admin-theme="adminTheme">
      <aside class="sidebar">
        <div class="logo-section">
          <div class="logo-icon">V</div>
          <h1>Vigor Admin</h1>
        </div>
        <nav class="nav-menu">
          <router-link to="/admin/dashboard" class="nav-item">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
            </svg>
            <span>仪表盘</span>
          </router-link>
          <router-link to="/admin/categories" class="nav-item">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path
                d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
              />
            </svg>
            <span>领域管理</span>
          </router-link>
          <router-link to="/admin/keywords" class="nav-item">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path
                d="M17.63 5.84C17.27 5.33 16.67 5 16 5L5 5.01C3.9 5.01 3 5.9 3 7v10c0 1.1.9 1.99 2 1.99L16 19c.67 0 1.27-.33 1.63-.84L22 12l-4.37-6.16z"
              />
            </svg>
            <span>关键词管理</span>
          </router-link>
          <router-link to="/admin/videos" class="nav-item">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path
                d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"
              />
            </svg>
            <span>视频管理</span>
          </router-link>
          <router-link to="/admin/tasks" class="nav-item">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path
                d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
              />
            </svg>
            <span>任务管理</span>
          </router-link>
          <router-link to="/admin/scheduled-tasks" class="nav-item">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path
                d="M12 2a10 10 0 1 0 10 10h-2a8 8 0 1 1-2.34-5.66L15 9h7V2l-2.9 2.9A9.96 9.96 0 0 0 12 2zm1 5h-2v6l5 3 1-1.73-4-2.27V7z"
              />
            </svg>
            <span>定时任务</span>
          </router-link>
        </nav>
        <div class="sidebar-footer">
          <button
            class="theme-toggle"
            :title="adminTheme === 'dark' ? '切换到浅色' : '切换到深色'"
            @click="toggleAdminTheme"
          >
            <svg
              v-if="adminTheme === 'dark'"
              viewBox="0 0 24 24"
              width="18"
              height="18"
              fill="currentColor"
            >
              <path
                d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 0 0 0-1.41l-1.06-1.06zm1.06-10.96a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"
              />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path
                d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"
              />
            </svg>
            <span>{{ adminTheme === 'dark' ? '浅色模式' : '深色模式' }}</span>
          </button>
          <button class="logout-btn" @click="handleLogout">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path
                d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"
              />
            </svg>
            <span>退出登录</span>
          </button>
        </div>
      </aside>
      <main class="main-content soft-scrollbar">
        <router-view />
      </main>
    </div>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NConfigProvider, darkTheme } from 'naive-ui'
import { useUserStore } from '@/stores/user'

const ADMIN_THEME_KEY = 'vigor:admin:theme'
type AdminTheme = 'light' | 'dark'

const router = useRouter()
const userStore = useUserStore()

const adminTheme = ref<AdminTheme>(
  (localStorage.getItem(ADMIN_THEME_KEY) as AdminTheme | null) || 'light'
)

const naiveTheme = computed(() => (adminTheme.value === 'dark' ? darkTheme : null))
let previousClientTheme: string | null = null

watch(adminTheme, (val) => {
  try {
    localStorage.setItem(ADMIN_THEME_KEY, val)
  } catch {
    // localStorage 不可用时静默失败
  }
})

onMounted(() => {
  previousClientTheme = document.documentElement.getAttribute('data-theme')
  document.documentElement.removeAttribute('data-theme')
})

onBeforeUnmount(() => {
  if (previousClientTheme) {
    document.documentElement.setAttribute('data-theme', previousClientTheme)
  }
})

function toggleAdminTheme() {
  adminTheme.value = adminTheme.value === 'dark' ? 'light' : 'dark'
}

function handleLogout() {
  userStore.logout()
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  background-color: var(--bg-secondary);
}

.sidebar {
  width: 240px;
  background-color: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.logo-section {
  padding: var(--spacing-xl);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #007aff, #5856d6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 20px;
}

.logo-section h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.nav-menu {
  flex: 1;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.nav-item:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.nav-item.router-link-active {
  background-color: var(--primary-color);
  color: white;
}

.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.theme-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-toggle:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.logout-btn:hover {
  background-color: var(--bg-secondary);
  color: var(--error-color);
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-xl);
}
</style>
