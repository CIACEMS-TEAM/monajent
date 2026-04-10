<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '@/Stores/agent'
import { useToast } from 'vue-toastification'

const router = useRouter()
const agent = useAgentStore()
const toast = useToast()

type Phase = 'welcome' | 'recording' | 'review' | 'analyzing' | 'done'

const open = ref(false)
const dismissed = ref(false)
const phase = ref<Phase>('welcome')
const transcript = ref('')
const interimText = ref('')
const extractedData = ref<Record<string, unknown> | null>(null)
const missingFields = ref<string[]>([])
const errorMsg = ref('')
const muted = ref(false)
const speaking = ref(false)

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

function getGreeting(): string {
  const h = new Date().getHours()
  if (h >= 5 && h < 12) return 'Bonjour'
  if (h >= 12 && h < 18) return 'Bon après-midi'
  return 'Bonsoir'
}

// ─── Synthèse vocale (Mona parle) ────────────────────────────

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

// Parler à l'ouverture du panneau
watch(open, (isOpen) => {
  if (isOpen && phase.value === 'welcome') {
    setTimeout(() => {
      monaSay(`${getGreeting()} ! Quelle annonce voulez-vous publier aujourd'hui ? Appuyez sur le micro et décrivez votre bien.`)
    }, 400)
  }
  if (!isOpen) monaStop()
})

function toggle() {
  if (dismissed.value) {
    dismissed.value = false
    open.value = true
    return
  }
  open.value = !open.value
}

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
  extractedData.value = null
  missingFields.value = []
  errorMsg.value = ''
  baseTranscript = ''
  clearSilenceTimer()
  stopRecording()
  monaStop()
}

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
        monaSay('Très bien ! Vous pouvez relire et modifier le texte si besoin, puis appuyez sur Analyser pour créer votre annonce.')
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
      monaSay('Très bien ! Vous pouvez relire et modifier le texte si besoin, puis appuyez sur Analyser pour créer votre annonce.')
    } else {
      phase.value = 'welcome'
    }
  }
}

function buildDoneSpeech(d: Record<string, unknown>, missing: string[]): string {
  const parts: string[] = ['C\'est bon, j\'ai pré-rempli le formulaire.']

  const title = d.title as string | undefined
  if (title) parts.push(`Le titre sera : ${title}.`)

  const price = d.price as number | undefined
  const city = d.city as string | undefined
  if (price && city) {
    parts.push(`${new Intl.NumberFormat('fr-FR').format(price)} francs à ${city}.`)
  } else if (price) {
    parts.push(`Prix : ${new Intl.NumberFormat('fr-FR').format(price)} francs.`)
  }

  if (missing.length > 0 && missing.length <= 4) {
    parts.push(`Il vous reste à compléter : ${missing.join(', ')}.`)
  } else if (missing.length > 4) {
    parts.push(`Il reste ${missing.length} champs à compléter manuellement.`)
  } else {
    parts.push('Tous les champs ont été remplis !')
  }

  parts.push('Vous pouvez ouvrir le formulaire pour vérifier et ajouter vos photos.')
  return parts.join(' ')
}

async function analyze() {
  const text = transcript.value.trim()
  if (!text) return

  phase.value = 'analyzing'
  errorMsg.value = ''

  try {
    const d = await agent.extractListingFromAi(text)
    extractedData.value = d
    missingFields.value = Array.isArray(d.missing_fields) ? d.missing_fields as string[] : []
    phase.value = 'done'
    monaSay(buildDoneSpeech(d, missingFields.value))
  } catch (e: any) {
    const msg = e?.response?.data?.detail
    errorMsg.value = typeof msg === 'string' ? msg : 'Mona rencontre un problème temporaire. Veuillez réessayer.'
    phase.value = 'review'
    monaSay('Désolée, je n\'ai pas pu analyser votre description. Vous pouvez modifier le texte et réessayer.')
  }
}

function navigateToNewListing() {
  open.value = false
  router.push({
    path: '/agent/listings',
    query: { action: 'new', _t: String(Date.now()) },
  })
}

function openFormWithData() {
  if (extractedData.value) {
    agent.aiPrefillData = extractedData.value
  }
  navigateToNewListing()
}

function openFormDirect() {
  agent.aiPrefillData = null
  navigateToNewListing()
}

