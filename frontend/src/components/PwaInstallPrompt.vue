<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import logoUrl from '@/assets/icons/logo_monajent_sf.png'

const DISMISS_KEY = 'monajent_pwa_dismiss'
const DISMISS_DAYS = 7

const show = ref(false)
const showIosGuide = ref(false)
let deferredPrompt: any = null

function isIos(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream
}

function isInStandaloneMode(): boolean {
  return window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as any).standalone === true
}

function isDismissed(): boolean {
  const ts = localStorage.getItem(DISMISS_KEY)
  if (!ts) return false
  return Date.now() - Number(ts) < DISMISS_DAYS * 86400000
}

function handleBeforeInstall(e: Event) {
  e.preventDefault()
  deferredPrompt = e
  if (!isDismissed() && !isInStandaloneMode()) {
    show.value = true
  }
}

async function install() {
  if (deferredPrompt) {
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    deferredPrompt = null
    if (outcome === 'accepted') {
      show.value = false
    }
  }
}

function dismiss() {
  show.value = false
  showIosGuide.value = false
  localStorage.setItem(DISMISS_KEY, String(Date.now()))
}

onMounted(() => {
  if (isInStandaloneMode()) return

  window.addEventListener('beforeinstallprompt', handleBeforeInstall)
  window.addEventListener('appinstalled', () => { show.value = false })

  if (isIos() && !isDismissed()) {
    setTimeout(() => {
      showIosGuide.value = true
      show.value = true
    }, 3000)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
})
</script>

<template>
  <Transition name="pwa-slide">
    <div v-if="show" class="pwa-banner">
      <button class="pwa-banner__close" @click="dismiss" aria-label="Fermer">&times;</button>

      <div class="pwa-banner__content">
        <img :src="logoUrl" alt="MonaJent" class="pwa-banner__logo" />
        <div class="pwa-banner__text">
          <strong class="pwa-banner__title">Installer MonaJent</strong>
          <p class="pwa-banner__desc">
            Accédez à MonaJent directement depuis votre écran d'accueil, comme une vraie application.
          </p>
        </div>
      </div>

      <!-- Android / Chrome / Edge -->
      <button v-if="!showIosGuide" class="pwa-banner__btn" @click="install">
        <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7 7-7z"/></svg>
        Installer l'application
      </button>

      <!-- iOS Safari guide -->
      <div v-else class="pwa-banner__ios">
        <p class="pwa-banner__ios-step">
          Appuyez sur
          <svg viewBox="0 0 24 24" width="20" height="20" class="pwa-banner__ios-icon">
            <path fill="#007AFF" d="M16 5l-1.42 1.42-1.59-1.59V16h-1.98V4.83L9.42 6.42 8 5l4-4 4 4zm4 5v11c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V10c0-1.1.9-2 2-2h3v2H6v11h12V10h-3V8h3c1.1 0 2 .9 2 2z"/>
          </svg>
          puis <strong>"Sur l'écran d'accueil"</strong>
        </p>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-banner {
  position: fixed;
  bottom: 60px;
  left: 12px;
  right: 12px;
  z-index: 999;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 -2px 24px rgba(0,0,0,.12), 0 0 0 1px rgba(0,0,0,.04);
  max-width: 420px;
  margin: 0 auto;
}

.pwa-banner__close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  font-size: 22px;
  color: #aaa;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}
.pwa-banner__close:hover { color: #555; }

.pwa-banner__content {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.pwa-banner__logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  object-fit: contain;
  flex-shrink: 0;
  background: #f5f5f5;
  padding: 4px;
}

.pwa-banner__title {
  font-size: 15px;
  font-weight: 700;
  color: #111;
  display: block;
  margin-bottom: 2px;
}
.pwa-banner__desc {
  font-size: 12.5px;
  line-height: 1.45;
  color: #666;
  margin: 0;
}

.pwa-banner__btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: #1DA53F;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
}
.pwa-banner__btn:hover {
  background: #178A33;
  box-shadow: 0 4px 14px rgba(29,165,63,.3);
}

.pwa-banner__ios {
  background: #f0f7ff;
  border-radius: 10px;
  padding: 12px 14px;
}
.pwa-banner__ios-step {
  font-size: 13.5px;
  color: #333;
  margin: 0;
  line-height: 1.5;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.pwa-banner__ios-icon {
  vertical-align: middle;
  flex-shrink: 0;
}

/* ─── Transition ──────────────────────────────── */
.pwa-slide-enter-active { transition: transform 0.4s cubic-bezier(.4,0,.2,1), opacity 0.3s; }
.pwa-slide-leave-active { transition: transform 0.3s ease, opacity 0.2s; }
.pwa-slide-enter-from { transform: translateY(100%); opacity: 0; }
.pwa-slide-leave-to { transform: translateY(100%); opacity: 0; }

/* ─── Desktop ─────────────────────────────────── */
@media (min-width: 769px) {
  .pwa-banner {
    bottom: 24px;
    left: auto;
    right: 24px;
  }
}

/* ─── Mobile bottom nav compensation ──────────── */
@media (max-width: 768px) {
  .pwa-banner {
    bottom: 68px;
  }
}
</style>
