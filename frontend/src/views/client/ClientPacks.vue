<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'

interface Pack {
  id: number
  virtual_total: number
  virtual_used: number
  has_physical_key: boolean
  is_locked_by_visit: boolean
  created_at: string
}

const packs = ref<Pack[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await http.get<Pack[]>('/api/client/packs/')
    packs.value = Array.isArray(data) ? data : (data as any).results ?? []
  } catch { /* handled by empty state */ }
  finally { loading.value = false }
})

function remaining(p: Pack) { return Math.max(p.virtual_total - p.virtual_used, 0) }

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="pk">
    <div class="pk__header">
      <h1 class="pk__title">Mes packs</h1>
    </div>

    <div v-if="loading" class="pk__loading">
      <div class="pk__spinner"></div>
    </div>

    <div v-else-if="packs.length === 0" class="pk__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M18 6h-2c0-2.21-1.79-4-4-4S8 3.79 8 6H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6-2c1.1 0 2 .9 2 2h-4c0-1.1.9-2 2-2zm6 16H6V8h2v2c0 .55.45 1 1 1s1-.45 1-1V8h4v2c0 .55.45 1 1 1s1-.45 1-1V8h2v12z"/></svg>
      <p>Vous n'avez pas encore de pack.</p>
      <router-link to="/home" class="pk__btn">Explorer les biens</router-link>
    </div>

    <div v-else class="pk__grid">
      <div v-for="pack in packs" :key="pack.id" class="pk__card">
        <div class="pk__card-top">
          <span class="pk__badge" :class="{ 'pk__badge--locked': pack.is_locked_by_visit }">
            {{ pack.is_locked_by_visit ? 'Visite en cours' : 'Actif' }}
          </span>
          <span class="pk__date">{{ formatDate(pack.created_at) }}</span>
        </div>
        <div class="pk__keys">
          <div class="pk__key">
            <div class="pk__key-value">{{ remaining(pack) }}</div>
            <div class="pk__key-label">clés virtuelles</div>
          </div>
          <div class="pk__key">
            <div class="pk__key-value">{{ pack.has_physical_key ? '1' : '0' }}</div>
            <div class="pk__key-label">visite gratuite</div>
          </div>
        </div>
        <div class="pk__bar">
          <div class="pk__bar-fill" :style="{ width: (pack.virtual_used / pack.virtual_total * 100) + '%' }"></div>
        </div>
        <div class="pk__bar-label">{{ pack.virtual_used }}/{{ pack.virtual_total }} clés utilisées</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pk { max-width: 800px; margin: 0 auto; }
.pk__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.pk__title { font-size: 24px; font-weight: 700; color: #0F0F0F; }
.pk__loading { display: flex; justify-content: center; padding: 64px 0; }
.pk__spinner { width: 32px; height: 32px; border: 3px solid #E0E0E0; border-top-color: #1DA53F; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.pk__empty { text-align: center; padding: 64px 16px; color: #606060; }
.pk__empty p { margin: 12px 0; }
.pk__btn { display: inline-block; padding: 10px 24px; background: #1DA53F; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; }
.pk__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.pk__card { background: #fff; border: 1px solid #E0E0E0; border-radius: 12px; padding: 20px; }
.pk__card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.pk__badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; background: rgba(29,165,63,.1); color: #1DA53F; }
.pk__badge--locked { background: rgba(245,158,11,.1); color: #d97706; }
.pk__date { font-size: 12px; color: #909090; }
.pk__keys { display: flex; gap: 24px; margin-bottom: 14px; }
.pk__key-value { font-size: 28px; font-weight: 800; color: #0F0F0F; }
.pk__key-label { font-size: 12px; color: #606060; }
.pk__bar { height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
.pk__bar-fill { height: 100%; background: #1DA53F; border-radius: 3px; transition: width .3s; }
.pk__bar-label { font-size: 11px; color: #909090; margin-top: 4px; }
</style>
