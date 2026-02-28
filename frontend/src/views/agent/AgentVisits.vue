<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import { useAgentStore, type AvailabilitySlot, type DateSlot } from '@/Stores/agent'
import MapPicker from '@/components/MapPicker.vue'

const agent = useAgentStore()
const toast = useToast()

const filter = ref<'ALL' | 'REQUESTED' | 'CONFIRMED' | 'DONE' | 'NO_SHOW' | 'CANCELED'>('ALL')
const noShowLoading = ref<number | null>(null)
const showNoShowModal = ref(false)
const noShowTarget = ref<number | null>(null)
const noShowReason = ref('')
const activeTab = ref<'visits' | 'availability' | 'agenda'>('visits')

const validateCodeId = ref<number | null>(null)
const codeInput = ref('')
const codeLoading = ref(false)
const confirmLoading = ref<number | null>(null)
const showConfirmModal = ref(false)
const confirmTarget = ref<number | null>(null)
const confirmForm = ref({
  scheduled_at: '',
  agent_note: '',
  meeting_address: '',
  meeting_latitude: null as number | null,
  meeting_longitude: null as number | null,
})

const showSlotForm = ref(false)
const slotForm = ref({ day_of_week: 0, start_time: '09:00', end_time: '12:00' })
const slotLoading = ref(false)

const showDateSlotForm = ref(false)
const dateSlotForm = ref({ date: '', start_time: '09:00', end_time: '12:00', note: '' })
const dateSlotLoading = ref(false)

onMounted(async () => {
  try { await Promise.all([agent.fetchVisits(), agent.fetchAvailability(), agent.fetchDateSlots()]) }
  catch (_) { /* handled by store */ }
})

const filtered = computed(() => {
  if (filter.value === 'ALL') return agent.visits
  return agent.visits.filter(v => v.status === filter.value)
})

function statusLabel(s: string) {
  const map: Record<string, string> = {
    REQUESTED: 'En attente',
    CONFIRMED: 'Confirmée',
    DONE: 'Terminée',
    NO_SHOW: 'Absent',
    CANCELED: 'Annulée',
    EXPIRED: 'Expirée',
  }
  return map[s] || s
}

function statusClass(s: string) { return s.toLowerCase() }

const filterTabs = [
  { key: 'ALL', label: 'Toutes' },
  { key: 'REQUESTED', label: 'En attente' },
  { key: 'CONFIRMED', label: 'Confirmées' },
  { key: 'DONE', label: 'Terminées' },
  { key: 'NO_SHOW', label: 'Absents' },
  { key: 'CANCELED', label: 'Annulées' },
]

function openConfirmModal(id: number) {
  confirmTarget.value = id
  confirmForm.value = { scheduled_at: '', agent_note: '', meeting_address: '', meeting_latitude: null, meeting_longitude: null }
  showConfirmModal.value = true
}

async function handleConfirm() {
  if (!confirmTarget.value) return
  confirmLoading.value = confirmTarget.value
  try {
    const payload: any = {}
    if (confirmForm.value.scheduled_at) payload.scheduled_at = confirmForm.value.scheduled_at
    if (confirmForm.value.agent_note) payload.agent_note = confirmForm.value.agent_note
    if (confirmForm.value.meeting_address) payload.meeting_address = confirmForm.value.meeting_address
    if (confirmForm.value.meeting_latitude != null) payload.meeting_latitude = confirmForm.value.meeting_latitude
    if (confirmForm.value.meeting_longitude != null) payload.meeting_longitude = confirmForm.value.meeting_longitude
    await agent.confirmVisit(confirmTarget.value, payload)
    toast.success('Visite confirmée')
    showConfirmModal.value = false
    confirmTarget.value = null
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Erreur lors de la confirmation')
  } finally {
    confirmLoading.value = null
  }
}

