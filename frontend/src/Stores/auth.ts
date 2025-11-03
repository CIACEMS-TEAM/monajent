import { defineStore } from 'pinia'
import http from '@/services/http'

export type Role = 'CLIENT' | 'AGENT' | 'ADMIN'

export interface MeResponse {
  id: number
  phone: string
  username: string | null
  email: string | null
  role: Role
}

interface LoginPayload { phone: string; password: string }
interface RegisterClientPayload { phone: string; username: string; password: string }
interface RegisterAgentPayload {
  phone: string
  password: string
  username?: string
  email?: string
  agency_name?: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: '' as string,
    me: null as MeResponse | null,
    bootstrapped: false,
  }),
  actions: {
    async login(payload: LoginPayload) {
      const { data } = await http.post<{ access: string }>('/api/auth/login', payload)
      this.accessToken = data.access
      await this.fetchMe()
    },
    async refresh() {
      const { data } = await http.post<{ access: string }>('/api/auth/refresh')
      this.accessToken = data.access
    },
    async logout() {
      try {
        await http.post('/api/auth/logout')
      } catch (_) {
        // ignore
      }
      this.accessToken = ''
      this.me = null
    },
    async fetchMe() {
      const { data } = await http.get<MeResponse>('/api/auth/me')
      this.me = data
    },
    async registerClient(payload: RegisterClientPayload) {
      return http.post('/api/auth/register/client', payload)
    },
    async registerAgent(payload: RegisterAgentPayload) {
      return http.post('/api/auth/register/agent', payload)
    },
    async bootstrap() {
      try {
        await this.refresh()
        await this.fetchMe()
      } catch (_) {
        // non authentifié au démarrage
      } finally {
        this.bootstrapped = true
      }
    },
  },
})


