import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { storage, TOKEN_KEY } from '@/utils/storage'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const apiKey = import.meta.env.VITE_API_KEY || ''

const instance: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.get<string>(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: AxiosError) => {
    const message = (error.response?.data as any)?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

export default instance
