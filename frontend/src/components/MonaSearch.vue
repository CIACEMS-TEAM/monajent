<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePublicStore } from '@/Stores/public'
import { useToast } from 'vue-toastification'
import notifSound from '@/assets/media/discord-sounds.mp3'

const router = useRouter()
const route = useRoute()
const pub = usePublicStore()
const toast = useToast()

type Phase = 'welcome' | 'recording' | 'review' | 'analyzing' | 'done'

const open = ref(false)
const dismissed = ref(false)
const phase = ref<Phase>('welcome')
const transcript = ref('')
const interimText = ref('')
const searchResult = ref<{
  query_params?: Record<string, unknown>
  search?: string | null
  ordering?: string | null
} | null>(null)
const resultCount = ref(0)
const locationTotal = ref(-1)
const errorMsg = ref('')
const muted = ref(false)
const speaking = ref(false)
const inviteBubble = ref(false)
const chatInput = ref('')
let inviteShowTimer: ReturnType<typeof setTimeout> | null = null
let inviteHideTimer: ReturnType<typeof setTimeout> | null = null
let inviteLoopTimer: ReturnType<typeof setInterval> | null = null
const notifAudio = typeof Audio !== 'undefined' ? new Audio(notifSound) : null

function getGreeting(): string {
  const h = new Date().getHours()
  if (h >= 5 && h < 12) return 'Bonjour'
  if (h >= 12 && h < 18) return 'Bon après-midi'
  return 'Bonsoir'
}

function playNotif() {
  if (!notifAudio) return
  notifAudio.currentTime = 0
  notifAudio.volume = 0.5
  notifAudio.play().catch(() => {})
}

let recognition: any = null
let baseTranscript = ''
let silenceTimer: ReturnType<typeof setTimeout> | null = null
const SILENCE_MS = 3500

function isMobile(): boolean {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
}

function clearSilenceTimer() {
  if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null }
}

function resetSilenceTimer() {
  clearSilenceTimer()
  if (isMobile() && phase.value === 'recording') {
    silenceTimer = setTimeout(() => {
      if (phase.value === 'recording' && transcript.value.trim()) {
        stopRecording()
      }
    }, SILENCE_MS)
  }
}

const displayText = computed(() => {
  if (interimText.value) return transcript.value + ' ' + interimText.value
  return transcript.value
})

const appliedFilters = computed(() => {
  if (!searchResult.value?.query_params) return []
  const labels: Record<string, string> = {
    listing_type: 'Type', city: 'Ville', city__icontains: 'Ville',
    neighborhood: 'Quartier', neighborhood__icontains: 'Quartier',
    price__gte: 'Prix min', price__lte: 'Prix max',
    rooms__gte: 'Pièces min', rooms__lte: 'Pièces max',
    bedrooms__gte: 'Chambres min', bedrooms__lte: 'Chambres max',
    surface_m2__gte: 'Surface min', surface_m2__lte: 'Surface max',
    furnishing: 'Ameublement',
  }
  const displayValues: Record<string, (v: unknown) => string> = {
    listing_type: v => v === 'LOCATION' ? 'Location' : 'Vente',
    furnishing: v => {
      const m: Record<string, string> = { FURNISHED: 'Meublé', UNFURNISHED: 'Non meublé', SEMI_FURNISHED: 'Semi-meublé' }
      return m[String(v)] || String(v)
    },
  }
  const out: { label: string; value: string }[] = []
  for (const [k, v] of Object.entries(searchResult.value.query_params)) {
    if (v === null || v === undefined || v === '') continue
    const label = labels[k] || k
    const display = displayValues[k] ? displayValues[k](v) : String(v)
    out.push({ label, value: display })
  }
  if (searchResult.value.search) {
    out.push({ label: 'Mots-clés', value: searchResult.value.search })
  }
  return out
})

// ─── Synthèse vocale ─────────────────────────────────────────

