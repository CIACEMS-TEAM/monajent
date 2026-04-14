<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import http from '@/services/http'
import posthog from 'posthog-js'

interface Visit {
  id: number
  listing_title: string
  listing_city: string
  agent_phone: string
  status: string
  slot_label: string | null
  scheduled_at: string | null
  verification_code: string | null
  client_note: string
  agent_note: string
  cancel_reason: string
  meeting_address: string
  meeting_map_url: string | null
  response_deadline: string | null
  created_at: string
}

const toast = useToast()
const visits = ref<Visit[]>([])
const loading = ref(true)
const filter = ref<'ALL' | 'REQUESTED' | 'CONFIRMED' | 'DONE' | 'CANCELED'>('ALL')

const showCancelModal = ref(false)
const cancelTarget = ref<number | null>(null)
const cancelReason = ref('')
const cancelLoading = ref(false)

onMounted(async () => {
  try {
    const { data } = await http.get<any>('/api/client/visits/')
    visits.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch {
    /* empty state */
  } finally {
    loading.value = false
  }
})

const filtered = computed(() => {
  if (filter.value === 'ALL') return visits.value
  return visits.value.filter((v) => v.status === filter.value)
})

const filterTabs = [
  { key: 'ALL', label: 'Toutes' },
  { key: 'REQUESTED', label: 'En attente' },
  { key: 'CONFIRMED', label: 'Confirmées' },
  { key: 'DONE', label: 'Terminées' },
  { key: 'CANCELED', label: 'Annulées' },
]

const cancelIsConfirmed = ref(false)

function openCancelModal(id: number) {
  cancelTarget.value = id
  cancelReason.value = ''
  const v = visits.value.find((v) => v.id === id)
  cancelIsConfirmed.value = v?.status === 'CONFIRMED'
  showCancelModal.value = true
}

async function handleCancel() {
  if (!cancelTarget.value || !cancelReason.value.trim()) {
    toast.error('Veuillez indiquer un motif')
    return
  }
  cancelLoading.value = true
  try {
    await http.post(`/api/client/visits/${cancelTarget.value}/cancel/`, {
      reason: cancelReason.value.trim(),
    })
    const v = visits.value.find((v) => v.id === cancelTarget.value)
    posthog.capture('visit_cancelled', {
      visit_id: cancelTarget.value,
      reason: cancelReason.value.trim(),
      previous_status: v?.status,
      listing_title: v?.listing_title,
    })
    if (v) {
      v.status = 'CANCELED'
      v.cancel_reason = cancelReason.value.trim()
    }
    toast.success('Visite annulée. Clé physique restaurée.')
    showCancelModal.value = false
    cancelTarget.value = null
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || "Erreur lors de l'annulation")
  } finally {
    cancelLoading.value = false
  }
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    REQUESTED: 'En attente',
    CONFIRMED: 'Confirmée',
    DONE: 'Terminée',
    CANCELED: 'Annulée',
    NO_SHOW: 'Absent',
    EXPIRED: 'Expirée',
  }
  return map[s] || s
}

function statusClass(s: string) {
  const map: Record<string, string> = {
    REQUESTED: 'st--pending',
    CONFIRMED: 'st--info',
    DONE: 'st--success',
    CANCELED: 'st--neutral',
    NO_SHOW: 'st--danger',
    EXPIRED: 'st--neutral',
  }
  return map[s] || 'st--neutral'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
}
</script>

