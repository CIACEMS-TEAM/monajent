<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'

interface Favorite {
  id: number
  listing_id: number
  listing_title: string
  listing_city: string
  listing_type: string
  listing_price: string
  listing_status: string
  thumbnail: string | null
  created_at: string
}

const favorites = ref<Favorite[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await http.get<any>('/api/client/favorites/')
    favorites.value = Array.isArray(data) ? data : data.results ?? []
  } catch { /* empty state */ }
  finally { loading.value = false }
})

async function removeFavorite(listingId: number) {
  try {
    await http.delete(`/api/client/favorites/${listingId}/`)
    favorites.value = favorites.value.filter(f => f.listing_id !== listingId)
  } catch { /* ignore */ }
}

function typeLabel(t: string) { return t === 'LOCATION' ? 'Location' : 'Vente' }
</script>

<template>
  <div class="fav">
    <h1 class="fav__title">Mes favoris</h1>

    <div v-if="loading" class="fav__loading"><div class="fav__spinner"></div></div>

    <div v-else-if="favorites.length === 0" class="fav__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/></svg>
      <p>Aucun favori pour l'instant.</p>
      <router-link to="/home" class="fav__btn">Explorer les biens</router-link>
    </div>

    <div v-else class="fav__grid">
      <div v-for="fav in favorites" :key="fav.id" class="fav__card">
        <div class="fav__thumb" :style="fav.thumbnail ? { backgroundImage: `url(${fav.thumbnail})` } : {}">
          <span class="fav__type" :class="fav.listing_type === 'LOCATION' ? 'fav__type--loc' : 'fav__type--vente'">
            {{ typeLabel(fav.listing_type) }}
          </span>
        </div>
        <div class="fav__body">
          <h3 class="fav__name">{{ fav.listing_title }}</h3>
          <p class="fav__city">{{ fav.listing_city }}</p>
          <p class="fav__price">{{ fav.listing_price }} F</p>
        </div>
        <button class="fav__remove" @click="removeFavorite(fav.listing_id)" title="Retirer des favoris">
          <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fav { max-width: 800px; margin: 0 auto; }
.fav__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 20px; }
.fav__loading { display: flex; justify-content: center; padding: 64px 0; }
.fav__spinner { width: 32px; height: 32px; border: 3px solid #E0E0E0; border-top-color: #1DA53F; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fav__empty { text-align: center; padding: 64px 16px; color: #606060; }
.fav__empty p { margin: 12px 0; }
.fav__btn { display: inline-block; padding: 10px 24px; background: #1DA53F; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; }
.fav__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.fav__card { background: #fff; border: 1px solid #E0E0E0; border-radius: 12px; overflow: hidden; position: relative; }
.fav__thumb { height: 140px; background: linear-gradient(135deg, #667eea, #764ba2); background-size: cover; background-position: center; position: relative; }
.fav__type { position: absolute; top: 8px; left: 8px; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.fav__type--loc { background: #2563eb; color: #fff; }
.fav__type--vente { background: #1DA53F; color: #fff; }
.fav__body { padding: 12px 16px; }
.fav__name { font-size: 14px; font-weight: 600; color: #0F0F0F; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.fav__city { font-size: 12px; color: #606060; margin-bottom: 4px; }
.fav__price { font-size: 14px; font-weight: 700; color: #1DA53F; }
.fav__remove { position: absolute; top: 8px; right: 8px; width: 30px; height: 30px; border-radius: 50%; background: rgba(0,0,0,.5); color: #fff; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background .15s; }
.fav__remove:hover { background: rgba(220,38,38,.8); }
</style>
