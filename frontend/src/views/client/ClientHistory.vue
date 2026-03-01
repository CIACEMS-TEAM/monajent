<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/services/http'
import { useToast } from 'vue-toastification'

interface ViewEntry {
  id: number
  video_id: number | null
  listing_id: number | null
  listing_title: string
  listing_city: string
  listing_status: string
  video_thumbnail: string | null
  video_duration: number | null
  agent_name: string
  agent_phone: string
  created_at: string
}

const views = ref<ViewEntry[]>([])
const loading = ref(true)
const router = useRouter()
const toast = useToast()

onMounted(async () => {
  try {
    const { data } = await http.get<any>('/api/client/views/')
    views.value = Array.isArray(data) ? data : data.results ?? []
  } catch { /* empty state */ }
  finally { loading.value = false }
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDuration(sec: number | null): string {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function mediaUrl(path: string | null): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const base = (import.meta as any).env?.VITE_API_BASE_URL || ''
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`
}

function isListingActive(entry: ViewEntry): boolean {
  return !!entry.listing_id && entry.listing_status === 'ACTIF'
}

function goToListing(entry: ViewEntry) {
  if (!isListingActive(entry)) {
    toast.info('Cette annonce n\'est plus disponible sur la plateforme.')
    return
  }
  router.push({ name: 'public-listing', params: { id: entry.listing_id! } })
}
</script>

<template>
  <div class="hist">
    <h1 class="hist__title">
      <i class="pi pi-history"></i>
      Historique de visionnage
    </h1>

    <div v-if="loading" class="hist__loading"><div class="hist__spinner"></div></div>

    <div v-else-if="views.length === 0" class="hist__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
      <p>Aucun visionnage pour l'instant.</p>
      <router-link to="/home" class="hist__btn">Explorer les biens</router-link>
    </div>

    <div v-else class="hist__list">
      <div
        v-for="entry in views"
        :key="entry.id"
        class="hist__card"
        :class="{ 'hist__card--clickable': isListingActive(entry), 'hist__card--inactive': !isListingActive(entry) }"
        @click="goToListing(entry)"
      >
        <div class="hist__thumb">
          <img
            v-if="entry.video_thumbnail"
            :src="mediaUrl(entry.video_thumbnail)"
            alt=""
            class="hist__thumb-img"
          />
          <div v-else class="hist__thumb-placeholder">
            <svg viewBox="0 0 24 24" width="28" height="28">
              <path fill="#1DA53F" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/>
            </svg>
          </div>
          <span v-if="entry.video_duration" class="hist__duration">
            {{ formatDuration(entry.video_duration) }}
          </span>
        </div>

        <div class="hist__info">
          <h3 class="hist__name">
            {{ entry.listing_title || `Vidéo #${entry.id}` }}
          </h3>
          <p class="hist__meta">
            <span v-if="entry.listing_city" class="hist__city">
              <i class="pi pi-map-marker"></i> {{ entry.listing_city }}
            </span>
            <span v-if="entry.agent_name" class="hist__agent">
              {{ entry.agent_name }}
            </span>
          </p>
          <p class="hist__date">{{ formatDate(entry.created_at) }}</p>
        </div>

        <div class="hist__trail">
          <span
            v-if="isListingActive(entry)"
            class="hist__status hist__status--active"
            title="Annonce disponible"
          >
            <i class="pi pi-external-link"></i> Voir
          </span>
          <span
            v-else
            class="hist__status hist__status--gone"
            title="Annonce indisponible"
          >
            <i class="pi pi-ban"></i> Indisponible
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hist { max-width: 800px; margin: 0 auto; padding: 0 16px; }
.hist__title {
  font-size: 22px; font-weight: 700; color: #0F0F0F;
  margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
}
.hist__title i { color: #1DA53F; }

.hist__loading { display: flex; justify-content: center; padding: 64px 0; }
.hist__spinner {
  width: 32px; height: 32px; border: 3px solid #E0E0E0;
  border-top-color: #1DA53F; border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.hist__empty { text-align: center; padding: 64px 16px; color: #606060; }
.hist__empty p { margin: 12px 0; }
.hist__btn {
  display: inline-block; padding: 10px 24px; background: #1DA53F;
  color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600;
}

.hist__list { display: flex; flex-direction: column; gap: 10px; }

.hist__card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border: 1px solid #E0E0E0; border-radius: 12px;
  padding: 12px 16px; transition: box-shadow .15s, border-color .15s;
}
.hist__card--clickable { cursor: pointer; }
.hist__card--clickable:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
  border-color: #1DA53F;
}
.hist__card--inactive { opacity: 0.7; cursor: default; }

/* Thumbnail */
.hist__thumb {
  position: relative; width: 80px; height: 56px;
  border-radius: 8px; overflow: hidden; flex-shrink: 0;
  background: #f0f0f0;
}
.hist__thumb-img {
  width: 100%; height: 100%; object-fit: cover;
}
.hist__thumb-placeholder {
  width: 100%; height: 100%; display: flex;
  align-items: center; justify-content: center; background: #f5f5f5;
}
.hist__duration {
  position: absolute; bottom: 3px; right: 4px;
  background: rgba(0,0,0,.7); color: #fff;
  font-size: 10px; font-weight: 600; padding: 1px 5px;
  border-radius: 3px;
}

/* Info */
.hist__info { flex: 1; min-width: 0; }
.hist__name {
  font-size: 14px; font-weight: 600; color: #0F0F0F;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin: 0 0 3px;
}
.hist__meta {
  display: flex; align-items: center; gap: 10px;
  font-size: 12px; color: #606060; margin: 0 0 2px;
}
.hist__city i { font-size: 11px; margin-right: 2px; }
.hist__date { font-size: 11px; color: #999; margin: 0; }

/* Trailing badge */
.hist__trail { flex-shrink: 0; }
.hist__status {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; padding: 4px 10px;
  border-radius: 6px; white-space: nowrap;
}
.hist__status--active { background: #f0fdf4; color: #16a34a; }
.hist__status--gone { background: #f5f5f5; color: #999; }

@media (max-width: 480px) {
  .hist__card { flex-wrap: wrap; padding: 10px 12px; gap: 10px; }
  .hist__thumb { width: 64px; height: 44px; }
  .hist__trail { width: 100%; text-align: right; }
}
</style>
