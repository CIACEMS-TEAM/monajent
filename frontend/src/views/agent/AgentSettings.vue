<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { useAgentStore } from '@/Stores/agent'
import { useAuthStore } from '@/Stores/auth'
import http, { mediaUrl } from '@/services/http'
import PdfThumbnail from '@/components/PdfThumbnail.vue'

const agent = useAgentStore()
const auth = useAuthStore()
const toast = useToast()

const tab = ref<'profile' | 'kyc' | 'security'>('profile')

const profileForm = reactive({
  agency_name: '',
  bio: '',
  contact_phone: '',
  contact_email: '',
})

const saving = ref(false)
const saved = ref(false)
const saveError = ref('')

function syncFormFromProfile() {
  if (!agent.profile) return
  profileForm.agency_name = agent.profile.agency_name || ''
  profileForm.bio = agent.profile.bio || ''
  profileForm.contact_phone = agent.profile.contact_phone || ''
  profileForm.contact_email = agent.profile.contact_email || ''
}

watch(() => agent.profile, syncFormFromProfile, { immediate: true })

onMounted(async () => {
  if (!agent.profile) {
    try { await agent.fetchProfile() } catch (_) {}
  }
  if (!agent.wallet) {
    try { await agent.fetchWallet() } catch (_) {}
  }
  syncFormFromProfile()
})

async function saveProfile() {
  saving.value = true
  saveError.value = ''
  try {
    await agent.updateProfile({
      agency_name: profileForm.agency_name,
      bio: profileForm.bio,
      contact_phone: profileForm.contact_phone,
      contact_email: profileForm.contact_email,
    })
    saved.value = true
    setTimeout(() => saved.value = false, 3000)
  } catch (e: any) {
    saveError.value = e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join(', ')
      || 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

// ─── Photo de profil ────────────────────────────
const photoInput = ref<HTMLInputElement | null>(null)
const uploadingPhoto = ref(false)
const photoFileName = ref('')
const photoUploaded = ref(false)
const photoError = ref('')

async function handlePhotoUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  photoFileName.value = file.name
  photoUploaded.value = false
  photoError.value = ''
  uploadingPhoto.value = true
  try {
    await agent.updateProfile({ profile_photo: file })
    photoUploaded.value = true
    setTimeout(() => photoUploaded.value = false, 5000)
  } catch (_) {
    photoError.value = 'Erreur lors de l\'envoi'
  }
  uploadingPhoto.value = false
}

// ─── Documents KYC ──────────────────────────────
const kycDocType = ref('CNI')
const uploadingSlot = ref<string | null>(null)
const rectoInput = ref<HTMLInputElement | null>(null)
const versoInput = ref<HTMLInputElement | null>(null)
const singleInput = ref<HTMLInputElement | null>(null)

const needsTwoSides = computed(() => kycDocType.value === 'CNI')

function docUrl(path: string | null | undefined): string {
  return mediaUrl(path) || ''
}

function isImage(path: string): boolean {
  return /\.(jpe?g|png|gif|webp|bmp|svg)$/i.test(path)
}

function isPdf(path: string): boolean {
  return /\.pdf$/i.test(path)
}

function getDoc(side: string) {
  return agent.documents.find(d => d.doc_type === kycDocType.value && d.side === side)
}

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

const submittingKyc = ref(false)

const kycDocsReady = computed(() => {
  if (needsTwoSides.value) {
    return !!getDoc('RECTO') && !!getDoc('VERSO')
  }
  return !!getDoc('SINGLE')
})

async function doSubmitKyc() {
  submittingKyc.value = true
  try {
    await agent.submitKyc()
    toast.success('Documents soumis pour vérification')
  } catch (err: any) {
    toast.error(err?.response?.data?.detail || 'Erreur lors de la soumission')
  }
  submittingKyc.value = false
}

async function handleKycUpload(e: Event, side: string) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!validateKycFile(file)) {
    (e.target as HTMLInputElement).value = ''
    return
  }
  uploadingSlot.value = side
  try {
    await agent.uploadDocument(file, kycDocType.value, side)
    toast.success('Document envoyé')
  } catch (err: any) {
    toast.error(err?.response?.data?.detail || err?.response?.data?.file?.[0] || 'Erreur lors de l\'envoi')
  }
  uploadingSlot.value = null
  const input = e.target as HTMLInputElement
  if (input) input.value = ''
}

// ─── Password Change ────────────────────────────
const pwdForm = reactive({ current_password: '', new_password: '', new_password_confirm: '' })
const pwdLoading = ref(false)
const showCurrentPwd = ref(false)
const showNewPwd = ref(false)
const showConfirmPwd = ref(false)

