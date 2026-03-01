import { defineStore } from 'pinia'
import http from '@/services/http'

export interface ClientDashboard {
  phone: string
  username: string
  member_since: string
  total_virtual_remaining: number
  total_physical_available: number
  active_packs_count: number
  total_videos_watched: number
  total_visits_requested: number
  visits_in_progress: number
  favorites_count: number
  saved_searches_count: number
}

export interface Payment {
  id: number
  tx_ref: string
  provider: string
  provider_label: string
  status: string
  status_label: string
  amount: string
  currency: string
  pack_id: number | null
  has_pack: boolean
  created_at: string
  updated_at: string
}

export interface ClientReport {
  id: number
  listing_id: number
  listing_title: string
  reason: string
  description: string
  status: string
  created_at: string
}

export const useClientStore = defineStore('client', {
  state: () => ({
    dashboard: null as ClientDashboard | null,
    dashboardLoading: false,
    payments: [] as Payment[],
    paymentsLoading: false,
    reports: [] as ClientReport[],
    reportsLoading: false,
  }),

  getters: {
    virtualKeys: (state) => state.dashboard?.total_virtual_remaining ?? 0,
    physicalKeys: (state) => state.dashboard?.total_physical_available ?? 0,
  },

  actions: {
    async fetchDashboard() {
      this.dashboardLoading = true
      try {
        const { data } = await http.get<ClientDashboard>('/api/client/dashboard/')
        this.dashboard = data
        return data
      } finally {
        this.dashboardLoading = false
      }
    },

    async fetchPayments() {
      this.paymentsLoading = true
      try {
        const { data } = await http.get<any>('/api/client/payments/')
        this.payments = Array.isArray(data) ? data : data.results ?? []
        return this.payments
      } finally {
        this.paymentsLoading = false
      }
    },

    async fetchReports() {
      this.reportsLoading = true
      try {
        const { data } = await http.get<any>('/api/client/reports/')
        this.reports = Array.isArray(data) ? data : data.results ?? []
        return this.reports
      } finally {
        this.reportsLoading = false
      }
    },
  },
})