function editTranscript(e: Event) {
  transcript.value = (e.target as HTMLTextAreaElement).value
}

onBeforeUnmount(() => {
  clearSilenceTimer()
  stopRecording()
  monaStop()
})

defineExpose({ toggle, open })
</script>

<template>
  <!-- FAB -->
  <button
    v-if="!open"
    class="mona-fab"
    :class="{ 'mona-fab--hidden': dismissed }"
    @click="toggle"
    title="Mona — Assistante IA"
  >
    <span class="mona-fab__icon">
      <svg viewBox="0 0 24 24" width="28" height="28" fill="none">
        <circle cx="12" cy="12" r="11" fill="#1DA53F"/>
        <path d="M12 3C7.03 3 3 6.58 3 11c0 2.48 1.38 4.7 3.55 6.15-.13 1.2-.72 2.27-1.55 3.1.98.03 2.2-.28 3.45-1.12.85.22 1.66.37 2.55.37 4.97 0 9-3.58 9-8s-4.03-8-9-8z" fill="rgba(255,255,255,.2)"/>
        <text x="12" y="15.5" text-anchor="middle" fill="#fff" font-size="11" font-weight="700" font-family="system-ui">M</text>
      </svg>
    </span>
  </button>

  <!-- Panel -->
  <Transition name="mona-slide">
    <div v-if="open" class="mona-panel">
      <div class="mona-panel__header">
        <div class="mona-panel__brand">
          <span class="mona-panel__avatar">M</span>
          <div>
            <span class="mona-panel__name">Mona</span>
            <span class="mona-panel__sub">
              <template v-if="speaking">
                <span class="mona-panel__speaking-dot"></span> Parle...
              </template>
              <template v-else>Assistante IA</template>
            </span>
          </div>
        </div>
        <div class="mona-panel__header-actions">
          <button
            class="mona-panel__btn-icon"
            :class="{ 'mona-panel__btn-icon--muted': muted }"
            @click="toggleMute"
            :title="muted ? 'Activer la voix' : 'Couper la voix'"
          >
            <svg v-if="!muted" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0014 8.77v6.46A4.47 4.47 0 0016.5 12zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
            <svg v-else viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M16.5 12A4.5 4.5 0 0014 8.77v2.06l2.47 2.47c.03-.1.03-.2.03-.3zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.796 8.796 0 0021 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06a8.99 8.99 0 003.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
          </button>
          <button class="mona-panel__btn-icon" @click="reset" title="Recommencer">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M17.65 6.35A7.96 7.96 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
          </button>
          <button class="mona-panel__btn-icon" @click="dismiss" title="Fermer">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
      </div>

      <div class="mona-panel__body">
        <!-- WELCOME -->
        <template v-if="phase === 'welcome'">
          <div class="mona-welcome">
            <p class="mona-welcome__msg">
              {{ getGreeting() }} ! Quelle annonce voulez-vous publier aujourd'hui ?
            </p>
            <p class="mona-welcome__hint">
              Appuyez sur le micro et décrivez votre bien. Je remplirai le formulaire pour vous.
            </p>
          </div>

          <div class="mona-actions">
            <button class="mona-mic-btn" @click="startRecording">
              <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#fff" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/><path fill="#fff" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
            </button>
            <span class="mona-actions__label">Parler</span>
          </div>

          <div class="mona-alt-actions">
            <button class="mona-alt-btn" @click="phase = 'review'">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1.003 1.003 0 000-1.42l-2.34-2.34a1.003 1.003 0 00-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z"/></svg>
              Saisir un texte
            </button>
            <button class="mona-alt-btn" @click="openFormDirect">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
              Formulaire direct
            </button>
          </div>
        </template>

        <!-- RECORDING -->
        <template v-if="phase === 'recording'">
          <div class="mona-recording">
            <p class="mona-recording__tip">Je vous écoute... Prenez votre temps.</p>
            <div class="mona-recording__bubble" v-if="displayText">
              <p>{{ displayText }}<span class="mona-recording__cursor">|</span></p>
            </div>
            <div class="mona-recording__bubble mona-recording__bubble--empty" v-else>
              <p>En attente de votre voix...</p>
            </div>
          </div>
          <div class="mona-actions">
            <button class="mona-mic-btn mona-mic-btn--active" @click="stopRecording">
              <svg viewBox="0 0 24 24" width="32" height="32"><rect x="6" y="6" width="12" height="12" rx="2" fill="#fff"/></svg>
            </button>
            <span class="mona-actions__label">Appuyez pour terminer</span>
          </div>
        </template>

        <!-- REVIEW -->
        <template v-if="phase === 'review'">
          <div class="mona-review">
            <p class="mona-review__label">Votre description :</p>
            <textarea
              class="mona-review__textarea"
              :value="transcript"
              @input="editTranscript"
              rows="5"
              placeholder="Décrivez votre bien ici...&#10;Ex : 3 pièces à Cocody Riviera Faya, loyer 250k, 2+2+1, climatisé avec parking."
            />
            <p v-if="errorMsg" class="mona-review__error">{{ errorMsg }}</p>
          </div>
          <div class="mona-review__actions">
            <button class="mona-btn mona-btn--secondary" @click="startRecording">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path fill="currentColor" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
              Re-dicter
            </button>
            <button
              class="mona-btn mona-btn--primary"
              :disabled="!transcript.trim()"
              @click="analyze"
            >
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M13 3L4 14h7l-2 7 9-11h-7l2-7z"/></svg>
              Analyser avec Mona
            </button>
          </div>
        </template>

        <!-- ANALYZING -->
        <template v-if="phase === 'analyzing'">
          <div class="mona-analyzing">
            <div class="mona-analyzing__scene">
              <div class="mona-analyzing__grid">
                <div class="mona-analyzing__block mona-analyzing__block--1"></div>
                <div class="mona-analyzing__block mona-analyzing__block--2"></div>
                <div class="mona-analyzing__block mona-analyzing__block--3"></div>
                <div class="mona-analyzing__block mona-analyzing__block--4"></div>
                <div class="mona-analyzing__block mona-analyzing__block--5"></div>
                <div class="mona-analyzing__block mona-analyzing__block--6"></div>
                <div class="mona-analyzing__block mona-analyzing__block--7"></div>
                <div class="mona-analyzing__block mona-analyzing__block--8"></div>
                <div class="mona-analyzing__block mona-analyzing__block--9"></div>
              </div>
              <div class="mona-analyzing__loupe">
                <svg viewBox="0 0 24 24" width="28" height="28"><path fill="#1DA53F" d="M13 3L4 14h7l-2 7 9-11h-7l2-7z"/></svg>
              </div>
            </div>
            <p class="mona-analyzing__text">Mona analyse votre description...</p>
            <p class="mona-analyzing__sub">Extraction des champs en cours</p>
          </div>
        </template>

        <!-- DONE -->
        <template v-if="phase === 'done' && extractedData">
          <div class="mona-done">
            <div class="mona-done__check">
              <svg viewBox="0 0 24 24" width="36" height="36"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
            </div>
            <p class="mona-done__title">Formulaire pré-rempli !</p>

            <div class="mona-done__preview">
              <div v-if="extractedData.title" class="mona-done__field">
                <span class="mona-done__key">Titre</span>
                <span class="mona-done__val">{{ extractedData.title }}</span>
              </div>
              <div v-if="extractedData.city || extractedData.neighborhood" class="mona-done__field">
                <span class="mona-done__key">Lieu</span>
                <span class="mona-done__val">{{ [extractedData.neighborhood, extractedData.city].filter(Boolean).join(', ') }}</span>
              </div>
              <div v-if="extractedData.price" class="mona-done__field">
                <span class="mona-done__key">Prix</span>
                <span class="mona-done__val">{{ new Intl.NumberFormat('fr-FR').format(Number(extractedData.price)) }} F CFA</span>
              </div>
              <div v-if="extractedData.rooms" class="mona-done__field">
                <span class="mona-done__key">Pièces</span>
                <span class="mona-done__val">{{ extractedData.rooms }} pièce(s){{ extractedData.bedrooms ? ` dont ${extractedData.bedrooms} ch.` : '' }}</span>
              </div>
            </div>

            <div v-if="missingFields.length" class="mona-done__missing">
              <p><strong>A compléter :</strong> {{ missingFields.join(', ') }}</p>
            </div>
          </div>

          <div class="mona-done__actions">
            <button class="mona-btn mona-btn--secondary" @click="reset">Recommencer</button>
            <button class="mona-btn mona-btn--primary" @click="openFormWithData">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
              Ouvrir le formulaire
            </button>
          </div>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ─── FAB ──────────────────────────────────────────────────── */
