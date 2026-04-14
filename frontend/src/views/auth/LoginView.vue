<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/Stores/auth'
import logoUrl from '@/assets/icons/logo_monajent_header.webp'
import posthog from 'posthog-js'

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
    posthog.identify(String(auth.me?.id), {
      phone: auth.me?.phone,
      role: auth.me?.role,
      username: auth.me?.username,
    })
    posthog.capture('user_logged_in', { role: auth.me?.role })
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
  <div class="lg-page">
    <header class="lg-header">
      <div class="lg-header__inner">
        <router-link to="/home" class="lg-back" aria-label="Retour à l'accueil">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path
              fill="currentColor"
              d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"
            />
          </svg>
        </router-link>
        <router-link to="/home">
          <img :src="logoUrl" alt="MonaJent" class="lg-logo" />
        </router-link>
      </div>
    </header>

    <main class="lg-main">
      <div class="lg-card">
        <div class="lg-card__head">
          <h1 class="lg-card__title">Bon retour</h1>
          <p class="lg-card__sub">Connectez-vous à votre espace MonaJent</p>
        </div>

        <form class="lg-form" @submit.prevent="submit">
          <div class="lg-field">
            <label class="lg-label" for="lg-phone">Téléphone</label>
            <div class="lg-input-wrap">
              <i class="pi pi-phone lg-input-icon"></i>
              <input
                id="lg-phone"
                class="lg-input lg-input--icon"
                v-model="form.phone"
                type="tel"
                placeholder="+225 07 00 00 00 00"
                autocomplete="tel"
              />
            </div>
          </div>

          <div class="lg-field">
            <label class="lg-label" for="lg-pwd">Mot de passe</label>
            <div class="lg-input-wrap">
              <i class="pi pi-lock lg-input-icon"></i>
              <input
                id="lg-pwd"
                class="lg-input lg-input--icon lg-input--pwd"
                :type="showPassword ? 'text' : 'password'"
                v-model="form.password"
                placeholder="••••••••"
                autocomplete="current-password"
              />
              <button
                class="lg-eye"
                type="button"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                tabindex="-1"
              >
                <svg v-if="!showPassword" viewBox="0 0 24 24" width="20" height="20">
                  <path
                    fill="currentColor"
                    d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
                  />
                </svg>
                <svg v-else viewBox="0 0 24 24" width="20" height="20">
                  <path
                    fill="currentColor"
                    d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46A11.8 11.8 0 001 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"
                  />
                </svg>
              </button>
            </div>
          </div>

          <button class="lg-btn" :disabled="loading" type="submit">
            <i v-if="loading" class="pi pi-spin pi-spinner" style="font-size: 16px"></i>
            <span>{{ loading ? 'Connexion...' : 'Se connecter' }}</span>
          </button>
        </form>

        <p class="lg-footer-text">
          Pas encore de compte ?
          <router-link to="/auth/join" class="lg-link">Créer un compte</router-link>
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.lg-page {
  min-height: 100vh;
  background: #f8faf9;
  display: flex;
  flex-direction: column;
}

.lg-header {
  padding: 14px 0;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}
.lg-header__inner {
  width: min(1128px, 92vw);
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.lg-logo {
  height: 30px;
  width: auto;
}
.lg-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #272727;
  transition: background 0.15s;
}
.lg-back:hover {
  background: #f2f2f2;
}

.lg-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
}

.lg-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  box-shadow:
    0 2px 12px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  padding: 36px 32px 32px;
}
.lg-card__head {
  text-align: center;
  margin-bottom: 28px;
}
.lg-card__title {
  font-size: 24px;
  font-weight: 700;
  color: #0f0f0f;
  margin: 0 0 6px;
}
.lg-card__sub {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.lg-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.lg-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.lg-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.lg-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.lg-input-icon {
  position: absolute;
  left: 14px;
  font-size: 15px;
  color: #9ca3af;
  pointer-events: none;
  z-index: 1;
}
.lg-input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #0f0f0f;
  font-size: 15px;
  font-family: inherit;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
.lg-input--icon {
  padding-left: 42px;
}
.lg-input--pwd {
  padding-right: 46px;
}
.lg-input::placeholder {
  color: #9ca3af;
}
.lg-input:focus {
  outline: none;
  border-color: #1da53f;
  box-shadow: 0 0 0 3px rgba(29, 165, 63, 0.12);
}

.lg-eye {
  position: absolute;
  right: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition:
    color 0.15s,
    background 0.15s;
}
.lg-eye:hover {
  color: #374151;
  background: #f3f4f6;
}

.lg-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 6px;
  padding: 13px 20px;
  border: none;
  border-radius: 10px;
  background: #1da53f;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.15s,
    transform 0.1s;
}
.lg-btn:hover:not(:disabled) {
  background: #178a33;
}
.lg-btn:active:not(:disabled) {
  transform: scale(0.98);
}
.lg-btn:disabled {
  opacity: 0.7;
  cursor: default;
}

.lg-footer-text {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  margin: 24px 0 0;
}
.lg-link {
  color: #1da53f;
  font-weight: 600;
  text-decoration: none;
}
.lg-link:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .lg-card {
    padding: 28px 20px 24px;
    border-radius: 14px;
    box-shadow: none;
    border: 1px solid #e5e7eb;
  }
  .lg-main {
    padding: 24px 12px;
  }
  .lg-card__title {
    font-size: 22px;
  }
  .lg-logo {
    height: 26px;
  }
}
</style>
