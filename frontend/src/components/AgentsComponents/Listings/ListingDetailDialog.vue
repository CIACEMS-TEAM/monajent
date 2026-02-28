<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAgentStore, type Listing } from '@/Stores/agent'
import { useToast } from 'vue-toastification'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import Button from 'primevue/button'

const props = defineProps<{
  visible: boolean
  listingId: number | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'edit', id: number): void
}>()

const agent = useAgentStore()
const toast = useToast()
const loading = ref(false)
const listing = ref<Listing | null>(null)

const origin = typeof window !== 'undefined' ? window.location.origin : ''

function shareUrl(): string {
  if (!listing.value) return ''
  return `${origin}/home/annonce/${listing.value.id}`
}

async function copyShareLink() {
  try {
    await navigator.clipboard.writeText(shareUrl())
    toast.success('Lien copié !')
  } catch (_) {
    toast.error('Impossible de copier le lien')
  }
}

function shareWhatsApp() {
  if (!listing.value) return
  const price = Number(listing.value.price).toLocaleString('fr-FR') + ' F CFA'
  const text = `${listing.value.title}\n${price} — ${listing.value.city}\n\n${shareUrl()}`
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank')
}

function shareFacebook() {
  window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl())}`, '_blank')
}

watch(() => props.visible, async (open) => {
  if (!open || !props.listingId) { listing.value = null; return }
  loading.value = true
  try {
    listing.value = await agent.fetchListing(props.listingId)
  } catch (_) {
    listing.value = null
  }
  loading.value = false
})

function close() { emit('update:visible', false) }

function openEdit() {
  if (props.listingId) {
    close()
    emit('edit', props.listingId)
  }
}

function mediaUrl(url: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http')) return url
  const base = (import.meta as any).env?.VITE_API_BASE_URL || origin
  return `${base}${url}`
}

function formatPrice(val: string | number): string {
  return Number(val).toLocaleString('fr-FR') + ' F CFA'
}

function statusSeverity(s: string) {
  const m: Record<string, "success" | "warn" | "danger" | "secondary"> = {
    ACTIF: 'success', INACTIF: 'secondary', EXPIRED: 'danger', SUSPENDED: 'warn',
  }
  return m[s]
}
function statusLabel(s: string) {
  const m: Record<string, string> = { ACTIF: 'Active', INACTIF: 'Inactive', EXPIRED: 'Expirée', SUSPENDED: 'Suspendue' }
  return m[s] || s
}
function typeLabel(t: string) {
  return t === 'LOCATION' ? 'Location' : 'Vente'
}
function furnishLabel(f: string) {
  const m: Record<string, string> = { FURNISHED: 'Meublé', UNFURNISHED: 'Non meublé', SEMI_FURNISHED: 'Semi-meublé' }
  return m[f] || '—'
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    @update:visible="(v: boolean) => emit('update:visible', v)"
    header="Détails de l'annonce"
    :modal="true"
    :closable="true"
    :draggable="false"
    :maximizable="true"
    :pt="{
      root: { class: 'ld-dialog-root' },
      content: { class: 'ld-dialog-content' },
    }"
  >
    <div v-if="loading" class="ld__loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem"></i>
      Chargement...
    </div>

    <div v-else-if="listing" class="ld">
      <!-- Header -->
      <div class="ld__head">
        <div class="ld__head-info">
          <h2 class="ld__title">{{ listing.title }}</h2>
          <div class="ld__head-tags">
            <Tag :value="typeLabel(listing.listing_type)" :severity="listing.listing_type === 'LOCATION' ? 'info' : 'warn'" />
            <Tag :value="statusLabel(listing.status)" :severity="statusSeverity(listing.status)" />
          </div>
        </div>
        <span class="ld__price">{{ formatPrice(listing.price) }}</span>
      </div>

      <!-- Photos -->
      <section v-if="listing.images.length" class="ld__section">
        <h3 class="ld__section-title">Photos</h3>
        <div class="ld__gallery">
          <div v-for="img in listing.images" :key="img.id" class="ld__gallery-item">
            <img :src="mediaUrl(img.image)!" alt="" />
          </div>
        </div>
      </section>

      <!-- Vidéos -->
      <section v-if="listing.videos.length" class="ld__section">
        <h3 class="ld__section-title">Vidéos</h3>
        <div class="ld__videos">
          <div v-for="vid in listing.videos" :key="vid.id" class="ld__video-card">
            <div class="ld__video-player">
              <video
                v-if="vid.stream_url || vid.file"
                :src="vid.stream_url || mediaUrl(vid.file)!"
                controls
                preload="metadata"
                :poster="vid.thumbnail ? mediaUrl(vid.thumbnail)! : undefined"
              ></video>
              <div v-else-if="vid.thumbnail" class="ld__video-poster">
                <img :src="mediaUrl(vid.thumbnail)!" alt="" />
              </div>
              <div v-else class="ld__video-empty">
                <i class="pi pi-video" style="font-size: 32px; color: #aaa"></i>
              </div>
            </div>
            <div class="ld__video-meta">
              <span>{{ vid.views_count }} vues</span>
              <span v-if="vid.duration_sec">{{ Math.floor(vid.duration_sec / 60) }}:{{ String(vid.duration_sec % 60).padStart(2, '0') }}</span>
              <span>{{ new Date(vid.created_at).toLocaleDateString('fr-FR') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Infos détaillées -->
      <div class="ld__details">
        <section class="ld__section">
          <h3 class="ld__section-title">Localisation</h3>
          <div class="ld__fields">
            <div class="ld__field">
              <span class="ld__label">Ville</span>
              <span class="ld__value">{{ listing.city }}</span>
            </div>
            <div class="ld__field" v-if="listing.neighborhood">
              <span class="ld__label">Quartier</span>
              <span class="ld__value">{{ listing.neighborhood }}</span>
            </div>
            <div class="ld__field" v-if="listing.address">
              <span class="ld__label">Adresse</span>
              <span class="ld__value">{{ listing.address }}</span>
            </div>
            <div class="ld__field" v-if="listing.latitude && listing.longitude">
              <span class="ld__label">Position GPS</span>
              <span class="ld__value">
                <a
                  :href="`https://www.google.com/maps?q=${listing.latitude},${listing.longitude}`"
                  target="_blank"
                  rel="noopener"
                  class="ld__map-link"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"/></svg>
                  Voir sur la carte
                </a>
              </span>
            </div>
          </div>
        </section>

        <section class="ld__section">
          <h3 class="ld__section-title">Caractéristiques</h3>
          <div class="ld__fields">
            <div class="ld__field" v-if="listing.rooms">
              <span class="ld__label">Pièces</span>
              <span class="ld__value">{{ listing.rooms }}</span>
            </div>
            <div class="ld__field" v-if="listing.bedrooms">
              <span class="ld__label">Chambres</span>
              <span class="ld__value">{{ listing.bedrooms }}</span>
            </div>
            <div class="ld__field" v-if="listing.bathrooms">
              <span class="ld__label">Salles de bain</span>
              <span class="ld__value">{{ listing.bathrooms }}</span>
            </div>
            <div class="ld__field" v-if="listing.surface_m2">
              <span class="ld__label">Surface</span>
              <span class="ld__value">{{ listing.surface_m2 }} m²</span>
            </div>
            <div class="ld__field" v-if="listing.furnishing">
              <span class="ld__label">Ameublement</span>
              <span class="ld__value">{{ furnishLabel(listing.furnishing) }}</span>
            </div>
          </div>
        </section>
      </div>

      <!-- Description -->
      <section v-if="listing.description" class="ld__section">
        <h3 class="ld__section-title">Description</h3>
        <p class="ld__description">{{ listing.description }}</p>
      </section>

      <!-- Commodités -->
      <section v-if="listing.amenities.length" class="ld__section">
        <h3 class="ld__section-title">Commodités</h3>
        <div class="ld__amenities">
          <Tag v-for="(a, i) in listing.amenities" :key="i" :value="a" severity="info" rounded />
        </div>
      </section>

      <!-- Conditions d'acquisition / location -->
      <section v-if="listing.deposit_months || listing.advance_months || listing.agency_fee_months || listing.other_conditions" class="ld__section">
        <h3 class="ld__section-title">
          {{ listing.listing_type === 'LOCATION' ? 'Conditions de location' : 'Conditions de vente' }}
        </h3>
        <div class="ld__conditions">
          <div v-if="listing.deposit_months" class="ld__condition-item">
            <i class="pi pi-shield"></i>
            <span><strong>{{ listing.deposit_months }}</strong> mois de caution</span>
            <span class="ld__condition-amount">{{ formatPrice(Number(listing.price) * listing.deposit_months) }}</span>
          </div>
          <div v-if="listing.advance_months" class="ld__condition-item">
            <i class="pi pi-calendar"></i>
            <span><strong>{{ listing.advance_months }}</strong> mois d'avance</span>
            <span class="ld__condition-amount">{{ formatPrice(Number(listing.price) * listing.advance_months) }}</span>
          </div>
          <div v-if="listing.agency_fee_months" class="ld__condition-item">
            <i class="pi pi-briefcase"></i>
            <span><strong>{{ listing.agency_fee_months }}</strong> mois de frais d'agence</span>
            <span class="ld__condition-amount">{{ formatPrice(Number(listing.price) * listing.agency_fee_months) }}</span>
          </div>
          <div v-if="listing.deposit_months || listing.advance_months || listing.agency_fee_months" class="ld__condition-total">
            <strong>Total à l'entrée :</strong>
            <strong>{{ formatPrice(Number(listing.price) * ((listing.deposit_months || 0) + (listing.advance_months || 0) + (listing.agency_fee_months || 0))) }}</strong>
          </div>
          <p v-if="listing.other_conditions" class="ld__condition-other">{{ listing.other_conditions }}</p>
        </div>
      </section>

      <!-- Dates & Expiration -->
      <section class="ld__section">
        <h3 class="ld__section-title">Dates & Validité</h3>
        <div class="ld__dates-grid">
          <div class="ld__date-card">
            <i class="pi pi-calendar-plus"></i>
            <div class="ld__date-info">
              <span class="ld__date-label">Créée le</span>
              <span class="ld__date-value">{{ new Date(listing.created_at).toLocaleDateString('fr-FR') }}</span>
            </div>
          </div>
          <div class="ld__date-card" v-if="listing.published_at">
            <i class="pi pi-check-circle" style="color: #1DA53F"></i>
            <div class="ld__date-info">
              <span class="ld__date-label">Publiée le</span>
              <span class="ld__date-value">{{ new Date(listing.published_at).toLocaleDateString('fr-FR') }}</span>
            </div>
          </div>
          <div class="ld__date-card" :class="{ 'ld__date-card--warn': listing.days_remaining <= 2 && listing.days_remaining > 0, 'ld__date-card--danger': listing.days_remaining <= 0 }" v-if="listing.expires_at">
            <i class="pi pi-clock" :style="{ color: listing.days_remaining <= 0 ? '#e53935' : listing.days_remaining <= 2 ? '#f57c00' : '#606060' }"></i>
            <div class="ld__date-info">
              <span class="ld__date-label">Expiration</span>
              <span class="ld__date-value">
                {{ new Date(listing.expires_at).toLocaleDateString('fr-FR') }}
                <Tag
                  :value="listing.days_remaining <= 0 ? 'Expirée' : listing.days_remaining === 1 ? '1 jour restant' : listing.days_remaining + ' jours restants'"
                  :severity="listing.days_remaining <= 0 ? 'danger' : listing.days_remaining <= 2 ? 'warn' : 'success'"
                  style="margin-left: 8px"
                />
              </span>
            </div>
          </div>
          <div class="ld__date-card" v-if="listing.updated_at !== listing.created_at">
            <i class="pi pi-pencil" style="color: #999"></i>
            <div class="ld__date-info">
              <span class="ld__date-label">Dernière modification</span>
              <span class="ld__date-value">{{ new Date(listing.updated_at).toLocaleDateString('fr-FR') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Stats -->
      <div class="ld__stats">
        <div class="ld__stat">
          <i class="pi pi-eye"></i>
          <span>{{ listing.views_count }} vues</span>
        </div>
        <div class="ld__stat">
          <i class="pi pi-heart"></i>
          <span>{{ listing.favorites_count }} favoris</span>
        </div>
        <div class="ld__stat" :class="{ 'ld__stat--alert': listing.reports_count > 0 }">
          <i class="pi pi-flag"></i>
          <span>{{ listing.reports_count }} signalement{{ listing.reports_count !== 1 ? 's' : '' }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="ld__footer">
        <Button label="Fermer" severity="secondary" text @click="close" />
        <div class="ld__footer-right">
          <Button icon="pi pi-whatsapp" severity="success" text rounded title="WhatsApp" @click="shareWhatsApp" />
          <Button icon="pi pi-facebook" severity="info" text rounded title="Facebook" @click="shareFacebook" />
          <Button icon="pi pi-link" severity="secondary" text rounded title="Copier le lien" @click="copyShareLink" />
          <Button label="Modifier" icon="pi pi-pencil" class="ld__edit-btn" @click="openEdit" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<style>
.ld-dialog-root {
  width: 90vw !important;
  max-width: 900px !important;
  max-height: 92vh;
}
.ld-dialog-content {
  overflow-y: auto;
  padding: 0 24px 24px !important;
}
@media (max-width: 768px) {
  .ld-dialog-root {
    width: 98vw !important;
    max-height: 96vh;
  }
}
</style>

<style scoped>
.ld__loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: #606060;
  justify-content: center;
}

.ld__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}
.ld__head-info {
  flex: 1;
  min-width: 0;
}
.ld__title {
  font-size: 22px;
  font-weight: 700;
  color: #0F0F0F;
  margin: 0 0 8px;
}
.ld__head-tags {
  display: flex;
  gap: 8px;
}
.ld__price {
  font-size: 22px;
  font-weight: 700;
  color: #1DA53F;
  white-space: nowrap;
}

/* Sections */
.ld__section {
  margin-bottom: 20px;
}
.ld__section-title {
  font-size: 14px;
  font-weight: 600;
  color: #272727;
  margin: 0 0 12px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Gallery */
.ld__gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}
.ld__gallery-item {
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16/10;
  background: #f2f2f2;
}
.ld__gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Videos */
.ld__videos {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}
.ld__video-card {
  border-radius: 10px;
  overflow: hidden;
  background: #0F0F0F;
}
.ld__video-player {
  width: 100%;
  aspect-ratio: 16/9;
}
.ld__video-player video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}
.ld__video-poster img,
.ld__video-empty {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ld__video-meta {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  font-size: 12px;
  color: #aaa;
  background: #1a1a1a;
}

/* Details grid */
.ld__details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 4px;
}
.ld__details .ld__section {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 0;
}
.ld__fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.ld__field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ld__label {
  font-size: 12px;
  color: #999;
  font-weight: 500;
}
.ld__value {
  font-size: 14px;
  color: #0F0F0F;
  font-weight: 500;
}
.ld__map-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #1DA53F;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
}
.ld__map-link:hover { text-decoration: underline; }

