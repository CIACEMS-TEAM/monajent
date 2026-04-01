<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '@/Stores/agent'
import { useToast } from 'vue-toastification'
import logoUrl from '@/assets/icons/logo_monajent_header.webp'

const URL = globalThis.URL
const router = useRouter()
const agent = useAgentStore()
const toast = useToast()

const step = ref(0)
const totalSteps = 5
const saving = ref(false)
const acceptedAgentConditions = ref(false)

const form = reactive({
  agency_name: '',
  bio: '',
  contact_phone: '',
  contact_email: '',
  profilePhoto: null as File | null,
  kycDocType: 'CNI' as string,
  kycRecto: null as File | null,
  kycVerso: null as File | null,
  kycSingle: null as File | null,
})

const photoInput = ref<HTMLInputElement | null>(null)
const rectoInput = ref<HTMLInputElement | null>(null)
const versoInput = ref<HTMLInputElement | null>(null)
const singleInput = ref<HTMLInputElement | null>(null)

const needsTwoSides = computed(() => form.kycDocType === 'CNI')

const KYC_MAX_SIZE = 5 * 1024 * 1024
const KYC_ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'pdf']

function validateKycFile(file: File): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!KYC_ALLOWED_EXT.includes(ext)) {
    toast.error('Format non supporté. Utilisez JPG, PNG ou PDF.')
    return false
  }
  if (file.size > KYC_MAX_SIZE) {
    toast.error('Le fichier dépasse 5 Mo. Veuillez réduire sa taille.')
    return false
  }
  return true
}

function handlePhotoChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) form.profilePhoto = f
}
function handleRectoChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f && validateKycFile(f)) form.kycRecto = f
}
function handleVersoChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f && validateKycFile(f)) form.kycVerso = f
}
function handleSingleChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f && validateKycFile(f)) form.kycSingle = f
}

const canProceed = computed(() => {
  if (step.value === 1) return acceptedAgentConditions.value
  if (step.value === 2) return !!form.agency_name.trim()
  if (step.value === 3) return !!(form.contact_phone.trim() || form.contact_email.trim())
  return true
})

onMounted(async () => {
  if (!agent.profile) {
    try { await agent.fetchProfile() } catch (_) {}
  }
  if (agent.profile) {
    form.agency_name = agent.profile.agency_name || ''
    form.bio = agent.profile.bio || ''
    form.contact_phone = agent.profile.contact_phone || ''
    form.contact_email = agent.profile.contact_email || ''
    acceptedAgentConditions.value = agent.profile.accepted_agent_conditions || false
  }
})

async function next() {
  if (step.value >= 1 && step.value <= 3 && !canProceed.value) {
    const msgs: Record<number, string> = {
      1: 'Vous devez accepter les conditions spécifiques agents.',
      2: 'Le nom d\'agence est obligatoire.',
      3: 'Au moins un moyen de contact est requis.',
    }
    toast.error(msgs[step.value] || 'Champ requis')
    return
  }

  saving.value = true
  try {
    if (step.value === 1) {
      await agent.acceptAgentConditions()
    } else if (step.value === 2) {
      const payload: Record<string, any> = { agency_name: form.agency_name, bio: form.bio }
      if (form.profilePhoto) payload.profile_photo = form.profilePhoto
      await agent.updateProfile(payload)
    } else if (step.value === 3) {
      await agent.updateProfile({ contact_phone: form.contact_phone, contact_email: form.contact_email })
    } else if (step.value === 4) {
      await uploadKycDocuments()
    }
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Erreur lors de la sauvegarde')
  }
  saving.value = false

  if (step.value < totalSteps - 1) step.value++
  else router.push('/agent')
}

async function uploadKycDocuments() {
  if (needsTwoSides.value) {
    if (form.kycRecto) await agent.uploadDocument(form.kycRecto, form.kycDocType, 'RECTO')
    if (form.kycVerso) await agent.uploadDocument(form.kycVerso, form.kycDocType, 'VERSO')
  } else {
    if (form.kycSingle) await agent.uploadDocument(form.kycSingle, form.kycDocType, 'SINGLE')
  }
}

function skipKyc() {
  if (step.value === 4) {
    router.push('/agent')
  }
}
</script>

