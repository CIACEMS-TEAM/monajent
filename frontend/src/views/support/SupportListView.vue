<template>
  <div class="sp">
    <!-- Header -->
    <div class="sp-header">
      <div class="sp-header__left">
        <h1 class="sp-header__title">Aide & Support</h1>
        <p class="sp-header__sub">
          Un problème, une question ou une idée ? Ouvrez un ticket et notre équipe vous répond rapidement.
        </p>
      </div>
      <router-link :to="createRoute" class="sp-header__cta">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Nouveau ticket
      </router-link>
    </div>

    <!-- Stats -->
    <div class="sp-stats">
      <div class="sp-stat" v-for="s in stats" :key="s.key" :class="'sp-stat--' + s.key">
        <span class="sp-stat__num">{{ s.count }}</span>
        <span class="sp-stat__label">{{ s.label }}</span>
      </div>
    </div>

    <!-- Toolbar: filters + search -->
    <div class="sp-toolbar">
      <div class="sp-filters">
        <button
          v-for="f in filters" :key="f.value"
          class="sp-filter" :class="{ 'sp-filter--active': activeFilter === f.value }"
          @click="activeFilter = f.value"
        >
          {{ f.label }}
          <span v-if="f.count > 0" class="sp-filter__badge">{{ f.count }}</span>
        </button>
      </div>
      <div class="sp-search">
        <svg class="sp-search__icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="searchQuery" type="text" placeholder="Rechercher un ticket..." class="sp-search__input" />
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="support.ticketsLoading" class="sp-skeleton">
      <div v-for="i in 4" :key="i" class="sp-skeleton__card">
        <div class="sp-skeleton__bar sp-skeleton__bar--sm"></div>
        <div class="sp-skeleton__bar sp-skeleton__bar--lg"></div>
        <div class="sp-skeleton__bar sp-skeleton__bar--md"></div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="displayedTickets.length === 0" class="sp-empty">
      <div class="sp-empty__icon">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#CBD5E1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
          <line x1="9" y1="9" x2="15" y2="9"/>
          <line x1="9" y1="13" x2="13" y2="13"/>
        </svg>
      </div>
      <h3 class="sp-empty__title">{{ emptyTitle }}</h3>
      <p class="sp-empty__text">{{ emptyText }}</p>
      <router-link v-if="!activeFilter && !searchQuery" :to="createRoute" class="sp-empty__cta">
        Créer mon premier ticket
      </router-link>
      <button v-else class="sp-empty__reset" @click="activeFilter = ''; searchQuery = ''">
        Réinitialiser les filtres
      </button>
    </div>

    <!-- Ticket list -->
    <TransitionGroup v-else name="ticket" tag="div" class="sp-tickets">
      <router-link
        v-for="ticket in displayedTickets" :key="ticket.id"
        :to="detailRoute(ticket.id)"
        class="sp-ticket"
      >
        <div class="sp-ticket__priority" :class="'sp-ticket__priority--' + (ticket.priority || 'NORMAL').toLowerCase()" :title="ticket.priority_label || 'Normal'"></div>
        <div class="sp-ticket__body">
          <div class="sp-ticket__row1">
            <span class="sp-badge" :class="'sp-badge--' + (ticket.status || '').toLowerCase()">
              {{ ticket.status_label }}
            </span>
            <span class="sp-ticket__cat">{{ ticket.category_label }}</span>
          </div>
          <h3 class="sp-ticket__subject">{{ ticket.subject }}</h3>
          <div class="sp-ticket__row3">
            <span class="sp-ticket__id">#{{ ticket.id }}</span>
            <span class="sp-ticket__sep">·</span>
            <span class="sp-ticket__msgs">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
              {{ ticket.messages_count }}
            </span>
            <span class="sp-ticket__sep">·</span>
            <span class="sp-ticket__time">{{ timeAgo(ticket.updated_at) }}</span>
          </div>
        </div>
        <svg class="sp-ticket__chevron" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
      </router-link>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSupportStore } from '@/Stores/support'

const support = useSupportStore()
const route = useRoute()

const isAgent = computed(() => route.path.startsWith('/agent'))
const createRoute = computed(() => isAgent.value ? '/agent/support/new' : '/home/support/new')
function detailRoute(id: number) {
  return isAgent.value ? `/agent/support/${id}` : `/home/support/${id}`
}