<template>
  <div class="vis">
    <h1 class="vis__title">Mes visites</h1>

    <!-- Filtres -->
    <div class="vis__tabs">
      <button
        v-for="tab in filterTabs"
        :key="tab.key"
        class="vis__tab"
        :class="{ active: filter === tab.key }"
        @click="filter = tab.key as any"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="vis__loading"><div class="vis__spinner"></div></div>

    <div v-else-if="filtered.length === 0" class="vis__empty">
      <svg viewBox="0 0 24 24" width="48" height="48">
        <path
          fill="#E0E0E0"
          d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
        />
      </svg>
      <p>Aucune visite dans cette catégorie.</p>
      <router-link v-if="filter === 'ALL'" to="/home" class="vis__explore-btn"
        >Explorer les biens</router-link
      >
    </div>

    <div v-else class="vis__list">
      <div v-for="visit in filtered" :key="visit.id" class="vis__card">
        <div class="vis__card-top">
          <span class="vis__status" :class="statusClass(visit.status)">{{
            statusLabel(visit.status)
          }}</span>
          <span class="vis__date">{{ formatDate(visit.created_at) }}</span>
        </div>

        <h3 class="vis__listing">{{ visit.listing_title || `Annonce #${visit.id}` }}</h3>
        <p class="vis__meta">
          <svg viewBox="0 0 24 24" width="14" height="14">
            <path
              fill="#606060"
              d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"
            />
          </svg>
          {{ visit.listing_city }}
          <span v-if="visit.agent_phone"> · Agent : {{ visit.agent_phone }}</span>
        </p>

        <!-- Créneau / Date RDV -->
        <div v-if="visit.scheduled_at" class="vis__info-row">
          <svg viewBox="0 0 24 24" width="14" height="14">
            <path
              fill="#1DA53F"
              d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm0 16H5V8h14v11z"
            />
          </svg>
          <span
            >Rendez-vous : <strong>{{ formatDateTime(visit.scheduled_at) }}</strong></span
          >
        </div>
        <div v-else-if="visit.slot_label" class="vis__info-row">
          <svg viewBox="0 0 24 24" width="14" height="14">
            <path
              fill="#606060"
              d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"
            />
          </svg>
          <span>Créneau : {{ visit.slot_label }}</span>
        </div>

        <!-- Lieu de RDV -->
        <div v-if="visit.meeting_address || visit.meeting_map_url" class="vis__info-row">
          <svg viewBox="0 0 24 24" width="14" height="14">
            <path
              fill="#1DA53F"
              d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"
            />
          </svg>
          <span v-if="visit.meeting_address">{{ visit.meeting_address }}</span>
          <a
            v-if="visit.meeting_map_url"
            :href="visit.meeting_map_url"
            target="_blank"
            rel="noopener"
            class="vis__map-link"
            >Voir sur la carte</a
          >
        </div>

        <!-- Note de l'agent -->
        <p v-if="visit.agent_note" class="vis__note vis__note--agent">
          <strong>Note de l'agent :</strong> {{ visit.agent_note }}
        </p>

        <!-- Motif d'annulation -->
        <p
          v-if="visit.cancel_reason && visit.status === 'CANCELED'"
          class="vis__note vis__note--cancel"
        >
          <strong>Motif d'annulation :</strong> {{ visit.cancel_reason }}
        </p>

        <!-- Code de vérification -->
        <div
          v-if="visit.verification_code && ['CONFIRMED', 'REQUESTED'].includes(visit.status)"
          class="vis__code"
        >
          <div class="vis__code-label">Votre code de vérification</div>
          <div class="vis__code-value">{{ visit.verification_code }}</div>
          <p class="vis__code-hint">Communiquez ce code à l'agent au moment de la visite.</p>
        </div>

        <!-- Note du client -->
        <p v-if="visit.client_note && visit.status !== 'CANCELED'" class="vis__note">
          <strong>Votre note :</strong> {{ visit.client_note }}
        </p>

        <!-- Actions -->
        <div v-if="['REQUESTED', 'CONFIRMED'].includes(visit.status)" class="vis__actions">
          <button class="vis__cancel-btn" @click="openCancelModal(visit.id)">
            Annuler la visite
          </button>
        </div>
      </div>
    </div>

    <!-- Modal annulation -->
    <div v-if="showCancelModal" class="modal-overlay" @click.self="showCancelModal = false">
      <div class="modal">
        <h3 class="modal__title">Annuler la visite</h3>
        <p v-if="cancelIsConfirmed" class="modal__warning modal__warning--danger">
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path fill="#dc2626" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
          </svg>
          L'agent a déjà confirmé ce rendez-vous. Si vous annulez maintenant, votre
          <strong>clé physique ne sera pas restaurée</strong>.
        </p>
        <p v-else class="modal__warning">
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path fill="#d97706" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
          </svg>
          Votre clé physique sera restaurée, mais la clé virtuelle consommée ne sera pas remboursée.
        </p>
        <div class="modal__field">
          <label>Motif de l'annulation <span class="req">*</span></label>
          <select v-model="cancelReason" class="modal__select">
            <option value="">— Sélectionnez un motif —</option>
            <option value="Je ne suis plus intéressé par ce bien">
              Plus intéressé par ce bien
            </option>
            <option value="Je ne suis plus disponible à cette date">
              Plus disponible à cette date
            </option>
            <option value="J'ai trouvé un autre bien">J'ai trouvé un autre bien</option>
            <option value="L'agent ne répond pas à mes appels">Agent injoignable</option>
            <option value="Autre">Autre</option>
          </select>
        </div>
        <div v-if="cancelReason === 'Autre'" class="modal__field">
          <label>Précisez <span class="req">*</span></label>
          <textarea
            v-model="cancelReason"
            class="modal__textarea"
            rows="2"
            placeholder="Décrivez brièvement la raison..."
          ></textarea>
        </div>
        <div class="modal__actions">
          <button
            class="modal__btn modal__btn--ghost"
            @click="showCancelModal = false"
            :disabled="cancelLoading"
          >
            Retour
          </button>
          <button
            class="modal__btn modal__btn--danger"
            @click="handleCancel"
            :disabled="cancelLoading || !cancelReason.trim()"
          >
            {{ cancelLoading ? 'Annulation...' : "Confirmer l'annulation" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vis {
  max-width: 800px;
  margin: 0 auto;
}
.vis__title {
  font-size: 24px;
  font-weight: 700;
  color: #0f0f0f;
  margin-bottom: 16px;
}

.vis__tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 20px;
}
.vis__tab {
  padding: 10px 18px;
  border: none;
  background: none;
  font-size: 14px;
  color: #606060;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.vis__tab:hover {
  color: #0f0f0f;
}
.vis__tab.active {
  color: #0f0f0f;
  font-weight: 600;
  border-bottom-color: #1da53f;
}

.vis__loading {
  display: flex;
  justify-content: center;
  padding: 64px 0;
}
.vis__spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e0e0e0;
  border-top-color: #1da53f;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.vis__empty {
  text-align: center;
  padding: 48px 16px;
  color: #606060;
}
.vis__empty p {
  margin: 12px 0;
  font-size: 14px;
}
.vis__explore-btn {
  display: inline-block;
  padding: 10px 24px;
  background: #1da53f;
  color: #fff;
  border-radius: 20px;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  margin-top: 8px;
}