function monaSay(text: string) {
  if (muted.value || !window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = 'fr-FR'
  utt.rate = 1.05
  utt.pitch = 1.1

  const voices = window.speechSynthesis.getVoices()
  const frVoice = voices.find(v => v.lang.startsWith('fr') && v.name.toLowerCase().includes('female'))
    || voices.find(v => v.lang.startsWith('fr'))
  if (frVoice) utt.voice = frVoice

  utt.onstart = () => { speaking.value = true }
  utt.onend = () => { speaking.value = false }
  utt.onerror = () => { speaking.value = false }
  window.speechSynthesis.speak(utt)
}

function monaStop() {
  if (window.speechSynthesis) window.speechSynthesis.cancel()
  speaking.value = false
}

function toggleMute() {
  muted.value = !muted.value
  if (muted.value) monaStop()
}

watch(open, (isOpen) => {
  if (isOpen && phase.value === 'welcome') {
    setTimeout(() => {
      monaSay(`${getGreeting()} ! Décrivez le bien que vous recherchez, votre budget et la localisation souhaitée.`)
    }, 400)
  }
  if (!isOpen) monaStop()
})

function toggle() {
  inviteBubble.value = false
  clearInviteLoop()
  if (dismissed.value) {
    dismissed.value = false
    open.value = true
    return
  }
  open.value = !open.value
}

defineExpose({ toggle })

function dismiss() {
  stopRecording()
  monaStop()
  open.value = false
  dismissed.value = true
}

function reset() {
  phase.value = 'welcome'
  transcript.value = ''
  interimText.value = ''
  searchResult.value = null
  resultCount.value = 0
  locationTotal.value = -1
  errorMsg.value = ''
  baseTranscript = ''
  pub.clearMonaSearch()
  clearSilenceTimer()
  stopRecording()
  monaStop()
}

// ─── Reconnaissance vocale (continue) ───────────────────────

function getSpeechRecognition() {
  const w = window as any
  const SR = w.SpeechRecognition || w.webkitSpeechRecognition
  if (!SR) return null
  return new SR()
}

function startRecording() {
  const r = getSpeechRecognition()
  if (!r) {
    toast.error('La reconnaissance vocale n\'est pas supportée par ce navigateur.')
    return
  }

  const mobile = isMobile()
  r.lang = 'fr-FR'
  r.continuous = !mobile
  r.interimResults = true

  r.onresult = (event: any) => {
    let sessionFinal = ''
    let interimPart = ''
    for (let i = 0; i < event.results.length; i++) {
      const result = event.results[i]
      if (result.isFinal) {
        sessionFinal += result[0].transcript + ' '
      } else {
        interimPart += result[0].transcript
      }
    }
    transcript.value = (baseTranscript + ' ' + sessionFinal).trim()
    interimText.value = interimPart
    if (sessionFinal || interimPart) resetSilenceTimer()
  }

  r.onerror = (e: any) => {
    if (e.error === 'no-speech' || e.error === 'aborted') return
    toast.error('Erreur micro : ' + e.error)
    phase.value = transcript.value.trim() ? 'review' : 'welcome'
  }

  r.onend = () => {
    if (phase.value !== 'recording') return
    baseTranscript = transcript.value
    interimText.value = ''
    try {
      r.start()
      resetSilenceTimer()
    } catch {
      if (baseTranscript.trim()) {
        phase.value = 'review'
        monaSay('Très bien ! Vous pouvez relire et modifier le texte, puis appuyez sur Rechercher.')
      } else {
        phase.value = 'welcome'
      }
    }
  }

  recognition = r
  baseTranscript = ''
  transcript.value = ''
  interimText.value = ''
  phase.value = 'recording'
  monaStop()
  clearSilenceTimer()

  try {
    r.start()
    resetSilenceTimer()
  } catch {
    toast.error('Impossible d\'activer le microphone.')
    phase.value = 'welcome'
  }
}

function stopRecording() {
  clearSilenceTimer()
  const wasRecording = phase.value === 'recording'
  if (wasRecording) phase.value = '_stopping' as Phase
  if (recognition) {
    try { recognition.stop() } catch { /* ignore */ }
    recognition = null
  }
  interimText.value = ''
  baseTranscript = ''
  if (wasRecording) {
    if (transcript.value.trim()) {
      phase.value = 'review'
      monaSay('Très bien ! Vous pouvez relire et modifier le texte, puis appuyez sur Rechercher.')
    } else {
      phase.value = 'welcome'
    }
  }
}

// ─── Analyse IA ──────────────────────────────────────────────

function intentToParams(intent: {
  query_params?: Record<string, unknown>
  search?: string | null
  ordering?: string | null
}): Record<string, string> {
  const out: Record<string, string> = {}
  if (intent.query_params) {
    for (const [k, v] of Object.entries(intent.query_params)) {
      if (v !== null && v !== undefined && v !== '') out[k] = String(v)
    }
  }
  if (intent.search) out.search = intent.search
  if (intent.ordering) out.ordering = intent.ordering
  return out
}

const emptyLocationName = computed(() => {
  if (resultCount.value > 0) return ''
  const city = appliedFilters.value.find(f => f.label === 'Ville')
  const quartier = appliedFilters.value.find(f => f.label === 'Quartier')
  const keywords = appliedFilters.value.find(f => f.label === 'Mots-clés')
  if (quartier) return quartier.value
  if (city) return city.value
  if (keywords) return keywords.value
  return ''
})

const narrowingHintText = computed(() => _narrowingHint(appliedFilters.value))

function hasFilterType(kind: 'price' | 'rooms' | 'type' | 'furnishing'): boolean {
  const map: Record<string, string[]> = {
    price: ['Prix min', 'Prix max'],
    rooms: ['Pièces min', 'Pièces max', 'Chambres min', 'Chambres max'],
    type: ['Type'],
    furnishing: ['Ameublement'],
  }
  return appliedFilters.value.some(f => map[kind]?.includes(f.label))
}

function _narrowingHint(filters: { label: string; value: string }[]): string {
  const hasPrice = filters.some(f => f.label === 'Prix min' || f.label === 'Prix max')
  const hasRooms = filters.some(f => f.label === 'Pièces min' || f.label === 'Pièces max')
  const hasBedrooms = filters.some(f => f.label === 'Chambres min' || f.label === 'Chambres max')
  const hasType = filters.some(f => f.label === 'Type')
  const hasFurnishing = filters.some(f => f.label === 'Ameublement')

  const hints: string[] = []
  if (hasPrice) hints.push('le budget')
  if (hasRooms || hasBedrooms) hints.push('le nombre de pièces')
  if (hasType) hints.push('le type de bien')
  if (hasFurnishing) hints.push('l\'ameublement')

  if (hints.length === 0) return 'vos critères'
  if (hints.length === 1) return hints[0]
  return hints.slice(0, -1).join(', ') + ' et ' + hints[hints.length - 1]
}

function buildDoneSpeech(count: number, filters: { label: string; value: string }[], locTotal: number): string {
  const parts: string[] = []
  const city = filters.find(f => f.label === 'Ville')
  const quartier = filters.find(f => f.label === 'Quartier')
  const type = filters.find(f => f.label === 'Type')
  const keywords = filters.find(f => f.label === 'Mots-clés')
  const locationName = quartier?.value || city?.value || keywords?.value || ''

  if (count === 0) {
    if (locTotal > 0 && locationName) {
      const s = locTotal > 1 ? 's' : ''
      parts.push(`Il y a ${locTotal} bien${s} disponible${s} dans la zone « ${locationName} »,`)
      parts.push(`mais aucun ne correspond à ${_narrowingHint(filters)}.`)
      parts.push('Essayez d\'ajuster vos critères pour voir les biens disponibles dans cette zone.')
    } else if (locationName) {
      parts.push(`Il n'y a pas encore de biens enregistrés dans la zone « ${locationName} » sur notre plateforme.`)
      parts.push('Nos agents y ajoutent de nouvelles annonces régulièrement.')
      parts.push('Vous pouvez essayer une zone proche ou élargir votre recherche.')
    } else {
      parts.push('Aucune annonce ne correspond à vos critères pour le moment.')
      parts.push('Essayez de modifier ou d\'élargir votre recherche.')
    }
  } else if (count === 1) {
    parts.push('J\'ai trouvé 1 annonce correspondant à vos critères.')
  } else {
    parts.push(`J'ai trouvé ${count} annonces correspondant à vos critères.`)
  }

  if (count > 0) {
    if (city && type) {
      parts.push(`${type.value} à ${city.value}.`)
    } else if (city) {
      parts.push(`À ${city.value}.`)
    }
    parts.push('Les résultats sont affichés ci-dessous.')
  }

  return parts.join(' ')
}

const RESTRICTING_KEYS = new Set([
  'price__gte', 'price__lte',
  'rooms__gte', 'rooms__lte',
  'bedrooms__gte', 'bedrooms__lte',
  'surface_m2__gte', 'surface_m2__lte',
  'furnishing', 'listing_type',
])

async function analyze() {
  const text = transcript.value.trim()
  if (!text) return

  phase.value = 'analyzing'
  errorMsg.value = ''
  locationTotal.value = -1

  try {
    const intent = await pub.fetchSearchIntent(text)
    searchResult.value = intent
    const params = intentToParams(intent)

    if (route.path !== '/home') {
      await router.push('/home')
    }

    const listings = await pub.fetchListings(params)
    resultCount.value = Array.isArray(listings) ? listings.length : pub.listings.length

    if (resultCount.value === 0) {
      const hasLocation = !!params.search
      const hasRestricting = Object.keys(params).some(k => RESTRICTING_KEYS.has(k))

      if (hasLocation && hasRestricting) {
        try {
          locationTotal.value = await pub.countListings({ search: params.search })
        } catch { locationTotal.value = -1 }
      }
    }

    pub.setMonaSearch(text)
    phase.value = 'done'
    monaSay(buildDoneSpeech(resultCount.value, appliedFilters.value, locationTotal.value))
  } catch (e: any) {
    const msg = e?.response?.data?.detail
    errorMsg.value = typeof msg === 'string' ? msg : 'Mona rencontre un problème temporaire. Veuillez réessayer.'
    phase.value = 'review'
    monaSay('Désolée, je n\'ai pas pu comprendre votre recherche. Vous pouvez modifier le texte et réessayer.')
  }
}

function closeAndViewResults() {
  open.value = false
}

function editTranscript(e: Event) {
  transcript.value = (e.target as HTMLTextAreaElement).value
}

function handleChatSubmit() {
  const text = chatInput.value.trim()
  if (!text) return
  transcript.value = text
  chatInput.value = ''
  analyze()
}

function handleFabSubmit() {
  const text = chatInput.value.trim()
  if (!text) { toggle(); return }
  dismissed.value = false
  transcript.value = text
  chatInput.value = ''
  analyze()
  open.value = true
}

function handleFabVoice() {
  inviteBubble.value = false
  clearInviteLoop()
  dismissed.value = false
  startRecording()
  open.value = true
}

function formatFilterValue(label: string, value: string): string {
  if (['Prix min', 'Prix max'].includes(label)) {
    const n = Number(value)
    return isNaN(n) ? value : new Intl.NumberFormat('fr-FR').format(n) + ' F'
  }
  return value
}

function dismissInvite() {
  inviteBubble.value = false
  if (inviteHideTimer) { clearTimeout(inviteHideTimer); inviteHideTimer = null }
}

function showInviteBubble() {
  if (open.value || dismissed.value) return
  if (!route.path.startsWith('/home')) { clearInviteLoop(); return }
  inviteBubble.value = true
  playNotif()
  inviteHideTimer = setTimeout(() => { inviteBubble.value = false }, 5000)
}

function clearInviteLoop() {
  if (inviteShowTimer) { clearTimeout(inviteShowTimer); inviteShowTimer = null }
  if (inviteHideTimer) { clearTimeout(inviteHideTimer); inviteHideTimer = null }
  if (inviteLoopTimer) { clearInterval(inviteLoopTimer); inviteLoopTimer = null }
}

onMounted(() => {
  if (!localStorage.getItem('monajent_onboarding_done')) return
  inviteShowTimer = setTimeout(() => {
    showInviteBubble()
    inviteLoopTimer = setInterval(showInviteBubble, 40000)
  }, 1500)
})

onBeforeUnmount(() => {
  clearInviteLoop()
  clearSilenceTimer()
  stopRecording()
  monaStop()
})
</script>

<template>
  <!-- FAB (mobile only — hidden on desktop) -->
  <button
    v-if="!open"
    class="ms-fab"
    :class="{ 'ms-fab--hidden': dismissed }"
    data-tour="mona"
    @click="toggle"
    title="Mona — Recherche IA"
  >
    <span class="ms-fab__icon">
      <svg viewBox="0 0 24 24" width="26" height="26" fill="none">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="#fff"/>
        <path d="M13.5 7.5l.9-1.9 1.9-.9-1.9-.9-.9-1.9-.9 1.9-1.9.9 1.9.9zm4.3 2.1l-.6 1.3-1.3.6 1.3.6.6 1.3.6-1.3 1.3-.6-1.3-.6zM9.2 7.6L8 10l-2.4 1.2L8 12.4 9.2 14.8l1.2-2.4 2.4-1.2-2.4-1.2z" fill="#1DA53F"/>
      </svg>
    </span>
  </button>

  <!-- Desktop: barre de saisie centrée (style ChatGPT/Gemini) -->
  <Transition name="ms-bar">
    <div v-if="!open" class="ms-fab-bar" data-tour="mona">
      <div class="ms-fab-bar__inner">
        <span class="ms-fab-bar__avatar">M</span>
        <input
          v-model="chatInput"
          class="ms-fab-bar__input"
          placeholder="Demandez à Mona..."
          @keyup.enter="handleFabSubmit"
        />
        <button class="ms-fab-bar__voice" @click="handleFabVoice" title="Recherche vocale">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path fill="currentColor" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
        </button>
      </div>
    </div>
  </Transition>

  <!-- Invite bubble -->
  <Transition name="ms-invite">
    <div v-if="inviteBubble && !open" class="ms-invite" @click="dismissInvite(); toggle()">
      <svg class="ms-invite__icon" viewBox="0 0 24 24" width="18" height="18"><path fill="#1DA53F" d="M12 1a9 9 0 00-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2a7 7 0 0114 0v2h-4v8h4v1h-7v2h7c1.66 0 3-1.34 3-3V10a9 9 0 00-9-9z"/></svg>
      <p class="ms-invite__text">{{ getGreeting() }} ! Dites-moi ce que vous cherchez, je vous trouve le bien idéal !</p>
      <button class="ms-invite__close" @click.stop="dismissInvite" aria-label="Fermer">&times;</button>
    </div>
  </Transition>

  <!-- Panel -->
  <Transition name="ms-slide">
    <div v-if="open" class="ms-panel">
      <div class="ms-panel__header">
        <div class="ms-panel__brand">
          <span class="ms-panel__avatar">M</span>
          <div>
            <span class="ms-panel__name">Mona</span>
            <span class="ms-panel__sub">
              <template v-if="speaking">
                <span class="ms-panel__speaking-dot"></span> Parle...
              </template>
              <template v-else>Recherche IA</template>
            </span>
          </div>
        </div>
        <div class="ms-panel__header-actions">
          <button
            class="ms-panel__btn-icon"
            :class="{ 'ms-panel__btn-icon--muted': muted }"
            @click="toggleMute"
            :title="muted ? 'Activer la voix' : 'Couper la voix'"
          >
            <svg v-if="!muted" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0014 8.77v6.46A4.47 4.47 0 0016.5 12zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
            <svg v-else viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M16.5 12A4.5 4.5 0 0014 8.77v2.06l2.47 2.47c.03-.1.03-.2.03-.3zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.796 8.796 0 0021 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06a8.99 8.99 0 003.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
          </button>
          <button class="ms-panel__btn-icon" @click="reset" title="Nouvelle recherche">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M17.65 6.35A7.96 7.96 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
          </button>
          <button class="ms-panel__btn-icon" @click="dismiss" title="Fermer">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
      </div>

      <div class="ms-panel__body">
        <!-- WELCOME -->
        <template v-if="phase === 'welcome'">
          <div class="ms-welcome">
            <p class="ms-welcome__msg">
              Quel bien recherchez-vous ?
            </p>
            <p class="ms-welcome__hint">
              Décrivez ce que vous cherchez : type de bien, budget, ville, quartier...
              Je trouverai les annonces qui correspondent.
            </p>
          </div>

          <div class="ms-welcome-actions">
            <div class="ms-actions">
              <button class="ms-mic-btn" @click="startRecording">
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#fff" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/><path fill="#fff" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
              </button>
              <span class="ms-actions__label">Parler</span>
            </div>

            <div class="ms-alt-actions">
              <button class="ms-alt-btn" @click="phase = 'review'">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1.003 1.003 0 000-1.42l-2.34-2.34a1.003 1.003 0 00-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z"/></svg>
                Saisir un texte
              </button>
            </div>
          </div>
        </template>

        <!-- RECORDING -->
        <template v-if="phase === 'recording'">
          <div class="ms-recording">
            <p class="ms-recording__tip">Je vous écoute... Décrivez votre recherche.</p>
            <div class="ms-recording__bubble" v-if="displayText">
              <p>{{ displayText }}<span class="ms-recording__cursor">|</span></p>
            </div>
            <div class="ms-recording__bubble ms-recording__bubble--empty" v-else>
              <p>En attente de votre voix...</p>
            </div>
          </div>
          <div class="ms-actions">
            <button class="ms-mic-btn ms-mic-btn--active" @click="stopRecording">
              <svg viewBox="0 0 24 24" width="32" height="32"><rect x="6" y="6" width="12" height="12" rx="2" fill="#fff"/></svg>
            </button>
            <span class="ms-actions__label">Appuyez pour terminer</span>
          </div>
        </template>

        <!-- REVIEW -->
        <template v-if="phase === 'review'">
          <div class="ms-review">
            <p class="ms-review__label">Votre recherche :</p>
            <textarea
              class="ms-review__textarea"
              :value="transcript"
              @input="editTranscript"
              rows="4"
              placeholder="Ex : Je cherche un 3 pièces à Cocody, budget 250 000 francs maximum, meublé si possible."
            />
            <p v-if="errorMsg" class="ms-review__error">{{ errorMsg }}</p>
          </div>
          <div class="ms-review__actions">
            <button class="ms-btn ms-btn--secondary" @click="startRecording">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path fill="currentColor" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
              Re-dicter
            </button>
            <button
              class="ms-btn ms-btn--primary"
              :disabled="!transcript.trim()"
              @click="analyze"
            >
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
              Rechercher avec Mona
            </button>
          </div>
        </template>

        <!-- ANALYZING -->
        <template v-if="phase === 'analyzing'">
          <div class="ms-analyzing">
            <div class="ms-analyzing__scene">
              <div class="ms-analyzing__grid">
                <div class="ms-analyzing__block ms-analyzing__block--1"></div>
                <div class="ms-analyzing__block ms-analyzing__block--2"></div>
                <div class="ms-analyzing__block ms-analyzing__block--3"></div>
                <div class="ms-analyzing__block ms-analyzing__block--4"></div>
                <div class="ms-analyzing__block ms-analyzing__block--5"></div>
                <div class="ms-analyzing__block ms-analyzing__block--6"></div>
                <div class="ms-analyzing__block ms-analyzing__block--7"></div>
                <div class="ms-analyzing__block ms-analyzing__block--8"></div>
                <div class="ms-analyzing__block ms-analyzing__block--9"></div>
              </div>
              <div class="ms-analyzing__loupe">
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#1DA53F" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
              </div>
            </div>
            <p class="ms-analyzing__text">Mona recherche pour vous...</p>
            <p class="ms-analyzing__sub">Analyse des critères &amp; tri des annonces</p>
          </div>
        </template>

        <!-- DONE -->
        <template v-if="phase === 'done'">
          <div class="ms-done">
            <div class="ms-done__check">
              <svg v-if="resultCount > 0" viewBox="0 0 24 24" width="36" height="36"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
              <svg v-else viewBox="0 0 24 24" width="36" height="36"><circle cx="12" cy="12" r="11" fill="#f59e0b"/><path fill="#fff" d="M12 5.99L19.53 19H4.47L12 5.99M12 2L1 21h22L12 2zm1 14h-2v2h2v-2zm0-6h-2v4h2v-4z"/></svg>
            </div>
            <p class="ms-done__title">
              {{ resultCount > 0 ? `${resultCount} annonce${resultCount > 1 ? 's' : ''} trouvée${resultCount > 1 ? 's' : ''}` : 'Aucun résultat' }}
            </p>

            <div v-if="appliedFilters.length" class="ms-done__filters">
              <p class="ms-done__filters-label">Filtres appliqués :</p>
              <div class="ms-done__chips">
                <span
                  v-for="(f, i) in appliedFilters"
                  :key="i"
                  class="ms-done__chip"
                >
                  <strong>{{ f.label }}</strong> {{ formatFilterValue(f.label, f.value) }}
                </span>
              </div>
            </div>

            <!-- Zone couverte, mais critères trop restrictifs -->
            <div v-if="resultCount === 0 && locationTotal > 0 && emptyLocationName" class="ms-done__empty">
              <p class="ms-done__empty-main">
                Il y a <strong>{{ locationTotal }} bien{{ locationTotal > 1 ? 's' : '' }}</strong> dans la zone
                <strong>« {{ emptyLocationName }} »</strong> mais aucun ne correspond à {{ narrowingHintText }}.
              </p>
              <div class="ms-done__empty-tips">
                <p v-if="hasFilterType('price')" class="ms-done__empty-tip">
                  <i class="pi pi-wallet"></i>
                  <span>Ajustez votre budget pour voir plus de résultats</span>
                </p>
                <p v-if="hasFilterType('rooms')" class="ms-done__empty-tip">
                  <i class="pi pi-th-large"></i>
                  <span>Essayez avec un autre nombre de pièces</span>
                </p>
                <p v-if="hasFilterType('type')" class="ms-done__empty-tip">
                  <i class="pi pi-home"></i>
                  <span>Cherchez aussi en location ou en vente</span>
                </p>
                <p class="ms-done__empty-tip">
                  <i class="pi pi-search"></i>
                  <span>Relancez sans filtre restrictif pour voir les {{ locationTotal }} bien{{ locationTotal > 1 ? 's' : '' }} disponibles</span>
                </p>
              </div>
            </div>

            <!-- Zone NON couverte ou aucun critère de localisation -->
            <div v-else-if="resultCount === 0" class="ms-done__empty">
              <p v-if="emptyLocationName" class="ms-done__empty-main">
                Il n'y a pas encore de biens enregistrés dans la zone <strong>« {{ emptyLocationName }} »</strong> sur notre plateforme.
              </p>
              <p v-else class="ms-done__empty-main">
                Aucune annonce ne correspond à vos critères pour le moment.
              </p>
              <div class="ms-done__empty-tips">
                <p class="ms-done__empty-tip">
                  <i class="pi pi-map-marker"></i>
                  <span v-if="emptyLocationName">Essayez une zone proche ou un quartier voisin</span>
                  <span v-else>Essayez une autre localisation</span>
                </p>
                <p class="ms-done__empty-tip">
                  <i class="pi pi-sliders-h"></i>
                  <span>Modifiez vos critères (budget, type de bien...)</span>
                </p>
                <p class="ms-done__empty-tip">
                  <i class="pi pi-clock"></i>
                  <span>De nouvelles annonces sont ajoutées régulièrement</span>
                </p>
              </div>
            </div>
          </div>

          <div class="ms-done__actions">
            <button class="ms-btn ms-btn--secondary" @click="reset">Nouvelle recherche</button>
            <button v-if="resultCount > 0" class="ms-btn ms-btn--primary" @click="closeAndViewResults">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
              Voir les résultats
            </button>
          </div>
        </template>
      </div>

      <!-- Desktop chat input bar -->
      <div v-if="phase === 'welcome'" class="ms-chat-bar">
        <div class="ms-chat-bar__wrap">
          <input
            v-model="chatInput"
            type="text"
            class="ms-chat-bar__input"
            placeholder="Décrivez ce que vous cherchez..."
            @keyup.enter="handleChatSubmit"
          />
          <button class="ms-chat-bar__voice" @click="startRecording" title="Recherche vocale">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="#fff" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path fill="#fff" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ─── FAB ──────────────────────────────────────────────────── */
.ms-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: #1DA53F;
  box-shadow: 0 4px 16px rgba(29,165,63,.35), 0 2px 4px rgba(0,0,0,.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .2s, box-shadow .2s, opacity .3s;
}
.ms-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(29,165,63,.45), 0 2px 8px rgba(0,0,0,.15);
}
.ms-fab--hidden {
  opacity: 0.6;
  transform: scale(0.85);
}
.ms-fab--hidden:hover {
  opacity: 1;
  transform: scale(1);
}
.ms-fab__icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ─── PANEL ────────────────────────────────────────────────── */
.ms-panel {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1001;
  width: 380px;
  max-height: calc(100vh - 100px);
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,.15), 0 0 0 1px rgba(0,0,0,.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ms-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f0faf3 0%, #fff 100%);
}
.ms-panel__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ms-panel__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #1DA53F;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ms-panel__name {
  font-weight: 700;
  font-size: 15px;
  color: #0F0F0F;
  display: block;
}
.ms-panel__sub {
  font-size: 11px;
  color: #1DA53F;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}
.ms-panel__speaking-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1DA53F;
  animation: ms-speak-dot 1s ease-in-out infinite;
}
@keyframes ms-speak-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: .4; transform: scale(.7); }
}
.ms-panel__header-actions {
  display: flex;
  gap: 4px;
}
.ms-panel__btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: background .15s, color .15s;
}
.ms-panel__btn-icon:hover {
  background: #f2f2f2;
  color: #333;
}
.ms-panel__btn-icon--muted {
  color: #dc2626;
}
.ms-panel__btn-icon--muted:hover {
  color: #dc2626;
  background: #fef2f2;
}

