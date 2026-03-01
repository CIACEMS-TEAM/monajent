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
    pendingToken: '' as string,
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
      const { data } = await http.post<any>('/api/auth/register/client', payload)
      if (data?.pending_token) this.pendingToken = data.pending_token
      return data
    },
    async registerAgent(payload: RegisterAgentPayload) {
      const { data } = await http.post<any>('/api/auth/register/agent', payload)
      if (data?.pending_token) this.pendingToken = data.pending_token
      return data
    },
    async otpRequest() {
      if (!this.pendingToken) return
      const { data } = await http.post<any>('/api/auth/otp/request', { pending_token: this.pendingToken })
      if (data?.pending_token) this.pendingToken = data.pending_token
      return data
    },
    async otpVerify(code: string) {
      if (!this.pendingToken) throw new Error('OTP non initialisé')
      const { data } = await http.post<{ access: string }>('/api/auth/otp/verify', {
        pending_token: this.pendingToken,
        code,
      })
      // À la réussite, on reçoit un access token et un cookie refresh HttpOnly
      this.accessToken = data.access
      this.pendingToken = ''
      await this.fetchMe()
      return data
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