.vis__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.vis__card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
}
.vis__card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.vis__status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.st--pending {
  background: #fef3c7;
  color: #d97706;
}
.st--info {
  background: #dbeafe;
  color: #2563eb;
}
.st--success {
  background: rgba(29, 165, 63, 0.1);
  color: #1da53f;
}
.st--danger {
  background: #fef2f2;
  color: #dc2626;
}
.st--neutral {
  background: #f2f2f2;
  color: #606060;
}
.vis__date {
  font-size: 12px;
  color: #909090;
}
.vis__listing {
  font-size: 16px;
  font-weight: 600;
  color: #0f0f0f;
  margin-bottom: 4px;
}
.vis__meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606060;
  margin-bottom: 8px;
}

.vis__info-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #272727;
  margin-bottom: 4px;
}
.vis__map-link {
  color: #1da53f;
  text-decoration: none;
  font-weight: 500;
  font-size: 13px;
}
.vis__map-link:hover {
  text-decoration: underline;
}

.vis__note {
  font-size: 13px;
  color: #606060;
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8f8f8;
  border-radius: 8px;
}
.vis__note--agent {
  background: #eff6ff;
  color: #1e40af;
}
.vis__note--cancel {
  background: #fef2f2;
  color: #991b1b;
}

.vis__code {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 14px 18px;
  margin: 10px 0;
  text-align: center;
}
.vis__code-label {
  font-size: 12px;
  color: #606060;
  margin-bottom: 4px;
}
.vis__code-value {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 6px;
  color: #1da53f;
  font-family: monospace;
}
.vis__code-hint {
  font-size: 11px;
  color: #888;
  margin-top: 6px;
}

.vis__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.vis__cancel-btn {
  padding: 8px 18px;
  border: 1px solid #dc2626;
  background: transparent;
  color: #dc2626;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.vis__cancel-btn:hover {
  background: rgba(220, 38, 38, 0.06);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal {
  background: #fff;
  border-radius: 16px;
  padding: 28px 32px;
  max-width: 440px;
  width: 90%;
}
.modal__title {
  font-size: 20px;
  font-weight: 700;
  color: #0f0f0f;
  margin-bottom: 12px;
}
.modal__warning {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 16px;
  line-height: 1.4;
}
.modal__warning svg {
  flex-shrink: 0;
  margin-top: 1px;
}
.modal__warning--danger {
  color: #991b1b;
  background: #fef2f2;
  border-color: #fecaca;
}
.modal__field {
  margin-bottom: 16px;
}
.modal__field label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #272727;
  margin-bottom: 6px;
}
.req {
  color: #dc2626;
}
.modal__select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  color: #0f0f0f;
  background: #fff;
}
.modal__select:focus {
  outline: none;
  border-color: #1da53f;
}
.modal__textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  color: #0f0f0f;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
}
.modal__textarea:focus {
  outline: none;
  border-color: #1da53f;
}
.modal__actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 8px;
}
.modal__btn {
  padding: 10px 22px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}
.modal__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.modal__btn--ghost {
  background: #f2f2f2;
  color: #272727;
}
.modal__btn--ghost:hover:not(:disabled) {
  background: #e5e5e5;
}
.modal__btn--danger {
  background: #dc2626;
  color: #fff;
}
.modal__btn--danger:hover:not(:disabled) {
  background: #b91c1c;
}
</style>
