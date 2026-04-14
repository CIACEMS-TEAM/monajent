<template>
  <div>
    <!-- Mona search banner -->
    <div v-if="pub.monaSearchActive" class="yt-search-banner yt-search-banner--mona">
      <div class="yt-search-banner__info">
        <span class="yt-search-banner__mona-icon">M</span>
        <span
          >Recherche Mona : <strong>« {{ pub.monaSearchLabel }} »</strong></span
        >
        <span v-if="!pub.listingsLoading" class="yt-search-banner__count">
          — {{ pub.listings.length }} résultat{{ pub.listings.length !== 1 ? 's' : '' }}
        </span>
      </div>
      <button class="yt-search-banner__clear" @click="clearMonaSearch">
        <i class="pi pi-times"></i> Effacer
      </button>
    </div>

    <!-- Text search banner -->
    <div v-else-if="activeSearch" class="yt-search-banner">
      <div class="yt-search-banner__info">
        <i class="pi pi-search"></i>
        <span
          >Résultats pour <strong>« {{ activeSearch }} »</strong></span
        >
        <span v-if="!pub.listingsLoading" class="yt-search-banner__count">
          — {{ pub.listings.length }} annonce{{ pub.listings.length !== 1 ? 's' : '' }}
        </span>
      </div>
      <button class="yt-search-banner__clear" @click="clearSearch">
        <i class="pi pi-times"></i> Effacer
      </button>
    </div>

    <!-- Category Chips (hidden during Mona search) -->
    <div v-if="!pub.monaSearchActive" class="yt-chips-bar">
      <div class="yt-chips-scroll">
        <button
          v-for="chip in chips"
          :key="chip.value"
          class="yt-chip"
          :class="{ active: activeChip === chip.value }"
          @click="selectChip(chip.value)"
        >
          {{ chip.label }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="pub.listingsLoading" class="yt-loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem; color: #1da53f"></i>
      <span>Chargement des annonces...</span>
    </div>

    <!-- Mona search: 0 results — contextual empty + suggestions -->
    <template v-else-if="pub.monaSearchActive && pub.listings.length === 0">
      <div class="yt-mona-empty">
        <div class="yt-mona-empty__icon">
          <svg viewBox="0 0 24 24" width="40" height="40">
            <circle cx="12" cy="12" r="11" fill="#f59e0b" />
            <path
              fill="#fff"
              d="M12 5.99L19.53 19H4.47L12 5.99M12 2L1 21h22L12 2zm1 14h-2v2h2v-2zm0-6h-2v4h2v-4z"
            />
          </svg>
        </div>
        <p class="yt-mona-empty__title">Aucun résultat pour cette recherche</p>
        <p class="yt-mona-empty__sub">
          Mona n'a trouvé aucune annonce correspondant à
          <strong>« {{ pub.monaSearchLabel }} »</strong>
        </p>
        <button class="yt-mona-empty__btn" @click="clearMonaSearch">
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path
              fill="currentColor"
              d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
            />
          </svg>
          Voir toutes les annonces
        </button>
      </div>

      <!-- Suggestions : biens disponibles -->
      <div v-if="suggestedListings.length > 0" class="yt-suggestions">
        <div class="yt-suggestions__header">
          <h3 class="yt-suggestions__title">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path
                fill="#1DA53F"
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
              />
            </svg>
            Biens disponibles sur la plateforme
          </h3>
          <span class="yt-suggestions__count"
            >{{ suggestedListings.length }} annonce{{
              suggestedListings.length !== 1 ? 's' : ''
            }}</span
          >
        </div>
        <div class="yt-grid">
          <div
            v-for="(listing, idx) in suggestedDisplay"
            :key="listing.id"
            class="yt-card"
            @click="handleCardClick(listing.slug)"
          >
            <div class="yt-card__thumb">
              <div
                class="yt-card__thumb-img"
                :style="!listing.coverImage ? { background: listing.thumbGradient } : {}"
              >
                <img
                  v-if="listing.coverImage"
                  :src="listing.coverImage"
                  :alt="listing.title"
                  class="yt-card__cover"
                  :loading="idx > 2 ? 'lazy' : undefined"
                />
                <div class="yt-card__play-overlay">
                  <svg viewBox="0 0 48 48" width="48" height="48">
                    <circle cx="24" cy="24" r="22" fill="rgba(0,0,0,0.65)" />
                    <path fill="#fff" d="M19 15l14 9-14 9V15z" />
                  </svg>
                </div>
              </div>
              <span v-if="listing.videosCount > 0" class="yt-card__video-badge"
                ><i class="pi pi-video"></i> {{ listing.videosCount }}</span
              >
              <span
                class="yt-card__type-badge"
                :class="listing.type === 'LOCATION' ? 'type-location' : 'type-vente'"
                >{{ listing.type === 'LOCATION' ? 'Location' : 'Vente' }}</span
              >
              <button
                v-if="auth.me?.role === 'CLIENT'"
                class="yt-card__fav"
                :class="{ 'yt-card__fav--active': pub.isFavorite(listing.id) }"
                @click="toggleFavorite($event, listing.id)"
              >
                <svg viewBox="0 0 24 24" width="22" height="22">
                  <path
                    :fill="pub.isFavorite(listing.id) ? '#ef4444' : 'none'"
                    :stroke="pub.isFavorite(listing.id) ? '#ef4444' : '#fff'"
                    stroke-width="2"
                    d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"
                  />
                </svg>
              </button>
            </div>
            <div class="yt-card__body">
              <div class="yt-card__avatar-wrap">
                <div class="yt-card__avatar" :style="{ backgroundColor: listing.agentColor }">
                  <img
                    v-if="listing.agentPhoto"
                    :src="listing.agentPhoto"
                    alt=""
                    class="yt-card__avatar-img"
                    loading="lazy"
                    width="36"
                    height="36"
                  />
                  <span v-else>{{ listing.agentInitial }}</span>
                </div>
                <svg
                  v-if="listing.agentVerified"
                  class="yt-card__avatar-badge"
                  viewBox="0 0 24 24"
                  width="14"
                  height="14"
                >
                  <circle cx="12" cy="12" r="11" fill="#1DA53F" stroke="#fff" stroke-width="2" />
                  <path
                    fill="#fff"
                    d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"
                  />
                </svg>
              </div>
              <div class="yt-card__meta">
                <h3 class="yt-card__title">{{ listing.title }}</h3>
                <p class="yt-card__agent">{{ listing.agentName }}</p>
                <p class="yt-card__stats">
                  <span class="yt-card__price">{{ listing.price }}</span>
                  <span class="yt-card__dot">&middot;</span>
                  {{ listing.views }}
                  <span class="yt-card__dot">&middot;</span>
                  {{ listing.publishedAgo }}
                </p>
                <p v-if="listing.conditions" class="yt-card__conditions">
                  <i class="pi pi-file-edit"></i> {{ listing.conditions }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Generic empty (no Mona, no search) -->
    <div v-else-if="pub.listings.length === 0" class="yt-empty">
      <i class="pi pi-home" style="font-size: 3rem; color: #ccc"></i>
      <p>Aucune annonce disponible pour le moment.</p>
    </div>

    <!-- Listings Grid -->
    <div v-else class="yt-grid">
      <div
        v-for="(listing, idx) in displayListings"
        :key="listing.id"
        class="yt-card"
        @click="handleCardClick(listing.slug)"
      >
        <div class="yt-card__thumb">
          <div
            class="yt-card__thumb-img"
            :style="!listing.coverImage ? { background: listing.thumbGradient } : {}"
          >
            <img
              v-if="listing.coverImage"
              :src="listing.coverImage"
              :alt="listing.title"
              class="yt-card__cover"
              :fetchpriority="idx === 0 ? 'high' : undefined"
              :loading="idx > 2 ? 'lazy' : undefined"
            />
            <div class="yt-card__play-overlay">
              <svg viewBox="0 0 48 48" width="48" height="48">
                <circle cx="24" cy="24" r="22" fill="rgba(0,0,0,0.65)" />
                <path fill="#fff" d="M19 15l14 9-14 9V15z" />
              </svg>
            </div>
          </div>
          <span v-if="listing.videosCount > 0" class="yt-card__video-badge">
            <i class="pi pi-video"></i> {{ listing.videosCount }}
          </span>
          <span class="yt-card__duration" v-if="listing.videoDuration">{{
            listing.videoDuration
          }}</span>
          <span
            class="yt-card__type-badge"
            :class="listing.type === 'LOCATION' ? 'type-location' : 'type-vente'"
          >
            {{ listing.type === 'LOCATION' ? 'Location' : 'Vente' }}
          </span>
          <button
            v-if="auth.me?.role === 'CLIENT'"
            class="yt-card__fav"
            :class="{ 'yt-card__fav--active': pub.isFavorite(listing.id) }"
            @click="toggleFavorite($event, listing.id)"
            :title="pub.isFavorite(listing.id) ? 'Retirer des favoris' : 'Ajouter aux favoris'"
          >
            <svg viewBox="0 0 24 24" width="22" height="22">
              <path
                :fill="pub.isFavorite(listing.id) ? '#ef4444' : 'none'"
                :stroke="pub.isFavorite(listing.id) ? '#ef4444' : '#fff'"
                stroke-width="2"
                d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"
              />
            </svg>
          </button>
        </div>

        <div class="yt-card__body">
          <div class="yt-card__avatar-wrap">
            <div class="yt-card__avatar" :style="{ backgroundColor: listing.agentColor }">
              <img
                v-if="listing.agentPhoto"
                :src="listing.agentPhoto"
                alt=""
                class="yt-card__avatar-img"
                loading="lazy"
                width="36"
                height="36"
              />
              <span v-else>{{ listing.agentInitial }}</span>
            </div>
            <svg
              v-if="listing.agentVerified"
              class="yt-card__avatar-badge"
              viewBox="0 0 24 24"
              width="14"
              height="14"
            >
              <circle cx="12" cy="12" r="11" fill="#1DA53F" stroke="#fff" stroke-width="2" />
              <path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z" />
            </svg>
          </div>
          <div class="yt-card__meta">
            <h3 class="yt-card__title">{{ listing.title }}</h3>
            <p class="yt-card__agent">{{ listing.agentName }}</p>
            <p class="yt-card__stats">
              <span class="yt-card__price">{{ listing.price }}</span>
              <span class="yt-card__dot">&middot;</span>
              {{ listing.views }}
              <span class="yt-card__dot">&middot;</span>
              {{ listing.publishedAgo }}
            </p>
            <p v-if="listing.conditions" class="yt-card__conditions">
              <i class="pi pi-file-edit"></i> {{ listing.conditions }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'
import { usePublicStore, type ListingListItem, type PublicListingAgent } from '@/Stores/public'
import { useToast } from 'vue-toastification'
import http, { API_BASE } from '@/services/http'
import posthog from 'posthog-js'

const auth = useAuthStore()
const pub = usePublicStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()

const activeSearch = computed(() => (route.query.q as string) || '')

const suggestedListings = ref<ListingListItem[]>([])

const suggestedDisplay = computed<DisplayListing[]>(() => suggestedListings.value.map(apiToDisplay))

async function toggleFavorite(e: Event, listingId: number) {
  e.stopPropagation()
  if (!auth.me) {
    router.push({ name: 'login', query: { redirect: '/home' } })
    return
  }
  if (auth.me.role !== 'CLIENT') return
  const isFav = await pub.toggleFavorite(listingId)
  posthog.capture('favorite_toggled', {
    listing_id: listingId,
    action: isFav ? 'added' : 'removed',
  })
  toast.success(isFav ? 'Ajouté aux favoris' : 'Retiré des favoris')
}

const activeChip = ref('all')
const knownCities = ref<string[]>([])

function captureAvailableCities(listings: ListingListItem[]) {
  const countMap = new Map<string, number>()
  for (const l of listings) {
    if (l.city) countMap.set(l.city, (countMap.get(l.city) || 0) + 1)
  }
  knownCities.value = [...countMap.entries()].sort((a, b) => b[1] - a[1]).map(([name]) => name)
}

const chips = computed(() => {
  const base: { label: string; value: string }[] = [
    { label: 'Tous', value: 'all' },
    { label: 'Location', value: 'LOCATION' },
    { label: 'Vente', value: 'VENTE' },
  ]
  for (const city of knownCities.value) {
    base.push({ label: city, value: city })
  }
  return base
})

interface DisplayListing {
  id: number
  slug: string
  title: string
  type: 'LOCATION' | 'VENTE'
  price: string
  conditions: string
  coverImage: string | null
  thumbGradient: string
  videosCount: number
  videoDuration: string
  agentName: string
  agentInitial: string
  agentColor: string
  agentPhoto: string | null
  agentVerified: boolean
  views: string
  publishedAgo: string
}

function mediaUrl(url: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http')) return url
  return `${API_BASE}${url}`
}

function formatPrice(val: string | number): string {
  return Number(val).toLocaleString('fr-FR') + ' F CFA'
}

function agentInitial(agent: PublicListingAgent): string {
  const name = agent.agency_name || agent.username || agent.phone
  return name.charAt(0).toUpperCase()
}

const agentColors = [
  '#e85d04',
  '#2d6a4f',
  '#0077b6',
  '#7b2cbf',
  '#d62828',
  '#457b9d',
  '#606c38',
  '#9d4edd',
]

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return "aujourd'hui"
  if (days === 1) return 'il y a 1 jour'
  if (days < 7) return `il y a ${days} jours`
  const weeks = Math.floor(days / 7)
  if (weeks === 1) return 'il y a 1 semaine'
  return `il y a ${weeks} semaines`
}

const placeholderGradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  'linear-gradient(135deg, #c3cfe2 0%, #f5f7fa 100%)',
  'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
  'linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)',
]

function conditionsLabel(item: ListingListItem): string {
  const parts: string[] = []
  if (item.deposit_months) parts.push(`${item.deposit_months} caution`)
  if (item.advance_months) parts.push(`${item.advance_months} avance`)
  if (item.agency_fee_months) parts.push(`${item.agency_fee_months} agence`)
  return parts.length ? parts.join(' + ') : ''
}

function apiToDisplay(item: ListingListItem): DisplayListing {
  const cover = item.cover_image
    ? item.cover_image.startsWith('http')
      ? item.cover_image
      : `${API_BASE}${item.cover_image}`
    : null
  const agentPhoto = item.agent.profile_photo ? mediaUrl(item.agent.profile_photo) : null
  return {
    id: item.id,
    slug: item.slug,
    title: item.title,
    type: item.listing_type,
    price: formatPrice(item.price),
    conditions: conditionsLabel(item),
    coverImage: cover,
    thumbGradient: placeholderGradients[item.id % placeholderGradients.length],
    videosCount: item.videos_count,
    videoDuration: '',
    agentName: item.agent.agency_name || item.agent.username || item.agent.phone,
    agentInitial: agentInitial(item.agent),
    agentColor: agentColors[item.agent.id % agentColors.length],
    agentPhoto,
    agentVerified: item.agent.verified,
    views: item.visits_count
      ? `${item.views_count} vues · ${item.visits_count} visites`
      : `${item.views_count} vues`,
    publishedAgo: timeAgo(item.created_at),
  }
}

const displayListings = computed<DisplayListing[]>(() => {
  return pub.listings.map(apiToDisplay)
})

function handleCardClick(slug: string) {
  posthog.capture('listing_clicked', { listing_slug: slug })
  router.push({ name: 'public-listing', params: { slug } })
}

async function loadListings() {
  const params: Record<string, string> = {}
  if (activeChip.value === 'LOCATION' || activeChip.value === 'VENTE') {
    params.listing_type = activeChip.value
  } else if (activeChip.value !== 'all') {
    params.city = activeChip.value
  }
  const q = ((route.query.q as string) || '').trim()
  if (q) params.search = q
  try {
    await pub.fetchListings(params)
    if (activeChip.value === 'all' && !q && knownCities.value.length === 0) {
      captureAvailableCities(pub.listings)
    }
  } catch (_) {}
}

function selectChip(value: string) {
  activeChip.value = value
  loadListings()
}

function clearSearch() {
  router.replace({ path: '/home', query: {} })
}

async function clearMonaSearch() {
  pub.clearMonaSearch()
  suggestedListings.value = []
  activeChip.value = 'all'
  await loadListings()
}

async function loadSuggestions() {
  try {
    const { data } = await http.get('/api/listings/', { params: { page: '1' } })
    const results: ListingListItem[] = Array.isArray(data) ? data : (data.results ?? [])
    suggestedListings.value = results
  } catch {
    suggestedListings.value = []
  }
}

watch(
  () => route.query.q,
  () => {
    loadListings()
  },
)

watch(
  () => pub.monaSearchActive && pub.listings.length === 0,
  (shouldLoad) => {
    if (shouldLoad) loadSuggestions()
    else suggestedListings.value = []
  },
)

onMounted(() => {
  if (pub.monaSearchActive) {
    pub.clearMonaSearch()
  }
  loadListings()
})
</script>

<style scoped>
/* Search banner */
.yt-search-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  margin-bottom: 0;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  flex-wrap: wrap;
}
.yt-search-banner--mona {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 50%, #f0faf3 100%);
  border-color: #86efac;
  margin-bottom: 16px;
}
.yt-search-banner__mona-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #1da53f;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.yt-search-banner__info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #166534;
  flex-wrap: wrap;
}
.yt-search-banner__info i {
  font-size: 15px;
  color: #1da53f;
}
.yt-search-banner__info strong {
  font-weight: 600;
}
.yt-search-banner__count {
  font-size: 13px;
  color: #15803d;
}
.yt-search-banner__clear {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: none;
  border-radius: 16px;
  background: #fff;
  color: #dc2626;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.yt-search-banner__clear:hover {
  background: #fef2f2;
}
.yt-search-banner__clear i {
  font-size: 11px;
}

