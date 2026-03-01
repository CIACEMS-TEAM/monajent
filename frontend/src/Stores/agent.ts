import { defineStore } from 'pinia'
import http, { API_BASE } from '@/services/http'

function absUrl(url: string | null | undefined): string | null {
  if (!url) return null
  return url.startsWith('http') ? url : `${API_BASE}${url}`
}

// ─── Types : Profil Agent ───────────────────────────────────

export interface AgentProfileAPI {
  phone: string
  username: string | null
  email: string | null
  role: string
  member_since: string
  agency_name: string
  verified: boolean
  kyc_status: 'NOT_SUBMITTED' | 'PENDING' | 'APPROVED' | 'REJECTED'
  kyc_rejection_reason: string
  bio: string
  contact_phone: string
  contact_email: string
  national_id_number: string
  national_id_document: string | null
  profile_photo: string | null
  documents: AgentDocument[]
  created_at: string
  updated_at: string
}

export interface AgentDocument {
  id: number
  file: string
  doc_type: 'CNI' | 'PASSPORT' | 'PERMIT' | 'OTHER'
  side: 'RECTO' | 'VERSO' | 'SINGLE'
  label: string
  uploaded_at: string
  updated_at: string
}

export interface AgentProfileUpdate {
  username?: string
  email?: string
  agency_name?: string
  bio?: string
  contact_phone?: string
  contact_email?: string
  national_id_number?: string
  national_id_document?: File | null
  profile_photo?: File | null
}

// ─── Types : Listings (alignés sur le backend) ──────────────

export interface ListingImage {
  id: number
  image: string
  caption: string
  order: number
  created_at: string
}

export interface ListingVideo {
  id: number
  file: string
  stream_url: string | null
  thumbnail: string | null
  duration_sec: number | null
  access_key: string
  views_count: number
  created_at: string
  updated_at: string
}

export interface ListingAgent {
  id: number
  phone: string
  username: string | null
  agency_name: string
  profile_photo: string | null
  verified: boolean
}

export interface ListingReportDetail {
  id: number
  reason: string
  reason_label: string
  description: string
  status: string
  status_label: string
  user_phone: string
  user_name: string
  created_at: string
}

export interface ListingFavoriteDetail {
  id: number
  user_phone: string
  user_name: string
  created_at: string
}

export interface Listing {
  id: number
  title: string
  description: string
  listing_type: 'LOCATION' | 'VENTE'
  status: 'ACTIF' | 'INACTIF' | 'EXPIRED' | 'SUSPENDED'
  city: string
  neighborhood: string
  address: string
  latitude: string | null
  longitude: string | null
  price: string
  rooms: number | null
  bedrooms: number | null
  bathrooms: number | null
  surface_m2: string | null
  furnishing: '' | 'FURNISHED' | 'UNFURNISHED' | 'SEMI_FURNISHED'
  amenities: string[]
  deposit_months: number | null
  advance_months: number | null
  agency_fee_months: number | null
  other_conditions: string
  views_count: number
  favorites_count: number
  reports_count: number
  published_at: string | null
  expires_at: string | null
  days_remaining: number
  images: ListingImage[]
  videos: ListingVideo[]
  reports_detail: ListingReportDetail[]
  favorites_detail: ListingFavoriteDetail[]
  created_at: string
  updated_at: string
}

export interface ListingListItem {
  id: number
  title: string
  listing_type: 'LOCATION' | 'VENTE'
  status: 'ACTIF' | 'INACTIF' | 'EXPIRED' | 'SUSPENDED'
  city: string
  neighborhood: string
  price: string
  rooms: number | null
  bedrooms: number | null
  surface_m2: string | null
  furnishing: string
  deposit_months: number | null
  advance_months: number | null
  agency_fee_months: number | null
  views_count: number
  favorites_count: number
  reports_count: number
  agent: ListingAgent
  cover_image: string | null
  videos_count: number
  published_at: string | null
  expires_at: string | null
  days_remaining: number
  created_at: string
}

export interface ListingCreatePayload {
  title: string
  description?: string
  listing_type: 'LOCATION' | 'VENTE'
  status?: 'ACTIF' | 'INACTIF'
  city: string
  neighborhood?: string
  address?: string
  latitude?: number | null
  longitude?: number | null
  price: number
  rooms?: number | null
  bedrooms?: number | null
  bathrooms?: number | null
  surface_m2?: number | null
  furnishing?: string
  amenities?: string[]
  deposit_months?: number | null
  advance_months?: number | null
  agency_fee_months?: number | null
  other_conditions?: string
}

// ─── Types : Wallet (alignées sur le backend) ───────────────

