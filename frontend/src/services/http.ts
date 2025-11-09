import axios from 'axios'
import type { AxiosError, AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
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
let pendingQueue: Array<() => void> = []

// Ajoute l'Authorization si un accessToken est présent en RAM
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const store = useAuthStore()
  if (store.accessToken) {
    config.headers = config.headers || ({} as any)
    ;(config.headers as any)['Authorization'] = `Bearer ${store.accessToken}`
  }
  return config
})

// Gestion 401 -> tente un refresh une seule fois puis rejoue la requête
http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status
    const url = (originalRequest?.url || '')

    // Ne pas tenter de refresh si l'endpoint est déjà /auth/refresh
    if (status === 401 && !originalRequest._retry && !url.includes('/api/auth/refresh')) {
      originalRequest._retry = true
      const store = useAuthStore()

      if (isRefreshing) {
        // file d'attente pendant un refresh déjà en cours
        await new Promise<void>((resolve) => pendingQueue.push(resolve))
      } else {
        try {
          isRefreshing = true
          await store.refresh()
        } finally {
          isRefreshing = false
          // réveille les requêtes en attente
          pendingQueue.forEach((resolve) => resolve())
          pendingQueue = []
        }
      }

      // Rejoue la requête avec le nouvel access token
      originalRequest.headers = originalRequest.headers || ({} as any)
      if (store.accessToken) {
        ;(originalRequest.headers as any)['Authorization'] = `Bearer ${store.accessToken}`
      }
      return http(originalRequest)
    }

    return Promise.reject(error)
  },
)

export default http


