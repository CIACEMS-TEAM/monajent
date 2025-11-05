<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useToast } from 'vue-toastification'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'
import logoUrl from '@/assets/icons/logo_monajent_sf.png'

const toast = useToast()
const router = useRouter()
const auth = useAuthStore()

const form = reactive({ phone: '', username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.phone || !form.username || !form.password) {
    toast.error('Tous les champs sont requis')
    return
  }
  loading.value = true
  try {
    await auth.registerClient(form)
    toast.success('Compte créé. Vérifiez l’OTP si activé, puis connectez-vous.')
    router.push('/auth/login')
  } catch (e: any) {
    const data = e?.response?.data || {}
    toast.error(data.detail || Object.values(data)[0]?.[0] || 'Erreur d’inscription')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="container">
        <img :src="logoUrl" alt="MonaJent" class="logo" />
      </div>
    </header>

    <div class="auth-container">
      <h1 class="title">Créer un compte client</h1>
      <form class="card" @submit.prevent="submit">
      <label class="label">Téléphone</label>
      <input class="input" v-model="form.phone" placeholder="Ex: +2250700..." />

      <label class="label">Nom d’utilisateur</label>
      <input class="input" v-model="form.username" placeholder="votre pseudo" />

      <label class="label">Mot de passe</label>
      <input class="input" v-model="form.password" type="password" placeholder="••••••••" />

      <button class="btn" :disabled="loading" type="submit">{{ loading ? 'Création...' : 'Créer mon compte' }}</button>

      <p class="muted">Plutôt agent ? <router-link to="/auth/signup/agent">Créer un compte agent</router-link></p>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; background: #fff; }
.header { padding: 16px 0; border-bottom: 1px solid #eee; }
.container { width: min(1128px, 92vw); margin: 0 auto; padding: 0 24px; display:flex; align-items:center; }
.logo { height: 96px; width: auto; }
.auth-container { max-width: 640px; margin: 56px auto; padding: 0 16px; }
.title { font-weight: 700; font-size: 30px; margin-bottom: 18px; }
.card { display: grid; gap: 14px; padding: 28px; border: 1px solid #e5e5e5; border-radius: 12px; background: #fff; }
.label { font-size: 14px; color: #333; }
.input { padding: 12px 14px; border-radius: 8px; border: 1px solid #dcdcdc; }
.input:focus { outline: none; border-color: #14A800; box-shadow: 0 0 0 3px rgba(20,168,0,.12); }
.btn { margin-top: 8px; padding: 12px 16px; border: none; border-radius: 8px; background: #14A800; color: #fff; cursor: pointer; font-weight: 600; }
.btn:disabled { opacity: .7; cursor: default; }
.muted { color: #555; font-size: 14px; margin-top: 8px; }
@media (max-width: 600px) { .logo { height: 68px; } }
</style>


