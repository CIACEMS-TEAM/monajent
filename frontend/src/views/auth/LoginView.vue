<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/Stores/auth'

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
    const dest = auth.me?.role === 'AGENT' ? '/agent' : (auth.me?.role === 'CLIENT' ? '/client' : '/home')
    router.push(dest)
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Échec de connexion')
  } finally {
    loading.value = false
  }
}
</script>

<template>
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
  
</template>

<style scoped>
.auth-container { max-width: 560px; margin: 64px auto; padding: 0 16px; }
.title { font-weight: 700; font-size: 28px; margin-bottom: 16px; }
.card { display: grid; gap: 12px; padding: 24px; border: 1px solid #e5e5e5; border-radius: 10px; background: #fff; }
.label { font-size: 14px; color: #333; }
.input { padding: 12px 14px; border-radius: 8px; border: 1px solid #dcdcdc; }
.input:focus { outline: none; border-color: #14A800; box-shadow: 0 0 0 3px rgba(20,168,0,.12); }
.btn { margin-top: 8px; padding: 12px 16px; border: none; border-radius: 8px; background: #14A800; color: #fff; cursor: pointer; font-weight: 600; }
.btn:disabled { opacity: .7; cursor: default; }
.muted { color: #555; font-size: 14px; margin-top: 8px; }
.password { display:flex; gap:8px; align-items:center; }
.password .toggle { padding: 10px 12px; border-radius: 8px; border: 1px solid #dcdcdc; background: #f8f8f8; cursor: pointer; }
</style>


