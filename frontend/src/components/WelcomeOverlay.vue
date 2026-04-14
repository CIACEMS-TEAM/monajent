<script setup lang="ts">
import { ref, onMounted } from 'vue'
import logoUrl from '@/assets/icons/logo_monajent.webp'

const STORAGE_KEY_PERMANENT = 'monajent_welcome_dismissed'
const STORAGE_KEY_SESSION = 'monajent_welcome_seen'

const emit = defineEmits<{ (e: 'closed'): void }>()

const visible = ref(false)

onMounted(() => {
  const permanentDismiss = localStorage.getItem(STORAGE_KEY_PERMANENT)
  const sessionDismiss = sessionStorage.getItem(STORAGE_KEY_SESSION)
  if (!permanentDismiss && !sessionDismiss) {
    visible.value = true
  }
})

function handleUnderstood() {
  sessionStorage.setItem(STORAGE_KEY_SESSION, '1')
  visible.value = false
  emit('closed')
}

function handleNeverShow() {
  localStorage.setItem(STORAGE_KEY_PERMANENT, '1')
  visible.value = false
  emit('closed')
}
</script>

<template>
  <Transition name="welcome-fade">
    <div v-if="visible" class="wo-backdrop">
      <div class="wo-modal">

        <!-- Header -->
        <div class="wo-header">
          <img :src="logoUrl" alt="MonaJent" class="wo-logo" />
        </div>

        <!-- Scrollable content -->
        <div class="wo-body">

          <!-- Hero -->
          <section class="wo-hero">
            <h1 class="wo-hero__title">
              Trouvez votre bien,<br /><span class="wo-green">parlez, c'est trouvé</span>
            </h1>
            <p class="wo-hero__subtitle">
              MonaJent simplifie votre recherche immobilière grâce à Mona,
              votre assistante IA. Décrivez ce que vous cherchez par la voix,
              explorez les biens en vidéo et trouvez le logement idéal en quelques secondes.
            </p>
          </section>

          <!-- How it works -->
          <section class="wo-section">
            <h2 class="wo-section__title">Comment ça marche ?</h2>

            <div class="wo-steps">
              <div class="wo-step">
                <div class="wo-step__icon wo-step__icon--1">
                  <svg viewBox="0 0 48 48" width="40" height="40">
                    <circle cx="24" cy="24" r="18" fill="none" stroke="currentColor" stroke-width="2.5" />
                    <path d="M16 24h16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
                    <path d="M24 18v12" stroke="#1DA53F" stroke-width="2.5" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="wo-step__num">1</div>
                <h3 class="wo-step__title">Créez votre compte</h3>
                <p class="wo-step__desc">
                  Inscription rapide et <strong>gratuite</strong>.
                  Accédez immédiatement à tous les biens disponibles.
                </p>
              </div>

              <div class="wo-step">
                <div class="wo-step__icon wo-step__icon--2">
                  <svg viewBox="0 0 48 48" width="40" height="40">
                    <!-- Microphone icon -->
                    <rect x="18" y="6" width="12" height="22" rx="6" fill="none" stroke="currentColor" stroke-width="2.5" />
                    <path d="M12 24c0 6.63 5.37 12 12 12s12-5.37 12-12" fill="none" stroke="#1DA53F" stroke-width="2.5" stroke-linecap="round" />
                    <path d="M24 36v6" stroke="#1DA53F" stroke-width="2.5" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="wo-step__num">2</div>
                <h3 class="wo-step__title">Parlez à Mona</h3>
                <p class="wo-step__desc">
                  Décrivez ce que vous cherchez <strong>par la voix</strong> :
                  quartier, budget, nombre de pièces… Mona comprend tout.
                </p>
              </div>

              <div class="wo-step">
                <div class="wo-step__icon wo-step__icon--3">
                  <svg viewBox="0 0 48 48" width="40" height="40">
                    <rect x="4" y="10" width="40" height="28" rx="4" fill="none" stroke="currentColor" stroke-width="2.5" />
                    <polygon points="20,18 20,30 32,24" fill="#1DA53F" />
                  </svg>
                </div>
                <div class="wo-step__num">3</div>
                <h3 class="wo-step__title">Explorez en vidéo</h3>
                <p class="wo-step__desc">
                  Visitez les biens en <strong>vidéo immersive</strong>,
                  comme si vous y étiez, directement depuis votre téléphone.
                </p>
              </div>
            </div>

            <!-- Placeholder for future YouTube iframe -->
            <!--
            <div class="wo-video-embed">
              <iframe
                src="https://www.youtube.com/embed/VIDEO_ID"
                title="Comment fonctionne MonaJent"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
              ></iframe>
            </div>
            -->
          </section>



        </div>

        <!-- Footer actions -->
        <div class="wo-footer">
          <button class="wo-btn wo-btn--primary" @click="handleUnderstood">
            J'ai compris, c'est parti !
          </button>
          <button class="wo-btn wo-btn--ghost" @click="handleNeverShow">
            Ne plus afficher
          </button>
        </div>

      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ===== Transition ===== */