const activeFilter = ref('')
const searchQuery = ref('')

const filters = computed(() => [
  { label: 'Tous', value: '', count: allTickets.value.length },
  { label: 'Ouverts', value: 'OPEN', count: countByStatus('OPEN') },
  { label: 'En cours', value: 'IN_PROGRESS', count: countByStatus('IN_PROGRESS') },
  { label: 'Résolus', value: 'RESOLVED', count: countByStatus('RESOLVED') },
  { label: 'Fermés', value: 'CLOSED', count: countByStatus('CLOSED') },
])

const stats = computed(() => [
  { key: 'open', label: 'Ouverts', count: countByStatus('OPEN') },
  { key: 'progress', label: 'En cours', count: countByStatus('IN_PROGRESS') },
  { key: 'resolved', label: 'Résolus', count: countByStatus('RESOLVED') },
])

const allTickets = computed(() => support.tickets ?? [])

function countByStatus(s: string) {
  return allTickets.value.filter(t => t.status === s).length
}

const filteredTickets = computed(() => {
  let list = allTickets.value
  if (activeFilter.value) list = list.filter(t => t.status === activeFilter.value)
  return list
})

const displayedTickets = computed(() => {
  if (!searchQuery.value.trim()) return filteredTickets.value
  const q = searchQuery.value.toLowerCase()
  return filteredTickets.value.filter(t =>
    t.subject.toLowerCase().includes(q)
    || String(t.id).includes(q)
    || (t.category_label || '').toLowerCase().includes(q)
  )
})

const emptyTitle = computed(() => {
  if (searchQuery.value) return 'Aucun résultat'
  if (activeFilter.value) return 'Aucun ticket dans cette catégorie'
  return 'Pas encore de ticket'
})

const emptyText = computed(() => {
  if (searchQuery.value) return `Aucun ticket ne correspond à « ${searchQuery.value} ».`
  if (activeFilter.value) return 'Essayez un autre filtre ou créez un nouveau ticket.'
  return 'Vous n\'avez pas encore contacté le support. N\'hésitez pas si vous avez besoin d\'aide !'
})

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'à l\'instant'
  if (mins < 60) return `il y a ${mins} min`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `il y a ${hours}h`
  const days = Math.floor(hours / 24)
  if (days < 7) return `il y a ${days}j`
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}

onMounted(() => support.fetchTickets())
</script>

<style scoped>
.sp {
  max-width: 860px;
  margin: 0 auto;
  padding: 28px 16px 40px;
}

