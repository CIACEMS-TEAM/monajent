<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'

interface ViewEntry {
  id: number
  video_title: string
  listing_title: string
  agent_name: string
  created_at: string
}

const views = ref<ViewEntry[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await http.get<any>('/api/client/views/')
    views.value = Array.isArray(data) ? data : data.results ?? []
  } catch { /* empty state */ }
  finally { loading.value = false }
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="hist">
    <h1 class="hist__title">Historique de visionnage</h1>

    <div v-if="loading" class="hist__loading"><div class="hist__spinner"></div></div>

    <div v-else-if="views.length === 0" class="hist__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
      <p>Aucun visionnage pour l'instant.</p>
      <router-link to="/home" class="hist__btn">Explorer les biens</router-link>
    </div>

    <div v-else class="hist__list">
      <div v-for="entry in views" :key="entry.id" class="hist__card">
        <div class="hist__icon">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#1DA53F" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
        </div>
        <div class="hist__info">
          <h3 class="hist__name">{{ entry.listing_title || entry.video_title || `Vidéo #${entry.id}` }}</h3>
          <p class="hist__meta">{{ entry.agent_name || '—' }} · {{ formatDate(entry.created_at) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hist { max-width: 800px; margin: 0 auto; }
.hist__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 20px; }
.hist__loading { display: flex; justify-content: center; padding: 64px 0; }
.hist__spinner { width: 32px; height: 32px; border: 3px solid #E0E0E0; border-top-color: #1DA53F; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.hist__empty { text-align: center; padding: 64px 16px; color: #606060; }
.hist__empty p { margin: 12px 0; }
.hist__btn { display: inline-block; padding: 10px 24px; background: #1DA53F; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; }
.hist__list { display: flex; flex-direction: column; gap: 8px; }
.hist__card { display: flex; align-items: center; gap: 14px; background: #fff; border: 1px solid #E0E0E0; border-radius: 10px; padding: 14px 18px; transition: box-shadow .15s; }
.hist__card:hover { box-shadow: 0 2px 10px rgba(0,0,0,.05); }
.hist__icon { flex-shrink: 0; }
.hist__info { flex: 1; min-width: 0; }
.hist__name { font-size: 14px; font-weight: 600; color: #0F0F0F; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist__meta { font-size: 12px; color: #606060; margin-top: 2px; }
</style>