/* Description */
.ld__description {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  margin: 0;
}

/* Amenities */
.ld__amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Conditions */
.ld__conditions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ld__condition-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #272727;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 8px;
}
.ld__condition-item i {
  color: #1DA53F;
  font-size: 16px;
  flex-shrink: 0;
}
.ld__condition-amount {
  margin-left: auto;
  font-weight: 600;
  color: #0F0F0F;
  white-space: nowrap;
}
.ld__condition-total {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  background: #e8f5e9;
  border-radius: 8px;
  font-size: 14px;
  color: #1DA53F;
}
.ld__condition-other {
  font-size: 13px;
  color: #606060;
  margin: 4px 0 0;
  font-style: italic;
}

/* Dates grid */
.ld__dates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}
.ld__date-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
}
.ld__date-card--warn {
  border-color: #ffe0b2;
  background: #fff8e1;
}
.ld__date-card--danger {
  border-color: #ffcdd2;
  background: #fce4ec;
}
.ld__date-card > i {
  font-size: 18px;
  margin-top: 2px;
  color: #606060;
}
.ld__date-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ld__date-label {
  font-size: 11px;
  color: #999;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.ld__date-value {
  font-size: 14px;
  color: #0F0F0F;
  font-weight: 500;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

/* Stats */
.ld__stats {
  display: flex;
  gap: 24px;
  padding: 14px 0;
  border-top: 1px solid #eee;
  margin-top: 8px;
}
.ld__stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606060;
}
.ld__stat--alert {
  color: #e53935;
  font-weight: 600;
}

/* Footer */
.ld__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.ld__footer-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.ld__edit-btn {
  background: #1DA53F !important;
  border-color: #1DA53F !important;
}
.ld__edit-btn:hover {
  background: #178A33 !important;
  border-color: #178A33 !important;
}

@media (max-width: 768px) {
  .ld__head { flex-direction: column; }
  .ld__details { grid-template-columns: 1fr; }
  .ld__gallery { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
  .ld__videos { grid-template-columns: 1fr; }
  .ld__stats { flex-wrap: wrap; gap: 12px; }
}
</style>