async function changePassword() {
  if (!pwdForm.current_password || !pwdForm.new_password) {
    toast.error('Remplissez tous les champs')
    return
  }
  if (pwdForm.new_password.length < 8) {
    toast.error('Le nouveau mot de passe doit contenir au moins 8 caractères')
    return
  }
  if (pwdForm.new_password !== pwdForm.new_password_confirm) {
    toast.error('Les mots de passe ne correspondent pas')
    return
  }
  pwdLoading.value = true
  try {
    await http.post('/api/auth/password/change', {
      current_password: pwdForm.current_password,
      new_password: pwdForm.new_password,
    })
    toast.success('Mot de passe modifié avec succès')
    pwdForm.current_password = ''
    pwdForm.new_password = ''
    pwdForm.new_password_confirm = ''
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Erreur lors du changement de mot de passe')
  } finally {
    pwdLoading.value = false
  }
}

// ─── PIN Wallet ─────────────────────────────────
const showPinModal = ref<'set' | 'change' | null>(null)
const pinForm = reactive({ pin: '', pin_confirm: '', current_pin: '', new_pin: '', new_pin_confirm: '' })
const pinLoading = ref(false)

function openSetPin() {
  pinForm.pin = ''
  pinForm.pin_confirm = ''
  showPinModal.value = 'set'
}

function openChangePin() {
  pinForm.current_pin = ''
  pinForm.new_pin = ''
  pinForm.new_pin_confirm = ''
  showPinModal.value = 'change'
}

async function submitSetPin() {
  if (pinForm.pin.length !== 4 || pinForm.pin_confirm.length !== 4) {
    toast.error('Le PIN doit contenir 4 chiffres')
    return
  }
  pinLoading.value = true
  try {
    await agent.setPin(pinForm.pin, pinForm.pin_confirm)
    toast.success('Code PIN configuré avec succès')
    showPinModal.value = null
  } catch (e: any) {
    const detail = e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join(', ')
    toast.error(detail || 'Erreur de configuration du PIN')
  } finally {
    pinLoading.value = false
  }
}

async function submitChangePin() {
  if (pinForm.new_pin.length !== 4 || pinForm.new_pin_confirm.length !== 4) {
    toast.error('Le PIN doit contenir 4 chiffres')
    return
  }
  pinLoading.value = true
  try {
    await agent.changePin(pinForm.current_pin, pinForm.new_pin, pinForm.new_pin_confirm)
    toast.success('Code PIN modifié avec succès')
    showPinModal.value = null
  } catch (e: any) {
    const detail = e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join(', ')
    toast.error(detail || 'Erreur de modification du PIN')
  } finally {
    pinLoading.value = false
  }
}
</script>