async function handleValidateCode() {
  if (!validateCodeId.value || codeInput.value.length !== 5) return
  codeLoading.value = true
  try {
    await agent.validateVisitCode(validateCodeId.value, codeInput.value)
    toast.success('Code validé ! Visite effectuée.')
    validateCodeId.value = null
    codeInput.value = ''
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Code incorrect')
  } finally {
    codeLoading.value = false
  }
}

function noShowAvailableIn(v: { scheduled_at: string | null }): string | null {
  if (!v.scheduled_at) return 'Fixez d\'abord une date de RDV'
  const threshold = new Date(new Date(v.scheduled_at).getTime() + 15 * 60_000)
  if (new Date() < threshold) {
    const diff = Math.ceil((threshold.getTime() - Date.now()) / 60_000)
    const h = Math.floor(diff / 60)
    const m = diff % 60
    const temps = h > 0 ? `${h}h${m > 0 ? m.toString().padStart(2, '0') : ''}` : `${m} min`
    return `Absent dans ${temps}`
  }
  return null
}

function openNoShowModal(id: number) {
  noShowTarget.value = id
  noShowReason.value = ''
  showNoShowModal.value = true
}

async function handleNoShow() {
  if (!noShowTarget.value) return
  if (!noShowReason.value.trim()) {
    toast.error('Veuillez indiquer un motif')
    return
  }
  noShowLoading.value = noShowTarget.value
  try {
    await agent.markNoShow(noShowTarget.value, noShowReason.value.trim())
    toast.success('Client marqué comme absent')
    showNoShowModal.value = false
    noShowTarget.value = null
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Erreur')
  } finally {
    noShowLoading.value = null
  }
}

async function handleCreateSlot() {
  slotLoading.value = true
  try {
    await agent.createAvailability({
      day_of_week: slotForm.value.day_of_week,
      start_time: slotForm.value.start_time,
      end_time: slotForm.value.end_time,
    })
    toast.success('Créneau ajouté')
    showSlotForm.value = false
    slotForm.value = { day_of_week: 0, start_time: '09:00', end_time: '12:00' }
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || e?.response?.data?.non_field_errors?.[0] || 'Erreur')
  } finally {
    slotLoading.value = false
  }
}

async function toggleSlot(slot: AvailabilitySlot) {
  try {
    await agent.updateAvailability(slot.id, { is_active: !slot.is_active })
  } catch (e: any) {
    toast.error('Erreur de mise à jour')
  }
}

async function deleteSlot(id: number) {
  try {
    await agent.deleteAvailability(id)
    toast.success('Créneau supprimé')
  } catch (e: any) {
    toast.error('Erreur de suppression')
  }
}

async function handleCreateDateSlot() {
  if (!dateSlotForm.value.date) { toast.error('Date requise'); return }
  dateSlotLoading.value = true
  try {
    await agent.createDateSlot({
      date: dateSlotForm.value.date,
      start_time: dateSlotForm.value.start_time,
      end_time: dateSlotForm.value.end_time,
      note: dateSlotForm.value.note,
    })
    toast.success('Créneau ajouté')
    showDateSlotForm.value = false
    dateSlotForm.value = { date: '', start_time: '09:00', end_time: '12:00', note: '' }
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || e?.response?.data?.non_field_errors?.[0] || 'Erreur')
  } finally {
    dateSlotLoading.value = false
  }
}

async function toggleDateSlot(slot: DateSlot) {
  try {
    await agent.updateDateSlot(slot.id, { is_active: !slot.is_active })
  } catch (_) {
    toast.error('Erreur de mise à jour')
  }
}

async function deleteDateSlot(id: number) {
  try {
    await agent.deleteDateSlot(id)
    toast.success('Créneau supprimé')
  } catch (_) {
    toast.error('Erreur de suppression')
  }
}

const dayOptions = [
  { value: 0, label: 'Lundi' },
  { value: 1, label: 'Mardi' },
  { value: 2, label: 'Mercredi' },
  { value: 3, label: 'Jeudi' },
  { value: 4, label: 'Vendredi' },
  { value: 5, label: 'Samedi' },
  { value: 6, label: 'Dimanche' },
]
</script>

