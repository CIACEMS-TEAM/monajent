<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePublicStore, type PublicListingVideo, type ListingListItem, type TeaserResult } from '@/Stores/public'
import { useAuthStore } from '@/Stores/auth'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { useToast } from 'vue-toastification'
import http, { API_BASE } from '@/services/http'

const route = useRoute()
const router = useRouter()
const pub = usePublicStore()
const auth = useAuthStore()
const toast = useToast()

const listingSlug = computed(() => route.params.slug as string)
const highlightVideoKey = computed(() => (route.query.video as string) || null)
const isClient = computed(() => auth.me?.role === 'CLIENT')
const isLoggedIn = computed(() => !!auth.me)

const watchLoading = ref(false)
const activeVideo = ref<PublicListingVideo | null>(null)
const showPaywall = ref(false)
const showNoPack = ref(false)
const showLoginPrompt = ref(false)
const heroIdx = ref(0)
const photoModalIdx = ref(-1)
const showPhotoModal = ref(false)
const descExpanded = ref(false)
const otherListings = ref<ListingListItem[]>([])
const activeChip = ref('all')

// ── Teaser state ──
let teaserVideoEl: HTMLVideoElement | null = null
const teaserStreamUrl = ref('')
const teaserSeconds = ref(15)
const teaserPlaying = ref(false)
const teaserPaused = ref(false)
const teaserAccessKey = ref('')
const teaserInfo = ref<TeaserResult | null>(null)
const teaserLoading = ref(false)
let teaserTimer: ReturnType<typeof setInterval> | null = null

function setTeaserRef(el: any) {
  teaserVideoEl = el instanceof HTMLVideoElement ? el : null
}

function clearTeaserTimer() {
  if (teaserTimer) { clearTimeout(teaserTimer); teaserTimer = null }
}

onUnmounted(() => clearTeaserTimer())

// ── Visite physique ──
interface AvailSlot {
  id: number
  day_of_week: number
  day_label: string
  start_time: string
  end_time: string
}
const showVisitModal = ref(false)
const visitSlots = ref<AvailSlot[]>([])
const visitSlotsLoading = ref(false)
const selectedSlotId = ref<number | null>(null)
const visitNote = ref('')
const visitSubmitting = ref(false)
const visitNoPackModal = ref(false)

// ── Signalement ──
const showReportModal = ref(false)
const reportReason = ref('')
const reportDescription = ref('')
const reportSubmitting = ref(false)
const reportReasons = [
  { value: 'ALREADY_SOLD', label: 'Bien déjà vendu' },
  { value: 'ALREADY_RENTED', label: 'Bien déjà loué' },
  { value: 'MISLEADING', label: 'Annonce trompeuse / vidéo ne correspond pas' },
  { value: 'DUPLICATE_VIDEO', label: 'Même vidéo sur une autre annonce' },
  { value: 'SCAM', label: 'Arnaque suspectée' },
  { value: 'OTHER', label: 'Autre' },
]

const knownCities = ref<string[]>([])

function captureAvailableCities(listings: ListingListItem[]) {
  const countMap = new Map<string, number>()
  for (const l of listings) {
    if (l.city) countMap.set(l.city, (countMap.get(l.city) || 0) + 1)
  }
  knownCities.value = [...countMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([name]) => name)
}

const chips = computed(() => {
  const base: { label: string; value: string }[] = [
    { label: 'Tous', value: 'all' },
    { label: 'Location', value: 'LOCATION' },
    { label: 'Vente', value: 'VENTE' },
  ]
  for (const city of knownCities.value) {
    base.push({ label: city, value: city })
  }
  return base
})

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

async function handleToggleFavorite() {
  if (!isLoggedIn.value) { showLoginPrompt.value = true; return }
  if (!isClient.value) { toast.info('Seuls les clients peuvent ajouter des favoris.'); return }
  if (!pub.listing) return
  const isFav = await pub.toggleFavorite(pub.listing.id)
  toast.success(isFav ? 'Ajouté aux favoris' : 'Retiré des favoris')
}

const heroImages = computed(() => pub.listing?.images ?? [])
const firstVideoThumb = computed(() => {
  const vid = pub.listing?.videos?.[0]
  return vid?.thumbnail ? mediaUrl(vid.thumbnail) : null
})
const heroHasImages = computed(() => heroImages.value.length > 0)

function heroPrev() {
  if (!heroHasImages.value) return
  if (!isLoggedIn.value) { showLoginPrompt.value = true; return }
  heroIdx.value = (heroIdx.value - 1 + heroImages.value.length) % heroImages.value.length
}
function heroNext() {
  if (!heroHasImages.value) return
  if (!isLoggedIn.value) { showLoginPrompt.value = true; return }
  heroIdx.value = (heroIdx.value + 1) % heroImages.value.length
}

function openPhotoModal(idx: number) {
  if (!isLoggedIn.value) { showLoginPrompt.value = true; return }
  pub.registerVisit(listingSlug.value)
  photoModalIdx.value = idx
  showPhotoModal.value = true
}
function photoModalPrev() {
  if (!heroHasImages.value) return
  photoModalIdx.value = (photoModalIdx.value - 1 + heroImages.value.length) % heroImages.value.length
}
function photoModalNext() {
  if (!heroHasImages.value) return
  photoModalIdx.value = (photoModalIdx.value + 1) % heroImages.value.length
}

const descriptionTruncated = computed(() => {
  const desc = pub.listing?.description
  if (!desc || typeof desc !== 'string') return ''
  return desc.length > 200 ? desc.slice(0, 200) + '...' : desc
})
const needsTruncation = computed(() => (typeof pub.listing?.description === 'string' ? pub.listing.description.length : 0) > 200)
const showToggle = computed(() => needsTruncation.value || (pub.listing?.amenities?.length ?? 0) > 0 || pub.listing?.address)

const hasVideos = computed(() => (pub.listing?.videos?.length ?? 0) > 0)
const firstVideo = computed(() => pub.listing?.videos?.[0] ?? null)

function goToListing(slug: string) {
  heroIdx.value = 0
  descExpanded.value = false
  router.push({ name: 'public-listing', params: { slug } })
}

function coverUrl(item: ListingListItem): string | null {
  if (!item.cover_image) return null
  return item.cover_image.startsWith('http') ? item.cover_image : `${API_BASE}${item.cover_image}`
}

