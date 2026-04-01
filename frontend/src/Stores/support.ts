import { defineStore } from 'pinia'
import http from '@/services/http'

// ─── Types ──────────────────────────────────────────────────

export interface SupportMessage {
  id: number
  author_phone: string
  author_name: string
  content: string
  is_staff_reply: boolean
  created_at: string
}

export interface SupportTicketList {
  id: number
  subject: string
  category: string
  category_label: string
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED'
  status_label: string
  priority: 'LOW' | 'NORMAL' | 'HIGH'
  priority_label: string
  messages_count: number
  last_reply_at: string | null
  created_at: string
  updated_at: string
}

export interface SupportTicketDetail extends SupportTicketList {
  messages: SupportMessage[]
}

export interface CreateTicketPayload {
  subject: string
  category: string
  content: string
}

// ─── Store ──────────────────────────────────────────────────

export const useSupportStore = defineStore('support', {
  state: () => ({
    tickets: [] as SupportTicketList[],
    ticketsLoading: false,
    ticketsError: '',
    currentTicket: null as SupportTicketDetail | null,
    currentTicketLoading: false,
  }),

  getters: {
    openTickets: (s) => s.tickets.filter(t => t.status !== 'CLOSED'),
    closedTickets: (s) => s.tickets.filter(t => t.status === 'CLOSED'),
  },

  actions: {
    async fetchTickets(statusFilter?: string) {
      this.ticketsLoading = true
      this.ticketsError = ''
      try {
        const params: Record<string, string> = {}
        if (statusFilter) params.status = statusFilter
        const { data } = await http.get<SupportTicketList[]>('/api/support/tickets/', { params })
        this.tickets = data
      } catch (e: any) {
        this.ticketsError = e?.response?.data?.detail || 'Erreur chargement tickets'
        throw e
      } finally {
        this.ticketsLoading = false
      }
    },

    async createTicket(payload: CreateTicketPayload) {
      const { data } = await http.post<SupportTicketDetail>('/api/support/tickets/', payload)
      this.tickets.unshift({
        ...data,
        messages_count: 1,
        last_reply_at: data.created_at,
      })
      return data
    },

    async fetchTicket(id: number) {
      this.currentTicketLoading = true
      try {
        const { data } = await http.get<SupportTicketDetail>(`/api/support/tickets/${id}/`)
        this.currentTicket = data
        return data
      } finally {
        this.currentTicketLoading = false
      }
    },

    async addMessage(ticketId: number, content: string) {
      const { data } = await http.post<SupportMessage>(
        `/api/support/tickets/${ticketId}/messages/`,
        { content },
      )
      if (this.currentTicket?.id === ticketId) {
        this.currentTicket.messages.push(data)
      }
      return data
    },

    async closeTicket(ticketId: number) {
      await http.post(`/api/support/tickets/${ticketId}/close/`)
      if (this.currentTicket?.id === ticketId) {
        this.currentTicket.status = 'CLOSED'
        this.currentTicket.status_label = 'Fermé'
      }
      const idx = this.tickets.findIndex(t => t.id === ticketId)
      if (idx >= 0) {
        this.tickets[idx].status = 'CLOSED'
        this.tickets[idx].status_label = 'Fermé'
      }
    },
  },
})