.ms-panel__body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

/* ─── WELCOME ──────────────────────────────────────────────── */
.ms-welcome__msg {
  font-size: 16px;
  font-weight: 600;
  color: #0F0F0F;
  margin: 0 0 6px;
  line-height: 1.4;
}
.ms-welcome__hint {
  font-size: 13px;
  color: #666;
  margin: 0 0 24px;
  line-height: 1.5;
}

/* ─── MIC BUTTON ───────────────────────────────────────────── */
.ms-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}
.ms-mic-btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: none;
  background: #1DA53F;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .15s, box-shadow .15s;
  box-shadow: 0 4px 16px rgba(29,165,63,.3);
}
.ms-mic-btn:hover {
  transform: scale(1.06);
  box-shadow: 0 6px 24px rgba(29,165,63,.4);
}
.ms-mic-btn--active {
  background: #dc2626;
  box-shadow: 0 4px 16px rgba(220,38,38,.3);
  animation: ms-pulse 1.5s infinite;
}
.ms-mic-btn--active:hover {
  box-shadow: 0 6px 24px rgba(220,38,38,.4);
}
@keyframes ms-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220,38,38,.4), 0 4px 16px rgba(220,38,38,.3); }
  50% { box-shadow: 0 0 0 14px rgba(220,38,38,0), 0 4px 16px rgba(220,38,38,.3); }
}
.ms-actions__label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