<template>
  <div class="vis">
    <h1 class="vis__title">Visites</h1>

    <!-- Section tabs -->
    <div class="vis__main-tabs">
      <button class="vis__main-tab" :class="{ active: activeTab === 'visits' }" @click="activeTab = 'visits'">
        Demandes de visite
        <span v-if="agent.pendingVisits > 0" class="vis__main-tab-badge">{{ agent.pendingVisits }}</span>
      </button>
      <button class="vis__main-tab" :class="{ active: activeTab === 'availability' }" @click="activeTab = 'availability'">
        Créneaux récurrents
      </button>
      <button class="vis__main-tab" :class="{ active: activeTab === 'agenda' }" @click="activeTab = 'agenda'">
        Agenda (dates)
      </button>
    </div>

    <!-- ═══ Tab Visites ═══ -->
    <template v-if="activeTab === 'visits'">
      <div class="vis__tabs">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          class="vis__tab"
          :class="{ active: filter === tab.key }"
          @click="filter = tab.key as any"
        >{{ tab.label }}</button>
      </div>

      <div v-if="agent.visitsLoading" class="vis__empty"><p>Chargement...</p></div>

      <div v-else class="vis__list">
        <div v-for="v in filtered" :key="v.id" class="vis__card">
          <div class="vis__card-top">
            <div class="vis__card-info">
              <h3 class="vis__card-listing">{{ v.listing_title }}</h3>
              <div class="vis__card-client">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#606060" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                <span class="vis__card-phone">{{ v.client_phone }}</span>
              </div>
              <div v-if="v.scheduled_at" class="vis__card-datetime">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#606060" d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm0 16H5V8h14v11z"/></svg>
                <span>{{ new Date(v.scheduled_at).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }) }}</span>
              </div>
              <div v-if="v.slot_label" class="vis__card-slot">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#606060" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
                <span>{{ v.slot_label }}</span>
              </div>
              <p v-if="v.client_note" class="vis__card-note">« {{ v.client_note }} »</p>
              <p v-if="v.agent_note" class="vis__card-note vis__card-note--agent">Note : {{ v.agent_note }}</p>
              <p v-if="v.cancel_reason && v.status === 'CANCELED'" class="vis__card-note vis__card-note--cancel">Motif d'annulation : {{ v.cancel_reason }}</p>
              <div v-if="v.meeting_address || v.meeting_map_url" class="vis__card-meeting">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#1DA53F" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"/></svg>
                <span v-if="v.meeting_address">{{ v.meeting_address }}</span>
                <a v-if="v.meeting_map_url" :href="v.meeting_map_url" target="_blank" rel="noopener" class="vis__map-link">Voir sur la carte</a>
              </div>
            </div>
            <div class="vis__card-right">
              <span class="vis__badge" :class="statusClass(v.status)">{{ statusLabel(v.status) }}</span>
              <span v-if="v.is_deadline_passed && v.status === 'REQUESTED'" class="vis__deadline">Délai dépassé</span>
            </div>
          </div>

          <!-- Validate code input (for confirmed visits) -->
          <div v-if="validateCodeId === v.id" class="vis__code-form">
            <label>Code du client (5 caractères) :</label>
            <div class="vis__code-row">
              <input
                v-model="codeInput"
                maxlength="5"
                placeholder="XXXXX"
                class="vis__code-input"
                @keyup.enter="handleValidateCode"
              />
              <button class="vis__btn vis__btn--complete" @click="handleValidateCode" :disabled="codeLoading || codeInput.length !== 5">
                {{ codeLoading ? '...' : 'Valider' }}
              </button>
              <button class="vis__btn vis__btn--cancel" @click="validateCodeId = null; codeInput = ''">Annuler</button>
            </div>
          </div>

          <!-- Actions -->
          <div v-if="(v.status === 'REQUESTED' || v.status === 'CONFIRMED') && validateCodeId !== v.id" class="vis__actions">
            <button
              v-if="v.status === 'REQUESTED'"
              class="vis__btn vis__btn--confirm"
              @click="openConfirmModal(v.id)"
            >Confirmer</button>
            <button
              v-if="v.status === 'CONFIRMED'"
              class="vis__btn vis__btn--complete"
              @click="validateCodeId = v.id"
            >Valider le code</button>
            <button
              v-if="v.status === 'CONFIRMED'"
              class="vis__btn vis__btn--noshow"
              :disabled="!!noShowAvailableIn(v)"
              :title="noShowAvailableIn(v) || 'Signaler l\'absence du client'"
              @click="openNoShowModal(v.id)"
            >
              <svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm4.2 14.2L11 13V7h1.5v5.2l4.5 2.7-.8 1.3z"/></svg>
              {{ noShowAvailableIn(v) || 'Client absent' }}
            </button>
          </div>
        </div>

        <div v-if="filtered.length === 0 && !agent.visitsLoading" class="vis__empty">
          <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
          <p>Aucune visite dans cette catégorie</p>
        </div>
      </div>
    </template>

    <!-- ═══ Tab Disponibilités ═══ -->
    <template v-if="activeTab === 'availability'">
      <div class="avail">
        <div class="avail__header">
          <p class="avail__desc">Définissez vos créneaux de disponibilité pour que les clients puissent demander des visites physiques.</p>
          <button class="avail__add-btn" @click="showSlotForm = true">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            Ajouter un créneau
          </button>
        </div>

        <div v-if="agent.availabilitySlotsLoading" class="vis__empty"><p>Chargement...</p></div>

        <div v-else-if="agent.availabilitySlots.length === 0" class="vis__empty">
          <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
          <p>Aucun créneau de disponibilité configuré</p>
        </div>

        <div v-else class="avail__list">
          <div v-for="slot in agent.availabilitySlots" :key="slot.id" class="avail__slot" :class="{ inactive: !slot.is_active }">
            <div class="avail__slot-info">
              <span class="avail__slot-day">{{ slot.day_label }}</span>
              <span class="avail__slot-time">{{ slot.start_time.slice(0,5) }} — {{ slot.end_time.slice(0,5) }}</span>
            </div>
            <div class="avail__slot-actions">
              <button class="avail__toggle" :class="{ on: slot.is_active }" @click="toggleSlot(slot)" :title="slot.is_active ? 'Désactiver' : 'Activer'">
                <span class="avail__toggle-track"><span class="avail__toggle-thumb"></span></span>
              </button>
              <button class="avail__delete" @click="deleteSlot(slot.id)" title="Supprimer">
                <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Add slot modal -->
        <div v-if="showSlotForm" class="wlt__modal-overlay" @click.self="showSlotForm = false">
          <div class="wlt__modal">
            <h3 class="wlt__modal-title">Ajouter un créneau</h3>
            <div class="wlt__modal-field">
              <label>Jour</label>
              <select v-model="slotForm.day_of_week" class="avail__select">
                <option v-for="d in dayOptions" :key="d.value" :value="d.value">{{ d.label }}</option>
              </select>
            </div>
            <div class="avail__time-row">
              <div class="wlt__modal-field">
                <label>Début</label>
                <input v-model="slotForm.start_time" type="time" class="avail__time-input" />
              </div>
              <div class="wlt__modal-field">
                <label>Fin</label>
                <input v-model="slotForm.end_time" type="time" class="avail__time-input" />
              </div>
            </div>
            <div class="wlt__modal-actions">
              <button class="wlt__modal-btn cancel" @click="showSlotForm = false" :disabled="slotLoading">Annuler</button>
              <button class="wlt__modal-btn confirm" @click="handleCreateSlot" :disabled="slotLoading">
                {{ slotLoading ? 'Ajout...' : 'Ajouter' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══ Tab Agenda (dates spécifiques) ═══ -->
    <template v-if="activeTab === 'agenda'">
      <div class="avail">
        <div class="avail__header">
          <p class="avail__desc">Indiquez des dates spécifiques où vous serez disponible pour des visites (agenda ponctuel).</p>
          <button class="avail__add-btn" @click="showDateSlotForm = true">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            Ajouter une date
          </button>
        </div>

        <div v-if="agent.dateSlotsLoading" class="vis__empty"><p>Chargement...</p></div>

        <div v-else-if="agent.dateSlots.length === 0" class="vis__empty">
          <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
          <p>Aucune date spécifique configurée</p>
        </div>

        <div v-else class="avail__list">
          <div v-for="slot in agent.dateSlots" :key="slot.id" class="avail__slot" :class="{ inactive: !slot.is_active }">
            <div class="avail__slot-info">
              <span class="avail__slot-day">{{ new Date(slot.date + 'T00:00:00').toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}</span>
              <span class="avail__slot-time">{{ slot.start_time.slice(0,5) }} — {{ slot.end_time.slice(0,5) }}</span>
              <span v-if="slot.note" class="avail__slot-note">{{ slot.note }}</span>
            </div>
            <div class="avail__slot-actions">
              <button class="avail__toggle" :class="{ on: slot.is_active }" @click="toggleDateSlot(slot)" :title="slot.is_active ? 'Désactiver' : 'Activer'">
                <span class="avail__toggle-track"><span class="avail__toggle-thumb"></span></span>
              </button>
              <button class="avail__delete" @click="deleteDateSlot(slot.id)" title="Supprimer">
                <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Add date slot modal -->
        <div v-if="showDateSlotForm" class="wlt__modal-overlay" @click.self="showDateSlotForm = false">
          <div class="wlt__modal">
            <h3 class="wlt__modal-title">Ajouter une date de disponibilité</h3>
            <div class="wlt__modal-field">
              <label>Date</label>
              <input v-model="dateSlotForm.date" type="date" class="avail__date-input" :min="new Date().toISOString().split('T')[0]" />
            </div>
            <div class="avail__time-row">
              <div class="wlt__modal-field">
                <label>Début</label>
                <input v-model="dateSlotForm.start_time" type="time" class="avail__time-input" />
              </div>
              <div class="wlt__modal-field">
                <label>Fin</label>
                <input v-model="dateSlotForm.end_time" type="time" class="avail__time-input" />
              </div>
            </div>
            <div class="wlt__modal-field">
              <label>Note (optionnel)</label>
              <input v-model="dateSlotForm.note" type="text" class="avail__date-input" placeholder="Ex: Disponible uniquement à Cocody" />
            </div>
            <div class="wlt__modal-actions">
              <button class="wlt__modal-btn cancel" @click="showDateSlotForm = false" :disabled="dateSlotLoading">Annuler</button>
              <button class="wlt__modal-btn confirm" @click="handleCreateDateSlot" :disabled="dateSlotLoading">
                {{ dateSlotLoading ? 'Ajout...' : 'Ajouter' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══ Modal Confirmation enrichie ═══ -->
    <div v-if="showConfirmModal" class="wlt__modal-overlay" @click.self="showConfirmModal = false">
      <div class="wlt__modal wlt__modal--lg">
        <h3 class="wlt__modal-title">Confirmer la visite</h3>
        <p class="confirm__subtitle">Planifiez le rendez-vous et indiquez le lieu de rencontre au client.</p>

        <div class="wlt__modal-field">
          <label>Date et heure du rendez-vous</label>
          <input
            v-model="confirmForm.scheduled_at"
            type="datetime-local"
            class="avail__date-input"
            :min="new Date().toISOString().slice(0, 16)"
          />
        </div>

        <div class="wlt__modal-field">
          <label>Lieu de rendez-vous</label>
          <input
            v-model="confirmForm.meeting_address"
            type="text"
            class="avail__date-input"
            placeholder="Ex: Devant la pharmacie du quartier, Carrefour Palmeraie..."
          />
        </div>

        <div class="confirm__coords-section">
          <label class="confirm__coords-label">Position du rendez-vous sur la carte</label>
          <MapPicker
            :latitude="confirmForm.meeting_latitude"
            :longitude="confirmForm.meeting_longitude"
            @update="(c) => { confirmForm.meeting_latitude = c.latitude; confirmForm.meeting_longitude = c.longitude }"
          />
          <div v-if="confirmForm.meeting_latitude && confirmForm.meeting_longitude" class="confirm__coords-info">
            <span class="confirm__coords-text">{{ confirmForm.meeting_latitude }}, {{ confirmForm.meeting_longitude }}</span>
            <a
              :href="`https://www.google.com/maps?q=${confirmForm.meeting_latitude},${confirmForm.meeting_longitude}`"
              target="_blank"
              rel="noopener"
              class="confirm__preview-link"
            >Google Maps</a>
          </div>
        </div>

        <div class="wlt__modal-field">
          <label>Note pour le client (optionnel)</label>
          <textarea
            v-model="confirmForm.agent_note"
            class="confirm__textarea"
            rows="3"
            placeholder="Ex: Apportez une pièce d'identité, prévoyez 30 min..."
          ></textarea>
        </div>

        <div class="wlt__modal-actions">
          <button class="wlt__modal-btn cancel" @click="showConfirmModal = false" :disabled="confirmLoading !== null">Annuler</button>
          <button class="wlt__modal-btn confirm" @click="handleConfirm" :disabled="confirmLoading !== null">
            {{ confirmLoading !== null ? 'Confirmation...' : 'Confirmer la visite' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ Modal NO_SHOW (motif obligatoire) ═══ -->
    <div v-if="showNoShowModal" class="wlt__modal-overlay" @click.self="showNoShowModal = false">
      <div class="wlt__modal">
        <h3 class="wlt__modal-title">Signaler l'absence du client</h3>
        <p class="noshow__info">
          <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#d97706" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
          Cette action est irréversible. Le client sera notifié et sa clé physique ne sera pas restaurée.
        </p>
        <div class="wlt__modal-field">
          <label>Motif de l'absence <span style="color: #dc2626">*</span></label>
          <select v-model="noShowReason" class="avail__select">
            <option value="">— Sélectionnez un motif —</option>
            <option value="Le client ne s'est pas présenté au rendez-vous">Le client ne s'est pas présenté</option>
            <option value="Le client est injoignable par téléphone">Client injoignable par téléphone</option>
            <option value="Le client a annulé de vive voix sans passer par l'application">Annulation verbale du client</option>
            <option value="Autre">Autre</option>
          </select>
        </div>
        <div v-if="noShowReason === 'Autre'" class="wlt__modal-field">
          <label>Précisez le motif <span style="color: #dc2626">*</span></label>
          <textarea
            v-model="noShowReason"
            class="confirm__textarea"
            rows="2"
            placeholder="Décrivez brièvement la situation..."
          ></textarea>
        </div>
        <div class="wlt__modal-actions">
          <button class="wlt__modal-btn cancel" @click="showNoShowModal = false" :disabled="noShowLoading !== null">Annuler</button>
          <button class="wlt__modal-btn noshow" @click="handleNoShow" :disabled="noShowLoading !== null || !noShowReason.trim()">
            {{ noShowLoading !== null ? '...' : 'Confirmer l\'absence' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vis { max-width: 900px; }
.vis__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 20px; }

.vis__main-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #E0E0E0;
  margin-bottom: 20px;
}
.vis__main-tab {
  padding: 12px 24px;
  border: none;
  background: none;
  font-size: 15px;
  font-weight: 500;
  color: #606060;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.vis__main-tab:hover { color: #0F0F0F; }
.vis__main-tab.active { color: #0F0F0F; font-weight: 600; border-bottom-color: #1DA53F; }
.vis__main-tab-badge {
  background: #dc2626;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
}

.vis__tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #E0E0E0;
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
.vis__tab:hover { color: #0F0F0F; }
.vis__tab.active { color: #0F0F0F; font-weight: 600; border-bottom-color: #0F0F0F; }

.vis__list { display: flex; flex-direction: column; gap: 12px; }

.vis__card {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
}

.vis__card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.vis__card-listing {
  font-size: 16px;
  font-weight: 600;
  color: #0F0F0F;
  margin-bottom: 8px;
}

.vis__card-client,
.vis__card-datetime,
.vis__card-slot {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #272727;
  margin-bottom: 4px;
}
.vis__card-phone { color: #606060; }
.vis__card-note {
  font-size: 13px;
  color: #606060;
  font-style: italic;
  margin-top: 6px;
}

.vis__card-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.vis__deadline {
  font-size: 11px;
  color: #dc2626;
  font-weight: 600;
  background: #fef2f2;
  padding: 2px 8px;
  border-radius: 8px;
}

.vis__badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  flex-shrink: 0;
}
.vis__badge.requested { background: #fef3c7; color: #d97706; }
.vis__badge.confirmed { background: #dbeafe; color: #2563eb; }
.vis__badge.done { background: rgba(29,165,63,.1); color: #1DA53F; }
.vis__badge.no_show { background: #fef2f2; color: #dc2626; }
.vis__badge.canceled { background: #f2f2f2; color: #606060; }
.vis__badge.expired { background: #f2f2f2; color: #606060; }

.vis__code-form {
  margin-top: 12px;
  padding: 14px 16px;
  background: #f8f8f8;
  border-radius: 8px;
}
.vis__code-form label { font-size: 13px; color: #606060; display: block; margin-bottom: 8px; }
.vis__code-row { display: flex; gap: 8px; align-items: center; }
.vis__code-input {
  padding: 8px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 4px;
  font-family: monospace;
  width: 120px;
  text-align: center;
}
.vis__code-input:focus { outline: none; border-color: #1DA53F; }

.vis__actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}
.vis__btn {
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: background .15s;
}
.vis__btn:disabled { opacity: 0.6; cursor: not-allowed; }
.vis__btn--confirm { background: #1DA53F; color: #fff; }
.vis__btn--confirm:hover:not(:disabled) { background: #178A33; }
.vis__btn--complete { background: #2563eb; color: #fff; }
.vis__btn--complete:hover:not(:disabled) { background: #1d4ed8; }
.vis__btn--cancel { background: #f2f2f2; color: #606060; }
.vis__btn--cancel:hover:not(:disabled) { background: #e5e5e5; }
.vis__btn--noshow { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.vis__btn--noshow:hover:not(:disabled) { background: #fee2e2; }

.vis__empty {
  text-align: center;
  padding: 48px 16px;
  color: #606060;
}
.vis__empty p { margin-top: 12px; font-size: 14px; }

/* ═══ Availability ═══ */
.avail__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}
.avail__desc { font-size: 14px; color: #606060; flex: 1; }
.avail__add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
}
.avail__add-btn:hover { background: #178A33; }

.avail__list { display: flex; flex-direction: column; gap: 8px; }
.avail__slot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 10px;
}
.avail__slot.inactive { opacity: 0.5; }
.avail__slot-day { font-weight: 600; color: #0F0F0F; font-size: 15px; display: block; }
.avail__slot-time { font-size: 14px; color: #606060; }
.avail__slot-actions { display: flex; align-items: center; gap: 12px; }

.avail__toggle { background: none; border: none; cursor: pointer; padding: 4px; }
.avail__toggle-track {
  display: block;
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: #ccc;
  position: relative;
  transition: background .2s;
}
.avail__toggle.on .avail__toggle-track { background: #1DA53F; }
.avail__toggle-thumb {
  display: block;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform .2s;
}
.avail__toggle.on .avail__toggle-thumb { transform: translateX(18px); }

.avail__delete {
  background: none;
  border: none;
  cursor: pointer;
  color: #dc2626;
  padding: 4px;
  opacity: 0.6;
  transition: opacity .15s;
}
.avail__delete:hover { opacity: 1; }

.avail__select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F0F0F;
  background: #fff;
}
.avail__select:focus { outline: none; border-color: #1DA53F; }

.avail__time-row { display: flex; gap: 16px; }
.avail__time-row .wlt__modal-field { flex: 1; }
.avail__time-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F0F0F;
  box-sizing: border-box;
}
.avail__time-input:focus { outline: none; border-color: #1DA53F; }

.avail__date-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F0F0F;
  box-sizing: border-box;
}
.avail__date-input:focus { outline: none; border-color: #1DA53F; }

.avail__slot-note {
  display: block;
  font-size: 12px;
  color: #888;
  font-style: italic;
  margin-top: 2px;
}

/* Modal reuse from wallet */
.wlt__modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.wlt__modal {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  max-width: 440px;
  width: 90%;
}
.wlt__modal-title { font-size: 20px; font-weight: 700; color: #0F0F0F; margin-bottom: 16px; }
.wlt__modal-field { margin-bottom: 18px; }
.wlt__modal-field label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #272727;
  margin-bottom: 8px;
}
.wlt__modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 8px; }
.wlt__modal-btn {
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}
.wlt__modal-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.wlt__modal-btn.cancel { background: #f2f2f2; color: #272727; }
.wlt__modal-btn.cancel:hover:not(:disabled) { background: #e5e5e5; }
.wlt__modal-btn.confirm { background: #1DA53F; color: #fff; }
.wlt__modal-btn.confirm:hover:not(:disabled) { background: #178A33; }

/* ═══ Confirm modal enrichi ═══ */
.wlt__modal--lg { max-width: 560px; max-height: 90vh; overflow-y: auto; }
.confirm__subtitle {
  font-size: 13px;
  color: #606060;
  margin-bottom: 18px;
}
.confirm__coords-section {
  margin-bottom: 18px;
}
.confirm__coords-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #272727;
  margin-bottom: 8px;
}
.confirm__coords-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  padding: 6px 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}
.confirm__coords-text {
  font-size: 13px;
  color: #272727;
  font-family: monospace;
  flex: 1;
}
.confirm__preview-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #1DA53F;
  text-decoration: none;
  font-weight: 500;
  flex-shrink: 0;
}
.confirm__preview-link:hover { text-decoration: underline; }
.confirm__textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px;
  color: #0F0F0F;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
}
.confirm__textarea:focus { outline: none; border-color: #1DA53F; }

/* NO_SHOW modal */
.noshow__info {
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
.noshow__info svg { flex-shrink: 0; margin-top: 1px; }
.wlt__modal-btn.noshow {
  background: #dc2626;
  color: #fff;
}
.wlt__modal-btn.noshow:hover:not(:disabled) { background: #b91c1c; }
.wlt__modal-btn.noshow:disabled { opacity: 0.5; }

/* Meeting point display in visit card */
.vis__card-meeting {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #272727;
  margin-top: 6px;
}
.vis__map-link {
  color: #1DA53F;
  text-decoration: none;
  font-weight: 500;
  font-size: 13px;
}
.vis__map-link:hover { text-decoration: underline; }
.vis__card-note--agent {
  color: #272727;
  font-style: normal;
  font-weight: 500;
}
.vis__card-note--cancel {
  color: #991b1b;
  font-style: normal;
  background: #fef2f2;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .avail__header { flex-direction: column; align-items: flex-start; }
  .avail__time-row { flex-direction: column; gap: 0; }
  .confirm__coords-row { flex-direction: column; gap: 0; }
}
</style>
