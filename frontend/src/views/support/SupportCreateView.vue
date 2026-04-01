<template>
  <div class="sc">
    <!-- Header -->
    <div class="sc-header">
      <router-link :to="backRoute" class="sc-header__back" title="Retour">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      </router-link>
      <div>
        <h1 class="sc-header__title">Nouveau ticket</h1>
        <p class="sc-header__sub">Décrivez votre demande et nous reviendrons vers vous rapidement.</p>
      </div>
    </div>

    <!-- Stepper -->
    <div class="sc-steps">
      <div class="sc-step" :class="{ 'sc-step--active': step >= 1, 'sc-step--done': step > 1 }">
        <span class="sc-step__dot">1</span>
        <span class="sc-step__label">Catégorie</span>
      </div>
      <div class="sc-step__line" :class="{ 'sc-step__line--active': step > 1 }"></div>
      <div class="sc-step" :class="{ 'sc-step--active': step >= 2, 'sc-step--done': step > 2 }">
        <span class="sc-step__dot">2</span>
        <span class="sc-step__label">Détails</span>
      </div>
      <div class="sc-step__line" :class="{ 'sc-step__line--active': step > 2 }"></div>
      <div class="sc-step" :class="{ 'sc-step--active': step >= 3 }">
        <span class="sc-step__dot">3</span>
        <span class="sc-step__label">Confirmation</span>
      </div>
    </div>

    <form class="sc-form" @submit.prevent="submit">
      <!-- Step 1: Category -->
      <Transition name="fade" mode="out-in">
        <div v-if="step === 1" key="step1" class="sc-section">
          <h2 class="sc-section__title">Quel type de demande ?</h2>
          <p class="sc-section__hint">Sélectionnez la catégorie qui correspond le mieux à votre besoin.</p>
          <div class="sc-cats">
            <button
              v-for="cat in categories" :key="cat.value"
              type="button"
              class="sc-cat" :class="{ 'sc-cat--active': form.category === cat.value }"
              @click="form.category = cat.value"
            >
              <div class="sc-cat__icon" :class="'sc-cat__icon--' + cat.value.toLowerCase()">
                <svg v-if="cat.value === 'BUG'" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M20 8h-2.81a5.985 5.985 0 00-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5c-.49 0-.96.06-1.41.17L8.41 3 7 4.41l1.62 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z"/></svg>
                <svg v-else-if="cat.value === 'SUGGESTION'" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"/></svg>
                <svg v-else-if="cat.value === 'COMPLAINT'" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
                <svg v-else-if="cat.value === 'HELP'" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
                <svg v-else viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
              </div>
              <div class="sc-cat__text">
                <strong>{{ cat.label }}</strong>
                <span>{{ cat.desc }}</span>
              </div>
              <div class="sc-cat__check" v-if="form.category === cat.value">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
              </div>
            </button>
          </div>
          <div class="sc-actions">
            <button type="button" class="sc-btn sc-btn--primary" :disabled="!form.category" @click="step = 2">
              Continuer
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </div>

        <!-- Step 2: Details -->
        <div v-else-if="step === 2" key="step2" class="sc-section">
          <h2 class="sc-section__title">Décrivez votre demande</h2>
          <p class="sc-section__hint">Plus vous êtes précis, plus vite nous pourrons vous aider.</p>

          <div class="sc-field">
            <label for="subject" class="sc-field__label">Sujet <span class="sc-field__req">*</span></label>
            <input
              id="subject" v-model="form.subject" type="text"
              placeholder="Ex : Impossible de publier une annonce"
              maxlength="255" required
              class="sc-field__input"
            />
            <div class="sc-field__footer">
              <span v-if="form.subject.length > 0 && form.subject.trim().length < 3" class="sc-field__error">Minimum 3 caractères</span>
              <span class="sc-field__count">{{ form.subject.length }}/255</span>
            </div>
          </div>

          <div class="sc-field">
            <label for="content" class="sc-field__label">Description <span class="sc-field__req">*</span></label>
            <textarea
              id="content" v-model="form.content"
              placeholder="Expliquez en détail votre problème, les étapes pour le reproduire, ce que vous attendiez..."
              rows="6" required
              class="sc-field__textarea"
            ></textarea>
            <div class="sc-field__footer">
              <span v-if="form.content.length > 0 && form.content.trim().length < 10" class="sc-field__error">Minimum 10 caractères</span>
              <span class="sc-field__count">{{ form.content.length }} car.</span>
            </div>
          </div>

          <div class="sc-actions">
            <button type="button" class="sc-btn sc-btn--ghost" @click="step = 1">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
              Retour
            </button>
            <button type="button" class="sc-btn sc-btn--primary" :disabled="!isStep2Valid" @click="step = 3">
              Continuer
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </div>

        <!-- Step 3: Confirm -->
        <div v-else-if="step === 3" key="step3" class="sc-section">
          <h2 class="sc-section__title">Récapitulatif</h2>
          <p class="sc-section__hint">Vérifiez les informations avant d'envoyer votre ticket.</p>

          <div class="sc-recap">
            <div class="sc-recap__row">
              <span class="sc-recap__label">Catégorie</span>
              <span class="sc-recap__value">{{ selectedCatLabel }}</span>
            </div>
            <div class="sc-recap__row">
              <span class="sc-recap__label">Sujet</span>
              <span class="sc-recap__value">{{ form.subject }}</span>
            </div>
            <div class="sc-recap__row sc-recap__row--full">
              <span class="sc-recap__label">Description</span>
              <p class="sc-recap__text">{{ form.content }}</p>
            </div>
          </div>

          <div v-if="error" class="sc-error">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
            {{ error }}
          </div>

          <div class="sc-actions">
            <button type="button" class="sc-btn sc-btn--ghost" @click="step = 2">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
              Modifier
            </button>
            <button type="submit" class="sc-btn sc-btn--primary" :disabled="submitting || !isValid">
              <svg v-if="!submitting" viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
              <span v-if="submitting" class="sc-btn__spinner"></span>
              {{ submitting ? 'Envoi...' : 'Envoyer le ticket' }}
            </button>
          </div>
        </div>
      </Transition>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSupportStore } from '@/Stores/support'

