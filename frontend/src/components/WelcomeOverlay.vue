<script setup lang="ts">
import { ref, onMounted } from 'vue'
import logoUrl from '@/assets/icons/logo_monajent.png'

const STORAGE_KEY_PERMANENT = 'monajent_welcome_dismissed'
const STORAGE_KEY_SESSION = 'monajent_welcome_seen'

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
}

function handleNeverShow() {
  localStorage.setItem(STORAGE_KEY_PERMANENT, '1')
  visible.value = false
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
              Bienvenue sur <span class="wo-green">MonaJent</span>
            </h1>
            <p class="wo-hero__subtitle">
              Le premier modèle africain de <strong>Pay-Per-View immobilier</strong>.<br />
              Visitez des biens virtuellement et physiquement, simplement avec des clés.
            </p>
          </section>

          <!-- How it works -->
          <section class="wo-section">
            <h2 class="wo-section__title">Comment ça marche ?</h2>

            <div class="wo-steps">
              <div class="wo-step">
                <div class="wo-step__icon wo-step__icon--1">
                  <svg viewBox="0 0 48 48" width="40" height="40">
                    <rect x="8" y="6" width="32" height="36" rx="4" fill="none" stroke="currentColor" stroke-width="2.5" />
                    <path d="M16 18h16M16 26h10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
                    <circle cx="34" cy="34" r="10" fill="#1DA53F" />
                    <path d="M30 34h8M34 30v8" stroke="#fff" stroke-width="2" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="wo-step__num">1</div>
                <h3 class="wo-step__title">Achetez un pack</h3>
                <p class="wo-step__desc">
                  Pour seulement <strong>500 F CFA</strong>, obtenez
                  <strong>33 clés virtuelles</strong> + <strong>1 clé physique</strong>
                  de visite gratuite.
                </p>
              </div>

              <div class="wo-step">
                <div class="wo-step__icon wo-step__icon--2">
                  <svg viewBox="0 0 48 48" width="40" height="40">
                    <rect x="4" y="10" width="40" height="28" rx="4" fill="none" stroke="currentColor" stroke-width="2.5" />
                    <polygon points="20,18 20,30 32,24" fill="#1DA53F" />
                  </svg>
                </div>
                <div class="wo-step__num">2</div>
                <h3 class="wo-step__title">Visionnez les vidéos</h3>
                <p class="wo-step__desc">
                  Chaque vidéo d'un bien immobilier consomme <strong>1 clé virtuelle</strong>.
                  Découvrez les biens comme si vous y étiez.
                </p>
              </div>

              <div class="wo-step">
                <div class="wo-step__icon wo-step__icon--3">
                  <svg viewBox="0 0 48 48" width="40" height="40">
                    <path d="M24 4C16.27 4 10 10.27 10 18c0 10.5 14 26 14 26s14-15.5 14-26C38 10.27 31.73 4 24 4z" fill="none" stroke="currentColor" stroke-width="2.5" />
                    <circle cx="24" cy="18" r="6" fill="#1DA53F" />
                  </svg>
                </div>
                <div class="wo-step__num">3</div>
                <h3 class="wo-step__title">Visitez gratuitement</h3>
                <p class="wo-step__desc">
                  Votre <strong>clé physique</strong> vous donne droit à une
                  <strong>visite gratuite</strong> chez l'agent immobilier de votre choix.
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

          <!-- Pricing highlight -->
          <section class="wo-pricing">
            <div class="wo-pricing__card">
              <div class="wo-pricing__badge">Pack découverte</div>
              <div class="wo-pricing__amount">500 <span class="wo-pricing__currency">F CFA</span></div>
              <ul class="wo-pricing__list">
                <li>
                  <svg viewBox="0 0 20 20" width="18" height="18"><path fill="#1DA53F" d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm-1 14.59l-4.3-4.3 1.41-1.41L9 11.76l5.89-5.89 1.41 1.42L9 13.59z"/></svg>
                  <span><strong>33</strong> clés virtuelles (visionnages vidéo)</span>
                </li>
                <li>
                  <svg viewBox="0 0 20 20" width="18" height="18"><path fill="#1DA53F" d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm-1 14.59l-4.3-4.3 1.41-1.41L9 11.76l5.89-5.89 1.41 1.42L9 13.59z"/></svg>
                  <span><strong>1</strong> visite physique gratuite</span>
                </li>
                <li>
                  <svg viewBox="0 0 20 20" width="18" height="18"><path fill="#1DA53F" d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm-1 14.59l-4.3-4.3 1.41-1.41L9 11.76l5.89-5.89 1.41 1.42L9 13.59z"/></svg>
                  <span>Paiement mobile : Orange Money, Wave, MTN</span>
                </li>
              </ul>
            </div>
          </section>

          <!-- Agents section -->
          <section class="wo-agents">
            <div class="wo-agents__icon">
              <svg viewBox="0 0 48 48" width="36" height="36">
                <path d="M24 4C14.06 4 6 12.06 6 22c0 5.52 2.52 10.44 6.46 13.72A21.9 21.9 0 0024 42a21.9 21.9 0 0011.54-6.28C39.48 32.44 42 27.52 42 22 42 12.06 33.94 4 24 4z" fill="none" stroke="currentColor" stroke-width="2" />
                <circle cx="24" cy="18" r="7" fill="none" stroke="#1DA53F" stroke-width="2" />
                <path d="M12 38c1.5-5 6.5-8.5 12-8.5s10.5 3.5 12 8.5" fill="none" stroke="#1DA53F" stroke-width="2" stroke-linecap="round" />
              </svg>
            </div>
            <h3 class="wo-agents__title">Vous êtes agent immobilier ?</h3>
            <p class="wo-agents__desc">
              Publiez vos biens, recevez des clients qualifiés et gagnez <strong>10 F CFA par visionnage</strong>.
              Inscription gratuite.
            </p>
          </section>
        </div>

        <!-- Footer actions -->
        <div class="wo-footer">
          <button class="wo-btn wo-btn--primary" @click="handleUnderstood">
            J'ai compris, explorer
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
  z-index: 500;
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
  height: 48px;
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

/* ===== Pricing ===== */
.wo-pricing {
  margin-bottom: 24px;
}

.wo-pricing__card {
  background: linear-gradient(135deg, var(--green-light), #f0fdf4);
  border: 1.5px solid var(--green);
  border-radius: 14px;
  padding: 24px;
  text-align: center;
}

.wo-pricing__badge {
  display: inline-block;
  background: var(--green);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  padding: 4px 14px;
  border-radius: 20px;
  margin-bottom: 12px;
}

.wo-pricing__amount {
  font-size: 40px;
  font-weight: 800;
  color: var(--text);
  line-height: 1.1;
  margin-bottom: 16px;
}

.wo-pricing__currency {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-3);
}

.wo-pricing__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 380px;
  margin: 0 auto;
}

.wo-pricing__list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-2);
  text-align: left;
}

.wo-pricing__list li svg {
  flex-shrink: 0;
}

/* ===== Agents callout ===== */
.wo-agents {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  text-align: center;
  margin-bottom: 8px;
}

.wo-agents__icon {
  color: var(--text-2);
  margin-bottom: 8px;
}

.wo-agents__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.wo-agents__desc {
  font-size: 13px;
  color: var(--text-3);
  line-height: 1.5;
  max-width: 400px;
  margin: 0 auto;
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

  .wo-pricing__amount {
    font-size: 32px;
  }

  .wo-footer {
    padding: 12px 20px 16px;
  }

  .wo-logo {
    height: 40px;
  }
}
</style>