async function loadOtherListings() {
  try {
    const params: Record<string, string> = {}
    if (activeChip.value === 'LOCATION' || activeChip.value === 'VENTE') params.listing_type = activeChip.value
    else if (activeChip.value !== 'all') params.city = activeChip.value
    await pub.fetchListings(params)
    otherListings.value = (pub.listings ?? []).filter(l => l.slug !== listingSlug.value).slice(0, 20)
    if (activeChip.value === 'all' && knownCities.value.length === 0) {
      captureAvailableCities(pub.listings ?? [])
    }
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
    await pub.fetchPublicListing(listingSlug.value)
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

watch(listingSlug, () => {
  loadListing()
  loadOtherListings()
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

function handleVirtualVisit() {
  if (!firstVideo.value) return
  launchTeaser(firstVideo.value)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function handlePhysicalVisit() {
  if (!isLoggedIn.value) { showLoginPrompt.value = true; return }
  if (!isClient.value) { toast.warning('Seuls les clients peuvent demander une visite.'); return }
  visitSlotsLoading.value = true
  showVisitModal.value = true
  selectedSlotId.value = null
  visitNote.value = ''
  try {
    const { data } = await http.get<any>(`/api/listings/${pub.listing!.id}/availability/`)
    visitSlots.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch {
    toast.error('Impossible de charger les créneaux disponibles.')
    showVisitModal.value = false
  } finally {
    visitSlotsLoading.value = false
  }
}

async function submitVisitRequest() {
  if (!selectedSlotId.value) { toast.error('Veuillez choisir un créneau.'); return }
  visitSubmitting.value = true
  try {
    await http.post('/api/client/visits/', {
      listing_id: pub.listing!.id,
      slot_id: selectedSlotId.value,
      client_note: visitNote.value.trim(),
    })
    showVisitModal.value = false
    toast.success('Demande de visite envoyée ! Vous recevrez une confirmation de l\'agent.')
    router.push({ name: 'client-visits' })
  } catch (e: any) {
    if (e?.response?.status === 402) {
      showVisitModal.value = false
      visitNoPackModal.value = true
    } else {
      toast.error(e?.response?.data?.detail || 'Erreur lors de la demande de visite.')
    }
  } finally {
    visitSubmitting.value = false
  }
}

function formatSlotTime(t: string) {
  if (!t) return ''
  return t.slice(0, 5)
}

// ── Signalement ──
function openReportModal() {
  if (!isLoggedIn.value) { showLoginPrompt.value = true; return }
  if (!isClient.value) { toast.warning('Seuls les clients peuvent signaler.'); return }
  reportReason.value = ''
  reportDescription.value = ''
  showReportModal.value = true
}

async function submitReport() {
  if (!reportReason.value) { toast.error('Veuillez choisir un motif.'); return }
  reportSubmitting.value = true
  try {
    await http.post(`/api/listings/${pub.listing!.id}/report/`, {
      listing: pub.listing!.id,
      reason: reportReason.value,
      description: reportDescription.value.trim(),
    })
    showReportModal.value = false
    toast.success('Signalement enregistré. Merci pour votre vigilance.')
  } catch (e: any) {
    if (e?.response?.status === 409) {
      toast.info('Vous avez déjà signalé cette annonce.')
      showReportModal.value = false
    } else {
      toast.error(e?.response?.data?.detail || 'Erreur lors du signalement.')
    }
  } finally {
    reportSubmitting.value = false
  }
}

function scrollToVideo(accessKey: string) {
  nextTick(() => {
    const el = document.getElementById(`video-${accessKey}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

async function handleWatch(vid: PublicListingVideo) {
  launchTeaser(vid)
}

async function launchTeaser(vid: PublicListingVideo) {
  if (pub.getUnlockedUrl(vid.access_key)) {
    activeVideo.value = vid
    scrollToVideo(vid.access_key)
    return
  }
  teaserLoading.value = true
  teaserAccessKey.value = vid.access_key
  activeVideo.value = vid
  try {
    const data = await pub.fetchTeaser(vid.access_key)
    teaserInfo.value = data

    if (data.is_agent_owner) {
      teaserStreamUrl.value = data.stream_url
      teaserPlaying.value = true
      teaserPaused.value = false
      return
    }

    // Freemium : utilisateur connecté → accès complet sans limite
    if (isLoggedIn.value) {
      pub.unlockedVideos[vid.access_key] = data.stream_url
      pub.registerVisit(listingSlug.value)
      resetTeaser()
      await nextTick()
      scrollToVideo(vid.access_key)
      return
    }

    // Non connecté → aperçu 10 secondes puis prompt de connexion
    teaserSeconds.value = 10
    teaserStreamUrl.value = data.stream_url
    teaserPlaying.value = true
    teaserPaused.value = false
    scrollToVideo(vid.access_key)

    await nextTick()
    startTeaserTimer()
  } catch {
    toast.error('Impossible de charger l\'aperçu vidéo.')
  } finally {
    teaserLoading.value = false
  }
}

function pauseTeaser() {
  if (teaserVideoEl) teaserVideoEl.pause()
  teaserPaused.value = true
  clearTeaserTimer()
}

function startTeaserTimer() {
  clearTeaserTimer()
  teaserTimer = setInterval(() => {
    if (!teaserVideoEl || teaserPaused.value) { clearTeaserTimer(); return }
    if (teaserVideoEl.currentTime >= teaserSeconds.value) {
      pauseTeaser()
    }
  }, 150)
}

function handleTeaserTimeUpdate(event: Event) {
  if (teaserPaused.value) return
  const el = event.target as HTMLVideoElement
  if (!el) return
  if (!teaserVideoEl) teaserVideoEl = el
  if (el.currentTime >= teaserSeconds.value) {
    pauseTeaser()
  }
}

function teaserGoLogin() {
  resetTeaser()
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

function teaserGoSignup() {
  resetTeaser()
  router.push({ name: 'signup-client' })
}

function teaserGoBuyPack() {
  resetTeaser()
  router.push({ name: 'client-packs' })
}

async function teaserUnlock() {
  if (!activeVideo.value) return
  watchLoading.value = true
  try {
    const result = await pub.watchVideo(activeVideo.value.access_key)
    pub.registerVisit(listingSlug.value)
    resetTeaser()
    toast.success('Vidéo débloquée !')
    scrollToVideo(activeVideo.value.access_key)
  } catch (e: any) {
    if (e?.response?.status === 402) {
      showLoginPrompt.value = true
    } else {
      toast.error(e?.response?.data?.detail || 'Erreur lors du déblocage')
    }
  } finally { watchLoading.value = false }
}

function resetTeaser() {
  clearTeaserTimer()
  if (teaserVideoEl) { teaserVideoEl.pause(); teaserVideoEl.src = '' }
  teaserVideoEl = null
  teaserPlaying.value = false
  teaserPaused.value = false
  teaserStreamUrl.value = ''
  teaserInfo.value = null
  teaserAccessKey.value = ''
}

async function confirmWatch() {
  if (!activeVideo.value) return
  watchLoading.value = true
  try {
    await pub.watchVideo(activeVideo.value.access_key)
    pub.registerVisit(listingSlug.value)
    showPaywall.value = false
    toast.success('Vidéo débloquée !')
  } catch (e: any) {
    if (e?.response?.status === 402) { showPaywall.value = false; showLoginPrompt.value = true }
    else toast.error(e?.response?.data?.detail || 'Erreur lors du visionnage')
  } finally { watchLoading.value = false }
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
function goLogin() { showLoginPrompt.value = false; router.push({ name: 'login' }) }

function spaUrl(): string { return window.location.origin + `/home/annonce/${listingSlug.value}` }
function ogUrl(): string { return `${window.location.origin}/share/${listingSlug.value}/` }
function shareText(): string {
  if (!pub.listing) return ogUrl()
  const type = pub.listing.listing_type === 'LOCATION' ? 'Location' : 'Vente'
  let loc = pub.listing.city || ''
  if (pub.listing.neighborhood) loc += `, ${pub.listing.neighborhood}`
  return `${pub.listing.title}\n${type} — ${formatPrice(pub.listing.price)}\n${loc}\n\n${ogUrl()}`
}
async function copyLink() {
  try { await navigator.clipboard.writeText(spaUrl()); toast.success('Lien copié !') }
  catch (_) { toast.error('Impossible de copier') }
}
function shareWhatsApp() { window.open(`https://wa.me/?text=${encodeURIComponent(shareText())}`, '_blank') }
function shareFacebook() { window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(ogUrl())}`, '_blank') }
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
        <!-- Player / Hero -->
        <div class="yw-player">

          <!-- ═══ HERO: Vidéo débloquée (lecture complète) ═══ -->
          <div v-if="firstVideo && pub.getUnlockedUrl(firstVideo.access_key)" class="yw-player__frame" @contextmenu="preventContextMenu">
            <video
              :src="pub.getUnlockedUrl(firstVideo.access_key)!"
              controls
              controlsList="nodownload noplaybackrate"
              disablePictureInPicture
              playsinline
              preload="metadata"
              :poster="firstVideoThumb || undefined"
              @error="(e: Event) => onVideoError(e, firstVideo!)"
              @contextmenu="preventContextMenu"
              class="yw-player__video"
            ></video>
            <div class="yw-player__watermark">MonaJent</div>
          </div>

          <!-- ═══ HERO: Teaser en cours ═══ -->
          <div v-else-if="teaserPlaying && firstVideo && teaserAccessKey === firstVideo.access_key" class="yw-player__frame" @contextmenu="preventContextMenu">
            <video
              :ref="setTeaserRef"
              :src="teaserStreamUrl"
              autoplay
              playsinline
              :poster="firstVideoThumb || undefined"
              controlsList="nodownload noplaybackrate"
              disablePictureInPicture
              @timeupdate="handleTeaserTimeUpdate"
              @contextmenu="preventContextMenu"
              class="yw-player__video"
            ></video>
            <div class="yw-player__watermark">MonaJent</div>

            <!-- Barre de progression teaser -->
            <div v-if="!teaserPaused" class="yw-teaser-bar yw-teaser-bar--hero">
              <div class="yw-teaser-bar__label">Aperçu</div>
              <div class="yw-teaser-bar__track">
                <div class="yw-teaser-bar__fill" :style="{ animationDuration: teaserSeconds + 's' }"></div>
              </div>
            </div>

            <!-- Overlay d'interruption (hero) -->
            <div v-if="teaserPaused" class="yw-teaser-ov">
              <div class="yw-teaser-ov__content">
                <div class="yw-teaser-ov__icon">
                  <svg viewBox="0 0 24 24" width="40" height="40"><path fill="#fff" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
                </div>
                <h3 class="yw-teaser-ov__title">Envie de voir la suite ?</h3>
                <p class="yw-teaser-ov__desc">
                  Connectez-vous pour accéder <strong>gratuitement</strong> à la vidéo complète.
                </p>
                <div class="yw-teaser-ov__btns">
                  <button class="yw-teaser-btn yw-teaser-btn--primary" @click="teaserGoLogin">
                    <i class="pi pi-sign-in"></i> Se connecter
                  </button>
                  <button class="yw-teaser-btn yw-teaser-btn--secondary" @click="teaserGoSignup">
                    <i class="pi pi-user-plus"></i> Créer un compte gratuit
                  </button>
                </div>
                <p class="yw-teaser-ov__sub">Inscription gratuite — accédez à toutes les vidéos</p>
              </div>
            </div>
          </div>

          <!-- ═══ HERO: Vidéo (thumbnail ou placeholder, cliquable pour lancer teaser) ═══ -->
          <div v-else-if="hasVideos" class="yw-player__frame yw-player__frame--vid" @click="handleVirtualVisit">
            <img v-if="firstVideoThumb" :src="firstVideoThumb" :alt="pub.listing.title" class="yw-player__img" />
            <div v-else class="yw-player__placeholder">
              <i class="pi pi-video" style="font-size:48px;color:#1DA53F"></i>
            </div>
            <div class="yw-player__play-ov">
              <div class="yw-player__play-btn"><i class="pi pi-play-circle"></i></div>
              <span class="yw-player__play-label">Voir la vidéo</span>
            </div>
          </div>

          <!-- ═══ HERO: Images (seulement si aucune vidéo) ═══ -->
          <div v-else-if="heroHasImages" class="yw-player__frame" :class="{ 'yw-player__frame--locked': !isLoggedIn && heroImages.length > 1 }" style="cursor:pointer" @click="openPhotoModal(heroIdx)">
            <img :src="mediaUrl(heroImages[heroIdx].image)!" :alt="pub.listing.title" class="yw-player__img" />
            <template v-if="heroImages.length > 1">
              <button class="yw-player__nav yw-player__nav--prev" @click.stop="heroPrev"><i class="pi pi-chevron-left"></i></button>
              <button class="yw-player__nav yw-player__nav--next" @click.stop="heroNext"><i class="pi pi-chevron-right"></i></button>
              <span class="yw-player__counter">{{ heroIdx + 1 }} / {{ heroImages.length }}</span>
            </template>
            <div v-if="!isLoggedIn && heroImages.length > 1" class="yw-player__lock-hint">
              <i class="pi pi-lock"></i> Connectez-vous pour voir les {{ heroImages.length }} photos
            </div>
          </div>

          <!-- ═══ HERO: Rien ═══ -->
          <div v-else class="yw-player__empty"><i class="pi pi-image" style="font-size:36px;color:#ccc"></i><span>Aucun média</span></div>

          <!-- Galerie photos superposée en bas du hero -->
          <div v-if="heroHasImages && hasVideos" class="yw-photos-ov">
            <div class="yw-photos-ov__strip">
              <div
                v-for="(img, i) in heroImages"
                :key="img.id"
                class="yw-photos-ov__item"
                @click.stop="openPhotoModal(i)"
              ><img :src="mediaUrl(img.image)!" :alt="`Photo ${i + 1}`" /></div>
              <div class="yw-photos-ov__count">
                <i class="pi pi-images"></i> {{ heroImages.length }}
              </div>
            </div>
          </div>
        </div>

        <!-- === CTA BUTTONS === -->
        <div class="yw-cta">
          <button v-if="hasVideos && !teaserPlaying && !pub.getUnlockedUrl(firstVideo?.access_key ?? '')" class="yw-cta__btn yw-cta__btn--virtual" @click="handleVirtualVisit">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>
            <span>Voir la vidéo</span>
            <small v-if="firstVideo">{{ durationStr(firstVideo.duration_sec) }}</small>
          </button>
          <button class="yw-cta__btn yw-cta__btn--physical" @click="handlePhysicalVisit">
            <i class="pi pi-calendar"></i>
            <span>Programmer une visite</span>
          </button>
        </div>

        <!-- Title -->
        <h1 class="yw-title">{{ pub.listing.title }}</h1>

        <!-- Meta -->
        <div class="yw-meta">
          <span class="yw-meta__info">
            {{ pub.listing.views_count }} vue{{ pub.listing.views_count !== 1 ? 's' : '' }}
            &middot; {{ pub.listing.visits_count }} visite{{ pub.listing.visits_count !== 1 ? 's' : '' }}
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
          <button
            v-if="isClient"
            class="yw-act yw-act--fav"
            :class="{ 'yw-act--fav-on': pub.isFavorite(pub.listing.id) }"
            @click="handleToggleFavorite"
          >
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path
                :fill="pub.isFavorite(pub.listing.id) ? '#ef4444' : 'none'"
                :stroke="pub.isFavorite(pub.listing.id) ? '#ef4444' : 'currentColor'"
                stroke-width="2"
                d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"
              />
            </svg>
            <span>{{ pub.isFavorite(pub.listing.id) ? 'Favori' : 'Favori' }}</span>
            <small class="yw-act__count">{{ pub.listing.favorites_count }}</small>
          </button>
          <button class="yw-act" @click="shareWhatsApp"><i class="pi pi-whatsapp"></i><span>WhatsApp</span></button>
          <button class="yw-act" @click="shareFacebook"><i class="pi pi-facebook"></i><span>Facebook</span></button>
          <button class="yw-act" @click="copyLink"><i class="pi pi-share-alt"></i><span>Partager</span></button>
          <button class="yw-act" @click="copyLink"><i class="pi pi-link"></i><span>Copier</span></button>
          <button class="yw-act yw-act--report" @click="openReportModal"><i class="pi pi-flag"></i><span>Signaler</span></button>
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
          <template v-if="descExpanded && pub.listing.amenities?.length">
            <div class="yw-desc__sub">Commodités</div>
            <div class="yw-desc__tags"><span v-for="(a, i) in (pub.listing.amenities ?? [])" :key="i" class="yw-desc__tag"><i class="pi pi-check"></i> {{ a }}</span></div>
          </template>
          <template v-if="descExpanded && pub.listing.address">
            <div class="yw-desc__sub">Adresse</div>
            <p class="yw-desc__text" style="margin:0">{{ pub.listing.address }}</p>
          </template>
          <button v-if="showToggle" class="yw-desc__more" @click.stop="descExpanded = !descExpanded">{{ descExpanded ? 'Afficher moins' : 'Afficher plus' }}</button>
        </div>

        <!-- Videos PPV -->
        <section v-if="(pub.listing.videos?.length ?? 0) > 1" class="yw-vids">
          <div class="yw-vids__head">
            <h2 class="yw-vids__title"><i class="pi pi-video"></i> {{ pub.listing.videos?.length ?? 0 }} vidéo{{ (pub.listing.videos?.length ?? 0) > 1 ? 's' : '' }}</h2>
          </div>
          <p v-if="!isLoggedIn" class="yw-vids__hint"><i class="pi pi-info-circle"></i> Connectez-vous pour accéder gratuitement à toutes les vidéos.</p>
          <div class="yw-vids__grid">
            <div v-for="vid in (pub.listing.videos ?? [])" :key="vid.id" :id="`video-${vid.access_key}`" class="yw-vcard" :class="{ 'yw-vcard--hl': highlightVideoKey === vid.access_key }">

              <!-- Vidéo DÉBLOQUÉE — player complet -->
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

              <!-- Teaser en cours sur cette vidéo → indiquer que ça joue dans le hero -->
              <div v-else-if="teaserPlaying && teaserAccessKey === vid.access_key" class="yw-vcard__locked yw-vcard__locked--active">
                <img v-if="vid.thumbnail" :src="mediaUrl(vid.thumbnail)!" alt="" class="yw-vcard__thumb" />
                <div v-else class="yw-vcard__nothumb"><i class="pi pi-video"></i></div>
                <div class="yw-vcard__ov">
                  <div class="yw-vcard__play yw-vcard__play--pulse"><i class="pi pi-play"></i></div>
                  <span class="yw-vcard__lbl">Lecture en cours ↑</span>
                </div>
              </div>

              <!-- Vidéo VERROUILLÉE — thumbnail avec play -->
              <div v-else class="yw-vcard__locked" @click="handleWatch(vid)">
                <img v-if="vid.thumbnail" :src="mediaUrl(vid.thumbnail)!" alt="" class="yw-vcard__thumb" />
                <div v-else class="yw-vcard__nothumb"><i class="pi pi-video"></i></div>
                <div class="yw-vcard__ov">
                  <div class="yw-vcard__play">
                    <i v-if="teaserLoading && teaserAccessKey === vid.access_key" class="pi pi-spin pi-spinner"></i>
                    <i v-else class="pi pi-play"></i>
                  </div>
                  <span class="yw-vcard__lbl">{{ isLoggedIn ? 'Voir la vidéo' : 'Aperçu' }}</span>
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
          <div v-for="item in otherListings" :key="item.id" class="yw-sg" @click="goToListing(item.slug)">
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
              <span class="yw-sg__stats"><span class="yw-sg__price">{{ formatPrice(item.price) }}</span> &middot; {{ item.views_count }} vues<template v-if="item.visits_count"> · {{ item.visits_count }} visites</template> &middot; {{ timeAgo(item.created_at) }}</span>
            </div>
          </div>
          <div v-if="!otherListings.length && !pub.listingsLoading" class="yw-sg-empty">Aucune autre annonce</div>
        </div>
      </aside>
    </div>

    <!-- ══ Photo modal (lightbox) ══ -->
    <Teleport to="body">
      <div v-if="showPhotoModal && heroHasImages" class="yw-lightbox" @click.self="showPhotoModal = false">
        <button class="yw-lightbox__close" @click="showPhotoModal = false"><i class="pi pi-times"></i></button>
        <button class="yw-lightbox__nav yw-lightbox__nav--prev" @click="photoModalPrev"><i class="pi pi-chevron-left"></i></button>
        <img :src="mediaUrl(heroImages[photoModalIdx].image)!" :alt="`Photo ${photoModalIdx + 1}`" class="yw-lightbox__img" />
        <button class="yw-lightbox__nav yw-lightbox__nav--next" @click="photoModalNext"><i class="pi pi-chevron-right"></i></button>
        <span class="yw-lightbox__counter">{{ photoModalIdx + 1 }} / {{ heroImages.length }}</span>
      </div>
    </Teleport>

    <!-- Paywall (masqué en mode freemium) -->
    <!-- showPaywall / showNoPack ne sont plus déclenchés dans le flux freemium -->

    <!-- Login required -->
    <Dialog :visible="showLoginPrompt" @update:visible="(v: boolean) => showLoginPrompt = v" header="Connexion requise" :modal="true" :style="{ width: '400px' }">
      <div class="yw-pw">
        <i class="pi pi-sign-in yw-pw__icon" style="color:#1DA53F"></i>
        <p>Connectez-vous ou créez un compte gratuit pour explorer les photos et vidéos de cette annonce.</p>
      </div>
      <template #footer>
        <Button label="Plus tard" severity="secondary" text @click="showLoginPrompt = false" />
        <Button label="Se connecter" icon="pi pi-sign-in" class="yw-pw__btn" @click="goLogin" />
      </template>
    </Dialog>

    <!-- ══ Visite physique — sélection créneau ══ -->
    <Dialog :visible="showVisitModal" @update:visible="(v: boolean) => showVisitModal = v" header="Programmer une visite" :modal="true" :closable="!visitSubmitting" :style="{ width: '520px' }">
      <div class="yw-visit-modal">
        <!-- Chargement créneaux -->
        <div v-if="visitSlotsLoading" class="yw-visit-modal__loading">
          <i class="pi pi-spin pi-spinner" style="font-size:24px;color:#1DA53F"></i>
          <span>Chargement des disponibilités...</span>
        </div>

        <!-- Aucun créneau -->
        <div v-else-if="visitSlots.length === 0" class="yw-visit-modal__empty">
          <i class="pi pi-calendar-times" style="font-size:32px;color:#ccc"></i>
          <p>Cet agent n'a pas encore configuré ses créneaux de disponibilité.</p>
        </div>

        <!-- Liste des créneaux -->
        <template v-else>
          <!-- Agent info + contact -->
          <div v-if="pub.listing" class="yw-visit-agent">
            <div class="yw-visit-agent__avatar">
              <img v-if="pub.listing.agent.profile_photo" :src="mediaUrl(pub.listing.agent.profile_photo)!" alt="" />
              <i v-else class="pi pi-user"></i>
            </div>
            <div class="yw-visit-agent__info">
              <span class="yw-visit-agent__name">{{ pub.listing.agent.agency_name || pub.listing.agent.username || pub.listing.agent.phone }}</span>
              <!--<span v-if="pub.listing.agent.contact_phone" class="yw-visit-agent__contact">
                <i class="pi pi-phone"></i> {{ pub.listing.agent.contact_phone }}
              </span>
              <span v-else-if="pub.listing.agent.phone" class="yw-visit-agent__contact">
                <i class="pi pi-phone"></i> {{ pub.listing.agent.phone }}
              </span>
              <span v-if="pub.listing.agent.contact_email" class="yw-visit-agent__contact">
                <i class="pi pi-envelope"></i> {{ pub.listing.agent.contact_email }}
              </span>-->
            </div>
          </div>

          <p class="yw-visit-modal__hint">Choisissez un créneau :</p>
          <div class="yw-visit-slots">
            <label
              v-for="slot in visitSlots"
              :key="slot.id"
              class="yw-visit-slot"
              :class="{ 'yw-visit-slot--on': selectedSlotId === slot.id }"
            >
              <input type="radio" :value="slot.id" v-model="selectedSlotId" class="yw-visit-slot__radio" />
              <div class="yw-visit-slot__body">
                <span class="yw-visit-slot__day">{{ slot.day_label }}</span>
                <span class="yw-visit-slot__time">{{ formatSlotTime(slot.start_time) }} — {{ formatSlotTime(slot.end_time) }}</span>
              </div>
              <i v-if="selectedSlotId === slot.id" class="pi pi-check-circle yw-visit-slot__check"></i>
            </label>
          </div>

          <div class="yw-visit-modal__note">
            <label>Note pour l'agent <small>(optionnel)</small></label>
            <textarea v-model="visitNote" rows="2" maxlength="500" placeholder="Précisez vos disponibilités, questions..."></textarea>
          </div>

          <div class="yw-visit-modal__info">
            <i class="pi pi-info-circle"></i>
            <span>L'agent vous contactera dès réception de votre demande. Il a <strong>48h pour confirmer</strong> le créneau choisi.</span>
          </div>
        </template>
      </div>
      <template #footer>
        <Button label="Annuler" severity="secondary" text @click="showVisitModal = false" :disabled="visitSubmitting" />
        <Button
          v-if="visitSlots.length > 0"
          label="Envoyer la demande"
          icon="pi pi-send"
          class="yw-pw__btn"
          :loading="visitSubmitting"
          :disabled="!selectedSlotId || visitSubmitting"
          @click="submitVisitRequest"
        />
      </template>
    </Dialog>

    <!-- Visite indisponible -->
    <Dialog :visible="visitNoPackModal" @update:visible="(v: boolean) => visitNoPackModal = v" header="Visite indisponible" :modal="true" :style="{ width: '440px' }">
      <div class="yw-pw">
        <i class="pi pi-calendar-times yw-pw__icon" style="color:#1DA53F"></i>
        <p>La programmation de visite n'est pas disponible pour le moment. Veuillez réessayer plus tard.</p>
      </div>
      <template #footer>
        <Button label="Fermer" severity="secondary" text @click="visitNoPackModal = false" />
      </template>
    </Dialog>

    <!-- ══ Signalement ══ -->
    <Dialog :visible="showReportModal" @update:visible="(v: boolean) => showReportModal = v" header="Signaler cette annonce" :modal="true" :closable="!reportSubmitting" :style="{ width: '460px' }">
      <div class="yw-report">
        <p class="yw-report__hint">Aidez-nous à maintenir la qualité des annonces. Choisissez un motif :</p>
        <div class="yw-report__reasons">
          <label
            v-for="r in reportReasons"
            :key="r.value"
            class="yw-report__reason"
            :class="{ 'yw-report__reason--on': reportReason === r.value }"
          >
            <input type="radio" :value="r.value" v-model="reportReason" />
            <span>{{ r.label }}</span>
          </label>
        </div>
        <div class="yw-report__desc">
          <label>Détails <small>(optionnel)</small></label>
          <textarea v-model="reportDescription" rows="3" maxlength="1000" placeholder="Décrivez le problème..."></textarea>
        </div>
      </div>
      <template #footer>
        <Button label="Annuler" severity="secondary" text @click="showReportModal = false" :disabled="reportSubmitting" />
        <Button
          label="Envoyer le signalement"
          icon="pi pi-flag"
          severity="danger"
          :loading="reportSubmitting"
          :disabled="!reportReason || reportSubmitting"
          @click="submitReport"
        />
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
.yw-player { margin-bottom: 4px; position: relative; }
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
.yw-player__video { width: 100%; height: 100%; object-fit: contain; background: #000; display: block; }
.yw-player__watermark {
  position: absolute; top: 10px; right: 12px;
  font-size: 12px; font-weight: 700; color: rgba(255,255,255,.2);
  letter-spacing: 1px; pointer-events: none; text-transform: uppercase;
  text-shadow: 0 1px 2px rgba(0,0,0,.3); z-index: 2;
}
.yw-player__play-ov--img {
  cursor: pointer; pointer-events: auto;
}
.yw-player__play-ov--img:hover .yw-player__play-btn { transform: scale(1.1); }
.yw-player__empty {
  width: 100%; aspect-ratio: 16 / 9; max-height: 420px;
  background: #e8e8e8; border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #999; font-size: 14px;
}
.yw-player__frame--vid { cursor: pointer; }
.yw-player__frame--vid .yw-player__img { filter: brightness(0.65); transition: filter 0.2s; }
.yw-player__frame--vid:hover .yw-player__img { filter: brightness(0.5); }
.yw-player__play-ov {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  pointer-events: none;
}
.yw-player__placeholder {
  width: 100%; height: 100%; background: linear-gradient(135deg, #1a1a2e, #16213e);
  display: flex; align-items: center; justify-content: center;
}
.yw-player__play-btn { font-size: 48px; color: #fff; filter: drop-shadow(0 2px 8px rgba(0,0,0,.4)); transition: transform 0.2s; }
.yw-player__frame--vid:hover .yw-player__play-btn { transform: scale(1.1); }
.yw-player__play-label { color: #fff; font-size: 14px; font-weight: 600; text-shadow: 0 1px 6px rgba(0,0,0,.5); }
.yw-player__nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: rgba(0,0,0,0.5); color: #fff; font-size: 13px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s; z-index: 2;
}
.yw-player__frame:hover .yw-player__nav { opacity: 1; }
.yw-player__frame--locked .yw-player__nav { opacity: 0.8; }
.yw-player__frame--locked:hover .yw-player__nav { opacity: 1; }
.yw-player__nav:hover { background: rgba(0,0,0,0.75); }
.yw-player__lock-hint {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.75));
  color: #fff; font-size: 12px; font-weight: 500;
  padding: 20px 12px 10px; text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  pointer-events: none;
}
.yw-player__lock-hint .pi-lock { font-size: 11px; }
.yw-player__nav--prev { left: 8px; }
.yw-player__nav--next { right: 8px; }
.yw-player__counter {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,0.65); color: #fff; font-size: 11px; font-weight: 500;
  padding: 2px 7px; border-radius: 4px;
}

/* Thumbs */
/* Photo overlay strip (inside hero) */
.yw-photos-ov {
  position: absolute; bottom: 8px; left: 8px; right: 8px; z-index: 5;
  pointer-events: auto;
}
.yw-photos-ov__strip {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 8px; border-radius: 8px;
  background: rgba(0, 0, 0, 0.55); backdrop-filter: blur(6px);
  overflow-x: auto; scrollbar-width: none;
}
.yw-photos-ov__strip::-webkit-scrollbar { display: none; }
.yw-photos-ov__item {
  width: 48px; height: 34px; border-radius: 4px; overflow: hidden; flex-shrink: 0;
  cursor: pointer; border: 2px solid transparent; opacity: 0.8; transition: all 0.15s;
}
.yw-photos-ov__item:hover { opacity: 1; border-color: #1DA53F; transform: scale(1.08); }
.yw-photos-ov__item img { width: 100%; height: 100%; object-fit: cover; display: block; }
.yw-photos-ov__count {
  flex-shrink: 0; color: rgba(255,255,255,0.85); font-size: 0.72rem; font-weight: 600;
  display: flex; align-items: center; gap: 3px; padding: 0 4px; white-space: nowrap;
}
.yw-photos-ov__count i { font-size: 0.8rem; }

/* Lightbox */
.yw-lightbox {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.92); display: flex; align-items: center; justify-content: center;
  animation: yw-ov-fadein 0.2s ease;
}
.yw-lightbox__img {
  max-width: 90vw; max-height: 85vh; object-fit: contain; border-radius: 6px;
  box-shadow: 0 4px 40px rgba(0,0,0,0.5);
}
.yw-lightbox__close {
  position: absolute; top: 16px; right: 20px;
  background: rgba(255,255,255,0.15); border: none; color: #fff;
  width: 40px; height: 40px; border-radius: 50%; font-size: 1.2rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.yw-lightbox__close:hover { background: rgba(255,255,255,0.3); }
.yw-lightbox__nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,0.15); border: none; color: #fff;
  width: 44px; height: 44px; border-radius: 50%; font-size: 1.1rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.yw-lightbox__nav:hover { background: rgba(255,255,255,0.3); }
.yw-lightbox__nav--prev { left: 16px; }
.yw-lightbox__nav--next { right: 16px; }
.yw-lightbox__counter {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  color: rgba(255,255,255,0.7); font-size: 0.85rem; font-weight: 600;
}

/* CTA Buttons */
.yw-cta {
  display: flex; gap: 10px; margin: 10px 0 6px; flex-wrap: wrap;
}
.yw-cta__btn {
  flex: 1; min-width: 160px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 18px; border: none; border-radius: 10px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.2s; color: #fff;
}
.yw-cta__btn small {
  font-size: 11px; font-weight: 400; opacity: 0.8; margin-left: 2px;
}
.yw-cta__btn--virtual {
  background: linear-gradient(135deg, #1DA53F, #168a34);
  box-shadow: 0 2px 8px rgba(29,165,63,.3);
}
.yw-cta__btn--virtual:hover {
  background: linear-gradient(135deg, #168a34, #117a2b);
  box-shadow: 0 4px 14px rgba(29,165,63,.4);
  transform: translateY(-1px);
}
.yw-cta__btn--physical {
  background: transparent;
  color: #1DA53F;
  border: 2px solid #1DA53F;
  box-shadow: none;
}
.yw-cta__btn--physical:hover {
  background: rgba(29,165,63,.08);
  color: #168a34;
  border-color: #168a34;
  transform: translateY(-1px);
}

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
.yw-act--fav { gap: 4px; }
.yw-act--fav svg { transition: transform 0.2s; }
.yw-act--fav:hover svg { transform: scale(1.2); }
.yw-act--fav-on { background: #fef2f2; color: #ef4444; }
.yw-act--fav-on:hover { background: #fee2e2; }
.yw-act__count { font-size: 11px; color: #888; margin-left: 2px; }
.yw-act--report { margin-left: auto; }
.yw-act--report:hover { background: #fef2f2; color: #dc2626; }

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
.yw-vcard__locked--active { pointer-events: none; }
.yw-vcard__locked--active .yw-vcard__thumb { filter: brightness(0.6); }
.yw-vcard__play--pulse {
  animation: yw-pulse 1.5s ease-in-out infinite;
  background: rgba(29,165,63,0.9) !important;
}
@keyframes yw-pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.15); } }
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
.yw-right {
  min-width: 0;
  position: sticky;
  top: 0;
  max-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Filters */
.yw-filters {
  display: flex; flex-wrap: wrap; gap: 6px;
  padding: 2px 0 12px; margin-bottom: 0;
  border-bottom: 1px solid #e5e5e5;
  background: #f9f9f9; z-index: 5;
  flex-shrink: 0;
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
.yw-suggestions {
  display: flex; flex-direction: column; gap: 8px;
  flex: 1; overflow-y: auto; padding-top: 12px;
  scrollbar-width: thin; scrollbar-color: #d4d4d4 transparent;
}
.yw-suggestions::-webkit-scrollbar { width: 5px; }
.yw-suggestions::-webkit-scrollbar-track { background: transparent; }
.yw-suggestions::-webkit-scrollbar-thumb { background: #d4d4d4; border-radius: 3px; }
.yw-suggestions::-webkit-scrollbar-thumb:hover { background: #b0b0b0; }

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

/* ===== TEASER ===== */
.yw-vcard__teaser {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  -webkit-user-select: none;
  user-select: none;
  background: #000;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}
.yw-vcard__teaser video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.yw-teaser-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(180deg, rgba(0,0,0,.6) 0%, transparent 100%);
  z-index: 3;
}
.yw-teaser-bar--hero { padding: 10px 16px; }
.yw-teaser-bar--hero .yw-teaser-bar__label { font-size: 13px; }
.yw-teaser-bar--hero .yw-teaser-bar__track { height: 4px; }
.yw-teaser-bar__label {
  font-size: 11px; font-weight: 600; color: #fff;
  white-space: nowrap; text-shadow: 0 1px 3px rgba(0,0,0,.5);
}
.yw-teaser-bar__track {
  flex: 1; height: 3px; border-radius: 2px;
  background: rgba(255,255,255,.25); overflow: hidden;
}
.yw-teaser-bar__fill {
  height: 100%; width: 0%;
  background: #1DA53F; border-radius: 2px;
  animation: teaser-progress linear forwards;
}
@keyframes teaser-progress {
  from { width: 0%; }
  to { width: 100%; }
}

/* Teaser overlay */
.yw-teaser-ov {
  position: absolute; inset: 0; z-index: 5;
  background: rgba(0, 0, 0, 0.82);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  animation: yw-ov-fadein 0.4s ease;
}
@keyframes yw-ov-fadein {
  from { opacity: 0; }
  to { opacity: 1; }
}

.yw-teaser-ov__content {
  text-align: center;
  padding: 24px 20px;
  max-width: 380px;
}
.yw-teaser-ov__icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: rgba(29, 165, 63, 0.8);
  display: inline-flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
  animation: yw-icon-bounce 0.5s ease;
}
@keyframes yw-icon-bounce {
  0% { transform: scale(0.5); opacity: 0; }
  60% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

.yw-teaser-ov__title {
  font-size: 18px; font-weight: 700; color: #fff;
  margin: 0 0 8px; text-shadow: 0 1px 4px rgba(0,0,0,.3);
}
.yw-teaser-ov__desc {
  font-size: 13px; color: rgba(255,255,255,.85);
  margin: 0 0 18px; line-height: 1.5;
}
.yw-teaser-ov__desc strong { color: #4ade80; }

.yw-teaser-ov__btns {
  display: flex; flex-direction: column; gap: 8px;
  margin-bottom: 12px;
}

.yw-teaser-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 11px 20px; border: none; border-radius: 10px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.2s; width: 100%;
}
.yw-teaser-btn--primary {
  background: #1DA53F; color: #fff;
  box-shadow: 0 2px 10px rgba(29,165,63,.4);
}
.yw-teaser-btn--primary:hover {
  background: #168a34; transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(29,165,63,.5);
}
.yw-teaser-btn--secondary {
  background: rgba(255,255,255,.15); color: #fff;
  border: 1px solid rgba(255,255,255,.25);
}
.yw-teaser-btn--secondary:hover {
  background: rgba(255,255,255,.25);
}
.yw-teaser-btn--pack {
  background: linear-gradient(135deg, #ea580c, #c2410c);
  color: #fff;
  box-shadow: 0 2px 10px rgba(234,88,12,.4);
}
.yw-teaser-btn--pack:hover {
  background: linear-gradient(135deg, #c2410c, #9a3412);
  transform: translateY(-1px);
}
.yw-teaser-btn--unlock {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  box-shadow: 0 2px 10px rgba(37,99,235,.4);
}
.yw-teaser-btn--unlock:hover {
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
  transform: translateY(-1px);
}
.yw-teaser-btn--unlock:disabled {
  opacity: 0.7; cursor: wait; transform: none;
}

.yw-teaser-ov__sub {
  font-size: 11px; color: rgba(255,255,255,.6);
  margin: 0; line-height: 1.4;
}
.yw-teaser-ov__sub strong { color: rgba(255,255,255,.85); }

/* ===== PAYWALL RICH ===== */
.yw-pw-rich { text-align: center; padding: 10px 0 4px; }

.yw-pw-rich__key {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 88px; height: 88px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37,99,235,.08), rgba(37,99,235,.02));
  margin-bottom: 12px;
  animation: yw-key-float 2.5s ease-in-out infinite;
}
.yw-pw-rich__key-img { width: 56px; height: 56px; object-fit: contain; transition: all 0.4s; }
.yw-pw-rich__badge {
  position: absolute; top: 2px; right: 2px;
  width: 26px; height: 26px; border-radius: 50%;
  background: #2563eb; color: #fff;
  font-size: 12px; font-weight: 800; line-height: 26px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(37,99,235,.4);
}

.yw-pw-rich__key--consuming .yw-pw-rich__key-img {
  animation: yw-key-consume 0.6s ease-out forwards;
}
.yw-pw-rich__key--consuming .yw-pw-rich__badge {
  animation: yw-badge-pop 0.4s ease-out forwards;
}

@keyframes yw-key-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
@keyframes yw-key-consume {
  0% { transform: scale(1) rotate(0deg); opacity: 1; }
  50% { transform: scale(1.2) rotate(-10deg); opacity: 0.7; }
  100% { transform: scale(0.6) rotate(15deg); opacity: 0.3; }
}
@keyframes yw-badge-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.5); }
  100% { transform: scale(1); background: #dc2626; }
}

.yw-pw-rich__title { font-size: 17px; font-weight: 700; color: #0f0f0f; margin: 0 0 6px; }
.yw-pw-rich__desc { font-size: 13px; color: #606060; margin: 0 0 14px; line-height: 1.5; }
.yw-pw-rich__free-hint {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 20px; font-size: 12px; color: #15803d;
}

/* ===== PAYWALL SIMPLE (no pack, login, etc.) ===== */
.yw-pw {
  text-align: center; padding: 16px 12px 8px;
  display: flex; flex-direction: column; align-items: center;
}
.yw-pw__icon {
  font-size: 44px; color: #1DA53F; margin-bottom: 16px;
  width: 72px; height: 72px; border-radius: 50%;
  background: rgba(29, 165, 63, 0.08);
  display: flex; align-items: center; justify-content: center;
}
.yw-pw p { font-size: 14px; color: #272727; margin: 0 0 6px; }
.yw-pw__sub { font-size: 12px; color: #999; }
.yw-pw__btn { background: #1DA53F !important; border-color: #1DA53F !important; }
.yw-pw__pack {
  display: flex; flex-direction: column; gap: 4px;
  background: #f8f9fa; border: 2px solid #1DA53F; border-radius: 10px; padding: 14px; margin-top: 14px;
}
.yw-pw__pack-price { font-size: 22px; font-weight: 700; color: #1DA53F; }
.yw-pw__pack-desc { font-size: 12px; color: #606060; }

/* ===== VISIT MODAL ===== */
.yw-visit-modal__loading,
.yw-visit-modal__empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; padding: 28px 0; color: #606060; text-align: center;
}
.yw-visit-modal__empty p { font-size: 14px; margin: 0; }

/* Agent info in modal */
.yw-visit-agent {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; background: #f8f9fa; border-radius: 10px; margin-bottom: 12px;
}
.yw-visit-agent__avatar {
  width: 40px; height: 40px; border-radius: 50%; background: #e8e8e8; overflow: hidden;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.yw-visit-agent__avatar img { width: 100%; height: 100%; object-fit: cover; }
.yw-visit-agent__avatar .pi-user { font-size: 18px; color: #aaa; }
.yw-visit-agent__info { display: flex; flex-direction: column; gap: 2px; }
.yw-visit-agent__name { font-size: 14px; font-weight: 600; color: #0f0f0f; }
.yw-visit-agent__contact { font-size: 12px; color: #606060; display: flex; align-items: center; gap: 4px; }
.yw-visit-agent__contact i { font-size: 11px; }

/* Free visit badge */
.yw-visit-free {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border: 1px solid #fde68a; border-radius: 10px; margin-bottom: 14px;
}
.yw-visit-free__icon { width: 32px; height: 32px; object-fit: contain; flex-shrink: 0; }
.yw-visit-free__text { display: flex; flex-direction: column; }
.yw-visit-free__text strong { font-size: 13px; color: #92400e; }
.yw-visit-free__text span { font-size: 11px; color: #a16207; }

.yw-visit-modal__hint { font-size: 14px; color: #272727; margin: 0 0 10px; font-weight: 500; }
.yw-visit-slots { display: flex; flex-direction: column; gap: 6px; max-height: 260px; overflow-y: auto; }
.yw-visit-slot {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border: 2px solid #e5e5e5; border-radius: 10px;
  cursor: pointer; transition: all 0.15s; background: #fff;
}
.yw-visit-slot:hover { border-color: #1DA53F; background: #f0fdf4; }
.yw-visit-slot--on { border-color: #1DA53F; background: #f0fdf4; }
.yw-visit-slot__radio { display: none; }
.yw-visit-slot__body { display: flex; flex-direction: column; flex: 1; }
.yw-visit-slot__day { font-size: 14px; font-weight: 600; color: #0f0f0f; }
.yw-visit-slot__time { font-size: 12px; color: #606060; }
.yw-visit-slot__check { color: #1DA53F; font-size: 18px; }
.yw-visit-modal__note { margin-top: 14px; }
.yw-visit-modal__note label { display: block; font-size: 13px; font-weight: 500; color: #272727; margin-bottom: 4px; }
.yw-visit-modal__note small { color: #909090; font-weight: 400; }
.yw-visit-modal__note textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; font-family: inherit; resize: vertical; box-sizing: border-box;
}
.yw-visit-modal__note textarea:focus { outline: none; border-color: #1DA53F; }
.yw-visit-modal__info {
  display: flex; align-items: flex-start; gap: 8px;
  margin-top: 12px; padding: 10px 12px; background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 8px; font-size: 12px; color: #166534; line-height: 1.4;
}
.yw-visit-modal__info .pi-info-circle { flex-shrink: 0; margin-top: 1px; color: #1DA53F; }

/* ===== REPORT MODAL ===== */
.yw-report__hint { font-size: 14px; color: #272727; margin: 0 0 12px; }
.yw-report__reasons { display: flex; flex-direction: column; gap: 4px; }
.yw-report__reason {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border: 1px solid #e5e5e5; border-radius: 8px;
  cursor: pointer; transition: all 0.15s; font-size: 13px; color: #272727;
}
.yw-report__reason:hover { border-color: #dc2626; background: #fef2f2; }
.yw-report__reason--on { border-color: #dc2626; background: #fef2f2; font-weight: 500; }
.yw-report__reason input { accent-color: #dc2626; }
.yw-report__desc { margin-top: 14px; }
.yw-report__desc label { display: block; font-size: 13px; font-weight: 500; color: #272727; margin-bottom: 4px; }
.yw-report__desc small { color: #909090; font-weight: 400; }
.yw-report__desc textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; font-family: inherit; resize: vertical; box-sizing: border-box;
}
.yw-report__desc textarea:focus { outline: none; border-color: #dc2626; }

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {
  .yw-grid { grid-template-columns: 1fr; }
  .yw-right {
    position: static; max-height: none; overflow: visible;
  }
  .yw-suggestions {
    flex-direction: row; flex-wrap: wrap; gap: 8px;
    max-height: 600px; overflow-y: auto; padding-top: 12px;
  }
  .yw-sg { min-width: 300px; flex: 1; }
}

@media (max-width: 640px) {
  .yw-player__frame { border-radius: 0; max-height: 260px; }
  .yw-title { font-size: 15px; padding: 0 12px; }
  .yw-meta { padding: 0 12px; }
  .yw-conditions { margin-left: 12px; margin-right: 12px; }
  .yw-conditions__other { padding: 0 12px; }
  .yw-actions { margin: 0 12px; }
  .yw-agent { margin: 0 12px; }
  .yw-desc { margin: 10px 12px; }
  .yw-cta { padding: 0 12px; flex-direction: column; }
  .yw-cta__btn { min-width: 0; padding: 10px 14px; font-size: 13px; }
  .yw-price { font-size: 15px; }
  .yw-act span { display: none; }
  .yw-act { padding: 5px 8px; }
  .yw-vids { padding: 10px 12px 0; }
  .yw-vids__grid { grid-template-columns: 1fr; }
  .yw-right { padding: 0 12px; }
  .yw-suggestions { flex-direction: column; max-height: 500px; }
  .yw-sg { min-width: 0; }
  .yw-sg__thumb { width: 130px; height: 73px; }
  .yw-teaser-ov__content { padding: 16px 14px; }
  .yw-teaser-ov__title { font-size: 15px; }
  .yw-teaser-ov__desc { font-size: 12px; }
  .yw-teaser-btn { font-size: 13px; padding: 10px 16px; }
}
</style>
