<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useAgentStore } from '@/Stores/agent'

const agent = useAgentStore()

function isoDate(d: Date) { return d.toISOString().slice(0, 10) }

const presets = [
  { label: '7j', days: 7 },
  { label: '14j', days: 14 },
  { label: '28j', days: 28 },
  { label: '90j', days: 90 },
] as const

const activePreset = ref(28)
const now = new Date()
const endDate = ref(isoDate(now))
const startDate = ref(isoDate(new Date(now.getTime() - 27 * 86400000)))

function applyPreset(days: number) {
  activePreset.value = days
  const end = new Date()
  endDate.value = isoDate(end)
  startDate.value = isoDate(new Date(end.getTime() - (days - 1) * 86400000))
}

async function loadAnalytics() {
  try { await agent.fetchAnalytics(startDate.value, endDate.value) }
  catch (_) { /* handled by store */ }
}

watch([startDate, endDate], () => {
  const s = new Date(startDate.value)
  const e = new Date(endDate.value)
  const diff = Math.round((e.getTime() - s.getTime()) / 86400000) + 1
  const match = presets.find(p => p.days === diff && endDate.value === isoDate(new Date()))
  activePreset.value = match ? match.days : 0
  loadAnalytics()
})

onMounted(loadAnalytics)

const data = computed(() => agent.analytics)

const periodLabel = computed(() => {
  const days = data.value?.period_days || 28
  return `${days}j`
})

const maxDayViews = computed(() =>
  Math.max(...(data.value?.daily_stats?.map((d: any) => d.views) ?? [0]), 1)
)

function formatDay(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}

const maxReportCount = computed(() =>
  Math.max(...(data.value?.reports_by_reason?.map((r: any) => r.count) ?? [0]), 1)
)
</script>

