import { defineStore } from 'pinia'
import http from '@/services/http'
import { useAuthStore } from '@/Stores/auth'

export interface NotificationItem {
  id: number
  category: 'KYC' | 'SYSTEM' | 'VISIT' | 'WALLET'
  title: string
  message: string
  link: string
  is_read: boolean
  created_at: string
}

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [] as NotificationItem[],
    unreadCount: 0,
    loading: false,
    _pollTimer: null as ReturnType<typeof setInterval> | null,
  }),

  actions: {
    async fetchNotifications() {
      const auth = useAuthStore()
      if (!auth.accessToken) return
      this.loading = true
      try {
        const { data } = await http.get<{ results?: NotificationItem[] } | NotificationItem[]>('/api/notifications/')
        this.notifications = Array.isArray(data) ? data : (data.results || [])
        this.unreadCount = this.notifications.filter(n => !n.is_read).length
      } catch (_) {
        /* noop */
      } finally {
        this.loading = false
      }
    },

    async fetchUnreadCount() {
      const auth = useAuthStore()
      if (!auth.accessToken) {
        this.stopPolling()
        return
      }
      try {
        const { data } = await http.get<{ count: number }>('/api/notifications/unread-count/')
        this.unreadCount = data.count
      } catch (_) { /* noop */ }
    },

    async markRead(ids: number[]) {
      try {
        await http.post('/api/notifications/read/', { ids })
        for (const n of this.notifications) {
          if (ids.includes(n.id)) n.is_read = true
        }
        this.unreadCount = this.notifications.filter(n => !n.is_read).length
      } catch (_) { /* noop */ }
    },

    async markAllRead() {
      try {
        await http.post('/api/notifications/read-all/')
        for (const n of this.notifications) n.is_read = true
        this.unreadCount = 0
      } catch (_) { /* noop */ }
    },

    startPolling(intervalMs = 60000) {
      this.stopPolling()
      this._pollTimer = setInterval(() => this.fetchUnreadCount(), intervalMs)
    },

    stopPolling() {
      if (this._pollTimer) {
        clearInterval(this._pollTimer)
        this._pollTimer = null
      }
    },
  },
})