export interface WalletData {
  balance: string
  total_earned: string
  total_withdrawn: string
  can_withdraw: boolean
  has_pin: boolean
  minimum_withdrawal: string
  pending_withdrawal: {
    id: number
    amount: string
    method: string
    phone_number: string
    created_at: string
  } | null
  created_at: string
  updated_at: string
}

export interface WalletEntry {
  id: number
  entry_type: 'CREDIT' | 'DEBIT'
  entry_type_label: string
  source: string
  source_label: string
  amount: string
  label: string
  withdrawal_method: string | null
  withdrawal_ref: string | null
  created_at: string
}

export interface Withdrawal {
  id: number
  amount: string
  method: string
  method_label: string
  phone_number: string
  status: 'PENDING' | 'COMPLETED' | 'REJECTED'
  status_label: string
  transaction_ref: string | null
  admin_note: string | null
  processed_at: string | null
  created_at: string
}

// ─── Types : Visits (alignées sur le backend) ────────────────

export interface Visit {
  id: number
  listing_id: number
  listing_title: string
  client_phone: string
  status: 'REQUESTED' | 'CONFIRMED' | 'DONE' | 'NO_SHOW' | 'CANCELED' | 'EXPIRED'
  slot_id: number | null
  slot_label: string | null
  scheduled_at: string | null
  response_deadline: string | null
  is_deadline_passed: boolean
  client_note: string
  agent_note: string
  cancel_reason: string
  meeting_address: string
  meeting_latitude: string | null
  meeting_longitude: string | null
  meeting_map_url: string | null
  created_at: string
}

export interface AvailabilitySlot {
  id: number
  day_of_week: number
  day_label: string
  start_time: string
  end_time: string
  is_active: boolean
}

export interface DateSlot {
  id: number
  date: string
  start_time: string
  end_time: string
  is_active: boolean
  note: string
}

export interface DailyStats {
  date: string
  views: number
}

// ─── Types : Dashboard & Analytics (API) ─────────────────────

export interface DashboardData {
  wallet: { balance: string; total_earned: string; has_pin: boolean }
  listings: { total: number; published: number; total_views: number; total_favorites: number }
  pending_visits: number
  recent_entries: {
    id: number; entry_type: string; source_label: string
    amount: string; label: string; created_at: string
  }[]
  latest_listing: {
    id: number; title: string; views_count: number
    favorites_count: number; price: string; created_at: string
  } | null
  top_listings: { id: number; title: string; views_count: number; favorites_count: number }[]
  views_28d: number
}

export interface ReportByReason {
  reason: string
  reason_label: string
  count: number
}

export interface AnalyticsData {
  daily_stats: DailyStats[]
  total_views_28d: number
  period_days: number
  trend_pct: number
  summary: {
    total_views: number; total_favorites: number; total_reports: number
    published_count: number; total_listings: number
    avg_views_per_listing: number
  }
  top_listings: { id: number; title: string; views_count: number; favorites_count: number }[]
  reports_by_reason: ReportByReason[]
  visits: { done: number; total: number; conversion_pct: number }
}

// ─── Store ──────────────────────────────────────────────────

