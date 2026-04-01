import { defineStore } from 'pinia'
import http from '@/services/http'

export interface PublicListingAgent {
  id: number
  phone: string
  username: string
  agency_name: string
  profile_photo: string | null
  verified: boolean
  contact_phone?: string
  contact_email?: string
}

export interface PublicListingImage {
  id: number
  image: string
  caption: string
  order: number
  created_at: string
}

export interface PublicListingVideo {
  id: number
  thumbnail: string | null
  duration_sec: number | null
  access_key: string
  views_count: number
  created_at: string
}

export interface PublicListing {
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
  agent: PublicListingAgent
  images: PublicListingImage[]
  videos: PublicListingVideo[]
  created_at: string
  updated_at: string
}

export interface WatchVideoResult {
  video_url: string
  video_id: number
  listing_id: number
  listing_title: string
  pack_remaining: number
  already_watched: boolean
}

export interface TeaserResult {
  stream_url: string
  teaser_seconds: number
  is_authenticated: boolean
  is_agent_owner: boolean
  is_unlocked: boolean
  keys_available: number
  video_id: number
  listing_id: number
  listing_title: string
  duration_sec: number | null
}

export interface ListingListItem {
  id: number
  title: string
  listing_type: 'LOCATION' | 'VENTE'
  status: string
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
  agent: PublicListingAgent
  cover_image: string | null
  videos_count: number
  created_at: string
}

export const usePublicStore = defineStore('public', {
  state: () => ({
    listing: null as PublicListing | null,
    listingLoading: false,
    unlockedVideos: {} as Record<string, string>,
    listings: [] as ListingListItem[],
    listingsLoading: false,
    virtualKeys: 0,
    physicalKeys: 0,
    keysLoaded: false,
    favoriteIds: new Set<number>(),
    favoritesLoaded: false,
  }),

  getters: {
    isFavorite: (state) => (listingId: number) => state.favoriteIds.has(listingId),
  },

  actions: {
    async fetchListings(params?: Record<string, string>) {
      this.listingsLoading = true
      try {
        const { data } = await http.get<ListingListItem[]>('/api/listings/', { params })
        this.listings = data
        return data
      } finally {
        this.listingsLoading = false
      }
    },

    async fetchPublicListing(id: number) {
      this.listingLoading = true
      try {
        const { data } = await http.get<PublicListing>(`/api/listings/${id}/`)
        this.listing = data
        return data
      } finally {
        this.listingLoading = false
      }
    },

    async fetchKeyCounts() {
      try {
        const { data } = await http.get<any[]>('/api/client/packs/')
        const packs = Array.isArray(data) ? data : (data as any).results ?? []
        this.virtualKeys = packs.reduce((s: number, p: any) => s + Math.max(p.virtual_total - p.virtual_used, 0), 0)
        this.physicalKeys = packs.reduce((s: number, p: any) => s + (p.has_physical_key ? 1 : 0), 0)
        this.keysLoaded = true
      } catch { /* silent */ }
    },

    async fetchTeaser(accessKey: string): Promise<TeaserResult> {
      const { data } = await http.get<TeaserResult>(
        `/api/videos/${accessKey}/teaser/`,
      )
      return data
    },

    async watchVideo(accessKey: string): Promise<WatchVideoResult> {
      const { data } = await http.post<WatchVideoResult>(
        `/api/videos/${accessKey}/watch/`,
      )
      this.unlockedVideos[accessKey] = data.video_url

      if (!data.already_watched) {
        if (this.virtualKeys > 0) this.virtualKeys--

        if (this.listing) {
          const vid = this.listing.videos.find(v => v.access_key === accessKey)
          if (vid) vid.views_count++
          this.listing.views_count++
        }
      }

      return data
    },

    getUnlockedUrl(accessKey: string): string | null {
      return this.unlockedVideos[accessKey] || null
    },

    async fetchFavoriteIds() {
      try {
        const { data } = await http.get<number[]>('/api/client/favorites/ids/')
        this.favoriteIds = new Set(data)
        this.favoritesLoaded = true
      } catch { /* silent */ }
    },

    async toggleFavorite(listingId: number): Promise<boolean> {
      const wasFav = this.favoriteIds.has(listingId)
      if (wasFav) {
        this.favoriteIds.delete(listingId)
        try {
          await http.delete(`/api/client/favorites/${listingId}/`)
        } catch {
          this.favoriteIds.add(listingId)
          return true
        }
        if (this.listing?.id === listingId) this.listing.favorites_count--
        return false
      } else {
        this.favoriteIds.add(listingId)
        try {
          await http.post(`/api/client/favorites/${listingId}/`)
        } catch {
          this.favoriteIds.delete(listingId)
          return false
        }
        if (this.listing?.id === listingId) this.listing.favorites_count++
        return true
      }
    },
  },
})