<template>
  <div class="anl">
    <h1 class="anl__title">Données analytiques</h1>

    <!-- Date range selector -->
    <div class="anl__daterange">
      <div class="anl__presets">
        <button
          v-for="p in presets" :key="p.days"
          class="anl__preset-btn"
          :class="{ active: activePreset === p.days }"
          @click="applyPreset(p.days)"
        >{{ p.label }}</button>
      </div>
      <div class="anl__date-inputs">
        <label class="anl__date-field">
          <span>Du</span>
          <input type="date" v-model="startDate" :max="endDate" />
        </label>
        <label class="anl__date-field">
          <span>Au</span>
          <input type="date" v-model="endDate" :min="startDate" :max="isoDate(new Date())" />
        </label>
      </div>
    </div>

    <div v-if="agent.analyticsLoading && !data" class="anl__loading">Chargement des statistiques...</div>

    <template v-else-if="data">
      <!-- Summary cards -->
      <div class="anl__summary">
        <div class="anl__summary-card">
          <span class="anl__summary-label">Vues ({{ periodLabel }})</span>
          <span class="anl__summary-val">{{ data.total_views_28d }}</span>
          <span class="anl__summary-period" :class="data.trend_pct >= 0 ? 'up' : 'down'">
            {{ data.trend_pct >= 0 ? '+' : '' }}{{ data.trend_pct }}%
            <span class="anl__summary-trend-label">vs {{ periodLabel }} précédents</span>
          </span>
        </div>
        <div class="anl__summary-card">
          <span class="anl__summary-label">Favoris</span>
          <span class="anl__summary-val">{{ data.summary.total_favorites }}</span>
          <span class="anl__summary-period">Total</span>
        </div>
        <div class="anl__summary-card">
          <span class="anl__summary-label">Annonces actives</span>
          <span class="anl__summary-val">{{ data.summary.published_count }}</span>
          <span class="anl__summary-period">sur {{ data.summary.total_listings }} au total</span>
        </div>
        <div class="anl__summary-card">
          <span class="anl__summary-label">Visites effectuées</span>
          <span class="anl__summary-val">{{ data.visits.done }}</span>
          <span class="anl__summary-period">{{ data.visits.conversion_pct }}% conversion</span>
        </div>
      </div>

      <!-- Chart -->
      <section class="anl__chart-section">
        <h2 class="anl__section-title">Vues sur la période sélectionnée</h2>
        <div class="anl__chart">
          <div class="anl__chart-bars">
            <div
              v-for="(day, i) in data.daily_stats"
              :key="i"
              class="anl__bar-col"
              :title="`${formatDay(day.date)}: ${day.views} vues`"
            >
              <div
                class="anl__bar"
                :style="{ height: (day.views / maxDayViews * 100) + '%' }"
              ></div>
            </div>
          </div>
          <div class="anl__chart-labels">
            <span>{{ formatDay(data.daily_stats[0]?.date || '') }}</span>
            <span>{{ formatDay(data.daily_stats[Math.floor(data.daily_stats.length / 2)]?.date || '') }}</span>
            <span>{{ formatDay(data.daily_stats[data.daily_stats.length - 1]?.date || '') }}</span>
          </div>
        </div>
      </section>

      <!-- Top content -->
      <section class="anl__top">
        <h2 class="anl__section-title">Top annonces par vues</h2>
        <div v-if="data.top_listings.length > 0">
          <!-- Desktop table -->
          <div class="anl__top-table anl__top-table--desktop">
            <div class="anl__top-head">
              <span class="anl__top-col anl__top-col--title">Annonce</span>
              <span class="anl__top-col">Vues</span>
              <span class="anl__top-col">Favoris</span>
              <span class="anl__top-col">Taux conv.</span>
            </div>
            <div v-for="l in data.top_listings" :key="l.id" class="anl__top-row">
              <span class="anl__top-col anl__top-col--title">
                <div class="anl__top-thumb">
                  <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#aaa" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
                </div>
                <span class="anl__top-name">{{ l.title }}</span>
              </span>
              <span class="anl__top-col">{{ l.views_count }}</span>
              <span class="anl__top-col">{{ l.favorites_count }}</span>
              <span class="anl__top-col">{{ l.views_count > 0 ? ((l.favorites_count / l.views_count) * 100).toFixed(1) + '%' : '—' }}</span>
            </div>
          </div>
          <!-- Mobile cards -->
          <div class="anl__top-cards">
            <div v-for="l in data.top_listings" :key="l.id" class="anl__top-card">
              <div class="anl__top-card-left">
                <div class="anl__top-thumb">
                  <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#aaa" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
                </div>
                <div class="anl__top-card-info">
                  <span class="anl__top-card-name">{{ l.title }}</span>
                  <div class="anl__top-card-stats">
                    <span><i class="pi pi-eye" style="font-size:11px"></i> {{ l.views_count }}</span>
                    <span><i class="pi pi-heart" style="font-size:11px"></i> {{ l.favorites_count }}</span>
                    <span>{{ l.views_count > 0 ? ((l.favorites_count / l.views_count) * 100).toFixed(1) + '%' : '—' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="anl__empty">Aucune annonce active</p>
      </section>

      <!-- Reports breakdown -->
      <section v-if="data.reports_by_reason?.length" class="anl__reports-section">
        <h2 class="anl__section-title">
          <i class="pi pi-flag" style="color: #e53935; font-size: 14px"></i>
          Signalements par motif ({{ data.summary.total_reports }} au total)
        </h2>
        <div class="anl__reports-grid">
          <div v-for="r in data.reports_by_reason" :key="r.reason" class="anl__report-card">
            <span class="anl__report-count">{{ r.count }}</span>
            <span class="anl__report-label">{{ r.reason_label }}</span>
            <div class="anl__report-bar">
              <div class="anl__report-bar-fill" :style="{ width: maxReportCount > 0 ? (r.count / maxReportCount * 100) + '%' : '0%' }"></div>
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="data.summary.total_reports === 0" class="anl__reports-section">
        <h2 class="anl__section-title">
          <i class="pi pi-check-circle" style="color: #1DA53F; font-size: 14px"></i>
          Signalements
        </h2>
        <p class="anl__empty anl__reports-ok">Aucun signalement sur vos annonces. Continuez comme ça !</p>
      </section>

      <!-- Average -->
      <section class="anl__avg">
        <div class="anl__avg-card">
          <span class="anl__avg-label">Moyenne de vues par annonce</span>
          <span class="anl__avg-val">{{ data.summary.avg_views_per_listing }}</span>
        </div>
        <div class="anl__avg-card">
          <span class="anl__avg-label">Total vues toutes annonces</span>
          <span class="anl__avg-val">{{ data.summary.total_views }}</span>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.anl { max-width: 1200px; }
.anl__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 20px; }
.anl__loading { padding: 48px 0; text-align: center; color: #606060; }
.anl__empty { color: #606060; font-size: 14px; padding: 12px 0; }

.anl__daterange {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.anl__presets {
  display: flex;
  gap: 6px;
}
.anl__preset-btn {
  padding: 6px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 20px;
  background: #fff;
  color: #606060;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all .15s;
}
.anl__preset-btn:hover { border-color: #1DA53F; color: #1DA53F; }
.anl__preset-btn.active {
  background: #1DA53F;
  color: #fff;
  border-color: #1DA53F;
}
.anl__date-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}
.anl__date-field {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606060;
}
.anl__date-field input {
  padding: 6px 10px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 13px;
  color: #0F0F0F;
}
.anl__date-field input:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}

.anl__summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.anl__summary-card {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}
.anl__summary-label { font-size: 13px; color: #606060; margin-bottom: 4px; }
.anl__summary-val { font-size: 28px; font-weight: 700; color: #0F0F0F; }
.anl__summary-period { font-size: 12px; color: #606060; margin-top: 4px; display: flex; align-items: center; gap: 6px; }
.anl__summary-period.up { color: #1DA53F; font-weight: 600; }
.anl__summary-period.down { color: #dc2626; font-weight: 600; }
.anl__summary-trend-label { font-weight: 400; color: #606060; }

.anl__section-title { font-size: 16px; font-weight: 600; color: #0F0F0F; margin-bottom: 16px; }

.anl__chart-section {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.anl__chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 160px;
  padding: 0 4px;
}
.anl__bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
}
.anl__bar {
  background: #1DA53F;
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height .3s;
  opacity: 0.75;
}
.anl__bar-col:hover .anl__bar { opacity: 1; }

.anl__chart-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #606060;
  margin-top: 8px;
  padding: 0 4px;
}

.anl__top {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.anl__top-head,
.anl__top-row {
  display: grid;
  grid-template-columns: 2fr 0.7fr 0.7fr 0.8fr;
  gap: 12px;
  padding: 10px 0;
  align-items: center;
}
.anl__top-head {
  border-bottom: 1px solid #E0E0E0;
  font-size: 12px;
  color: #606060;
  font-weight: 500;
}
.anl__top-row {
  border-bottom: 1px solid #f2f2f2;
  font-size: 14px;
  color: #0F0F0F;
}
.anl__top-col--title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.anl__top-thumb {
  width: 44px;
  height: 28px;
  background: #f2f2f2;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.anl__top-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Reports */
.anl__reports-section {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}
.anl__reports-section .anl__section-title {
  display: flex; align-items: center; gap: 8px;
}
.anl__reports-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.anl__report-card {
  display: grid;
  grid-template-columns: 40px 1fr;
  grid-template-rows: auto auto;
  gap: 2px 10px;
  align-items: center;
  padding: 10px 12px;
  background: #fef2f2;
  border-radius: 8px;
}
.anl__report-count {
  grid-row: 1 / 3;
  font-size: 22px; font-weight: 700; color: #e53935;
  text-align: center;
}
.anl__report-label {
  font-size: 13px; font-weight: 500; color: #333;
}
.anl__report-bar {
  height: 4px; background: #fecaca; border-radius: 2px;
  overflow: hidden;
}
.anl__report-bar-fill {
  height: 100%; background: #e53935; border-radius: 2px;
  transition: width 0.3s;
}
.anl__reports-ok {
  color: #1DA53F; font-weight: 500;
}

.anl__avg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.anl__avg-card {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}
.anl__avg-label { font-size: 13px; color: #606060; margin-bottom: 4px; }
.anl__avg-val { font-size: 24px; font-weight: 700; color: #1DA53F; }

/* ====== MOBILE CARDS for top listings ====== */
.anl__top-cards { display: none; }

.anl__top-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f2f2f2;
}
.anl__top-card:last-child { border-bottom: none; }
.anl__top-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.anl__top-card-info { flex: 1; min-width: 0; }
.anl__top-card-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #0F0F0F;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.anl__top-card-stats {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #606060;
}
.anl__top-card-stats span {
  display: flex;
  align-items: center;
  gap: 3px;
}

@media (max-width: 900px) {
  .anl__summary { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .anl__title { font-size: 20px; }
  .anl__summary { grid-template-columns: repeat(2, 1fr); }
  .anl__summary-val { font-size: 22px; }
  .anl__summary-card { padding: 14px; }
  .anl__avg { grid-template-columns: 1fr; }
  .anl__avg-val { font-size: 20px; }
  .anl__chart-section { padding: 14px; }
  .anl__top { padding: 14px; }
  .anl__reports-section { padding: 14px; }

  .anl__top-table--desktop { display: none; }
  .anl__top-cards { display: flex; flex-direction: column; }

  .anl__daterange { flex-direction: column; align-items: flex-start; gap: 10px; }
  .anl__date-inputs { width: 100%; }
  .anl__date-field { flex: 1; }
  .anl__date-field input { width: 100%; }
}
@media (max-width: 480px) {
  .anl__summary { grid-template-columns: 1fr; }
  .anl__presets { width: 100%; justify-content: space-between; }
}
</style>
