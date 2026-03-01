<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/Stores/auth'
import logoUrl from '@/assets/icons/logo_monajent_header.png'

const router = useRouter()
const toast = useToast()
const auth = useAuthStore()

const form = reactive({ phone: '', password: '' })
const loading = ref(false)
const showPassword = ref(false)

async function submit() {
  if (!form.phone || !form.password) {
    toast.error('Téléphone et mot de passe requis')
    return
  }
  loading.value = true
  try {
    await auth.login(form)
    toast.success('Connexion réussie')
    const dest = auth.me?.role === 'AGENT' ? '/agent' : '/home'
    router.push(dest)
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Échec de connexion')
  } finally {
    loading.value = false
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
      <h1 class="title">Se connecter</h1>
      <form class="card" @submit.prevent="submit">
        <label class="label">Téléphone</label>
        <input class="input" v-model="form.phone" placeholder="Ex: +2250700..." />

        <label class="label">Mot de passe</label>
        <div class="password">
          <input class="input" :type="showPassword ? 'text' : 'password'" v-model="form.password" placeholder="••••••••" />
          <button class="toggle" type="button" @click="showPassword = !showPassword">{{ showPassword ? 'Masquer' : 'Voir' }}</button>
        </div>

        <button class="btn" :disabled="loading" type="submit">{{ loading ? 'Connexion...' : 'Se connecter' }}</button>

        <p class="muted">Pas de compte ? <router-link to="/auth/join">Créer un compte</router-link></p>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; background: #fff; }
.header { padding: 16px 0; border-bottom: 1px solid #E0E0E0; }
.container { width: min(1128px, 92vw); margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 12px; }
.logo { height: 32px; width: auto; }
.back-btn { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; color: #272727; transition: background .15s; }
.back-btn:hover { background: #f2f2f2; }
.auth-container { max-width: 560px; margin: 48px auto; padding: 0 16px; }
.title { font-weight: 700; font-size: 28px; margin-bottom: 16px; color: #0F0F0F; }
.card { display: grid; gap: 12px; padding: 24px; border: 1px solid #E0E0E0; border-radius: 10px; background: #fff; }
.label { font-size: 14px; color: #272727; }
.input { padding: 12px 14px; border-radius: 8px; border: 1px solid #E0E0E0; color: #0F0F0F; }
.input:focus { outline: none; border-color: #1DA53F; box-shadow: 0 0 0 3px rgba(29,165,63,.15); }
.btn { margin-top: 8px; padding: 12px 16px; border: none; border-radius: 8px; background: #1DA53F; color: #fff; cursor: pointer; font-weight: 600; transition: background .15s; }
.btn:hover { background: #178A33; }
.btn:disabled { opacity: .7; cursor: default; }
.muted { color: #272727; font-size: 14px; margin-top: 8px; }
.muted a { color: #1DA53F; }
.password { display: flex; gap: 8px; align-items: center; }
.password .toggle { padding: 10px 12px; border-radius: 8px; border: 1px solid #E0E0E0; background: #f8f8f8; cursor: pointer; }
@media (max-width: 600px) { .logo { height: 26px; } }
</style>