/* ── Header ──────────────────────────────── */
.sp-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}
.sp-header__title {
  font-size: 24px;
  font-weight: 800;
  color: #111827;
  letter-spacing: -0.3px;
}
.sp-header__sub {
  margin-top: 4px;
  font-size: 14px;
  color: #6B7280;
  line-height: 1.5;
  max-width: 440px;
}
.sp-header__cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.1s;
  box-shadow: 0 1px 3px rgba(29,165,63,.25);
}
.sp-header__cta:hover { background: #178A33; }
.sp-header__cta:active { transform: scale(0.97); }

/* ── Stats ───────────────────────────────── */
.sp-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.sp-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 12px;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  transition: border-color 0.2s;
}
.sp-stat--open { border-left: 3px solid #16A34A; }
.sp-stat--progress { border-left: 3px solid #3B82F6; }
.sp-stat--resolved { border-left: 3px solid #F59E0B; }
.sp-stat__num {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
  line-height: 1;
}
.sp-stat__label {
  font-size: 12px;
  color: #6B7280;
  margin-top: 4px;
  font-weight: 500;
}

/* ── Toolbar ─────────────────────────────── */
.sp-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.sp-filters {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
}
.sp-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  color: #4B5563;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.sp-filter:hover { border-color: #1DA53F; color: #1DA53F; }
.sp-filter--active {
  background: #111827;
  color: #fff;
  border-color: #111827;
}
.sp-filter--active:hover { background: #1F2937; color: #fff; border-color: #1F2937; }
.sp-filter__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  background: #F3F4F6;
  color: #4B5563;
}
.sp-filter--active .sp-filter__badge {
  background: rgba(255,255,255,.2);
  color: #fff;
}
.sp-search {
  position: relative;
  min-width: 200px;
}
.sp-search__icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #9CA3AF;
  pointer-events: none;
}
.sp-search__input {
  width: 100%;
  padding: 8px 12px 8px 32px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 13px;
  color: #111827;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.sp-search__input::placeholder { color: #9CA3AF; }
.sp-search__input:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.1);
}

/* ── Skeleton ────────────────────────────── */
.sp-skeleton { display: flex; flex-direction: column; gap: 12px; }
.sp-skeleton__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 20px;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
}
.sp-skeleton__bar {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.sp-skeleton__bar--sm { width: 30%; }
.sp-skeleton__bar--lg { width: 80%; height: 14px; }
.sp-skeleton__bar--md { width: 50%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── Empty state ─────────────────────────── */
.sp-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 56px 24px;
  text-align: center;
}
.sp-empty__icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F8FAFC;
  border-radius: 50%;
  margin-bottom: 16px;
}
.sp-empty__title {
  font-size: 17px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 6px;
}
.sp-empty__text {
  font-size: 14px;
  color: #6B7280;
  max-width: 360px;
  line-height: 1.5;
  margin-bottom: 20px;
}
.sp-empty__cta {
  padding: 10px 24px;
  background: #1DA53F;
  color: #fff;
  border-radius: 10px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.2s;
}
.sp-empty__cta:hover { background: #178A33; }
.sp-empty__reset {
  padding: 8px 20px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  color: #4B5563;
  cursor: pointer;
  transition: all 0.15s;
}
.sp-empty__reset:hover { border-color: #111827; color: #111827; }

/* ── Ticket list ─────────────────────────── */
.sp-tickets { display: flex; flex-direction: column; gap: 10px; }

.sp-ticket {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.1s;
}
.sp-ticket:hover {
  border-color: #C3E6CB;
  box-shadow: 0 4px 12px rgba(29,165,63,.08);
  transform: translateY(-1px);
}
.sp-ticket:active { transform: translateY(0); }

.sp-ticket__priority {
  width: 4px;
  min-height: 42px;
  border-radius: 4px;
  flex-shrink: 0;
}
.sp-ticket__priority--low { background: #D1D5DB; }
.sp-ticket__priority--normal { background: #3B82F6; }
.sp-ticket__priority--high { background: #EF4444; }

.sp-ticket__body { flex: 1; min-width: 0; }

.sp-ticket__row1 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.sp-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 6px;
  letter-spacing: 0.3px;
  line-height: 1.5;
}
.sp-badge--open { background: #DCFCE7; color: #15803D; }
.sp-badge--in_progress { background: #DBEAFE; color: #1D4ED8; }
.sp-badge--resolved { background: #FEF3C7; color: #B45309; }
.sp-badge--closed { background: #F3F4F6; color: #6B7280; }

.sp-ticket__cat {
  font-size: 12px;
  color: #9CA3AF;
  font-weight: 500;
}

.sp-ticket__subject {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  line-height: 1.35;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sp-ticket__row3 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9CA3AF;
}
.sp-ticket__msgs {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.sp-ticket__sep { color: #D1D5DB; }
.sp-ticket__id { font-weight: 600; color: #6B7280; }

.sp-ticket__chevron {
  flex-shrink: 0;
  color: #D1D5DB;
  transition: color 0.15s, transform 0.15s;
}
.sp-ticket:hover .sp-ticket__chevron {
  color: #1DA53F;
  transform: translateX(2px);
}

/* ── Transitions ─────────────────────────── */
.ticket-enter-active,
.ticket-leave-active { transition: all 0.25s ease; }
.ticket-enter-from { opacity: 0; transform: translateY(10px); }
.ticket-leave-to { opacity: 0; transform: translateX(-10px); }
.ticket-move { transition: transform 0.3s ease; }

/* ── Responsive ──────────────────────────── */
@media (max-width: 640px) {
  .sp { padding: 20px 12px 32px; }
  .sp-header { flex-direction: column; gap: 12px; }
  .sp-header__cta { align-self: stretch; justify-content: center; }
  .sp-stats { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .sp-stat { padding: 10px 8px; }
  .sp-stat__num { font-size: 18px; }
  .sp-toolbar { flex-direction: column; align-items: stretch; }
  .sp-search { min-width: unset; }
  .sp-ticket__subject { white-space: normal; }
}
</style>