/* Mona empty state */
.yt-mona-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px 24px;
  text-align: center;
}
.yt-mona-empty__icon {
  margin-bottom: 4px;
}
.yt-mona-empty__title {
  font-size: 17px;
  font-weight: 700;
  color: #0f0f0f;
  margin: 0;
}
.yt-mona-empty__sub {
  font-size: 14px;
  color: #606060;
  line-height: 1.5;
  margin: 0;
  max-width: 420px;
}
.yt-mona-empty__sub strong {
  color: #333;
  font-weight: 600;
}
.yt-mona-empty__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 24px;
  background: #1da53f;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s,
    transform 0.15s;
}
.yt-mona-empty__btn:hover {
  background: #178a33;
  transform: translateY(-1px);
}

/* Suggestions section */
.yt-suggestions {
  margin-top: 8px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}
.yt-suggestions__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.yt-suggestions__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #0f0f0f;
  margin: 0;
}
.yt-suggestions__count {
  font-size: 13px;
  color: #15803d;
  font-weight: 500;
}

.yt-chips-bar {
  position: sticky;
  top: 56px;
  background: #fff;
  padding: 12px 0;
  z-index: 50;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 24px;
}
.yt-chips-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 4px;
}
.yt-chips-scroll::-webkit-scrollbar {
  display: none;
}
.yt-chip {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: #f2f2f2;
  color: #0f0f0f;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background 0.15s,
    color 0.15s;
}
.yt-chip:hover {
  background: #e0e0e0;
}
.yt-chip.active {
  background: #0f0f0f;
  color: #fff;
}
.yt-chip.active:hover {
  background: #272727;
}