/* ─── ALT ACTIONS ──────────────────────────────────────────── */
.ms-alt-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.ms-alt-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
  color: #555;
  cursor: pointer;
  transition: all .15s;
}
.ms-alt-btn:hover {
  border-color: #1DA53F;
  color: #1DA53F;
  background: rgba(29,165,63,.04);
}

/* ─── RECORDING ────────────────────────────────────────────── */
.ms-recording__tip {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin: 0 0 12px;
  text-align: center;
}
.ms-recording__bubble {
  background: #f7f7f7;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  min-height: 60px;
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}
.ms-recording__bubble--empty {
  color: #999;
  font-style: italic;
}
.ms-recording__bubble p { margin: 0; }
.ms-recording__cursor {
  animation: ms-blink .8s step-end infinite;
  color: #1DA53F;
  font-weight: 700;
}
@keyframes ms-blink {
  50% { opacity: 0; }
}

/* ─── REVIEW ───────────────────────────────────────────────── */
.ms-review__label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px;
}
.ms-review__textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  color: #333;
  resize: vertical;
  background: #fafafa;
  transition: border-color .15s;
  box-sizing: border-box;
}
.ms-review__textarea:focus {
  outline: none;
  border-color: #1DA53F;
  background: #fff;
}
.ms-review__textarea::placeholder { color: #aaa; }
.ms-review__error {
  color: #dc2626;
  font-size: 13px;
  margin: 8px 0 0;
}
.ms-review__actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  justify-content: flex-end;
}

