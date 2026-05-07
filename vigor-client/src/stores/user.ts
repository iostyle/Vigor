import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'
import { adminApi } from '@/api/admin'

export const useUserStore = defineStore('user', () => {
  const isAdmin = ref(false)
  const username = ref<string | null>(null)
  const token = ref<string | null>(null)
  const isLoggedIn = ref(false)

  function init() {
    const savedToken = storage.get<string>(TOKEN_KEY)
    const savedUser = storage.get<{ username: string }>(USER_KEY)
    if (savedToken && savedUser) {
      token.value = savedToken
      username.value = savedUser.username
      isAdmin.value = true
      isLoggedIn.value = true
    }
  }

  async function login(user: string, pass: string) {
    try {
      const res = await adminApi.login(user, pass)
      token.value = res.token
      username.value = user
      isAdmin.value = true
      isLoggedIn.value = true
      storage.set(TOKEN_KEY, res.token)
      storage.set(USER_KEY, { username: user })
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  async function logout() {
    try {
      await adminApi.logout()
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      token.value = null
      username.value = null
      isAdmin.value = false
      isLoggedIn.value = false
      storage.remove(TOKEN_KEY)
      storage.remove(USER_KEY)
    }
  }

  init()

  return {
    isAdmin,
    username,
    token,
    isLoggedIn,
    login,
    logout
  }
})