.welcome-fade-enter-active,
.welcome-fade-leave-active {
  transition: opacity 0.35s ease;
}
.welcome-fade-enter-active .wo-modal,
.welcome-fade-leave-active .wo-modal {
  transition: transform 0.35s ease, opacity 0.35s ease;
}
.welcome-fade-enter-from,
.welcome-fade-leave-to {
  opacity: 0;
}
.welcome-fade-enter-from .wo-modal {
  transform: translateY(24px) scale(0.97);
  opacity: 0;
}
.welcome-fade-leave-to .wo-modal {
  transform: translateY(-12px) scale(0.98);
  opacity: 0;
}

/* ===== Variables ===== */
.wo-backdrop {
  --green: #1DA53F;
  --green-dark: #178A33;
  --green-light: rgba(29, 165, 63, 0.08);
  --green-ring: rgba(29, 165, 63, 0.18);
  --text: #0F0F0F;
  --text-2: #272727;
  --text-3: #606060;
  --border: #E0E0E0;
  --bg-card: #F9FAFB;
  --radius: 16px;

  position: fixed;
  inset: 0;
  z-index: 1100;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

/* ===== Modal container ===== */
.wo-modal {
  background: #fff;
  border-radius: var(--radius);
  width: 100%;
  max-width: 620px;
  max-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

/* ===== Header ===== */
.wo-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 24px 12px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.wo-logo {
  height: 80px;
  width: auto;
}

/* ===== Scrollable body ===== */
.wo-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 32px 24px;
  scroll-behavior: smooth;
}

.wo-body::-webkit-scrollbar {
  width: 6px;
}
.wo-body::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}
.wo-body::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

/* ===== Hero ===== */
.wo-hero {
  text-align: center;
  padding: 32px 0 24px;
}

.wo-hero__title {
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
  line-height: 1.25;
  margin-bottom: 12px;
}

.wo-green {
  color: var(--green);
}

.wo-hero__subtitle {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-2);
  max-width: 480px;
  margin: 0 auto;
}

/* ===== Sections ===== */
.wo-section {
  margin-bottom: 28px;
}

.wo-section__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  text-align: center;
  margin-bottom: 20px;
}

/* ===== Steps ===== */
.wo-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.wo-step {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 16px;
  text-align: center;
  position: relative;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.wo-step:hover {
  border-color: var(--green);
  box-shadow: 0 4px 16px var(--green-ring);
}

.wo-step__icon {
  color: var(--text);
  margin-bottom: 8px;
  display: flex;
  justify-content: center;
}

.wo-step__num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
}

.wo-step__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.wo-step__desc {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--text-3);
}

/* ===== Video embed placeholder ===== */
.wo-video-embed {
  margin-top: 20px;
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}
.wo-video-embed iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* ===== Footer / Actions ===== */
.wo-footer {
  padding: 16px 32px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
  background: #fff;
}

.wo-btn {
  width: 100%;
  padding: 14px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s, color 0.15s;
  border: none;
}

.wo-btn--primary {
  background: var(--green);
  color: #fff;
}

.wo-btn--primary:hover {
  background: var(--green-dark);
  box-shadow: 0 6px 20px rgba(29, 165, 63, 0.35);
}

.wo-btn--ghost {
  background: transparent;
  color: var(--text-3);
  font-weight: 500;
  font-size: 13px;
}

.wo-btn--ghost:hover {
  color: var(--text);
  background: var(--bg-card);
}

/* ===== Responsive ===== */
@media (max-width: 640px) {
  .wo-backdrop {
    padding: 0;
    align-items: flex-end;
  }

  .wo-modal {
    max-width: 100%;
    max-height: 95vh;
    border-radius: 20px 20px 0 0;
  }

  .wo-body {
    padding: 0 20px 20px;
  }

  .wo-hero__title {
    font-size: 22px;
  }

  .wo-steps {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .wo-step {
    display: grid;
    grid-template-columns: 48px 1fr;
    grid-template-rows: auto auto;
    gap: 0 12px;
    text-align: left;
    padding: 16px;
  }

  .wo-step__icon {
    grid-row: 1 / 3;
    align-self: center;
    justify-content: center;
    margin-bottom: 0;
  }

  .wo-step__num {
    display: none;
  }

  .wo-step__title {
    font-size: 14px;
    margin-bottom: 2px;
  }

  .wo-step__desc {
    font-size: 12px;
  }

  .wo-footer {
    padding: 12px 20px 16px;
  }

  .wo-logo {
    height: 64px;
  }
}
</style>
