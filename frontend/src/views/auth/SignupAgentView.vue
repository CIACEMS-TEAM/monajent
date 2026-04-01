<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useToast } from 'vue-toastification'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'
import logoUrl from '@/assets/icons/logo_monajent_header.webp'

const toast = useToast()
const router = useRouter()
const auth = useAuthStore()

const form = reactive({ phone: '', password: '', username: '', email: '', agency_name: '' })
const acceptedCgu = ref(false)
const acceptedPrivacy = ref(false)
const loading = ref(false)
const otpMode = ref(false)
const otpCode = ref('')
const otpLoading = ref(false)

async function submit() {
  if (!form.phone || !form.password) {
    toast.error('Téléphone et mot de passe requis')
    return
  }
  if (!acceptedCgu.value || !acceptedPrivacy.value) {
    toast.error('Vous devez accepter les CGU et la politique de confidentialité')
    return
  }
  loading.value = true
  try {
    const data = await auth.registerAgent({
      phone: form.phone,
      password: form.password,
      username: form.username || undefined,
      email: form.email || undefined,
      agency_name: form.agency_name || undefined,
      accepted_cgu: acceptedCgu.value,
      accepted_privacy: acceptedPrivacy.value,
    })
    if (data?.pending_token) {
      otpMode.value = true
      toast.success('OTP envoyé. Vérifiez vos messages.')
    } else {
      toast.success('Si éligible, un OTP a été envoyé.')
      router.push('/auth/login')
    }
  } catch (e: any) {
    const data = e?.response?.data || {}
    toast.error(data.detail || Object.values(data)[0]?.[0] || 'Erreur d\'inscription')
  } finally {
    loading.value = false
  }
}

async function resendOtp() {
  try {
    otpLoading.value = true
    await auth.otpRequest()
    toast.success('OTP renvoyé')
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Échec réenvoi OTP')
  } finally {
    otpLoading.value = false
  }
}

async function verifyOtp() {
  if (!otpCode.value) { toast.error('Entrez le code OTP'); return }
  try {
    otpLoading.value = true
    await auth.otpVerify(otpCode.value)
    toast.success('Compte vérifié')
    const dest = auth.me?.role === 'AGENT' ? '/agent' : '/home'
    router.push(dest)
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Échec de vérification OTP')
  } finally {
    otpLoading.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="container">
        <router-link to="/home" class="back-btn" aria-label="Retour à l'accueil">
          <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
        </router-link>
        <router-link to="/home">
          <img :src="logoUrl" alt="MonaJent" class="logo" />
        </router-link>
      </div>
    </header>

    <div class="auth-container">
      <h1 class="title">Créer un compte agent</h1>
      <form v-if="!otpMode" class="card" @submit.prevent="submit">
        <label class="label">Téléphone</label>
        <input class="input" v-model="form.phone" placeholder="Ex: +2250700..." />

        <label class="label">Mot de passe</label>
        <input class="input" v-model="form.password" type="password" placeholder="••••••••" />

        <label class="label">Nom d'utilisateur (optionnel)</label>
        <input class="input" v-model="form.username" placeholder="votre pseudo" />

        <label class="label">Email (optionnel)</label>
        <input class="input" v-model="form.email" type="email" placeholder="contact@exemple.com" />

        <label class="label">Nom de l'agence (optionnel)</label>
        <input class="input" v-model="form.agency_name" placeholder="Votre agence" />

        <div class="consent-group">
          <label class="consent">
            <input type="checkbox" v-model="acceptedCgu" />
            <span>J'accepte les <a href="/legal/cgu" target="_blank">Conditions Générales d'Utilisation</a></span>
          </label>
          <label class="consent">
            <input type="checkbox" v-model="acceptedPrivacy" />
            <span>J'accepte la <a href="/legal/confidentialite" target="_blank">Politique de Confidentialité</a></span>
          </label>
        </div>

        <button class="btn" :disabled="loading || !acceptedCgu || !acceptedPrivacy" type="submit">{{ loading ? 'Création...' : 'Créer mon compte' }}</button>
        <p class="muted">Vous êtes client ? <router-link to="/auth/signup/client">Créer un compte client</router-link></p>
        <p class="muted">Déjà un compte ? <router-link to="/auth/login">Se connecter</router-link></p>
      </form>
      <div v-else class="card">
        <p class="label">Entrez le code OTP reçu par SMS</p>
        <input class="input" v-model="otpCode" maxlength="6" placeholder="Code à 6 chiffres" />
        <div style="display:flex; gap:8px;">
          <button class="btn" :disabled="otpLoading" @click="verifyOtp">{{ otpLoading ? 'Vérification...' : 'Vérifier' }}</button>
          <button class="btn" :disabled="otpLoading" @click="resendOtp">Renvoyer OTP</button>
        </div>
        <p class="muted">Besoin d'aide ? Vérifiez le numéro saisi et réessayez.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; background: #fff; }
.header { padding: 16px 0; border-bottom: 1px solid #E0E0E0; }
.container { width: min(1128px, 92vw); margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 12px; }
.logo { height: 32px; width: auto; }
.back-btn { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; color: #272727; transition: background .15s; text-decoration: none; }
.back-btn:hover { background: #f2f2f2; }
.auth-container { max-width: 640px; margin: 56px auto; padding: 0 16px; }
.title { font-weight: 700; font-size: 30px; margin-bottom: 18px; color: #0F0F0F; }
.card { display: grid; gap: 14px; padding: 28px; border: 1px solid #E0E0E0; border-radius: 12px; background: #fff; }
.label { font-size: 14px; color: #272727; }
.input { padding: 12px 14px; border-radius: 8px; border: 1px solid #E0E0E0; color: #0F0F0F; }
.input:focus { outline: none; border-color: #1DA53F; box-shadow: 0 0 0 3px rgba(29,165,63,.15); }
.btn { margin-top: 8px; padding: 12px 16px; border: none; border-radius: 8px; background: #1DA53F; color: #fff; cursor: pointer; font-weight: 600; transition: background .15s; }
.btn:hover { background: #178A33; }
.btn:disabled { opacity: .7; cursor: default; }
.muted { color: #272727; font-size: 14px; margin-top: 8px; }
.muted a { color: #1DA53F; }
.consent-group { display: flex; flex-direction: column; gap: 10px; }
.consent { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; color: #272727; cursor: pointer; line-height: 1.5; }
.consent input[type="checkbox"] { margin-top: 3px; width: 18px; height: 18px; accent-color: #1DA53F; flex-shrink: 0; cursor: pointer; }
.consent a { color: #1DA53F; text-decoration: none; }
.consent a:hover { text-decoration: underline; }
@media (max-width: 600px) { .logo { height: 26px; } }
</style>