.yt-loading,
.yt-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 20px;
  color: #606060;
  font-size: 15px;
}

.yt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.yt-card {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.15s;
}
.yt-card:hover {
  transform: translateY(-1px);
}
.yt-card__thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  overflow: hidden;
  background: #f2f2f2;
}
.yt-card__thumb-img {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.yt-card__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.yt-card__play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}
.yt-card:hover .yt-card__play-overlay {
  opacity: 1;
}
.yt-card__video-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.yt-card__duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}
.yt-card__video-badge + .yt-card__duration {
  display: none;
}
.yt-card__type-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}
.type-location {
  background: #2563eb;
  color: #fff;
}
.type-vente {
  background: #1da53f;
  color: #fff;
}

.yt-card__fav {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.35);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    transform 0.2s,
    background 0.2s;
  z-index: 2;
}
.yt-card__fav:hover {
  background: rgba(0, 0, 0, 0.55);
  transform: scale(1.15);
}
.yt-card__fav--active {
  background: rgba(255, 255, 255, 0.9);
}
.yt-card__fav--active:hover {
  background: rgba(255, 255, 255, 1);
}
.yt-card__fav svg {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.yt-card__body {
  display: flex;
  gap: 12px;
  padding: 12px 4px 8px;
}
.yt-card__avatar-wrap {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}
.yt-card__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
}
.yt-card__avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.yt-card__avatar-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  display: block;
}
.yt-card__meta {
  flex: 1;
  min-width: 0;
}
.yt-card__title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  color: #0f0f0f;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}
.yt-card__agent {
  font-size: 12px;
  color: #606060;
  margin-bottom: 2px;
}
.yt-card__stats {
  font-size: 12px;
  color: #606060;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.yt-card__price {
  font-weight: 600;
  color: #1da53f;
}
.yt-card__dot {
  margin: 0 4px;
}
.yt-card__conditions {
  font-size: 11px;
  color: #d97706;
  margin: 2px 0 0;
  display: flex;
  align-items: center;
  gap: 4px;
}
.yt-card__conditions i {
  font-size: 10px;
}

@media (max-width: 768px) {
  .yt-chips-bar {
    margin-bottom: 16px;
  }
  .yt-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 480px) {
  .yt-grid {
    gap: 12px;
  }
  .yt-card__thumb {
    border-radius: 0;
  }
  .yt-chips-bar {
    padding: 12px 12px;
  }
}
</style>