<template>
  <div class="stg">
    <h1 class="stg__title">Paramètres</h1>

    <div class="stg__tabs">
      <button class="stg__tab" :class="{ active: tab === 'profile' }" @click="tab = 'profile'">Profil</button>
      <button class="stg__tab" :class="{ active: tab === 'kyc' }" @click="tab = 'kyc'">Vérification KYC</button>
      <button class="stg__tab" :class="{ active: tab === 'security' }" @click="tab = 'security'">Sécurité</button>
    </div>

    <!-- ═══ Profile tab ═══ -->
    <div v-if="tab === 'profile'" class="stg__content">
      <section class="stg__card">
        <h2 class="stg__card-title">Photo de profil</h2>
        <div class="stg__photo-row">
          <div class="stg__photo-circle">
            <img v-if="agent.profilePhoto" :src="agent.profilePhoto" alt="Photo" class="stg__photo-img" />
            <span v-else class="stg__photo-initials">
              {{ (agent.agencyName || auth.me?.username || 'A').charAt(0).toUpperCase() }}
            </span>
          </div>
          <div class="stg__photo-actions">
            <input ref="photoInput" type="file" accept="image/*" hidden @change="handlePhotoUpload" />
            <button class="stg__photo-btn" :disabled="uploadingPhoto" @click="photoInput?.click()">
              {{ uploadingPhoto ? 'Envoi en cours...' : 'Modifier la photo' }}
            </button>
            <div v-if="photoFileName && !photoUploaded && !photoError && !uploadingPhoto" class="stg__photo-file">
              <svg viewBox="0 0 24 24" width="14" height="14"><path fill="#606060" d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/></svg>
              {{ photoFileName }}
            </div>
            <div v-if="uploadingPhoto" class="stg__photo-status uploading">
              <span class="stg__photo-spinner"></span> Chargement de {{ photoFileName }}...
            </div>
            <div v-if="photoUploaded" class="stg__photo-status success">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#1DA53F" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
              Photo mise à jour avec succès
            </div>
            <div v-if="photoError" class="stg__photo-status error">
              <svg viewBox="0 0 24 24" width="16" height="16"><path fill="#dc2626" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
              {{ photoError }}
            </div>
            <p v-if="!uploadingPhoto && !photoUploaded && !photoError" class="stg__photo-hint">Taille recommandée : 200x200px, formats JPG ou PNG</p>
          </div>
        </div>
      </section>

      <section class="stg__card">
        <h2 class="stg__card-title">Informations de l'agence</h2>
        <form class="stg__form" @submit.prevent="saveProfile">
          <div class="stg__field">
            <label>Nom de l'agence</label>
            <input v-model="profileForm.agency_name" placeholder="Votre agence" />
          </div>
          <div class="stg__field">
            <label>Bio / Description</label>
            <textarea v-model="profileForm.bio" rows="3" placeholder="Décrivez votre activité..."></textarea>
          </div>
          <div class="stg__field-row">
            <div class="stg__field">
              <label>Téléphone de contact</label>
              <input v-model="profileForm.contact_phone" placeholder="+2250700..." />
            </div>
            <div class="stg__field">
              <label>Email de contact</label>
              <input v-model="profileForm.contact_email" type="email" placeholder="contact@agence.com" />
            </div>
          </div>
          <div class="stg__form-footer">
            <span v-if="saveError" class="stg__error">{{ saveError }}</span>
            <span v-if="saved" class="stg__saved">Modifications enregistrées</span>
            <button class="stg__save-btn" type="submit" :disabled="saving">
              {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
            </button>
          </div>
        </form>
      </section>
    </div>

    <!-- ═══ KYC tab ═══ -->
    <div v-else-if="tab === 'kyc'" class="stg__content">
      <!-- Status banner -->
      <section class="stg__card">
        <h2 class="stg__card-title">Statut de vérification</h2>
        <div class="stg__kyc-status">
          <div v-if="agent.kycStatus === 'APPROVED'" class="stg__kyc-badge verified">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#1DA53F" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
            <span>Identité vérifiée — Vous pouvez publier vos annonces</span>
          </div>
          <div v-else-if="agent.kycStatus === 'PENDING'" class="stg__kyc-badge pending">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#d97706" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 13h-2v-2h2v2zm0-4h-2V7h2v4z"/></svg>
            <span>Documents soumis — En attente de vérification par notre équipe</span>
          </div>
          <div v-else-if="agent.kycStatus === 'REJECTED'" class="stg__kyc-badge rejected">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#dc2626" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
            <div>
              <strong>Vérification rejetée</strong>
              <p v-if="agent.kycRejectionReason" class="stg__kyc-reject-reason">{{ agent.kycRejectionReason }}</p>
              <p class="stg__kyc-reject-hint">Veuillez soumettre un document officiel, lisible et en cours de validité.</p>
            </div>
          </div>
          <div v-else class="stg__kyc-badge none">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#606060" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
            <span>Non vérifié — Chargez vos documents puis cliquez sur « Soumettre »</span>
          </div>
        </div>
      </section>

      <!-- Documents KYC -->
      <section class="stg__card">
        <h2 class="stg__card-title">Pièce d'identité</h2>

        <div class="stg__field" style="max-width:400px;margin-bottom:20px">
          <label>Type de document</label>
          <select v-model="kycDocType" :disabled="!agent.isKycEditable" class="stg__select">
            <option value="CNI">Carte Nationale d'Identité</option>
            <option value="PASSPORT">Passeport</option>
            <option value="PERMIT">Permis de conduire</option>
            <option value="OTHER">Autre</option>
          </select>
        </div>

        <p v-if="agent.isKycEditable" class="stg__kyc-hint">Formats acceptés : <strong>JPG, PNG, PDF</strong> — Taille maximale : <strong>5 Mo</strong> par fichier</p>

        <!-- Upload slots -->
        <div class="stg__kyc-slots">
          <template v-if="needsTwoSides">
            <div class="stg__kyc-slot" v-for="side in (['RECTO', 'VERSO'] as const)" :key="side">
              <h3 class="stg__kyc-slot-title">{{ side === 'RECTO' ? 'Recto (face avant)' : 'Verso (face arrière)' }}</h3>
              <div v-if="getDoc(side)" class="stg__kyc-slot-doc">
                <a :href="docUrl(getDoc(side)!.file)" target="_blank" class="stg__kyc-slot-preview">
                  <img v-if="isImage(getDoc(side)!.file)" :src="docUrl(getDoc(side)!.file)" :alt="side" />
                  <PdfThumbnail v-else-if="isPdf(getDoc(side)!.file)" :url="docUrl(getDoc(side)!.file)" :height="160" />
                  <div v-else class="stg__kyc-slot-file"><span class="stg__kyc-slot-ext">{{ getDoc(side)!.file.split('.').pop()?.toUpperCase() }}</span></div>
                </a>
                <div class="stg__kyc-slot-meta">
                  <span class="stg__kyc-slot-date">Chargé le {{ new Date(getDoc(side)!.uploaded_at).toLocaleDateString('fr-FR') }}</span>
                  <button v-if="agent.isKycEditable" class="stg__doc-btn view" @click="side === 'RECTO' ? rectoInput?.click() : versoInput?.click()">Remplacer</button>
                </div>
              </div>
              <div v-else-if="agent.isKycEditable" class="stg__kyc-slot-upload" @click="side === 'RECTO' ? rectoInput?.click() : versoInput?.click()">
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#aaa" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/></svg>
                <span v-if="uploadingSlot === side">Envoi en cours...</span>
                <span v-else>Importer le {{ side === 'RECTO' ? 'recto' : 'verso' }}</span>
              </div>
            </div>
            <input ref="rectoInput" type="file" accept=".jpg,.jpeg,.png,.pdf" hidden @change="(e: Event) => handleKycUpload(e, 'RECTO')" />
            <input ref="versoInput" type="file" accept=".jpg,.jpeg,.png,.pdf" hidden @change="(e: Event) => handleKycUpload(e, 'VERSO')" />
          </template>

          <template v-else>
            <div class="stg__kyc-slot stg__kyc-slot--wide">
              <h3 class="stg__kyc-slot-title">Document</h3>
              <div v-if="getDoc('SINGLE')" class="stg__kyc-slot-doc">
                <a :href="docUrl(getDoc('SINGLE')!.file)" target="_blank" class="stg__kyc-slot-preview">
                  <img v-if="isImage(getDoc('SINGLE')!.file)" :src="docUrl(getDoc('SINGLE')!.file)" alt="Document" />
                  <PdfThumbnail v-else-if="isPdf(getDoc('SINGLE')!.file)" :url="docUrl(getDoc('SINGLE')!.file)" :height="160" />
                  <div v-else class="stg__kyc-slot-file"><span class="stg__kyc-slot-ext">{{ getDoc('SINGLE')!.file.split('.').pop()?.toUpperCase() }}</span></div>
                </a>
                <div class="stg__kyc-slot-meta">
                  <span class="stg__kyc-slot-date">Chargé le {{ new Date(getDoc('SINGLE')!.uploaded_at).toLocaleDateString('fr-FR') }}</span>
                  <button v-if="agent.isKycEditable" class="stg__doc-btn view" @click="singleInput?.click()">Remplacer</button>
                </div>
              </div>
              <div v-else-if="agent.isKycEditable" class="stg__kyc-slot-upload" @click="singleInput?.click()">
                <svg viewBox="0 0 24 24" width="32" height="32"><path fill="#aaa" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/></svg>
                <span v-if="uploadingSlot === 'SINGLE'">Envoi en cours...</span>
                <span v-else>Importer le document</span>
              </div>
            </div>
            <input ref="singleInput" type="file" accept=".jpg,.jpeg,.png,.pdf" hidden @change="(e: Event) => handleKycUpload(e, 'SINGLE')" />
          </template>
        </div>

        <!-- Bouton Soumettre -->
        <div v-if="agent.isKycEditable && kycDocsReady" class="stg__kyc-submit-bar">
          <button class="stg__kyc-submit-btn" :disabled="submittingKyc" @click="doSubmitKyc">
            {{ submittingKyc ? 'Envoi en cours...' : 'Soumettre pour vérification' }}
          </button>
          <span class="stg__kyc-submit-hint">Une fois soumis, vos documents ne pourront plus être modifiés jusqu'à la réponse de notre équipe.</span>
        </div>

        <p v-if="agent.kycStatus === 'PENDING'" class="stg__kyc-readonly-hint">Vos documents sont en cours de vérification. Vous ne pouvez pas les modifier.</p>
        <p v-if="agent.kycStatus === 'APPROVED'" class="stg__kyc-readonly-hint">Vos documents sont vérifiés et ne peuvent plus être modifiés.</p>
      </section>

      <section class="stg__card">
        <h2 class="stg__card-title">Pourquoi vérifier son identité ?</h2>
        <ul class="stg__benefits">
          <li>Indispensable pour publier et activer vos annonces</li>
          <li>Badge vérifié visible sur toutes vos annonces</li>
          <li>Confiance accrue des clients</li>
          <li>Priorité dans les résultats de recherche</li>
        </ul>
      </section>
    </div>

    <!-- ═══ Security tab ═══ -->
    <div v-else-if="tab === 'security'" class="stg__content">
      <section class="stg__card">
        <h2 class="stg__card-title">Informations du compte</h2>
        <div class="stg__info-row">
          <span class="stg__info-label">Téléphone</span>
          <span class="stg__info-val">{{ agent.profile?.phone || auth.me?.phone }}</span>
        </div>
        <div class="stg__info-row">
          <span class="stg__info-label">Nom d'utilisateur</span>
          <span class="stg__info-val">{{ agent.profile?.username || auth.me?.username || '—' }}</span>
        </div>
        <div class="stg__info-row">
          <span class="stg__info-label">Email</span>
          <span class="stg__info-val">{{ agent.profile?.email || '—' }}</span>
        </div>
        <div class="stg__info-row">
          <span class="stg__info-label">Rôle</span>
          <span class="stg__info-val">Agent</span>
        </div>
        <div class="stg__info-row">
          <span class="stg__info-label">Membre depuis</span>
          <span class="stg__info-val">{{ agent.profile?.member_since ? new Date(agent.profile.member_since).toLocaleDateString('fr-FR') : '—' }}</span>
        </div>
      </section>

      <section class="stg__card">
        <h2 class="stg__card-title">PIN Wallet</h2>
        <p class="stg__card-desc">
          {{ agent.walletHasPin
            ? 'Votre code PIN de retrait est configuré. Vous pouvez le modifier à tout moment.'
            : 'Configurez votre code PIN à 4 chiffres pour sécuriser vos retraits.' }}
        </p>
        <div class="stg__pin-status" v-if="agent.walletHasPin">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="#1DA53F" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
          <span>PIN actif</span>
        </div>
        <div class="stg__pin-actions">
          <button v-if="!agent.walletHasPin" class="stg__pin-btn" @click="openSetPin">Configurer le PIN</button>
          <button v-if="agent.walletHasPin" class="stg__pin-btn secondary" @click="openChangePin">Modifier le PIN</button>
        </div>
      </section>

      <section class="stg__card">
        <h2 class="stg__card-title">Mot de passe</h2>
        <p class="stg__card-desc">Modifiez votre mot de passe de connexion.</p>
        <div class="stg__pwd-form">
          <div class="stg__modal-field">
            <label>Mot de passe actuel</label>
            <div class="stg__pwd-input-wrap">
              <input v-model="pwdForm.current_password" :type="showCurrentPwd ? 'text' : 'password'" placeholder="••••••••" />
              <button type="button" class="stg__pwd-eye" @click="showCurrentPwd = !showCurrentPwd" tabindex="-1">
                <svg v-if="!showCurrentPwd" viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                <svg v-else viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46A11.804 11.804 0 001 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>
              </button>
            </div>
          </div>
          <div class="stg__modal-field">
            <label>Nouveau mot de passe</label>
            <div class="stg__pwd-input-wrap">
              <input v-model="pwdForm.new_password" :type="showNewPwd ? 'text' : 'password'" placeholder="8 caractères minimum" />
              <button type="button" class="stg__pwd-eye" @click="showNewPwd = !showNewPwd" tabindex="-1">
                <svg v-if="!showNewPwd" viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                <svg v-else viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46A11.804 11.804 0 001 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>
              </button>
            </div>
          </div>
          <div class="stg__modal-field">
            <label>Confirmer le nouveau mot de passe</label>
            <div class="stg__pwd-input-wrap">
              <input v-model="pwdForm.new_password_confirm" :type="showConfirmPwd ? 'text' : 'password'" placeholder="••••••••" />
              <button type="button" class="stg__pwd-eye" @click="showConfirmPwd = !showConfirmPwd" tabindex="-1">
                <svg v-if="!showConfirmPwd" viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                <svg v-else viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46A11.804 11.804 0 001 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>
              </button>
            </div>
          </div>
          <button class="stg__pin-btn" @click="changePassword" :disabled="pwdLoading" style="margin-top: 8px">
            {{ pwdLoading ? 'Modification...' : 'Modifier le mot de passe' }}
          </button>
        </div>
      </section>

      <section class="stg__card">
        <h2 class="stg__card-title">Onboarding</h2>
        <p class="stg__card-desc">Relancez le processus d'accueil pour compléter votre profil.</p>
        <router-link to="/agent/onboarding" class="stg__onboarding-link">Relancer l'onboarding</router-link>
      </section>
    </div>

    <!-- ═══ PIN Modal ═══ -->
    <div v-if="showPinModal" class="stg__modal-overlay" @click.self="showPinModal = null">
      <div class="stg__modal">
        <!-- Set PIN -->
        <template v-if="showPinModal === 'set'">
          <h3 class="stg__modal-title">Configurer votre code PIN</h3>
          <p class="stg__modal-desc">Ce code à 4 chiffres sera requis pour chaque demande de retrait.</p>
          <div class="stg__modal-field">
            <label>Code PIN</label>
            <input v-model="pinForm.pin" type="password" maxlength="4" placeholder="••••" inputmode="numeric" />
          </div>
          <div class="stg__modal-field">
            <label>Confirmer le PIN</label>
            <input v-model="pinForm.pin_confirm" type="password" maxlength="4" placeholder="••••" inputmode="numeric" />
          </div>
          <div class="stg__modal-actions">
            <button class="stg__modal-btn cancel" @click="showPinModal = null" :disabled="pinLoading">Annuler</button>
            <button class="stg__modal-btn confirm" @click="submitSetPin" :disabled="pinLoading">
              {{ pinLoading ? 'Traitement...' : 'Configurer' }}
            </button>
          </div>
        </template>

        <!-- Change PIN -->
        <template v-if="showPinModal === 'change'">
          <h3 class="stg__modal-title">Modifier votre code PIN</h3>
          <div class="stg__modal-field">
            <label>PIN actuel</label>
            <input v-model="pinForm.current_pin" type="password" maxlength="4" placeholder="••••" inputmode="numeric" />
          </div>
          <div class="stg__modal-field">
            <label>Nouveau PIN</label>
            <input v-model="pinForm.new_pin" type="password" maxlength="4" placeholder="••••" inputmode="numeric" />
          </div>
          <div class="stg__modal-field">
            <label>Confirmer le nouveau PIN</label>
            <input v-model="pinForm.new_pin_confirm" type="password" maxlength="4" placeholder="••••" inputmode="numeric" />
          </div>
          <div class="stg__modal-actions">
            <button class="stg__modal-btn cancel" @click="showPinModal = null" :disabled="pinLoading">Annuler</button>
            <button class="stg__modal-btn confirm" @click="submitChangePin" :disabled="pinLoading">
              {{ pinLoading ? 'Traitement...' : 'Modifier' }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stg { max-width: 900px; }
.stg__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 20px; }

.stg__tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #E0E0E0;
  margin-bottom: 24px;
}
.stg__tab {
  padding: 12px 20px;
  border: none;
  background: none;
  font-size: 14px;
  color: #606060;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.stg__tab:hover { color: #0F0F0F; }
.stg__tab.active { color: #0F0F0F; font-weight: 600; border-bottom-color: #0F0F0F; }

.stg__content { display: flex; flex-direction: column; gap: 20px; }

.stg__card {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 24px;
}
.stg__card-title { font-size: 16px; font-weight: 600; color: #0F0F0F; margin-bottom: 16px; }
.stg__card-desc { font-size: 14px; color: #606060; margin-bottom: 16px; line-height: 1.5; }

/* Photo */
.stg__photo-row { display: flex; align-items: center; gap: 20px; }
.stg__photo-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #1DA53F;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.stg__photo-img { width: 100%; height: 100%; object-fit: cover; }
.stg__photo-initials { color: #fff; font-size: 28px; font-weight: 700; }
.stg__photo-btn {
  padding: 8px 18px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
  color: #1DA53F;
  font-weight: 500;
  cursor: pointer;
  transition: background .15s;
}
.stg__photo-btn:hover { background: rgba(29,165,63,.06); }
.stg__photo-btn:disabled { opacity: .6; cursor: not-allowed; }
.stg__photo-hint { font-size: 12px; color: #606060; margin-top: 6px; }

.stg__photo-file {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  font-size: 13px;
  color: #606060;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stg__photo-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 8px;
}
.stg__photo-status.uploading {
  color: #606060;
  background: #f8f8f8;
}
.stg__photo-status.success {
  color: #1DA53F;
  background: rgba(29,165,63,.06);
}
.stg__photo-status.error {
  color: #dc2626;
  background: #fef2f2;
}
.stg__photo-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #E0E0E0;
  border-top-color: #1DA53F;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Form */
.stg__form { display: flex; flex-direction: column; gap: 18px; }
.stg__field label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #272727;
  margin-bottom: 6px;
}
.stg__field input,
.stg__field textarea,
.stg__field select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F0F0F;
  box-sizing: border-box;
  background: #fff;
}
.stg__field input:focus,
.stg__field textarea:focus,
.stg__field select:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}
.stg__field textarea { resize: vertical; }
.stg__field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.stg__form-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
}
.stg__saved { font-size: 14px; color: #1DA53F; font-weight: 500; }
.stg__error { font-size: 14px; color: #dc2626; font-weight: 500; }
.stg__save-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 20px;
  background: #1DA53F;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
}
.stg__save-btn:hover { background: #178A33; }
.stg__save-btn:disabled { opacity: .6; cursor: not-allowed; }

/* KYC */
.stg__kyc-status { margin-bottom: 4px; }
.stg__kyc-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
}
.stg__kyc-badge.verified { background: rgba(29,165,63,.06); color: #1DA53F; }
.stg__kyc-badge.pending { background: #fef3c7; color: #d97706; }
.stg__kyc-badge.none { background: #f8f8f8; color: #606060; }

.stg__kyc-form { display: flex; flex-direction: column; gap: 16px; }

.stg__select {
  width: 100%; padding: 10px 12px; border: 1px solid #E0E0E0; border-radius: 8px;
  font-size: 15px; color: #0F0F0F; background: #fff; box-sizing: border-box;
}
.stg__select:disabled { background: #f5f5f5; color: #909090; cursor: not-allowed; }
.stg__select:focus { outline: none; border-color: #1DA53F; box-shadow: 0 0 0 3px rgba(29,165,63,.12); }

.stg__kyc-slots {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.stg__kyc-slot--wide { grid-column: 1 / -1; max-width: 400px; }
.stg__kyc-slot-title { font-size: 14px; font-weight: 600; color: #272727; margin: 0 0 10px; }

.stg__kyc-slot-upload {
  border: 2px dashed #E0E0E0; border-radius: 12px; padding: 32px 16px;
  text-align: center; cursor: pointer; color: #606060; font-size: 14px;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  transition: border-color .15s;
}
.stg__kyc-slot-upload:hover { border-color: #1DA53F; }

.stg__kyc-slot-doc { display: flex; flex-direction: column; gap: 8px; }
.stg__kyc-slot-preview {
  display: block; height: 160px; border-radius: 10px; overflow: hidden;
  background: #f0f0f0; text-decoration: none;
}
.stg__kyc-slot-preview img { width: 100%; height: 100%; object-fit: cover; }
.stg__kyc-slot-file {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
}
.stg__kyc-slot-ext {
  font-size: 16px; font-weight: 700; color: #fff; background: #dc2626;
  padding: 4px 14px; border-radius: 6px;
}
.stg__kyc-slot-meta {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.stg__kyc-slot-date { font-size: 12px; color: #606060; }
.stg__kyc-badge.rejected { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.stg__kyc-badge.rejected strong { display: block; margin-bottom: 4px; }
.stg__kyc-reject-reason { font-size: 13px; margin: 4px 0 0; font-style: italic; }
.stg__kyc-reject-hint { font-size: 13px; margin: 4px 0 0; color: #b91c1c; }

.stg__kyc-submit-bar {
  margin-top: 20px; padding: 16px; background: #f0fdf4; border-radius: 10px;
  border: 1px solid #bbf7d0; display: flex; flex-direction: column; gap: 8px; align-items: flex-start;
}
.stg__kyc-submit-btn {
  padding: 10px 28px; border: none; border-radius: 20px; background: #1DA53F;
  color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; transition: background .15s;
}
.stg__kyc-submit-btn:hover:not(:disabled) { background: #178A33; }
.stg__kyc-submit-btn:disabled { opacity: .5; cursor: not-allowed; }
.stg__kyc-submit-hint { font-size: 12px; color: #606060; }

.stg__kyc-readonly-hint {
  margin-top: 16px; font-size: 13px; color: #606060; font-style: italic;
}
.stg__kyc-hint {
  font-size: 13px; color: #606060; margin: 0 0 16px; padding: 8px 12px;
  background: #f8f9fa; border-radius: 8px; border-left: 3px solid #1DA53F;
}

.stg__docs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.stg__doc-card {
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  transition: box-shadow .2s;
}
.stg__doc-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.08);
}
.stg__doc-preview {
  position: relative;
  height: 200px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  text-decoration: none;
  transition: background .15s;
}
.stg__doc-preview:hover { background: #e5e5e5; }
.stg__doc-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.stg__doc-file-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 100%;
}
.stg__doc-file-ext {
  font-size: 14px;
  font-weight: 700;
  color: #606060;
  background: #E0E0E0;
  padding: 3px 12px;
  border-radius: 6px;
}
.stg__doc-file-ext--pdf {
  background: #dc2626;
  color: #fff;
}
.stg__doc-file-hint {
  font-size: 12px;
  color: #909090;
}
.stg__doc-verified-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #1DA53F;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.stg__doc-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stg__doc-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.stg__doc-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: background .15s;
  border: 1px solid #E0E0E0;
  background: #fff;
  color: #272727;
}
.stg__doc-btn:hover { background: #f2f2f2; }
.stg__doc-btn.view { color: #1DA53F; border-color: #1DA53F; }
.stg__doc-btn.view:hover { background: rgba(29,165,63,.06); }
.stg__doc-btn.download { color: #2563eb; border-color: #2563eb; }
.stg__doc-btn.download:hover { background: rgba(37,99,235,.06); }
.stg__doc-btn.delete { color: #dc2626; border-color: #dc2626; }
.stg__doc-btn.delete:hover { background: #fef2f2; }
.stg__doc-btn.delete:disabled { opacity: .5; cursor: not-allowed; }

/* Lightbox */
.stg__lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0,0,0,.85);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.stg__lightbox-close {
  position: absolute;
  top: 16px;
  right: 20px;
  font-size: 36px;
  color: #fff;
  background: none;
  border: none;
  cursor: pointer;
  line-height: 1;
}
.stg__lightbox-close:hover { color: #ddd; }
.stg__lightbox-img {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
}

.stg__docs-list { display: flex; flex-direction: column; gap: 8px; }
.stg__doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border: 1px solid #f2f2f2;
  border-radius: 8px;
}
.stg__doc-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #0F0F0F;
}
.stg__doc-label { font-weight: 500; }
.stg__doc-date { color: #606060; font-size: 13px; }
.stg__doc-delete {
  padding: 6px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 6px;
  background: #fff;
  color: #dc2626;
  font-size: 13px;
  cursor: pointer;
  transition: background .15s;
}
.stg__doc-delete:hover { background: #fef2f2; }
.stg__doc-delete:disabled { opacity: .5; cursor: not-allowed; }

.stg__upload-area {
  border: 2px dashed #E0E0E0;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  color: #606060;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: border-color .15s;
}
.stg__upload-area:hover { border-color: #1DA53F; }

.stg__benefits {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.stg__benefits li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #272727;
}
.stg__benefits li::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1DA53F;
  flex-shrink: 0;
}

/* Security */
.stg__info-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f2f2f2;
}
.stg__info-row:last-child { border-bottom: none; }
.stg__info-label { font-size: 14px; color: #606060; }
.stg__info-val { font-size: 14px; color: #0F0F0F; font-weight: 500; }

.stg__pin-actions { display: flex; gap: 12px; }
.stg__pin-btn {
  padding: 10px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background: #1DA53F;
  color: #fff;
  transition: background .15s;
}
.stg__pin-btn:hover { background: #178A33; }
.stg__pin-btn.secondary { background: #f2f2f2; color: #272727; }
.stg__pin-btn.secondary:hover { background: #e5e5e5; }

.stg__pwd-form {
  max-width: 400px;
}
.stg__pwd-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.stg__pwd-form .stg__modal-field input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 15px;
  box-sizing: border-box;
}
.stg__pwd-form .stg__modal-field input:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}
.stg__pwd-eye {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background .15s;
}
.stg__pwd-eye:hover {
  background: rgba(0,0,0,.06);
}

.stg__onboarding-link {
  display: inline-block;
  padding: 10px 20px;
  border: 1px solid #1DA53F;
  border-radius: 20px;
  color: #1DA53F;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: background .15s;
}
.stg__onboarding-link:hover { background: rgba(29,165,63,.06); }

.stg__pin-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #1DA53F;
  font-weight: 500;
}

/* PIN Modal */
.stg__modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stg__modal {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  max-width: 400px;
  width: 90%;
}
.stg__modal-title { font-size: 20px; font-weight: 700; color: #0F0F0F; margin-bottom: 8px; }
.stg__modal-desc { font-size: 14px; color: #606060; margin-bottom: 20px; }
.stg__modal-field { margin-bottom: 16px; }
.stg__modal-field label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #272727;
  margin-bottom: 6px;
}
.stg__modal-field input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 20px;
  color: #0F0F0F;
  box-sizing: border-box;
  text-align: center;
  letter-spacing: 8px;
}
.stg__modal-field input:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}
.stg__modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 8px; }
.stg__modal-btn {
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}
.stg__modal-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.stg__modal-btn.cancel { background: #f2f2f2; color: #272727; }
.stg__modal-btn.cancel:hover:not(:disabled) { background: #e5e5e5; }
.stg__modal-btn.confirm { background: #1DA53F; color: #fff; }
.stg__modal-btn.confirm:hover:not(:disabled) { background: #178A33; }

@media (max-width: 600px) {
  .stg__field-row { grid-template-columns: 1fr; }
  .stg__photo-row { flex-direction: column; text-align: center; }
}
</style>