const router = useRouter()
const route = useRoute()
const support = useSupportStore()

const isAgent = computed(() => route.path.startsWith('/agent'))
const backRoute = computed(() => isAgent.value ? '/agent/support' : '/home/support')

const step = ref(1)

const categories = [
  { value: 'HELP',       label: 'Aide',        desc: 'J\'ai besoin d\'assistance pour utiliser la plateforme' },
  { value: 'BUG',        label: 'Bug',          desc: 'Quelque chose ne fonctionne pas comme prévu' },
  { value: 'SUGGESTION', label: 'Suggestion',   desc: 'J\'ai une idée pour améliorer MonaJent' },
  { value: 'COMPLAINT',  label: 'Réclamation',  desc: 'Je souhaite signaler un problème important' },
  { value: 'OTHER',      label: 'Autre',        desc: 'Ma demande ne correspond à aucune catégorie' },
]

const form = reactive({ category: '', subject: '', content: '' })
const submitting = ref(false)
const error = ref('')

const selectedCatLabel = computed(() => categories.find(c => c.value === form.category)?.label || '')

const isStep2Valid = computed(() =>
  form.subject.trim().length >= 3 && form.content.trim().length >= 10
)

const isValid = computed(() =>
  form.category && isStep2Valid.value
)

async function submit() {
  if (!isValid.value || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const ticket = await support.createTicket({
      category: form.category,
      subject: form.subject.trim(),
      content: form.content.trim(),
    })
    router.push(isAgent.value ? `/agent/support/${ticket.id}` : `/home/support/${ticket.id}`)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Erreur lors de la création du ticket. Veuillez réessayer.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.sc {
  max-width: 680px;
  margin: 0 auto;
  padding: 28px 16px 40px;
}

/* ── Header ──────────────────────────────── */
.sc-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 28px;
}
.sc-header__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: #374151;
  text-decoration: none;
  transition: background 0.15s;
  flex-shrink: 0;
  margin-top: 2px;
}
.sc-header__back:hover { background: #F3F4F6; }
.sc-header__title {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
  letter-spacing: -0.2px;
}
.sc-header__sub {
  font-size: 14px;
  color: #6B7280;
  margin-top: 2px;
}

/* ── Stepper ─────────────────────────────── */
.sc-steps {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 28px;
  padding: 0 8px;
}
.sc-step {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sc-step__dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: #F3F4F6;
  color: #9CA3AF;
  transition: all 0.3s;
}
.sc-step--active .sc-step__dot {
  background: #1DA53F;
  color: #fff;
}
.sc-step--done .sc-step__dot {
  background: #DCFCE7;
  color: #16A34A;
}
.sc-step__label {
  font-size: 13px;
  font-weight: 500;
  color: #9CA3AF;
  transition: color 0.3s;
}
.sc-step--active .sc-step__label { color: #111827; }
.sc-step--done .sc-step__label { color: #16A34A; }
.sc-step__line {
  flex: 1;
  height: 2px;
  background: #E5E7EB;
  margin: 0 8px;
  border-radius: 2px;
  transition: background 0.3s;
}
.sc-step__line--active { background: #1DA53F; }

/* ── Section ─────────────────────────────── */
.sc-section { }
.sc-section__title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}
.sc-section__hint {
  font-size: 14px;
  color: #6B7280;
  margin-bottom: 20px;
}

/* ── Categories ──────────────────────────── */
.sc-cats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}
.sc-cat {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  width: 100%;
}
.sc-cat:hover { border-color: #C3E6CB; background: #FAFFFE; }
.sc-cat--active {
  border-color: #1DA53F;
  background: #F0FDF4;
  box-shadow: 0 0 0 3px rgba(29,165,63,.1);
}

.sc-cat__icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sc-cat__icon--bug { background: #FEE2E2; color: #DC2626; }
.sc-cat__icon--suggestion { background: #FEF3C7; color: #D97706; }
.sc-cat__icon--complaint { background: #FFE4E6; color: #E11D48; }
.sc-cat__icon--help { background: #DBEAFE; color: #2563EB; }
.sc-cat__icon--other { background: #F3F4F6; color: #6B7280; }

.sc-cat__text {
  flex: 1;
  min-width: 0;
}
.sc-cat__text strong {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 2px;
}
.sc-cat__text span {
  font-size: 13px;
  color: #6B7280;
  line-height: 1.4;
}
.sc-cat__check {
  color: #1DA53F;
  flex-shrink: 0;
}

/* ── Form fields ─────────────────────────── */
.sc-field {
  margin-bottom: 20px;
}
.sc-field__label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
}
.sc-field__req { color: #EF4444; }
.sc-field__input,
.sc-field__textarea {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  font-size: 14px;
  color: #111827;
  background: #fff;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.sc-field__input:focus,
.sc-field__textarea:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.1);
}
.sc-field__input::placeholder,
.sc-field__textarea::placeholder { color: #9CA3AF; }
.sc-field__textarea { resize: vertical; min-height: 130px; line-height: 1.6; }

.sc-field__footer {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  padding: 0 2px;
}
.sc-field__count { font-size: 11px; color: #D1D5DB; margin-left: auto; }
.sc-field__error { font-size: 12px; color: #EF4444; }

/* ── Recap ───────────────────────────────── */
.sc-recap {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.sc-recap__row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 8px 0;
}
.sc-recap__row:not(:last-child) { border-bottom: 1px solid #F3F4F6; }
.sc-recap__row--full { flex-direction: column; gap: 4px; }
.sc-recap__label {
  font-size: 12px;
  font-weight: 600;
  color: #9CA3AF;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  min-width: 90px;
}
.sc-recap__value { font-size: 14px; color: #111827; font-weight: 500; }
.sc-recap__text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

/* ── Error ───────────────────────────────── */
.sc-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 10px;
  color: #DC2626;
  font-size: 13px;
  margin-bottom: 16px;
}

/* ── Actions ─────────────────────────────── */
.sc-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 4px;
}
.sc-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}
.sc-btn--primary {
  background: #1DA53F;
  color: #fff;
  box-shadow: 0 1px 3px rgba(29,165,63,.25);
}
.sc-btn--primary:hover:not(:disabled) { background: #178A33; }
.sc-btn--primary:active:not(:disabled) { transform: scale(0.97); }
.sc-btn--primary:disabled { opacity: 0.4; cursor: not-allowed; }
.sc-btn--ghost {
  background: transparent;
  color: #6B7280;
  border: 1px solid #E5E7EB;
}
.sc-btn--ghost:hover { border-color: #111827; color: #111827; }

.sc-btn__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Transitions ─────────────────────────── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from { opacity: 0; transform: translateX(20px); }
.fade-leave-to { opacity: 0; transform: translateX(-20px); }

/* ── Responsive ──────────────────────────── */
@media (max-width: 640px) {
  .sc { padding: 20px 12px 32px; }
  .sc-step__label { display: none; }
  .sc-cat { padding: 12px 14px; }
  .sc-cat__icon { width: 36px; height: 36px; }
}
</style>
