import axios from 'axios'
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/Stores/auth'

// Crée une instance Axios configurée pour l'API
const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'

const http: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // indispensable pour le cookie HttpOnly (refresh)
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
})

let isRefreshing = false
let pendingQueue: Array<{ resolve: () => void; reject: (err: any) => void }> = []

// Ajoute l'Authorization si un accessToken est présent en RAM
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const store = useAuthStore()
  if (store.accessToken) {
    config.headers = config.headers || ({} as any)
    ;(config.headers as any)['Authorization'] = `Bearer ${store.accessToken}`
  }
  return config
})

let refreshFailed = false

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status
    const url = (originalRequest?.url || '')

    if (status === 401 && url.includes('/api/auth/refresh')) {
      refreshFailed = true
      return Promise.reject(error)
    }

    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const store = useAuthStore()

      if (refreshFailed) {
        forceLogout(store)
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise<void>((resolve, reject) => {
          pendingQueue.push({ resolve, reject })
        }).then(() => {
          if (refreshFailed) return Promise.reject(error)
          originalRequest.headers = originalRequest.headers || ({} as any)
          if (store.accessToken) {
            ;(originalRequest.headers as any)['Authorization'] = `Bearer ${store.accessToken}`
          }
          return http(originalRequest)
        })
      }

      try {
        isRefreshing = true
        refreshFailed = false
        await store.refresh()
      } catch (_) {
        refreshFailed = true
        forceLogout(store)
        pendingQueue.forEach((p) => p.reject(error))
        pendingQueue = []
        return Promise.reject(error)
      } finally {
        isRefreshing = false
        if (!refreshFailed) {
          pendingQueue.forEach((p) => p.resolve())
        }
        pendingQueue = []
      }

      originalRequest.headers = originalRequest.headers || ({} as any)
      if (store.accessToken) {
        ;(originalRequest.headers as any)['Authorization'] = `Bearer ${store.accessToken}`
      }
      return http(originalRequest)
    }

    return Promise.reject(error)
  },
)

function forceLogout(store: ReturnType<typeof useAuthStore>) {
  store.accessToken = ''
  store.me = null
  refreshFailed = false
  if (window.location.pathname !== '/auth/login') {
    window.location.href = '/auth/login'
  }
}

export { API_BASE }

export function mediaUrl(url: string | null | undefined): string | null {
  if (!url) return null
  if (url.startsWith('http')) return url
  return `${API_BASE}${url}`
}

export default http
