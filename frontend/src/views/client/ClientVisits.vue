<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'

interface Visit {
  id: number
  listing_title: string
  listing_city: string
  agent_name: string
  status: string
  scheduled_date: string | null
  verification_code: string | null
  created_at: string
}

const visits = ref<Visit[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await http.get<any>('/api/client/visits/')
    visits.value = Array.isArray(data) ? data : data.results ?? []
  } catch { /* empty state */ }
  finally { loading.value = false }
})

async function cancelVisit(id: number) {
  try {
    await http.post(`/api/client/visits/${id}/cancel/`)
    const v = visits.value.find(v => v.id === id)
    if (v) v.status = 'CANCELLED'
  } catch { /* ignore */ }
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    REQUESTED: 'En attente',
    CONFIRMED: 'Confirmée',
    DONE: 'Terminée',
    CANCELLED: 'Annulée',
    NO_SHOW: 'No-show',
    EXPIRED: 'Expirée',
  }
  return map[s] || s
}

function statusClass(s: string) {
  const map: Record<string, string> = {
    REQUESTED: 'st--pending',
    CONFIRMED: 'st--success',
    DONE: 'st--success',
    CANCELLED: 'st--neutral',
    NO_SHOW: 'st--danger',
    EXPIRED: 'st--neutral',
  }
  return map[s] || 'st--neutral'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="vis">
    <h1 class="vis__title">Mes visites</h1>

    <div v-if="loading" class="vis__loading"><div class="vis__spinner"></div></div>

    <div v-else-if="visits.length === 0" class="vis__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
      <p>Aucune visite pour l'instant.</p>
      <router-link to="/home" class="vis__btn">Explorer les biens</router-link>
    </div>

    <div v-else class="vis__list">
      <div v-for="visit in visits" :key="visit.id" class="vis__card">
        <div class="vis__card-top">
          <span class="vis__status" :class="statusClass(visit.status)">{{ statusLabel(visit.status) }}</span>
          <span class="vis__date">{{ formatDate(visit.created_at) }}</span>
        </div>
        <h3 class="vis__listing">{{ visit.listing_title || `Annonce #${visit.id}` }}</h3>
        <p class="vis__meta">{{ visit.listing_city }} · Agent : {{ visit.agent_name || '—' }}</p>
        <div v-if="visit.verification_code && ['CONFIRMED', 'REQUESTED'].includes(visit.status)" class="vis__code">
          Code de vérification : <strong>{{ visit.verification_code }}</strong>
        </div>
        <div class="vis__actions">
          <button
            v-if="['REQUESTED', 'CONFIRMED'].includes(visit.status)"
            class="vis__cancel"
            @click="cancelVisit(visit.id)"
          >
            Annuler la visite
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vis { max-width: 800px; margin: 0 auto; }
.vis__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 20px; }
.vis__loading { display: flex; justify-content: center; padding: 64px 0; }
.vis__spinner { width: 32px; height: 32px; border: 3px solid #E0E0E0; border-top-color: #1DA53F; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.vis__empty { text-align: center; padding: 64px 16px; color: #606060; }
.vis__empty p { margin: 12px 0; }
.vis__btn { display: inline-block; padding: 10px 24px; background: #1DA53F; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; }
.vis__list { display: flex; flex-direction: column; gap: 12px; }
.vis__card { background: #fff; border: 1px solid #E0E0E0; border-radius: 12px; padding: 20px; }
.vis__card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.vis__status { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.st--pending { background: rgba(245,158,11,.1); color: #d97706; }
.st--success { background: rgba(29,165,63,.1); color: #1DA53F; }
.st--danger { background: rgba(220,38,38,.1); color: #dc2626; }
.st--neutral { background: #f2f2f2; color: #606060; }
.vis__date { font-size: 12px; color: #909090; }
.vis__listing { font-size: 16px; font-weight: 600; color: #0F0F0F; margin-bottom: 4px; }
.vis__meta { font-size: 13px; color: #606060; margin-bottom: 8px; }
.vis__code { font-size: 14px; color: #272727; background: #f8f8f8; padding: 10px 14px; border-radius: 8px; margin-bottom: 10px; }
.vis__code strong { color: #1DA53F; font-size: 16px; letter-spacing: 2px; }
.vis__actions { display: flex; gap: 8px; }
.vis__cancel { padding: 6px 16px; border: 1px solid #dc2626; background: transparent; color: #dc2626; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background .15s; }
.vis__cancel:hover { background: rgba(220,38,38,.06); }
</style>