/* ─── BUTTONS ──────────────────────────────────────────────── */
.ms-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all .15s;
}
.ms-btn--primary {
  background: #1DA53F;
  color: #fff;
}
.ms-btn--primary:hover:not(:disabled) { background: #178A33; }
.ms-btn--primary:disabled { opacity: .5; cursor: not-allowed; }
.ms-btn--secondary {
  background: #f5f5f5;
  color: #555;
  border: 1px solid #e0e0e0;
}
.ms-btn--secondary:hover { background: #eee; color: #333; }

/* ─── ANALYZING ────────────────────────────────────────────── */
.ms-analyzing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 0;
}
.ms-analyzing__scene {
  position: relative;
  width: 80px;
  height: 80px;
}
.ms-analyzing__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  width: 100%;
  height: 100%;
}
.ms-analyzing__block {
  border-radius: 4px;
  animation: ms-block-shuffle 2.4s ease-in-out infinite;
}
.ms-analyzing__block--1 { background: #1DA53F; animation-delay: 0s; }
.ms-analyzing__block--2 { background: #a7f3d0; animation-delay: 0.15s; }
.ms-analyzing__block--3 { background: #2563eb; animation-delay: 0.3s; }
.ms-analyzing__block--4 { background: #bbf7d0; animation-delay: 0.45s; }
.ms-analyzing__block--5 { background: #1DA53F; animation-delay: 0.6s; }
.ms-analyzing__block--6 { background: #93c5fd; animation-delay: 0.75s; }
.ms-analyzing__block--7 { background: #2563eb; animation-delay: 0.9s; }
.ms-analyzing__block--8 { background: #a7f3d0; animation-delay: 1.05s; }
.ms-analyzing__block--9 { background: #1DA53F; animation-delay: 1.2s; }

@keyframes ms-block-shuffle {
  0%, 100% { transform: scale(1); opacity: 0.6; border-radius: 4px; }
  25% { transform: scale(0.6) rotate(45deg); opacity: 0.3; border-radius: 50%; }
  50% { transform: scale(1.1); opacity: 1; border-radius: 4px; }
  75% { transform: scale(0.8) rotate(-20deg); opacity: 0.5; border-radius: 6px; }
}

.ms-analyzing__loupe {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.9);
  border-radius: 50%;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  animation: ms-loupe-move 2.4s ease-in-out infinite;
}
@keyframes ms-loupe-move {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  30% { transform: translate(-30%, -60%) scale(1.05); }
  60% { transform: translate(-70%, -40%) scale(0.95); }
}

.ms-analyzing__text {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0;
}
.ms-analyzing__sub {
  font-size: 12px;
  color: #888;
  margin: 0;
}

/* ─── DONE ─────────────────────────────────────────────────── */
.ms-done {
  text-align: center;
}
.ms-done__check {
  margin-bottom: 10px;
}
.ms-done__title {
  font-size: 16px;
  font-weight: 700;
  color: #0F0F0F;
  margin: 0 0 16px;
}
.ms-done__filters {
  text-align: left;
  margin-bottom: 12px;
}
.ms-done__filters-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin: 0 0 8px;
}
.ms-done__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.ms-done__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #f0faf3;
  border: 1px solid #bbf0ca;
  border-radius: 16px;
  font-size: 12px;
  color: #166534;
}
.ms-done__chip strong {
  font-weight: 600;
  color: #15803d;
}
.ms-done__empty {
  margin-top: 4px;
  text-align: left;
}
.ms-done__empty-main {
  font-size: 13px;
  color: #555;
  line-height: 1.5;
  margin: 0 0 12px;
  text-align: center;
}
.ms-done__empty-main strong {
  color: #0f0f0f;
  font-weight: 600;
}
.ms-done__empty-tips {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #f8faf9;
  border: 1px solid #e8f0eb;
  border-radius: 10px;
  padding: 10px 12px;
}
.ms-done__empty-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #555;
  margin: 0;
  line-height: 1.4;
}
.ms-done__empty-tip i {
  font-size: 13px;
  color: #1DA53F;
  flex-shrink: 0;
}
.ms-done__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 14px;
}

/* ─── TRANSITION ───────────────────────────────────────────── */
.ms-slide-enter-active { transition: all .25s cubic-bezier(.4,0,.2,1); }
.ms-slide-leave-active { transition: all .2s cubic-bezier(.4,0,1,1); }
.ms-slide-enter-from,
.ms-slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(.96);
}

/* ─── INVITE BUBBLE ────────────────────────────────────────── */
.ms-invite {
  position: fixed;
  bottom: 90px;
  right: 24px;
  z-index: 1001;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 280px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 24px rgba(0,0,0,.12), 0 0 0 1px rgba(29,165,63,.15);
  cursor: pointer;
  animation: ms-invite-bounce 0.6s ease-out;
}
.ms-invite__icon {
  flex-shrink: 0;
  margin-top: 1px;
}
.ms-invite__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: #333;
  font-weight: 500;
}
.ms-invite__close {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 18px;
  color: #aaa;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  margin: -2px -4px 0 0;
}
.ms-invite__close:hover { color: #555; }

@keyframes ms-invite-bounce {
  0% { opacity: 0; transform: translateY(20px) scale(0.9); }
  60% { transform: translateY(-4px) scale(1.02); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.ms-invite-enter-active { animation: ms-invite-bounce 0.5s ease-out; }
.ms-invite-leave-active { transition: opacity 0.3s, transform 0.3s; }
.ms-invite-leave-to { opacity: 0; transform: translateY(10px) scale(0.95); }

/* ─── DESKTOP: FAB BAR + CENTERED PANEL ──────────────────── */
.ms-fab-bar { display: none; }
.ms-chat-bar { display: none; }

@media (min-width: 769px) {
  .ms-fab { display: none !important; }

  /* ── Barre centrée style ChatGPT/Gemini ── */
  .ms-fab-bar {
    display: block;
    position: fixed;
    bottom: 24px;
    left: 0;
    right: 0;
    z-index: 1000;
    pointer-events: none;
    padding: 0 24px;
  }
  .ms-fab-bar__inner {
    pointer-events: all;
    max-width: 580px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fff;
    border: 1.5px solid #e0e0e0;
    border-radius: 28px;
    padding: 6px 8px 6px 8px;
    box-shadow: 0 2px 20px rgba(0,0,0,.08), 0 0 0 1px rgba(0,0,0,.02);
    transition: border-color .2s, box-shadow .2s;
    animation: ms-bar-glow 2.5s ease-in-out infinite;
  }
  .ms-fab-bar__inner:focus-within {
    border-color: #1DA53F;
    box-shadow: 0 4px 28px rgba(0,0,0,.1), 0 0 0 3px rgba(29,165,63,.08);
    animation: none;
  }
  @keyframes ms-bar-glow {
    0%, 100% {
      box-shadow: 0 2px 20px rgba(0,0,0,.08), 0 0 0 1px rgba(0,0,0,.02);
      border-color: #e0e0e0;
    }
    50% {
      box-shadow: 0 2px 24px rgba(29,165,63,.18), 0 0 0 3px rgba(29,165,63,.10);
      border-color: rgba(29,165,63,.4);
    }
  }
  .ms-fab-bar__avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: #1DA53F;
    color: #fff;
    font-weight: 700;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    position: relative;
  }
  .ms-fab-bar__avatar::after {
    content: '';
    position: absolute;
    inset: -3px;
    border-radius: 50%;
    border: 2px solid rgba(29,165,63,.4);
    animation: ms-avatar-sonar 2.5s ease-out infinite;
    pointer-events: none;
  }
  @keyframes ms-avatar-sonar {
    0% { transform: scale(1); opacity: .6; }
    70% { transform: scale(1.5); opacity: 0; }
    100% { transform: scale(1.5); opacity: 0; }
  }
  .ms-fab-bar__input {
    flex: 1;
    border: none;
    background: none;
    outline: none;
    font-size: 15px;
    color: #333;
    font-family: inherit;
    min-width: 0;
    padding: 10px 0;
  }
  .ms-fab-bar__input::placeholder { color: #aaa; }
  .ms-fab-bar__voice {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: #f5f5f5;
    color: #666;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: background .15s, color .15s, transform .15s;
  }
  .ms-fab-bar__voice:hover {
    background: #1DA53F;
    color: #fff;
    transform: scale(1.06);
  }

  /* Transition enter/leave */
  .ms-bar-enter-active { transition: all .3s cubic-bezier(.4,0,.2,1); }
  .ms-bar-leave-active { transition: all .2s ease; }
  .ms-bar-enter-from,
  .ms-bar-leave-to {
    opacity: 0;
    transform: translateY(16px);
  }

  /* ── Panel centré ── */
  .ms-panel {
    width: 480px;
    right: auto;
    left: calc(50% - 240px);
    bottom: 84px;
  }

  .ms-welcome-actions { display: none; }

  .ms-welcome__msg {
    font-size: 20px;
    text-align: center;
    margin-bottom: 8px;
  }
  .ms-welcome__hint {
    text-align: center;
    margin-bottom: 16px;
  }

  /* Barre de chat dans le panel (fallback) */
  .ms-chat-bar {
    display: block;
    padding: 14px 16px 16px;
    border-top: 1px solid #f0f0f0;
    background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
    border-radius: 0 0 16px 16px;
  }
  .ms-chat-bar__wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #fff;
    border: 1.5px solid #e0e0e0;
    border-radius: 26px;
    padding: 4px 5px 4px 18px;
    transition: border-color .2s, box-shadow .2s;
  }
  .ms-chat-bar__wrap:focus-within {
    border-color: #1DA53F;
    box-shadow: 0 0 0 3px rgba(29,165,63,.08);
  }
  .ms-chat-bar__input {
    flex: 1;
    border: none;
    background: none;
    outline: none;
    font-size: 14px;
    color: #333;
    font-family: inherit;
    min-width: 0;
    padding: 8px 0;
  }
  .ms-chat-bar__input::placeholder { color: #aaa; }
  .ms-chat-bar__voice {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: none;
    background: #1DA53F;
    color: #fff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: background .15s, transform .15s;
  }
  .ms-chat-bar__voice:hover {
    background: #178A33;
    transform: scale(1.08);
  }

  /* Invite bubble : centrée au-dessus de la barre */
  .ms-invite {
    right: auto;
    left: 50%;
    transform: translateX(-50%);
    bottom: 90px;
  }
}

/* ─── MOBILE ───────────────────────────────────────────────── */
@media (max-width: 768px) {
  .ms-fab {
    display: none !important;
  }
  .ms-invite {
    bottom: 62px;
    right: auto;
    left: 50%;
    transform: translateX(-50%);
    max-width: min(280px, calc(100vw - 32px));
  }
  .ms-panel {
    width: calc(100vw - 16px);
    right: 8px;
    bottom: 8px;
    max-height: calc(100vh - 70px);
  }
}
</style>