<template>
  <div class="ob-page">
    <header class="ob-header">
      <router-link to="/agent" class="ob-logo">
        <img :src="logoUrl" alt="MonaJent" />
        <span class="ob-logo__studio">Studio</span>
      </router-link>
    </header>

    <div class="ob-body">
      <div class="ob-progress">
        <div v-for="i in totalSteps" :key="i" class="ob-progress__dot" :class="{ active: i - 1 <= step }"></div>
      </div>

      <!-- Step 0: Welcome -->
      <div v-if="step === 0" class="ob-step">
        <div class="ob-step__icon">
          <svg viewBox="0 0 64 64" width="80" height="80">
            <circle cx="32" cy="32" r="30" fill="rgba(29,165,63,0.1)" stroke="#1DA53F" stroke-width="2"/>
            <path fill="#1DA53F" d="M24 18l20 14-20 14V18z"/>
          </svg>
        </div>
        <h1 class="ob-step__title">Bienvenue sur MonaJent Studio</h1>
        <p class="ob-step__desc">Configurons votre espace agent en quelques étapes pour que vos clients puissent vous trouver.</p>
        <div class="ob-step__features">
          <div class="ob-feature"><svg viewBox="0 0 24 24" width="28" height="28"><path fill="#1DA53F" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg><span>Publiez vos annonces vidéo</span></div>
          <div class="ob-feature"><svg viewBox="0 0 24 24" width="28" height="28"><path fill="#1DA53F" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg><span>Suivez vos statistiques</span></div>
          <div class="ob-feature"><svg viewBox="0 0 24 24" width="28" height="28"><path fill="#1DA53F" d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg><span>Gérez vos revenus</span></div>
        </div>
      </div>

      <!-- Step 1: Conditions spécifiques agents (OBLIGATOIRE) -->
      <div v-else-if="step === 1" class="ob-step">
        <div class="ob-step__icon">
          <svg viewBox="0 0 64 64" width="80" height="80">
            <circle cx="32" cy="32" r="30" fill="rgba(29,165,63,0.1)" stroke="#1DA53F" stroke-width="2"/>
            <path fill="#1DA53F" d="M20 16h24v4H20zm0 8h24v4H20zm0 8h16v4H20z"/>
          </svg>
        </div>
        <h1 class="ob-step__title">Conditions d'utilisation agent</h1>
        <p class="ob-step__desc">Avant de configurer votre profil, veuillez prendre connaissance des conditions applicables aux agents partenaires Monajent.</p>

        <div class="ob-conditions">
          <div class="ob-conditions__item">
            <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#1DA53F" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
            <span>Publier uniquement des biens <strong>réels et disponibles</strong></span>
          </div>
          <div class="ob-conditions__item">
            <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#1DA53F" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
            <span>Assurer les <strong>visites physiques</strong> programmées</span>
          </div>
          <div class="ob-conditions__item">
            <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#1DA53F" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
            <span>Fournir des informations <strong>exactes</strong> sur les biens</span>
          </div>
          <div class="ob-conditions__item">
            <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#1DA53F" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
            <span>Respecter les utilisateurs et la charte de la plateforme</span>
          </div>
        </div>

        <a href="/legal/conditions-agents" target="_blank" class="ob-conditions__link">
          <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
          Lire les conditions complètes
        </a>

        <div class="ob-conditions__accept">
          <label class="ob-consent">
            <input type="checkbox" v-model="acceptedAgentConditions" />
            <span>J'accepte les <strong>conditions spécifiques applicables aux agents</strong> Monajent</span>
          </label>
        </div>
      </div>

      <!-- Step 2: Profile (OBLIGATOIRE) -->
      <div v-else-if="step === 2" class="ob-step">
        <h1 class="ob-step__title">Votre profil agence</h1>
        <p class="ob-step__desc">Ces informations seront visibles par les clients.</p>
        <div class="ob-form">
          <div class="ob-form__group">
            <label>Photo de profil</label>
            <div class="ob-form__photo">
              <div class="ob-form__photo-circle">
                <img v-if="form.profilePhoto" :src="URL.createObjectURL(form.profilePhoto)" alt="" class="ob-form__photo-img" />
                <img v-else-if="agent.profilePhoto" :src="agent.profilePhoto" alt="" class="ob-form__photo-img" />
                <svg v-else viewBox="0 0 24 24" width="32" height="32"><path fill="#aaa" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
              </div>
              <div>
                <input ref="photoInput" type="file" accept="image/*" hidden @change="handlePhotoChange" />
                <button class="ob-form__photo-btn" type="button" @click="photoInput?.click()">
                  {{ form.profilePhoto ? form.profilePhoto.name : 'Importer une photo' }}
                </button>
              </div>
            </div>
          </div>
          <div class="ob-form__group">
            <label>Nom de l'agence / indépendant <span class="ob-required">*</span></label>
            <input v-model="form.agency_name" placeholder="Ex: Immobilière Prestige CI" />
          </div>
          <div class="ob-form__group">
            <label>Bio / Description</label>
            <textarea v-model="form.bio" placeholder="Décrivez votre agence en quelques mots..." rows="3"></textarea>
          </div>
        </div>
      </div>

      <!-- Step 3: Contact (OBLIGATOIRE) -->
      <div v-else-if="step === 3" class="ob-step">
        <h1 class="ob-step__title">Coordonnées de contact</h1>
        <p class="ob-step__desc">Comment vos clients peuvent vous joindre. <span class="ob-required">Au moins un champ requis.</span></p>
        <div class="ob-form">
          <div class="ob-form__group">
            <label>Téléphone de contact</label>
            <input v-model="form.contact_phone" placeholder="+2250700112233" />
          </div>
          <div class="ob-form__group">
            <label>Email de contact</label>
            <input v-model="form.contact_email" type="email" placeholder="contact@monagence.com" />
          </div>
        </div>
      </div>

      <!-- Step 4: KYC (OPTIONNEL) -->
      <div v-else-if="step === 4" class="ob-step">
        <h1 class="ob-step__title">Vérification d'identité (KYC)</h1>
        <p class="ob-step__desc">
          Soumettez une pièce d'identité pour obtenir le badge vérifié et pouvoir publier vos annonces.
          <strong>Cette étape peut être faite plus tard depuis vos paramètres.</strong>
        </p>

        <div class="ob-form">
          <div class="ob-form__group">
            <label>Type de document</label>
            <select v-model="form.kycDocType" class="ob-select">
              <option value="CNI">Carte Nationale d'Identité</option>
              <option value="PASSPORT">Passeport</option>
              <option value="PERMIT">Permis de conduire</option>
              <option value="OTHER">Autre</option>
            </select>
          </div>

          <p class="ob-form__hint">Formats acceptés : <strong>JPG, PNG, PDF</strong> — Taille max : <strong>5 Mo</strong> par fichier</p>

          <template v-if="needsTwoSides">
            <div class="ob-form__group">
              <label>Recto (face avant) <span class="ob-required">*</span></label>
              <div class="ob-form__upload" @click="rectoInput?.click()">
                <input ref="rectoInput" type="file" accept=".jpg,.jpeg,.png,.pdf" hidden @change="handleRectoChange" />
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#aaa" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/></svg>
                <span v-if="form.kycRecto" class="ob-form__upload-name">{{ form.kycRecto.name }}</span>
                <span v-else>Importer le recto</span>
              </div>
            </div>
            <div class="ob-form__group">
              <label>Verso (face arrière) <span class="ob-required">*</span></label>
              <div class="ob-form__upload" @click="versoInput?.click()">
                <input ref="versoInput" type="file" accept=".jpg,.jpeg,.png,.pdf" hidden @change="handleVersoChange" />
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#aaa" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/></svg>
                <span v-if="form.kycVerso" class="ob-form__upload-name">{{ form.kycVerso.name }}</span>
                <span v-else>Importer le verso</span>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="ob-form__group">
              <label>Document <span class="ob-required">*</span></label>
              <div class="ob-form__upload" @click="singleInput?.click()">
                <input ref="singleInput" type="file" accept=".jpg,.jpeg,.png,.pdf" hidden @change="handleSingleChange" />
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#aaa" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/></svg>
                <span v-if="form.kycSingle" class="ob-form__upload-name">{{ form.kycSingle.name }}</span>
                <span v-else>Importer le document</span>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Actions -->
      <div class="ob-actions">
        <button v-if="step > 0" class="ob-actions__back" @click="step--">Retour</button>
        <div class="ob-actions__right">
          <button v-if="step === 4" class="ob-actions__skip" @click="skipKyc">Faire la vérification plus tard</button>
          <button
            class="ob-actions__next"
            :disabled="saving || (step >= 1 && step <= 3 && !canProceed)"
            @click="next"
          >
            {{ saving ? 'Enregistrement...' : step === totalSteps - 1 ? 'Soumettre et terminer' : 'Continuer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ob-page { min-height: 100vh; background: #fff; }
.ob-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 24px; border-bottom: 1px solid #E0E0E0;
}
.ob-logo { display: flex; align-items: center; gap: 6px; text-decoration: none; }
.ob-logo img { height: 28px; width: auto; }
.ob-logo__studio { font-size: 18px; font-weight: 500; color: #606060; }

.ob-body { max-width: 640px; margin: 0 auto; padding: 40px 24px 80px; }

.ob-progress { display: flex; gap: 8px; margin-bottom: 40px; }
.ob-progress__dot { flex: 1; height: 4px; border-radius: 2px; background: #E0E0E0; transition: background .3s; }
.ob-progress__dot.active { background: #1DA53F; }

.ob-step { text-align: center; }
.ob-step__icon { margin-bottom: 24px; }
.ob-step__title { font-size: 28px; font-weight: 700; color: #0F0F0F; margin-bottom: 12px; }
.ob-step__desc { font-size: 16px; color: #272727; line-height: 1.6; max-width: 480px; margin: 0 auto 32px; }
.ob-required { color: #dc2626; font-weight: 600; }

.ob-step__features { display: flex; flex-direction: column; gap: 16px; max-width: 360px; margin: 0 auto; text-align: left; }
.ob-feature { display: flex; align-items: center; gap: 14px; padding: 14px 18px; border: 1px solid #E0E0E0; border-radius: 12px; font-size: 15px; color: #0F0F0F; }

.ob-form { text-align: left; display: flex; flex-direction: column; gap: 20px; max-width: 480px; margin: 0 auto; }
.ob-form__group label { display: block; font-size: 14px; font-weight: 500; color: #272727; margin-bottom: 6px; }
.ob-form__group input,
.ob-form__group textarea,
.ob-select {
  width: 100%; padding: 12px 14px; border: 1px solid #E0E0E0; border-radius: 8px;
  font-size: 15px; color: #0F0F0F; box-sizing: border-box; background: #fff;
}
.ob-form__group input:focus, .ob-form__group textarea:focus, .ob-select:focus {
  outline: none; border-color: #1DA53F; box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}
.ob-form__group textarea { resize: vertical; }

.ob-form__photo { display: flex; align-items: center; gap: 16px; }
.ob-form__photo-circle {
  width: 64px; height: 64px; border-radius: 50%; background: #f2f2f2;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; overflow: hidden;
}
.ob-form__photo-btn {
  padding: 8px 16px; border: 1px solid #E0E0E0; border-radius: 8px; background: #fff;
  cursor: pointer; font-size: 14px; color: #1DA53F; font-weight: 500; transition: background .15s;
}
.ob-form__photo-btn:hover { background: rgba(29,165,63,.06); }
.ob-form__photo-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }

.ob-form__upload {
  border: 2px dashed #E0E0E0; border-radius: 12px; padding: 28px;
  text-align: center; cursor: pointer; color: #606060; font-size: 14px;
  display: flex; flex-direction: column; align-items: center; gap: 8px; transition: border-color .15s;
}
.ob-form__upload:hover { border-color: #1DA53F; }
.ob-form__upload-name { font-weight: 600; color: #1DA53F; word-break: break-all; }
.ob-form__hint {
  font-size: 13px; color: #606060; margin: 0; padding: 8px 12px;
  background: #f8f9fa; border-radius: 8px; border-left: 3px solid #1DA53F;
}

.ob-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 48px; }
.ob-actions__right { display: flex; gap: 12px; margin-left: auto; flex-wrap: wrap; }
.ob-actions__back { padding: 10px 20px; border: none; background: none; font-size: 14px; color: #606060; cursor: pointer; }
.ob-actions__back:hover { color: #0F0F0F; }
.ob-actions__skip {
  padding: 10px 20px; border: 1px solid #E0E0E0; border-radius: 20px; background: #fff;
  font-size: 14px; color: #272727; cursor: pointer; transition: background .15s;
}
.ob-actions__skip:hover { background: #f2f2f2; }
.ob-actions__next {
  padding: 10px 24px; border: none; border-radius: 20px; background: #1DA53F;
  color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: background .15s;
}
.ob-actions__next:hover { background: #178A33; }
.ob-actions__next:disabled { opacity: .5; cursor: not-allowed; }

.ob-conditions { display: flex; flex-direction: column; gap: 14px; max-width: 480px; margin: 0 auto 24px; text-align: left; }
.ob-conditions__item { display: flex; align-items: flex-start; gap: 12px; padding: 12px 16px; border: 1px solid #E0E0E0; border-radius: 10px; font-size: 15px; color: #272727; line-height: 1.5; }
.ob-conditions__item svg { flex-shrink: 0; margin-top: 1px; }
.ob-conditions__link {
  display: inline-flex; align-items: center; gap: 6px;
  color: #1DA53F; font-size: 14px; font-weight: 500; text-decoration: none;
  margin-bottom: 24px;
}
.ob-conditions__link:hover { text-decoration: underline; }
.ob-conditions__accept { max-width: 480px; margin: 0 auto; text-align: left; }
.ob-consent {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px; border: 2px solid #E0E0E0; border-radius: 12px;
  cursor: pointer; transition: border-color .2s; font-size: 15px; color: #272727; line-height: 1.5;
}
.ob-consent:has(input:checked) { border-color: #1DA53F; background: rgba(29,165,63,.04); }
.ob-consent input[type="checkbox"] { margin-top: 2px; width: 20px; height: 20px; accent-color: #1DA53F; flex-shrink: 0; cursor: pointer; }

@media (max-width: 600px) {
  .ob-step__title { font-size: 22px; }
  .ob-body { padding: 24px 16px 60px; }
  .ob-actions__right { flex-direction: column; align-items: stretch; }
}
</style>
