<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo-section">
        <div class="logo-icon">V</div>
        <h1>Vigor Admin</h1>
        <p>管理员登录</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="username"
            type="text"
            class="input"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input
            v-model="password"
            type="password"
            class="input"
            placeholder="请输入密码"
            required
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="btn-login" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  // 简单校验: admin / admin123
  if (username.value === 'admin' && password.value === 'admin123') {
    loading.value = true
    errorMessage.value = ''

    // 模拟登录延迟
    setTimeout(() => {
      // 手动设置登录状态
      const mockToken = 'mock-admin-token'
      storage.set(TOKEN_KEY, mockToken)
      storage.set(USER_KEY, { username: username.value })

      userStore.isLoggedIn = true
      userStore.isAdmin = true
      userStore.username = username.value
      userStore.token = mockToken

      loading.value = false
      router.push('/admin/dashboard')
    }, 500)
  } else {
    errorMessage.value = '用户名或密码错误'
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
}

.login-card {
  background-color: var(--bg-primary);
  padding: var(--spacing-xxl);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  min-width: 380px;
}

.logo-section {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.logo-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto var(--spacing-md);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #007aff, #5856d6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 28px;
}

h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

p {
  font-size: 14px;
  color: var(--text-secondary);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.input {
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  transition: all var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.error-message {
  padding: 10px 12px;
  background-color: rgba(255, 59, 48, 0.1);
  border: 1px solid var(--error-color);
  border-radius: var(--radius-md);
  color: var(--error-color);
  font-size: 13px;
  text-align: center;
}

.btn-login {
  padding: 12px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.btn-login:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
