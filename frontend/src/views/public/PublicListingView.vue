<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePublicStore, type PublicListingVideo, type ListingListItem } from '@/Stores/public'
import { useAuthStore } from '@/Stores/auth'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { useToast } from 'vue-toastification'
import { API_BASE } from '@/services/http'

const route = useRoute()
const router = useRouter()
const pub = usePublicStore()
const auth = useAuthStore()
const toast = useToast()

const listingId = computed(() => Number(route.params.id))
const highlightVideoKey = computed(() => (route.query.video as string) || null)
const isClient = computed(() => auth.me?.role === 'CLIENT')

const watchLoading = ref(false)
const activeVideo = ref<PublicListingVideo | null>(null)
const showPaywall = ref(false)
const showNoPack = ref(false)
const heroIdx = ref(0)
const descExpanded = ref(false)
const otherListings = ref<ListingListItem[]>([])
const activeChip = ref('all')

const chips = [
  { label: 'Tous', value: 'all' },
  { label: 'Location', value: 'LOCATION' },
  { label: 'Vente', value: 'VENTE' },
  { label: 'Abidjan', value: 'Abidjan' },
  { label: 'Cocody', value: 'Cocody' },
  { label: 'Plateau', value: 'Plateau' },
  { label: 'Marcory', value: 'Marcory' },
  { label: 'Yopougon', value: 'Yopougon' },
]

function mediaUrl(url: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http')) return url
  return `${API_BASE}${url}`
}

function formatPrice(val: string | number): string {
  return Number(val).toLocaleString('fr-FR') + ' F CFA'
}

function furnishLabel(f: string): string {
  const m: Record<string, string> = { FURNISHED: 'Meublé', UNFURNISHED: 'Non meublé', SEMI_FURNISHED: 'Semi-meublé' }
  return m[f] || ''
}

