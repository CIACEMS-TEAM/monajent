<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePublicStore } from '@/Stores/public'
import { useToast } from 'vue-toastification'
import http from '@/services/http'

interface Favorite {
  id: number
  listing_id: number
  listing_slug: string
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
const router = useRouter()
const pub = usePublicStore()
const toast = useToast()

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
    pub.favoriteIds.delete(listingId)
    toast.success('Retiré des favoris')
  } catch { /* ignore */ }
}

function goToListing(slug: string) {
  router.push({ name: 'public-listing', params: { slug } })
}

function typeLabel(t: string) { return t === 'LOCATION' ? 'Location' : 'Vente' }

function formatPrice(val: string | number) {
  return Number(val).toLocaleString('fr-FR') + ' F CFA'
}

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
</script>

<template>
  <div class="fav">
    <h1 class="fav__title">
      <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#ef4444" d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/></svg>
      Mes favoris
      <span v-if="!loading" class="fav__count">({{ favorites.length }})</span>
    </h1>

    <div v-if="loading" class="fav__loading"><div class="fav__spinner"></div></div>

    <div v-else-if="favorites.length === 0" class="fav__empty">
      <svg viewBox="0 0 24 24" width="56" height="56"><path fill="#E0E0E0" d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/></svg>
      <p>Aucun favori pour l'instant.</p>
      <p class="fav__hint">Explorez les annonces et cliquez sur le coeur pour sauvegarder vos biens préférés.</p>
      <router-link to="/home" class="fav__btn">Explorer les biens</router-link>
    </div>

    <div v-else class="fav__grid">
      <div v-for="fav in favorites" :key="fav.id" class="fav__card" @click="goToListing(fav.listing_slug)">
        <div class="fav__thumb" :style="fav.thumbnail ? { backgroundImage: `url(${fav.thumbnail})` } : {}">
          <span class="fav__type" :class="fav.listing_type === 'LOCATION' ? 'fav__type--loc' : 'fav__type--vente'">
            {{ typeLabel(fav.listing_type) }}
          </span>
          <span v-if="fav.listing_status !== 'ACTIF'" class="fav__status-badge">
            {{ fav.listing_status === 'EXPIRED' ? 'Expirée' : fav.listing_status === 'INACTIF' ? 'Inactive' : fav.listing_status }}
          </span>
        </div>
        <div class="fav__body">
          <h3 class="fav__name">{{ fav.listing_title }}</h3>
          <p class="fav__city"><i class="pi pi-map-marker"></i> {{ fav.listing_city }}</p>
          <div class="fav__bottom">
            <span class="fav__price">{{ formatPrice(fav.listing_price) }}</span>
            <span class="fav__date">{{ timeAgo(fav.created_at) }}</span>
          </div>
        </div>
        <button class="fav__remove" @click.stop="removeFavorite(fav.listing_id)" title="Retirer des favoris">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fav { max-width: 900px; margin: 0 auto; padding: 0 16px; }
.fav__title {
  font-size: 22px; font-weight: 700; color: #0F0F0F;
  margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
}
.fav__count { font-size: 16px; font-weight: 400; color: #888; }
.fav__loading { display: flex; justify-content: center; padding: 64px 0; }
.fav__spinner { width: 32px; height: 32px; border: 3px solid #E0E0E0; border-top-color: #1DA53F; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fav__empty { text-align: center; padding: 64px 16px; color: #606060; }
.fav__empty p { margin: 12px 0; }
.fav__hint { font-size: 14px; color: #888; }
.fav__btn { display: inline-block; padding: 10px 24px; background: #1DA53F; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 8px; }
.fav__btn:hover { background: #168a34; }

.fav__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }

.fav__card {
  background: #fff; border: 1px solid #E0E0E0; border-radius: 12px;
  overflow: hidden; position: relative; cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
}
.fav__card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-2px); }

.fav__thumb {
  height: 160px; background: linear-gradient(135deg, #667eea, #764ba2);
  background-size: cover; background-position: center; position: relative;
}
.fav__type {
  position: absolute; top: 8px; left: 8px; padding: 3px 8px;
  border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase;
}
.fav__type--loc { background: #2563eb; color: #fff; }
.fav__type--vente { background: #1DA53F; color: #fff; }
.fav__status-badge {
  position: absolute; bottom: 8px; left: 8px; padding: 2px 8px;
  border-radius: 4px; font-size: 11px; font-weight: 600;
  background: rgba(0,0,0,0.7); color: #fbbf24;
}

.fav__body { padding: 12px 16px; }
.fav__name {
  font-size: 14px; font-weight: 600; color: #0F0F0F; margin-bottom: 4px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.fav__city { font-size: 12px; color: #606060; margin-bottom: 8px; display: flex; align-items: center; gap: 4px; }
.fav__city i { font-size: 11px; }
.fav__bottom { display: flex; align-items: center; justify-content: space-between; }
.fav__price { font-size: 14px; font-weight: 700; color: #1DA53F; }
.fav__date { font-size: 11px; color: #999; }

.fav__remove {
  position: absolute; top: 8px; right: 8px;
  width: 34px; height: 34px; border-radius: 50%;
  background: rgba(255,255,255,0.9); color: #ef4444;
  border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, transform 0.15s;
}
.fav__remove:hover { background: #fef2f2; transform: scale(1.15); }

@media (max-width: 480px) {
  .fav__grid { grid-template-columns: 1fr; }
  .fav__thumb { height: 140px; }
}
</style>