.mona-fab {
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
.mona-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(29,165,63,.45), 0 2px 8px rgba(0,0,0,.15);
}
.mona-fab--hidden {
  opacity: 0.6;
  transform: scale(0.85);
}
.mona-fab--hidden:hover {
  opacity: 1;
  transform: scale(1);
}
.mona-fab__icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ─── PANEL ────────────────────────────────────────────────── */
.mona-panel {
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

.mona-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f0faf3 0%, #fff 100%);
}
.mona-panel__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.mona-panel__avatar {
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
.mona-panel__name {
  font-weight: 700;
  font-size: 15px;
  color: #0F0F0F;
  display: block;
}
.mona-panel__sub {
  font-size: 11px;
  color: #1DA53F;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}
.mona-panel__speaking-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1DA53F;
  animation: mona-speak-dot 1s ease-in-out infinite;
}
@keyframes mona-speak-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: .4; transform: scale(.7); }
}
.mona-panel__header-actions {
  display: flex;
  gap: 4px;
}
.mona-panel__btn-icon {
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
.mona-panel__btn-icon:hover {
  background: #f2f2f2;
  color: #333;
}
.mona-panel__btn-icon--muted {
  color: #dc2626;
}
.mona-panel__btn-icon--muted:hover {
  color: #dc2626;
  background: #fef2f2;
}

.mona-panel__body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

/* ─── WELCOME ──────────────────────────────────────────────── */
.mona-welcome__msg {
  font-size: 16px;
  font-weight: 600;
  color: #0F0F0F;
  margin: 0 0 6px;
  line-height: 1.4;
}
.mona-welcome__hint {
  font-size: 13px;
  color: #666;
  margin: 0 0 24px;
  line-height: 1.5;
}

/* ─── MIC BUTTON ───────────────────────────────────────────── */
.mona-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}
.mona-mic-btn {
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
.mona-mic-btn:hover {
  transform: scale(1.06);
  box-shadow: 0 6px 24px rgba(29,165,63,.4);
}
.mona-mic-btn--active {
  background: #dc2626;
  box-shadow: 0 4px 16px rgba(220,38,38,.3);
  animation: mona-pulse 1.5s infinite;
}
.mona-mic-btn--active:hover {
  box-shadow: 0 6px 24px rgba(220,38,38,.4);
}
@keyframes mona-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220,38,38,.4), 0 4px 16px rgba(220,38,38,.3); }
  50% { box-shadow: 0 0 0 14px rgba(220,38,38,0), 0 4px 16px rgba(220,38,38,.3); }
}
.mona-actions__label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