function durationStr(sec: number | null): string {
  if (!sec) return ''
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`
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

function heroPrev() {
  if (!pub.listing) return
  heroIdx.value = (heroIdx.value - 1 + pub.listing.images.length) % pub.listing.images.length
}
function heroNext() {
  if (!pub.listing) return
  heroIdx.value = (heroIdx.value + 1) % pub.listing.images.length
}

const descriptionTruncated = computed(() => {
  if (!pub.listing?.description) return ''
  return pub.listing.description.length > 200
    ? pub.listing.description.slice(0, 200) + '...'
    : pub.listing.description
})
const needsTruncation = computed(() => (pub.listing?.description?.length ?? 0) > 200)
const showToggle = computed(() => needsTruncation.value || (pub.listing?.amenities?.length ?? 0) > 0 || pub.listing?.address)

function goToListing(id: number) {
  heroIdx.value = 0
  descExpanded.value = false
  router.push({ name: 'public-listing', params: { id } })
}

function coverUrl(item: ListingListItem): string | null {
  if (!item.cover_image) return null
  return item.cover_image.startsWith('http') ? item.cover_image : `${API_BASE}${item.cover_image}`
}

function agentInitial(agent: { agency_name: string; username: string; phone: string }): string {
  return (agent.agency_name || agent.username || agent.phone).charAt(0).toUpperCase()
}

const agentColors = ['#e85d04', '#2d6a4f', '#0077b6', '#7b2cbf', '#d62828', '#457b9d', '#606c38', '#9d4edd']

async function loadOtherListings() {
  try {
    const params: Record<string, string> = {}
    if (activeChip.value === 'LOCATION' || activeChip.value === 'VENTE') params.listing_type = activeChip.value
    else if (activeChip.value !== 'all') params.city = activeChip.value
    await pub.fetchListings(params)
    otherListings.value = pub.listings.filter(l => l.id !== listingId.value).slice(0, 20)
  } catch (_) {}
}

function selectChip(value: string) {
  activeChip.value = value
  loadOtherListings()
}

async function loadListing() {
  heroIdx.value = 0
  descExpanded.value = false
  try {
    await pub.fetchPublicListing(listingId.value)
  } catch (e: any) {
    if (e?.response?.status === 404) toast.error('Annonce introuvable ou expirée')
  }
  if (highlightVideoKey.value && pub.listing) {
    await nextTick()
    const el = document.getElementById(`video-${highlightVideoKey.value}`)
    if (el) setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300)
  }
}

onMounted(() => {
  loadListing()
  loadOtherListings()
})

watch(listingId, () => {
  loadListing()
  loadOtherListings()
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

async function handleWatch(vid: PublicListingVideo) {
  if (pub.getUnlockedUrl(vid.access_key)) { activeVideo.value = vid; return }
  activeVideo.value = vid
  showPaywall.value = true
}

async function confirmWatch() {
  if (!activeVideo.value) return
  watchLoading.value = true
  try {
    const result = await pub.watchVideo(activeVideo.value.access_key)
    showPaywall.value = false
    toast[result.already_watched ? 'info' : 'success'](
      result.already_watched ? 'Vidéo déjà vue — aucune clé consommée' : `Vidéo débloquée ! ${result.pack_remaining} clés restantes`
    )
  } catch (e: any) {
    if (e?.response?.status === 402) { showPaywall.value = false; showNoPack.value = true }
    else toast.error(e?.response?.data?.detail || 'Erreur lors du visionnage')
  } finally { watchLoading.value = false }
}

async function refreshVideoToken(vid: PublicListingVideo) {
  try {
    const result = await pub.watchVideo(vid.access_key)
    toast.info('Lien vidéo renouvelé')
    return result.video_url
  } catch {
    toast.error('Impossible de recharger la vidéo. Veuillez réessayer.')
    return null
  }
}

function onVideoError(event: Event, vid: PublicListingVideo) {
  const videoEl = event.target as HTMLVideoElement
  if (!videoEl) return
  const code = videoEl.error?.code
  if (code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED || code === MediaError.MEDIA_ERR_NETWORK) {
    pub.unlockedVideos[vid.access_key] = ''
    toast.warning('Le lien vidéo a expiré. Cliquez pour le recharger.')
  }
}

function preventContextMenu(e: Event) { e.preventDefault() }

function goBuyPack() { showNoPack.value = false; router.push({ name: 'client-packs' }) }

function shareUrl(): string { return window.location.origin + `/home/annonce/${listingId.value}` }
function shareText(): string {
  if (!pub.listing) return shareUrl()
  return `${pub.listing.title}\n${formatPrice(pub.listing.price)} — ${pub.listing.city}\n\n${shareUrl()}`
}
async function copyLink() {
  try { await navigator.clipboard.writeText(shareUrl()); toast.success('Lien copié !') }
  catch (_) { toast.error('Impossible de copier') }
}
function shareWhatsApp() { window.open(`https://wa.me/?text=${encodeURIComponent(shareText())}`, '_blank') }
function shareFacebook() { window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl())}`, '_blank') }
</script>

<template>
  <div class="yw">
    <!-- Loading -->
    <div v-if="pub.listingLoading" class="yw-state">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem; color: #1DA53F"></i>
      <span>Chargement...</span>
    </div>

    <!-- Not found -->
    <div v-else-if="!pub.listing" class="yw-state">
      <i class="pi pi-exclamation-triangle" style="font-size: 3rem; color: #e53935"></i>
      <h2>Annonce introuvable</h2>
      <p>Cette annonce a été supprimée ou a expiré.</p>
      <Button label="Retour" icon="pi pi-arrow-left" @click="router.push({ name: 'home' })" />
    </div>

    <!-- ===== CONTENT ===== -->
    <div v-else class="yw-grid">
      <!-- ===== LEFT: LISTING DETAIL ===== -->
      <div class="yw-left">
        <!-- Player -->
        <div class="yw-player">
          <div v-if="pub.listing.images.length" class="yw-player__frame">
            <img :src="mediaUrl(pub.listing.images[heroIdx].image)!" :alt="pub.listing.title" class="yw-player__img" />
            <template v-if="pub.listing.images.length > 1">
              <button class="yw-player__nav yw-player__nav--prev" @click.stop="heroPrev"><i class="pi pi-chevron-left"></i></button>
              <button class="yw-player__nav yw-player__nav--next" @click.stop="heroNext"><i class="pi pi-chevron-right"></i></button>
              <span class="yw-player__counter">{{ heroIdx + 1 }} / {{ pub.listing.images.length }}</span>
            </template>
          </div>
          <div v-else class="yw-player__empty"><i class="pi pi-image" style="font-size:36px;color:#ccc"></i><span>Aucune photo</span></div>
        </div>

        <!-- Thumbstrip -->
        <div v-if="pub.listing.images.length > 1" class="yw-thumbs">
          <div
            v-for="(img, i) in pub.listing.images"
            :key="img.id"
            class="yw-thumbs__item"
            :class="{ 'yw-thumbs__item--on': heroIdx === i }"
            @click="heroIdx = i"
          ><img :src="mediaUrl(img.image)!" alt="" /></div>
        </div>

        <!-- Title -->
        <h1 class="yw-title">{{ pub.listing.title }}</h1>

        <!-- Meta -->
        <div class="yw-meta">
          <span class="yw-meta__info">
            {{ pub.listing.views_count }} vue{{ pub.listing.views_count !== 1 ? 's' : '' }}
            &middot; {{ pub.listing.city }}<template v-if="pub.listing.neighborhood">, {{ pub.listing.neighborhood }}</template>
            <a
              v-if="pub.listing.latitude && pub.listing.longitude"
              :href="`https://www.google.com/maps?q=${pub.listing.latitude},${pub.listing.longitude}`"
              target="_blank"
              rel="noopener"
              class="yw-map-link"
              title="Voir sur la carte"
            ><i class="pi pi-map-marker"></i> Carte</a>
          </span>
          <div class="yw-meta__price">
            <span class="yw-price">{{ formatPrice(pub.listing.price) }}</span>
            <span v-if="pub.listing.listing_type === 'LOCATION'" class="yw-price-per">/mois</span>
            <span class="yw-badge" :class="pub.listing.listing_type === 'LOCATION' ? 'yw-badge--loc' : 'yw-badge--sale'">
              {{ pub.listing.listing_type === 'LOCATION' ? 'Location' : 'Vente' }}
            </span>
          </div>
        </div>

        <!-- Conditions d'acquisition -->
        <div v-if="pub.listing.deposit_months || pub.listing.advance_months || pub.listing.agency_fee_months" class="yw-conditions">
          <div class="yw-conditions__row" v-if="pub.listing.deposit_months">
            <span class="yw-conditions__label">Caution</span>
            <span class="yw-conditions__val">{{ pub.listing.deposit_months }} mois &middot; {{ formatPrice(Number(pub.listing.price) * pub.listing.deposit_months) }}</span>
          </div>
          <div class="yw-conditions__row" v-if="pub.listing.advance_months">
            <span class="yw-conditions__label">Avance</span>
            <span class="yw-conditions__val">{{ pub.listing.advance_months }} mois &middot; {{ formatPrice(Number(pub.listing.price) * pub.listing.advance_months) }}</span>
          </div>
          <div class="yw-conditions__row" v-if="pub.listing.agency_fee_months">
            <span class="yw-conditions__label">Frais d'agence</span>
            <span class="yw-conditions__val">{{ pub.listing.agency_fee_months }} mois &middot; {{ formatPrice(Number(pub.listing.price) * pub.listing.agency_fee_months) }}</span>
          </div>
          <div class="yw-conditions__total">
            <span>Total à l'entrée</span>
            <strong>{{ formatPrice(Number(pub.listing.price) * ((pub.listing.deposit_months || 0) + (pub.listing.advance_months || 0) + (pub.listing.agency_fee_months || 0))) }}</strong>
          </div>
        </div>
        <p v-if="pub.listing.other_conditions" class="yw-conditions__other">{{ pub.listing.other_conditions }}</p>

        <!-- Actions -->
        <div class="yw-actions">
          <button class="yw-act" @click="shareWhatsApp"><i class="pi pi-whatsapp"></i><span>WhatsApp</span></button>
          <button class="yw-act" @click="shareFacebook"><i class="pi pi-facebook"></i><span>Facebook</span></button>
          <button class="yw-act" @click="copyLink"><i class="pi pi-share-alt"></i><span>Partager</span></button>
          <button class="yw-act" @click="copyLink"><i class="pi pi-link"></i><span>Copier</span></button>
        </div>

        <!-- Agent -->
        <div class="yw-agent">
          <div class="yw-agent__avatar-wrap">
            <div class="yw-agent__avatar">
              <img v-if="pub.listing.agent.profile_photo" :src="mediaUrl(pub.listing.agent.profile_photo)!" alt="" />
              <i v-else class="pi pi-user"></i>
            </div>
            <svg v-if="pub.listing.agent.verified" class="yw-agent__avatar-badge" viewBox="0 0 24 24" width="18" height="18"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
          </div>
          <div class="yw-agent__info">
            <span class="yw-agent__name">
              {{ pub.listing.agent.agency_name || pub.listing.agent.username || pub.listing.agent.phone }}
              <svg v-if="pub.listing.agent.verified" class="yw-agent__name-badge" viewBox="0 0 24 24" width="15" height="15"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
            </span>
            <span class="yw-agent__role">Agent immobilier</span>
          </div>
        </div>

        <!-- Description -->
        <div class="yw-desc" @click="descExpanded = !descExpanded">
          <div class="yw-desc__chips" v-if="pub.listing.rooms || pub.listing.surface_m2 || pub.listing.bedrooms || pub.listing.bathrooms || pub.listing.furnishing">
            <span v-if="pub.listing.surface_m2" class="yw-chip">{{ pub.listing.surface_m2 }} m²</span>
            <span v-if="pub.listing.rooms" class="yw-chip">{{ pub.listing.rooms }} pièce{{ pub.listing.rooms > 1 ? 's' : '' }}</span>
            <span v-if="pub.listing.bedrooms" class="yw-chip">{{ pub.listing.bedrooms }} ch.</span>
            <span v-if="pub.listing.bathrooms" class="yw-chip">{{ pub.listing.bathrooms }} SDB</span>
            <span v-if="pub.listing.furnishing" class="yw-chip">{{ furnishLabel(pub.listing.furnishing) }}</span>
          </div>
          <template v-if="pub.listing.description">
            <p class="yw-desc__text">{{ descExpanded ? pub.listing.description : descriptionTruncated }}</p>
          </template>
          <template v-if="descExpanded && pub.listing.amenities.length">
            <div class="yw-desc__sub">Commodités</div>
            <div class="yw-desc__tags"><span v-for="(a, i) in pub.listing.amenities" :key="i" class="yw-desc__tag"><i class="pi pi-check"></i> {{ a }}</span></div>
          </template>
          <template v-if="descExpanded && pub.listing.address">
            <div class="yw-desc__sub">Adresse</div>
            <p class="yw-desc__text" style="margin:0">{{ pub.listing.address }}</p>
          </template>
          <button v-if="showToggle" class="yw-desc__more" @click.stop="descExpanded = !descExpanded">{{ descExpanded ? 'Afficher moins' : 'Afficher plus' }}</button>
        </div>

        <!-- Videos PPV -->
        <section v-if="pub.listing.videos.length" class="yw-vids">
          <div class="yw-vids__head">
            <h2 class="yw-vids__title"><i class="pi pi-video"></i> {{ pub.listing.videos.length }} vidéo{{ pub.listing.videos.length > 1 ? 's' : '' }}</h2>
            <span class="yw-ppv">Pay-Per-View</span>
          </div>
          <p class="yw-vids__hint"><i class="pi pi-info-circle"></i> 1 clé par visionnage. Déjà débloquée = gratuite.</p>
          <div class="yw-vids__grid">
            <div v-for="vid in pub.listing.videos" :key="vid.id" :id="`video-${vid.access_key}`" class="yw-vcard" :class="{ 'yw-vcard--hl': highlightVideoKey === vid.access_key }">
              <!-- Vidéo débloquée — player sécurisé -->
              <div v-if="pub.getUnlockedUrl(vid.access_key)" class="yw-vcard__player" @contextmenu="preventContextMenu">
                <video
                  :src="pub.getUnlockedUrl(vid.access_key)!"
                  controls
                  controlsList="nodownload noplaybackrate"
                  disablePictureInPicture
                  preload="metadata"
                  :poster="vid.thumbnail ? mediaUrl(vid.thumbnail)! : undefined"
                  @error="(e: Event) => onVideoError(e, vid)"
                  @contextmenu="preventContextMenu"
                ></video>
                <div class="yw-vcard__watermark">MonaJent</div>
              </div>
              <!-- Vidéo verrouillée -->
              <div v-else class="yw-vcard__locked" @click="isClient ? handleWatch(vid) : undefined">
                <img v-if="vid.thumbnail" :src="mediaUrl(vid.thumbnail)!" alt="" class="yw-vcard__thumb" />
                <div v-else class="yw-vcard__nothumb"><i class="pi pi-video"></i></div>
                <div class="yw-vcard__ov">
                  <div class="yw-vcard__play"><i class="pi pi-lock"></i></div>
                  <span class="yw-vcard__lbl">{{ isClient ? 'Débloquer (1 clé)' : 'Connectez-vous pour visionner' }}</span>
                </div>
                <span v-if="vid.duration_sec" class="yw-vcard__dur">{{ durationStr(vid.duration_sec) }}</span>
              </div>
              <div class="yw-vcard__foot">
                <span v-if="vid.duration_sec"><i class="pi pi-clock"></i> {{ durationStr(vid.duration_sec) }}</span>
                <span><i class="pi pi-eye"></i> {{ vid.views_count }} vue{{ vid.views_count !== 1 ? 's' : '' }}</span>
                <span v-if="pub.listing.agent.verified" class="yw-vcard__verified">
                  <svg viewBox="0 0 24 24" width="13" height="13"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
                  Vérifié
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- ===== RIGHT: SIDEBAR (filtres + autres annonces) ===== -->
      <aside class="yw-right">
        <!-- Filter chips -->
        <div class="yw-filters">
          <button
            v-for="c in chips"
            :key="c.value"
            class="yw-filter"
            :class="{ 'yw-filter--on': activeChip === c.value }"
            @click="selectChip(c.value)"
          >{{ c.label }}</button>
        </div>

        <!-- Other listings -->
        <div class="yw-suggestions">
          <div v-for="item in otherListings" :key="item.id" class="yw-sg" @click="goToListing(item.id)">
            <div class="yw-sg__thumb">
              <img v-if="coverUrl(item)" :src="coverUrl(item)!" :alt="item.title" />
              <div v-else class="yw-sg__nothumb"><i class="pi pi-image"></i></div>
              <span v-if="item.videos_count > 0" class="yw-sg__vcnt"><i class="pi pi-video"></i> {{ item.videos_count }}</span>
              <span class="yw-sg__type" :class="item.listing_type === 'LOCATION' ? 'yw-sg__type--loc' : 'yw-sg__type--sale'">
                {{ item.listing_type === 'LOCATION' ? 'Location' : 'Vente' }}
              </span>
            </div>
            <div class="yw-sg__body">
              <span class="yw-sg__title">{{ item.title }}</span>
              <span class="yw-sg__agent">{{ item.agent.agency_name || item.agent.username || item.agent.phone }}</span>
              <span class="yw-sg__stats"><span class="yw-sg__price">{{ formatPrice(item.price) }}</span> &middot; {{ item.views_count }} vues &middot; {{ timeAgo(item.created_at) }}</span>
            </div>
          </div>
          <div v-if="!otherListings.length && !pub.listingsLoading" class="yw-sg-empty">Aucune autre annonce</div>
        </div>
      </aside>
    </div>

    <!-- Paywall -->
    <Dialog :visible="showPaywall" @update:visible="(v: boolean) => showPaywall = v" header="Débloquer la vidéo" :modal="true" :closable="!watchLoading" :style="{ width: '420px' }">
      <div class="yw-pw"><i class="pi pi-video yw-pw__icon"></i><p>Ce visionnage consommera <strong>1 clé virtuelle</strong>.</p><p class="yw-pw__sub">Vidéo déjà vue = gratuite.</p></div>
      <template #footer>
        <Button label="Annuler" severity="secondary" text @click="showPaywall = false" :disabled="watchLoading" />
        <Button label="Visionner" icon="pi pi-play" class="yw-pw__btn" :loading="watchLoading" @click="confirmWatch" />
      </template>
    </Dialog>

    <!-- No Pack -->
    <Dialog :visible="showNoPack" @update:visible="(v: boolean) => showNoPack = v" header="Aucun pack actif" :modal="true" :style="{ width: '440px' }">
      <div class="yw-pw"><i class="pi pi-wallet yw-pw__icon" style="color:#f57c00"></i><p>Plus de clés. Achetez un pack pour voir les vidéos.</p>
        <div class="yw-pw__pack"><span class="yw-pw__pack-price">500 F CFA</span><span class="yw-pw__pack-desc">33 vidéos + 1 visite gratuite</span></div>
      </div>
      <template #footer>
        <Button label="Plus tard" severity="secondary" text @click="showNoPack = false" />
        <Button label="Acheter un pack" icon="pi pi-wallet" class="yw-pw__btn" @click="goBuyPack" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.yw { width: 100%; }