export const useAgentStore = defineStore('agent', {
  state: () => ({
    // Profil
    profile: null as AgentProfileAPI | null,
    profileLoading: false,
    profileError: '',
    documents: [] as AgentDocument[],

    // Listings (API réelle)
    listings: [] as ListingListItem[],
    listingsLoading: false,
    listingsError: '',
    currentListing: null as Listing | null,
    currentListingLoading: false,

    // Wallet (API réelle)
    wallet: null as WalletData | null,
    walletLoading: false,
    walletEntries: [] as WalletEntry[],
    walletEntriesLoading: false,
    withdrawals: [] as Withdrawal[],
    withdrawalsLoading: false,

    // Visits (API réelle)
    visits: [] as Visit[],
    visitsLoading: false,
    availabilitySlots: [] as AvailabilitySlot[],
    availabilitySlotsLoading: false,
    dateSlots: [] as DateSlot[],
    dateSlotsLoading: false,

    // Dashboard & Analytics (API réelle)
    dashboard: null as DashboardData | null,
    dashboardLoading: false,
    analytics: null as AnalyticsData | null,
    analyticsLoading: false,
    dailyStats: [] as DailyStats[],
  }),

  getters: {
    agencyName: (s) => s.profile?.agency_name || '',
    profilePhoto: (s) => absUrl(s.profile?.profile_photo),
    isVerified: (s) => s.profile?.verified ?? false,
    kycStatus: (s) => {
      if (s.profile?.verified) return 'APPROVED'
      return s.profile?.kyc_status ?? 'NOT_SUBMITTED'
    },
    kycRejectionReason: (s) => s.profile?.kyc_rejection_reason ?? '',
    isKycEditable: (s) => {
      const st = s.profile?.kyc_status
      return !st || st === 'NOT_SUBMITTED' || st === 'REJECTED'
    },
    hasKycDocuments: (s) =>
      !!(s.profile?.national_id_document) || s.documents.length > 0,
    isProfileComplete: (s) =>
      !!(s.profile?.agency_name) && !!(s.profile?.contact_phone || s.profile?.contact_email),
    totalViews: (s) => s.listings.reduce((t, l) => t + l.views_count, 0),
    publishedCount: (s) => s.listings.filter(l => l.status === 'ACTIF').length,
    inactifCount: (s) => s.listings.filter(l => l.status === 'INACTIF').length,
    expiredCount: (s) => s.listings.filter(l => l.status === 'EXPIRED').length,
    walletBalance: (s) => parseFloat(s.wallet?.balance || '0'),
    walletTotalEarned: (s) => parseFloat(s.wallet?.total_earned || '0'),
    walletTotalWithdrawn: (s) => parseFloat(s.wallet?.total_withdrawn || '0'),
    walletHasPin: (s) => s.wallet?.has_pin ?? false,
    walletCanWithdraw: (s) => s.wallet?.can_withdraw ?? false,
    walletMinWithdrawal: (s) => parseFloat(s.wallet?.minimum_withdrawal || '0'),
    pendingVisits: (s) => s.visits.filter(v => v.status === 'REQUESTED').length,
    confirmedVisits: (s) => s.visits.filter(v => v.status === 'CONFIRMED').length,
  },

  actions: {
    // ═══ Profil API ═══════════════════════════════════════════

    async fetchProfile() {
      this.profileLoading = true
      this.profileError = ''
      try {
        const { data } = await http.get<AgentProfileAPI>('/api/agent/profile/')
        this.profile = data
        this.documents = data.documents || []
      } catch (e: any) {
        this.profileError = e?.response?.data?.detail || 'Erreur chargement profil'
        throw e
      } finally {
        this.profileLoading = false
      }
    },

    async updateProfile(payload: AgentProfileUpdate) {
      const fd = new FormData()
      for (const [key, value] of Object.entries(payload)) {
        if (value === undefined) continue
        if (value === null) {
          fd.append(key, '')
        } else if (value instanceof File) {
          fd.append(key, value)
        } else {
          fd.append(key, String(value))
        }
      }
      const { data } = await http.patch<AgentProfileAPI>('/api/agent/profile/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      this.profile = data
      this.documents = data.documents || []
      return data
    },

    // ═══ Documents KYC ════════════════════════════════════════

    async fetchDocuments() {
      const { data } = await http.get<AgentDocument[]>('/api/agent/profile/documents/')
      this.documents = data
    },

    async uploadDocument(file: File, docType: string, side: string, label?: string) {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('doc_type', docType)
      fd.append('side', side)
      if (label) fd.append('label', label)
      const { data } = await http.post<AgentDocument>('/api/agent/profile/documents/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const idx = this.documents.findIndex(d => d.doc_type === data.doc_type && d.side === data.side)
      if (idx >= 0) this.documents[idx] = data
      else this.documents.push(data)
      return data
    },

    async deleteDocument(id: number) {
      await http.delete(`/api/agent/profile/documents/${id}/`)
      this.documents = this.documents.filter(d => d.id !== id)
    },

    async submitKyc() {
      const { data } = await http.post<{ detail: string; kyc_status: string }>('/api/agent/profile/kyc/submit/')
      if (this.profile) {
        this.profile.kyc_status = data.kyc_status as any
        this.profile.kyc_rejection_reason = ''
      }
      return data
    },

    // ═══ Listings API ═════════════════════════════════════════

    async fetchListings() {
      this.listingsLoading = true
      this.listingsError = ''
      try {
        const { data } = await http.get<ListingListItem[]>('/api/agent/listings/')
        this.listings = data
      } catch (e: any) {
        this.listingsError = e?.response?.data?.detail || 'Erreur chargement annonces'
        throw e
      } finally {
        this.listingsLoading = false
      }
    },

    async fetchListing(id: number) {
      this.currentListingLoading = true
      try {
        const { data } = await http.get<Listing>(`/api/agent/listings/${id}/`)
        this.currentListing = data
        return data
      } catch (e: any) {
        throw e
      } finally {
        this.currentListingLoading = false
      }
    },

    async createListing(payload: ListingCreatePayload) {
      const { data } = await http.post<ListingCreatePayload & { id: number }>('/api/agent/listings/', payload)
      await this.fetchListings()
      return data
    },

    async updateListing(id: number, payload: Partial<ListingCreatePayload>) {
      await http.patch(`/api/agent/listings/${id}/`, payload)
      const full = await this.fetchListing(id)
      await this.fetchListings()
      return full
    },

    async deleteListing(id: number) {
      await http.delete(`/api/agent/listings/${id}/`)
      this.listings = this.listings.filter(l => l.id !== id)
      if (this.currentListing?.id === id) this.currentListing = null
    },

    async bulkAction(ids: number[], action: 'activate' | 'deactivate' | 'delete') {
      const { data } = await http.post<{ detail: string }>('/api/agent/listings/bulk/', { ids, action })
      await this.fetchListings()
      return data
    },

    async renewListing(id: number) {
      const { data } = await http.post<{ detail: string; expires_at: string; status: string }>(
        `/api/agent/listings/${id}/renew/`,
      )
      await this.fetchListings()
      return data
    },

    async toggleListingStatus(id: number) {
      const listing = this.listings.find(l => l.id === id)
      if (!listing) return
      const newStatus = listing.status === 'ACTIF' ? 'INACTIF' : 'ACTIF'
      await http.patch(`/api/agent/listings/${id}/`, { status: newStatus })
      await this.fetchListings()
      return newStatus
    },

    // ═══ Listing Images ═══════════════════════════════════════

    async uploadListingImage(listingId: number, file: File, caption = '', order = 0) {
      const fd = new FormData()
      fd.append('image', file)
      fd.append('caption', caption)
      fd.append('order', String(order))
      const { data } = await http.post<ListingImage>(
        `/api/agent/listings/${listingId}/images/`,
        fd,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      if (this.currentListing?.id === listingId) {
        this.currentListing.images.push(data)
      }
      return data
    },

    async deleteListingImage(listingId: number, imageId: number) {
      await http.delete(`/api/agent/listings/${listingId}/images/${imageId}/`)
      if (this.currentListing?.id === listingId) {
        this.currentListing.images = this.currentListing.images.filter(i => i.id !== imageId)
      }
    },

    // ═══ Listing Videos ═══════════════════════════════════════

    async uploadListingVideo(listingId: number, file: File, thumbnail?: File, durationSec?: number) {
      const fd = new FormData()
      fd.append('file', file)
      if (thumbnail) fd.append('thumbnail', thumbnail)
      if (durationSec !== undefined) fd.append('duration_sec', String(durationSec))
      const { data } = await http.post<ListingVideo>(
        `/api/agent/listings/${listingId}/videos/`,
        fd,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      if (this.currentListing?.id === listingId) {
        this.currentListing.videos.push(data)
      }
      return data
    },

    async deleteListingVideo(listingId: number, videoId: number) {
      await http.delete(`/api/agent/listings/${listingId}/videos/${videoId}/`)
      if (this.currentListing?.id === listingId) {
        this.currentListing.videos = this.currentListing.videos.filter(v => v.id !== videoId)
      }
    },

    // ═══ Wallet API ═════════════════════════════════════════════

    async fetchWallet() {
      this.walletLoading = true
      try {
        const { data } = await http.get<WalletData>('/api/agent/wallet/')
        this.wallet = data
      } finally {
        this.walletLoading = false
      }
    },

    async fetchWalletEntries(params?: { source?: string; entry_type?: string }) {
      this.walletEntriesLoading = true
      try {
        const { data } = await http.get<WalletEntry[]>('/api/agent/wallet/entries/', { params })
        this.walletEntries = data
      } finally {
        this.walletEntriesLoading = false
      }
    },

    async fetchWithdrawals() {
      this.withdrawalsLoading = true
      try {
        const { data } = await http.get<Withdrawal[]>('/api/agent/wallet/withdrawals/')
        this.withdrawals = data
      } finally {
        this.withdrawalsLoading = false
      }
    },

    async setPin(pin: string, pin_confirm: string) {
      const { data } = await http.post('/api/agent/wallet/set-pin/', { pin, pin_confirm })
      if (this.wallet) this.wallet.has_pin = true
      return data
    },

    async changePin(current_pin: string, new_pin: string, new_pin_confirm: string) {
      const { data } = await http.post('/api/agent/wallet/change-pin/', {
        current_pin, new_pin, new_pin_confirm,
      })
      return data
    },

    async requestWithdrawal(payload: { pin: string; amount: number; method: string; phone_number: string }) {
      const { data } = await http.post<Withdrawal>('/api/agent/wallet/withdraw/', payload)
      await this.fetchWallet()
      await this.fetchWithdrawals()
      return data
    },

    // ═══ Visits API ═══════════════════════════════════════════

    async fetchVisits() {
      this.visitsLoading = true
      try {
        const { data } = await http.get<Visit[]>('/api/agent/visits/')
        this.visits = data
      } finally {
        this.visitsLoading = false
      }
    },

    async confirmVisit(id: number, payload?: {
      scheduled_at?: string
      agent_note?: string
      meeting_address?: string
      meeting_latitude?: number | null
      meeting_longitude?: number | null
    }) {
      const { data } = await http.post(`/api/agent/visits/${id}/confirm/`, payload || {})
      await this.fetchVisits()
      return data
    },

    async validateVisitCode(id: number, code: string) {
      const { data } = await http.post(`/api/agent/visits/${id}/validate-code/`, { code })
      await this.fetchVisits()
      return data
    },

    async markNoShow(id: number, reason: string) {
      const { data } = await http.post(`/api/agent/visits/${id}/no-show/`, { reason })
      await this.fetchVisits()
      return data
    },

    // ═══ Availability API ═════════════════════════════════════

    async fetchAvailability() {
      this.availabilitySlotsLoading = true
      try {
        const { data } = await http.get<AvailabilitySlot[]>('/api/agent/availability/')
        this.availabilitySlots = data
      } finally {
        this.availabilitySlotsLoading = false
      }
    },

    async createAvailability(payload: { day_of_week: number; start_time: string; end_time: string }) {
      const { data } = await http.post<AvailabilitySlot>('/api/agent/availability/', payload)
      this.availabilitySlots.push(data)
      return data
    },

    async updateAvailability(id: number, payload: Partial<AvailabilitySlot>) {
      const { data } = await http.patch<AvailabilitySlot>(`/api/agent/availability/${id}/`, payload)
      const idx = this.availabilitySlots.findIndex(s => s.id === id)
      if (idx >= 0) this.availabilitySlots[idx] = data
      return data
    },

    async deleteAvailability(id: number) {
      await http.delete(`/api/agent/availability/${id}/`)
      this.availabilitySlots = this.availabilitySlots.filter(s => s.id !== id)
    },

    // ═══ Date Slots (agenda) API ═════════════════════════════

    async fetchDateSlots() {
      this.dateSlotsLoading = true
      try {
        const { data } = await http.get<DateSlot[]>('/api/agent/date-slots/')
        this.dateSlots = Array.isArray(data) ? data : (data as any).results || []
      } finally {
        this.dateSlotsLoading = false
      }
    },

    async createDateSlot(payload: { date: string; start_time: string; end_time: string; note?: string }) {
      const { data } = await http.post<DateSlot>('/api/agent/date-slots/', payload)
      this.dateSlots.push(data)
      return data
    },

    async updateDateSlot(id: number, payload: Partial<DateSlot>) {
      const { data } = await http.patch<DateSlot>(`/api/agent/date-slots/${id}/`, payload)
      const idx = this.dateSlots.findIndex(s => s.id === id)
      if (idx >= 0) this.dateSlots[idx] = data
      return data
    },

    async deleteDateSlot(id: number) {
      await http.delete(`/api/agent/date-slots/${id}/`)
      this.dateSlots = this.dateSlots.filter(s => s.id !== id)
    },

    // ═══ Dashboard & Analytics API ══════════════════════════════

    async fetchDashboard() {
      this.dashboardLoading = true
      try {
        const { data } = await http.get<DashboardData>('/api/agent/dashboard/')
        this.dashboard = data
      } finally {
        this.dashboardLoading = false
      }
    },

    async fetchAnalytics(startDate?: string, endDate?: string) {
      this.analyticsLoading = true
      try {
        const params: Record<string, string> = {}
        if (startDate) params.start_date = startDate
        if (endDate) params.end_date = endDate
        const { data } = await http.get<AnalyticsData>('/api/agent/analytics/', { params })
        this.analytics = data
        this.dailyStats = data.daily_stats
      } finally {
        this.analyticsLoading = false
      }
    },

    // ═══ Reset (logout) ═══════════════════════════════════════

    $resetAgent() {
      this.profile = null
      this.documents = []
      this.profileError = ''
      this.listings = []
      this.currentListing = null
      this.wallet = null
      this.walletEntries = []
      this.withdrawals = []
      this.visits = []
      this.availabilitySlots = []
      this.dateSlots = []
      this.dashboard = null
      this.analytics = null
      this.dailyStats = []
    },
  },
})
