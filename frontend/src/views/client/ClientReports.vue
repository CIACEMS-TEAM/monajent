<script setup lang="ts">
import { onMounted } from 'vue'
import { useClientStore } from '@/Stores/client'

const client = useClientStore()

onMounted(() => {
  client.fetchReports()
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

const reasonLabels: Record<string, string> = {
  ALREADY_SOLD: 'Bien déjà vendu',
  ALREADY_RENTED: 'Bien déjà loué',
  MISLEADING: 'Annonce trompeuse',
  DUPLICATE_VIDEO: 'Vidéo en double',
  SCAM: 'Arnaque suspectée',
  OTHER: 'Autre',
}

const statusConfig: Record<string, { label: string; cls: string }> = {
  PENDING: { label: 'En attente', cls: 'rpt__badge--pending' },
  REVIEWED: { label: 'Examiné', cls: 'rpt__badge--reviewed' },
  RESOLVED: { label: 'Résolu', cls: 'rpt__badge--resolved' },
  DISMISSED: { label: 'Rejeté', cls: 'rpt__badge--dismissed' },
}
</script>

<template>
  <div class="rpt">
    <h1 class="rpt__title">
      <i class="pi pi-flag"></i>
      Mes signalements
    </h1>

    <div v-if="client.reportsLoading && client.reports.length === 0" class="rpt__loading">
      <div class="rpt__spinner"></div>
    </div>

    <div v-else-if="client.reports.length === 0" class="rpt__empty">
      <svg viewBox="0 0 24 24" width="56" height="56"><path fill="#E0E0E0" d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg>
      <p>Aucun signalement pour l'instant.</p>
      <p class="rpt__hint">Quand vous signalez une annonce suspecte, elle apparaîtra ici.</p>
    </div>

    <div v-else class="rpt__list">
      <div v-for="r in client.reports" :key="r.id" class="rpt__card">
        <div class="rpt__card-head">
          <router-link :to="{ name: 'public-listing', params: { slug: r.listing_slug } }" class="rpt__listing-title">
            {{ r.listing_title }}
          </router-link>
          <span class="rpt__badge" :class="statusConfig[r.status]?.cls">
            {{ statusConfig[r.status]?.label || r.status }}
          </span>
        </div>
        <div class="rpt__card-reason">
          <span class="rpt__reason-badge">{{ reasonLabels[r.reason] || r.reason }}</span>
        </div>
        <p v-if="r.description" class="rpt__desc">{{ r.description }}</p>
        <span class="rpt__date">Signalé le {{ formatDate(r.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rpt { max-width: 700px; margin: 0 auto; padding: 0 16px; }
.rpt__title {
  font-size: 22px; font-weight: 700; color: #0F0F0F;
  margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
}
.rpt__title i { color: #e53935; }

.rpt__loading { display: flex; justify-content: center; padding: 64px 0; }
.rpt__spinner {
  width: 32px; height: 32px; border: 3px solid #E0E0E0;
  border-top-color: #1DA53F; border-radius: 50%;
  animation: rpt-spin 0.7s linear infinite;
}
@keyframes rpt-spin { to { transform: rotate(360deg); } }

.rpt__empty { text-align: center; padding: 64px 16px; color: #606060; }
.rpt__empty p { margin: 8px 0; }
.rpt__hint { font-size: 14px; color: #888; }

.rpt__list { display: flex; flex-direction: column; gap: 12px; }

.rpt__card {
  padding: 16px; border-radius: 12px;
  background: #fff; border: 1px solid #e0e0e0;
  transition: box-shadow 0.15s;
}
.rpt__card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.05); }

.rpt__card-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 10px; margin-bottom: 8px;
}
.rpt__listing-title {
  font-size: 15px; font-weight: 600; color: #0f0f0f;
  text-decoration: none; flex: 1; min-width: 0;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.rpt__listing-title:hover { color: #1DA53F; }

.rpt__badge {
  font-size: 11px; font-weight: 600; padding: 3px 8px;
  border-radius: 4px; white-space: nowrap; flex-shrink: 0;
}
.rpt__badge--pending { background: #fef3c7; color: #d97706; }
.rpt__badge--reviewed { background: #dbeafe; color: #2563eb; }
.rpt__badge--resolved { background: #dcfce7; color: #16a34a; }
.rpt__badge--dismissed { background: #f2f2f2; color: #888; }

.rpt__card-reason { margin-bottom: 6px; }
.rpt__reason-badge {
  font-size: 12px; font-weight: 500; color: #e53935;
  padding: 2px 8px; background: #fef2f2; border-radius: 4px;
}

.rpt__desc {
  font-size: 13px; color: #555; line-height: 1.5;
  margin: 6px 0 8px; font-style: italic;
}

.rpt__date { font-size: 12px; color: #999; }

@media (max-width: 480px) {
  .rpt__card { padding: 14px; }
  .rpt__card-head { flex-direction: column; }
}
</style>
