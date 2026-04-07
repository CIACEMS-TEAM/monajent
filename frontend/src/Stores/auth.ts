import { defineStore } from 'pinia'
import http from '@/services/http'

/** Rafraîchir l'access ~2 min avant expiration JWT */
const PROACTIVE_REFRESH_BEFORE_MS = 120_000
/** Délai minimum avant le premier refresh planifié (évite boucles si JWT mal formé) */
const PROACTIVE_REFRESH_MIN_DELAY_MS = 15_000
/** Au retour sur l'onglet, refresh si l'access expire dans cet intervalle */
const VISIBILITY_REFRESH_IF_EXPIRES_WITHIN_MS = 180_000

let proactiveRefreshTimer: ReturnType<typeof setTimeout> | null = null
let visibilityHandler: (() => void) | null = null

/** Lit le claim `exp` (secondes UTC) depuis un JWT sans dépendance externe */
function jwtExpMs(token: string): number | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    let base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const pad = base64.length % 4
    if (pad) base64 += '='.repeat(4 - pad)
    const payload = JSON.parse(atob(base64)) as { exp?: number }
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export type Role = 'CLIENT' | 'AGENT' | 'ADMIN'

export interface MeResponse {
  id: number
  phone: string
  username: string | null
  email: string | null
  role: Role
}

interface LoginPayload { phone: string; password: string }
interface RegisterClientPayload { phone: string; username: string; password: string; accepted_cgu: boolean; accepted_privacy: boolean }
interface RegisterAgentPayload {
  phone: string
  password: string
  username?: string
  email?: string
  agency_name?: string
  accepted_cgu: boolean
  accepted_privacy: boolean
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: '' as string,
    me: null as MeResponse | null,
    bootstrapped: false,
    pendingToken: '' as string,
  }),
  actions: {
    clearSessionMaintenance() {
      if (proactiveRefreshTimer !== null) {
        clearTimeout(proactiveRefreshTimer)
        proactiveRefreshTimer = null
      }
      if (visibilityHandler !== null && typeof document !== 'undefined') {
        document.removeEventListener('visibilitychange', visibilityHandler)
        visibilityHandler = null
      }
    },

    /** Planifie un POST /auth/refresh avant expiration pour éviter 401 au milieu d'une action */
    scheduleProactiveRefresh() {
      this.clearSessionMaintenance()
      if (!this.accessToken) return

      const attachVisibility = () => {
        if (visibilityHandler !== null || typeof document === 'undefined') return
        visibilityHandler = () => {
          if (document.visibilityState !== 'visible') return
          const auth = useAuthStore()
          if (!auth.accessToken) return
          const exp = jwtExpMs(auth.accessToken)
          if (!exp) return
          if (exp - Date.now() < VISIBILITY_REFRESH_IF_EXPIRES_WITHIN_MS) {
            auth.refresh().catch(() => {})
          }
        }
        document.addEventListener('visibilitychange', visibilityHandler)
      }
      attachVisibility()

      const expMs = jwtExpMs(this.accessToken)
      if (!expMs) return
      const delay = Math.max(
        expMs - Date.now() - PROACTIVE_REFRESH_BEFORE_MS,
        PROACTIVE_REFRESH_MIN_DELAY_MS,
      )
      proactiveRefreshTimer = setTimeout(() => {
        proactiveRefreshTimer = null
        const auth = useAuthStore()
        if (!auth.accessToken) return
        auth.refresh().catch(() => {})
      }, delay)
    },

    async login(payload: LoginPayload) {
      const { data } = await http.post<{ access: string }>('/api/auth/login', payload)
      this.accessToken = data.access
      await this.fetchMe()
      this.scheduleProactiveRefresh()
    },
    async refresh() {
      const { data } = await http.post<{ access: string }>('/api/auth/refresh')
      this.accessToken = data.access
      this.scheduleProactiveRefresh()
    },
    async logout() {
      this.clearSessionMaintenance()
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
      this.scheduleProactiveRefresh()
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