.yw-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px; min-height: 50vh; color: #606060; text-align: center; padding: 40px 20px;
}
.yw-state h2 { margin: 0; color: #0f0f0f; }
.yw-state p { margin: 0; }

/* ===== GRID LAYOUT ===== */
.yw-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 20px;
}

/* ===== LEFT ===== */
.yw-left { min-width: 0; }

/* Player */
.yw-player { margin-bottom: 4px; }
.yw-player__frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 420px;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}
.yw-player__img { width: 100%; height: 100%; object-fit: contain; display: block; }
.yw-player__empty {
  width: 100%; aspect-ratio: 16 / 9; max-height: 420px;
  background: #e8e8e8; border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #999; font-size: 14px;
}
.yw-player__nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: rgba(0,0,0,0.5); color: #fff; font-size: 13px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s; z-index: 2;
}
.yw-player__frame:hover .yw-player__nav { opacity: 1; }
.yw-player__nav:hover { background: rgba(0,0,0,0.75); }
.yw-player__nav--prev { left: 8px; }
.yw-player__nav--next { right: 8px; }
.yw-player__counter {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,0.65); color: #fff; font-size: 11px; font-weight: 500;
  padding: 2px 7px; border-radius: 4px;
}

/* Thumbs */
.yw-thumbs { display: flex; gap: 5px; margin: 4px 0 6px; overflow-x: auto; scrollbar-width: thin; }
.yw-thumbs__item {
  width: 56px; height: 32px; border-radius: 5px; overflow: hidden; flex-shrink: 0;
  cursor: pointer; border: 2px solid transparent; opacity: 0.5; transition: all 0.15s;
}
.yw-thumbs__item--on { border-color: #0f0f0f; opacity: 1; }
.yw-thumbs__item:hover { opacity: 0.8; }
.yw-thumbs__item img { width: 100%; height: 100%; object-fit: cover; display: block; }

/* Title */
.yw-title { font-size: 17px; font-weight: 600; color: #0f0f0f; margin: 8px 0 4px; line-height: 1.4; }

/* Meta */
.yw-meta { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.yw-meta__info { font-size: 13px; color: #606060; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.yw-map-link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: #1DA53F;
  text-decoration: none;
  font-size: 12px;
  font-weight: 500;
  background: rgba(29,165,63,.08);
  padding: 2px 8px;
  border-radius: 10px;
}
.yw-map-link:hover { text-decoration: underline; background: rgba(29,165,63,.15); }
.yw-meta__price { display: flex; align-items: center; gap: 6px; }
.yw-price { font-size: 16px; font-weight: 700; color: #1DA53F; }
.yw-price-per { font-size: 12px; color: #606060; }
.yw-badge { font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 4px; text-transform: uppercase; }
.yw-badge--loc { background: #e8f0fe; color: #1a73e8; }
.yw-badge--sale { background: #e6f4ea; color: #137333; }

/* Conditions */
.yw-conditions {
  background: #f8f9fa;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 4px;
}
.yw-conditions__row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}
.yw-conditions__label { color: #606060; }
.yw-conditions__val { font-weight: 500; color: #272727; }
.yw-conditions__total {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  padding-top: 6px;
  border-top: 1px solid #e0e0e0;
  color: #1DA53F;
}
.yw-conditions__other {
  font-size: 12px;
  color: #606060;
  font-style: italic;
  margin: 0 0 4px;
}

/* Actions */
.yw-actions { display: flex; gap: 6px; padding: 6px 0; border-top: 1px solid #e5e5e5; border-bottom: 1px solid #e5e5e5; flex-wrap: wrap; }
.yw-act {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 18px; border: none;
  background: #f2f2f2; color: #0f0f0f; font-size: 12px; font-weight: 500;
  cursor: pointer; transition: background 0.15s; white-space: nowrap;
}
.yw-act:hover { background: #e5e5e5; }
.yw-act i { font-size: 14px; }

/* Agent */
.yw-agent { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #e5e5e5; }
.yw-agent__avatar-wrap { position: relative; flex-shrink: 0; }
.yw-agent__avatar {
  width: 36px; height: 36px; border-radius: 50%; background: #e8e8e8; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.yw-agent__avatar img { width: 100%; height: 100%; object-fit: cover; }
.yw-agent__avatar .pi-user { font-size: 16px; color: #aaa; }
.yw-agent__avatar-badge {
  position: absolute; bottom: -2px; right: -3px;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,.2));
}
.yw-agent__info { display: flex; flex-direction: column; }
.yw-agent__name { font-size: 13px; font-weight: 600; color: #0f0f0f; display: flex; align-items: center; }
.yw-agent__name-badge { margin-left: 4px; flex-shrink: 0; }
.yw-agent__role { font-size: 11px; color: #606060; }

/* Description */
.yw-desc {
  background: #f2f2f2; border-radius: 10px; padding: 10px 12px;
  margin: 10px 0; cursor: pointer; transition: background 0.15s;
}
.yw-desc:hover { background: #e8e8e8; }
.yw-desc__chips { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 6px; }
.yw-chip {
  background: #fff; border: 1px solid #ddd; color: #0f0f0f;
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;
}
.yw-desc__text { font-size: 13px; color: #0f0f0f; line-height: 1.5; margin: 0; white-space: pre-wrap; }
.yw-desc__sub { font-size: 12px; font-weight: 600; color: #0f0f0f; margin: 10px 0 4px; }
.yw-desc__tags { display: flex; flex-wrap: wrap; gap: 3px 12px; }
.yw-desc__tag { font-size: 12px; color: #333; display: flex; align-items: center; gap: 3px; }
.yw-desc__tag .pi-check { color: #1DA53F; font-size: 11px; }
.yw-desc__more {
  background: none; border: none; color: #0f0f0f;
  font-size: 12px; font-weight: 600; cursor: pointer; padding: 4px 0 0;
}

/* Videos */
.yw-vids { padding-top: 10px; }
.yw-vids__head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.yw-vids__title { font-size: 15px; font-weight: 600; color: #0f0f0f; margin: 0; display: flex; align-items: center; gap: 5px; }
.yw-ppv { background: #1DA53F; color: #fff; font-size: 9px; font-weight: 700; padding: 2px 7px; border-radius: 10px; }
.yw-vids__hint { font-size: 11px; color: #606060; margin: 0 0 10px; display: flex; align-items: center; gap: 5px; }
.yw-vids__hint .pi-info-circle { color: #1DA53F; font-size: 13px; }
.yw-vids__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }

.yw-vcard { border-radius: 8px; overflow: hidden; background: #fff; border: 1px solid #e5e5e5; }
.yw-vcard--hl { box-shadow: 0 0 0 2px #1DA53F; }
.yw-vcard__player {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  -webkit-user-select: none;
  user-select: none;
}
.yw-vcard__player video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  border-radius: 8px 8px 0 0;
}
.yw-vcard__watermark {
  position: absolute;
  top: 10px;
  right: 12px;
  font-size: 11px;
  font-weight: 700;
  color: rgba(255,255,255,.25);
  letter-spacing: 1px;
  pointer-events: none;
  text-transform: uppercase;
  text-shadow: 0 1px 2px rgba(0,0,0,.3);
}
.yw-vcard__locked { position: relative; width: 100%; aspect-ratio: 16/9; cursor: pointer; overflow: hidden; }
.yw-vcard__thumb { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.5); transition: filter 0.15s; }
.yw-vcard__locked:hover .yw-vcard__thumb { filter: brightness(0.4); }
.yw-vcard__nothumb { width: 100%; height: 100%; background: #e8e8e8; display: flex; align-items: center; justify-content: center; }
.yw-vcard__nothumb .pi-video { font-size: 24px; color: #bbb; }
.yw-vcard__ov { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; }
.yw-vcard__play {
  width: 44px; height: 44px; border-radius: 50%; background: rgba(29,165,63,0.9);
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: 16px; transition: transform 0.15s;
}
.yw-vcard__locked:hover .yw-vcard__play { transform: scale(1.1); }
.yw-vcard__lbl { color: #fff; font-size: 11px; font-weight: 500; text-shadow: 0 1px 4px rgba(0,0,0,0.5); }
.yw-vcard__dur { position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.75); color: #fff; font-size: 10px; padding: 1px 5px; border-radius: 3px; }
.yw-vcard__foot { display: flex; gap: 10px; padding: 6px 8px; font-size: 11px; color: #606060; align-items: center; }
.yw-vcard__foot i { margin-right: 2px; }
.yw-vcard__verified {
  display: inline-flex; align-items: center; gap: 3px;
  color: #1DA53F; font-weight: 600; margin-left: auto;
}

/* ===== RIGHT SIDEBAR ===== */
.yw-right { min-width: 0; }

/* Filters */
.yw-filters {
  display: flex; flex-wrap: wrap; gap: 6px;
  padding-bottom: 12px; margin-bottom: 12px;
  border-bottom: 1px solid #e5e5e5;
  position: sticky; top: 0; background: #f9f9f9; z-index: 5; padding-top: 2px;
}
.yw-filter {
  padding: 5px 10px; border-radius: 6px; border: none;
  background: #f2f2f2; color: #0f0f0f; font-size: 12px; font-weight: 500;
  cursor: pointer; white-space: nowrap; transition: all 0.15s;
}
.yw-filter:hover { background: #e0e0e0; }
.yw-filter--on { background: #0f0f0f; color: #fff; }
.yw-filter--on:hover { background: #272727; }

/* Suggestions */
.yw-suggestions { display: flex; flex-direction: column; gap: 8px; }

.yw-sg {
  display: flex; gap: 8px; cursor: pointer; border-radius: 8px;
  padding: 4px; transition: background 0.15s;
}
.yw-sg:hover { background: #f2f2f2; }

.yw-sg__thumb {
  width: 168px; height: 94px; border-radius: 8px; overflow: hidden;
  position: relative; flex-shrink: 0; background: #e8e8e8;
}
.yw-sg__thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.yw-sg__nothumb { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.yw-sg__nothumb .pi-image { font-size: 20px; color: #ccc; }
.yw-sg__vcnt {
  position: absolute; bottom: 3px; right: 3px;
  background: rgba(0,0,0,0.75); color: #fff; font-size: 10px; font-weight: 500;
  padding: 1px 5px; border-radius: 3px; display: flex; align-items: center; gap: 2px;
}
.yw-sg__type {
  position: absolute; top: 3px; left: 3px;
  font-size: 8px; font-weight: 700; padding: 1px 5px; border-radius: 2px; text-transform: uppercase;
}
.yw-sg__type--loc { background: #2563eb; color: #fff; }
.yw-sg__type--sale { background: #1DA53F; color: #fff; }

.yw-sg__body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; padding: 2px 0; }
.yw-sg__title {
  font-size: 13px; font-weight: 500; color: #0f0f0f; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.yw-sg__agent { font-size: 11px; color: #606060; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.yw-sg__stats { font-size: 11px; color: #606060; }
.yw-sg__price { font-weight: 600; color: #1DA53F; }
.yw-sg-empty { font-size: 13px; color: #999; text-align: center; padding: 20px 0; }

/* ===== PAYWALL ===== */
.yw-pw { text-align: center; padding: 8px 0; }
.yw-pw__icon { font-size: 36px; color: #1DA53F; margin-bottom: 14px; display: block; }
.yw-pw p { font-size: 14px; color: #272727; margin: 0 0 6px; }
.yw-pw__sub { font-size: 12px; color: #999; }
.yw-pw__btn { background: #1DA53F !important; border-color: #1DA53F !important; }
.yw-pw__pack {
  display: flex; flex-direction: column; gap: 4px;
  background: #f8f9fa; border: 2px solid #1DA53F; border-radius: 10px; padding: 14px; margin-top: 14px;
}
.yw-pw__pack-price { font-size: 22px; font-weight: 700; color: #1DA53F; }
.yw-pw__pack-desc { font-size: 12px; color: #606060; }

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {
  .yw-grid { grid-template-columns: 1fr; }
  .yw-right { order: -1; }
  .yw-filters { position: static; }
  .yw-suggestions { flex-direction: row; flex-wrap: wrap; gap: 8px; }
  .yw-sg { min-width: 300px; flex: 1; }
}

@media (max-width: 640px) {
  .yw-player__frame { border-radius: 0; max-height: 260px; }
  .yw-title { font-size: 15px; }
  .yw-price { font-size: 15px; }
  .yw-act span { display: none; }
  .yw-act { padding: 5px 8px; }
  .yw-vids__grid { grid-template-columns: 1fr; }
  .yw-suggestions { flex-direction: column; }
  .yw-sg { min-width: 0; }
  .yw-sg__thumb { width: 130px; height: 73px; }
}
</style>
