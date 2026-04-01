<template>
  <div class="support-list">
    <div class="support-list__header">
      <h1 class="support-list__title">Aide & Support</h1>
      <router-link :to="createRoute" class="support-list__new-btn">
        <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        Nouveau ticket
      </router-link>
    </div>

    <div class="support-list__filters">
      <button
        v-for="f in filters"
        :key="f.value"
        class="support-list__filter"
        :class="{ active: activeFilter === f.value }"
        @click="setFilter(f.value)"
      >{{ f.label }}</button>
    </div>

    <div v-if="support.ticketsLoading" class="support-list__loading">Chargement...</div>
    <div v-else-if="filteredTickets.length === 0" class="support-list__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#ccc" d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
      <p>Aucun ticket pour le moment</p>
      <router-link :to="createRoute" class="support-list__empty-btn">Créer un ticket</router-link>
    </div>

    <div v-else class="support-list__items">
      <router-link
        v-for="ticket in filteredTickets"
        :key="ticket.id"
        :to="detailRoute(ticket.id)"
        class="support-list__card"
      >
        <div class="support-list__card-top">
          <span class="support-list__badge" :class="'badge--' + ticket.status.toLowerCase()">
            {{ ticket.status_label }}
          </span>
          <span class="support-list__cat">{{ ticket.category_label }}</span>
        </div>
        <div class="support-list__subject">{{ ticket.subject }}</div>
        <div class="support-list__meta">
          <span>#{{ ticket.id }}</span>
          <span>{{ ticket.messages_count }} message{{ ticket.messages_count > 1 ? 's' : '' }}</span>
          <span>{{ formatDate(ticket.updated_at) }}</span>
        </div>
      </router-link>
    </div>
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

const filters = [
  { label: 'Tous', value: '' },
  { label: 'Ouverts', value: 'OPEN' },
  { label: 'En cours', value: 'IN_PROGRESS' },
  { label: 'Résolus', value: 'RESOLVED' },
  { label: 'Fermés', value: 'CLOSED' },
]
const activeFilter = ref('')

const filteredTickets = computed(() => {
  if (!activeFilter.value) return support.tickets
  return support.tickets.filter(t => t.status === activeFilter.value)
})

function setFilter(value: string) {
  activeFilter.value = value
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

onMounted(() => support.fetchTickets())
</script>

<style scoped>
.support-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 0;
}

.support-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.support-list__title {
  font-size: 22px;
  font-weight: 700;
  color: #0f0f0f;
}

.support-list__new-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
}
.support-list__new-btn:hover { background: #178A33; }

.support-list__filters {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.support-list__filter {
  padding: 6px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  background: #fff;
  font-size: 13px;
  color: #606060;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.support-list__filter:hover { border-color: #1DA53F; color: #1DA53F; }
.support-list__filter.active {
  background: #0f0f0f;
  color: #fff;
  border-color: #0f0f0f;
}

.support-list__loading {
  text-align: center;
  padding: 40px;
  color: #888;
}

.support-list__empty {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}
.support-list__empty p { margin: 12px 0 20px; font-size: 15px; }
.support-list__empty-btn {
  display: inline-block;
  padding: 10px 24px;
  background: #1DA53F;
  color: #fff;
  border-radius: 20px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.support-list__items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.support-list__card {
  display: block;
  padding: 16px 20px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  text-decoration: none;
  color: #0f0f0f;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.support-list__card:hover {
  border-color: #1DA53F;
  box-shadow: 0 2px 8px rgba(29,165,63,.1);
}

.support-list__card-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.support-list__badge {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 10px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}
.badge--open { background: #dcfce7; color: #16a34a; }
.badge--in_progress { background: #dbeafe; color: #2563eb; }
.badge--resolved { background: #fef3c7; color: #d97706; }
.badge--closed { background: #f3f4f6; color: #6b7280; }

.support-list__cat {
  font-size: 12px;
  color: #888;
}

.support-list__subject {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.3;
}

.support-list__meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #888;
}
</style>