/* ─── ALT ACTIONS ──────────────────────────────────────────── */
.mona-alt-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.mona-alt-btn {
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
.mona-alt-btn:hover {
  border-color: #1DA53F;
  color: #1DA53F;
  background: rgba(29,165,63,.04);
}

/* ─── RECORDING ────────────────────────────────────────────── */
.mona-recording__tip {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin: 0 0 12px;
  text-align: center;
}
.mona-recording__bubble {
  background: #f7f7f7;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  min-height: 60px;
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}
.mona-recording__bubble--empty {
  color: #999;
  font-style: italic;
}
.mona-recording__bubble p { margin: 0; }
.mona-recording__cursor {
  animation: mona-blink .8s step-end infinite;
  color: #1DA53F;
  font-weight: 700;
}
@keyframes mona-blink {
  50% { opacity: 0; }
}

/* ─── REVIEW ───────────────────────────────────────────────── */
.mona-review__label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px;
}
.mona-review__textarea {
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
.mona-review__textarea:focus {
  outline: none;
  border-color: #1DA53F;
  background: #fff;
}
.mona-review__textarea::placeholder { color: #aaa; }
.mona-review__error {
  color: #dc2626;
  font-size: 13px;
  margin: 8px 0 0;
}
.mona-review__actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  justify-content: flex-end;
}

/* ─── BUTTONS ──────────────────────────────────────────────── */
.mona-btn {
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
.mona-btn--primary {
  background: #1DA53F;
  color: #fff;
}
.mona-btn--primary:hover:not(:disabled) { background: #178A33; }
.mona-btn--primary:disabled { opacity: .5; cursor: not-allowed; }
.mona-btn--secondary {
  background: #f5f5f5;
  color: #555;
  border: 1px solid #e0e0e0;
}
.mona-btn--secondary:hover { background: #eee; color: #333; }

/* ─── ANALYZING ────────────────────────────────────────────── */
.mona-analyzing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 0;
}
.mona-analyzing__scene {
  position: relative;
  width: 80px;
  height: 80px;
}
.mona-analyzing__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  width: 100%;
  height: 100%;
}
.mona-analyzing__block {
  border-radius: 4px;
  animation: mona-block-shuffle 2.4s ease-in-out infinite;
}
.mona-analyzing__block--1 { background: #1DA53F; animation-delay: 0s; }
.mona-analyzing__block--2 { background: #a7f3d0; animation-delay: 0.15s; }
.mona-analyzing__block--3 { background: #ea580c; animation-delay: 0.3s; }
.mona-analyzing__block--4 { background: #bbf7d0; animation-delay: 0.45s; }
.mona-analyzing__block--5 { background: #1DA53F; animation-delay: 0.6s; }
.mona-analyzing__block--6 { background: #fed7aa; animation-delay: 0.75s; }
.mona-analyzing__block--7 { background: #ea580c; animation-delay: 0.9s; }
.mona-analyzing__block--8 { background: #a7f3d0; animation-delay: 1.05s; }
.mona-analyzing__block--9 { background: #1DA53F; animation-delay: 1.2s; }

@keyframes mona-block-shuffle {
  0%, 100% { transform: scale(1); opacity: 0.6; border-radius: 4px; }
  25% { transform: scale(0.6) rotate(45deg); opacity: 0.3; border-radius: 50%; }
  50% { transform: scale(1.1); opacity: 1; border-radius: 4px; }
  75% { transform: scale(0.8) rotate(-20deg); opacity: 0.5; border-radius: 6px; }
}

.mona-analyzing__loupe {
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
  animation: mona-loupe-move 2.4s ease-in-out infinite;
}
@keyframes mona-loupe-move {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  30% { transform: translate(-30%, -60%) scale(1.05); }
  60% { transform: translate(-70%, -40%) scale(0.95); }
}

.mona-analyzing__text {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0;
}
.mona-analyzing__sub {
  font-size: 12px;
  color: #888;
  margin: 0;
}

/* ─── DONE ─────────────────────────────────────────────────── */
.mona-done {
  text-align: center;
}
.mona-done__check {
  margin-bottom: 10px;
}
.mona-done__title {
  font-size: 16px;
  font-weight: 700;
  color: #0F0F0F;
  margin: 0 0 16px;
}
.mona-done__preview {
  text-align: left;
  background: #f7f9f8;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}
.mona-done__field {
  display: flex;
  gap: 8px;
  padding: 5px 0;
  font-size: 13px;
  border-bottom: 1px solid #eee;
}
.mona-done__field:last-child { border-bottom: none; }
.mona-done__key {
  color: #888;
  font-weight: 500;
  min-width: 55px;
  flex-shrink: 0;
}
.mona-done__val {
  color: #333;
  font-weight: 600;
}
.mona-done__missing {
  background: #FFF7ED;
  border: 1px solid #FDBA74;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 12px;
  color: #9A3412;
  text-align: left;
  line-height: 1.4;
  margin-bottom: 6px;
}
.mona-done__missing p { margin: 0; }
.mona-done__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 14px;
}

/* ─── TRANSITION ───────────────────────────────────────────── */
.mona-slide-enter-active { transition: all .25s cubic-bezier(.4,0,.2,1); }
.mona-slide-leave-active { transition: all .2s cubic-bezier(.4,0,1,1); }
.mona-slide-enter-from,
.mona-slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(.96);
}

/* ─── MOBILE ───────────────────────────────────────────────── */
@media (max-width: 1023px) {
  .mona-fab {
    display: none;
  }
  .mona-panel {
    width: calc(100vw - 16px);
    right: 8px;
    bottom: 74px;
    max-height: calc(100vh - 140px);
  }
}
@media (max-width: 480px) {
  .mona-panel {
    width: calc(100vw - 12px);
    right: 6px;
    bottom: 70px;
    max-height: calc(100vh - 130px);
  }
}
</style>
