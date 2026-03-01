<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/Stores/auth'
import http from '@/services/http'

const toast = useToast()
const auth = useAuthStore()

interface ProfileData {
  phone: string
  username: string | null
  email: string | null
  role: string
  member_since: string
  whatsapp_phone: string
  is_phone_verified: boolean
  language: string
  preferences: Record<string, any>
  kyc_status: string
}

const profile = ref<ProfileData | null>(null)
const loading = ref(true)
const saving = ref(false)
const editing = ref(false)

const form = reactive({
  username: '',
  email: '',
  whatsapp_phone: '',
  language: 'fr',
})

onMounted(async () => {
  try {
    const { data } = await http.get<ProfileData>('/api/client/profile/')
    profile.value = data
    form.username = data.username || ''
    form.email = data.email || ''
    form.whatsapp_phone = data.whatsapp_phone || ''
    form.language = data.language || 'fr'
  } catch (e: any) {
    toast.error('Impossible de charger le profil')
  } finally {
    loading.value = false
  }
})

function startEdit() {
  editing.value = true
}

function cancelEdit() {
  if (profile.value) {
    form.username = profile.value.username || ''
    form.email = profile.value.email || ''
    form.whatsapp_phone = profile.value.whatsapp_phone || ''
    form.language = profile.value.language || 'fr'
  }
  editing.value = false
}

async function saveProfile() {
  saving.value = true
  try {
    const { data } = await http.patch<ProfileData>('/api/client/profile/', {
      username: form.username,
      email: form.email,
      whatsapp_phone: form.whatsapp_phone,
      language: form.language,
    })
    profile.value = data
    editing.value = false
    toast.success('Profil mis à jour')
    await auth.fetchMe()
  } catch (e: any) {
    const errs = e?.response?.data
    if (errs && typeof errs === 'object') {
      const msg = Object.values(errs).flat().join(', ')
      toast.error(msg || 'Erreur de mise à jour')
    } else {
      toast.error('Erreur de mise à jour')
    }
  } finally {
    saving.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

function kycLabel(status: string) {
  const map: Record<string, string> = {
    NONE: 'Non vérifié',
    PENDING: 'En cours de vérification',
    VERIFIED: 'Vérifié',
  }
  return map[status] || status
}

function kycClass(status: string) {
  const map: Record<string, string> = {
    NONE: 'badge--neutral',
    PENDING: 'badge--warning',
    VERIFIED: 'badge--success',
  }
  return map[status] || 'badge--neutral'
}
</script>

<template>
  <div class="prof">
    <h1 class="prof__title">Mon profil</h1>

    <!-- Loading -->
    <div v-if="loading" class="prof__loading">
      <div class="prof__spinner"></div>
    </div>

    <template v-else-if="profile">
      <!-- Info card -->
      <div class="prof__card">
        <div class="prof__card-header">
          <div class="prof__avatar">
            {{ (profile.username?.[0] || profile.phone?.[0] || 'C').toUpperCase() }}
          </div>
          <div>
            <div class="prof__name">{{ profile.username || 'Client' }}</div>
            <div class="prof__phone">{{ profile.phone }}</div>
            <div class="prof__since">Membre depuis {{ formatDate(profile.member_since) }}</div>
          </div>
          <div class="prof__badges">
            <span class="badge" :class="kycClass(profile.kyc_status)">{{ kycLabel(profile.kyc_status) }}</span>
            <span v-if="profile.is_phone_verified" class="badge badge--success">Téléphone vérifié</span>
          </div>
        </div>
      </div>

      <!-- Edit form -->
      <div class="prof__card">
        <div class="prof__card-title-row">
          <h2 class="prof__card-title">Informations personnelles</h2>
          <button v-if="!editing" class="prof__edit-btn" @click="startEdit">Modifier</button>
        </div>

        <div class="prof__fields">
          <div class="prof__field">
            <label class="prof__label">Nom d'utilisateur</label>
            <input
              v-if="editing"
              class="prof__input"
              v-model="form.username"
              placeholder="Votre pseudo"
            />
            <div v-else class="prof__value">{{ profile.username || '—' }}</div>
          </div>

          <div class="prof__field">
            <label class="prof__label">Email</label>
            <input
              v-if="editing"
              class="prof__input"
              v-model="form.email"
              type="email"
              placeholder="votre@email.com"
            />
            <div v-else class="prof__value">{{ profile.email || '—' }}</div>
          </div>

          <div class="prof__field">
            <label class="prof__label">WhatsApp</label>
            <input
              v-if="editing"
              class="prof__input"
              v-model="form.whatsapp_phone"
              placeholder="+2250700..."
            />
            <div v-else class="prof__value">{{ profile.whatsapp_phone || '—' }}</div>
          </div>

          <div class="prof__field">
            <label class="prof__label">Langue</label>
            <select v-if="editing" class="prof__input" v-model="form.language">
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
            <div v-else class="prof__value">{{ form.language === 'fr' ? 'Français' : 'English' }}</div>
          </div>
        </div>

        <div v-if="editing" class="prof__actions">
          <button class="prof__btn prof__btn--primary" :disabled="saving" @click="saveProfile">
            {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
          </button>
          <button class="prof__btn prof__btn--ghost" @click="cancelEdit">Annuler</button>
        </div>
      </div>

      <!-- Security -->
      <div class="prof__card">
        <h2 class="prof__card-title">Sécurité</h2>
        <div class="prof__fields">
          <div class="prof__field">
            <label class="prof__label">Téléphone (identifiant)</label>
            <div class="prof__value">{{ profile.phone }}</div>
          </div>
          <div class="prof__field">
            <label class="prof__label">Mot de passe</label>
            <div class="prof__value">••••••••</div>
          </div>
        </div>
        <p class="prof__hint">
          Pour modifier votre mot de passe, utilisez la fonction "Mot de passe oublié" depuis l'écran de connexion.
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.prof { max-width: 720px; margin: 0 auto; }

.prof__title {
  font-size: 24px; font-weight: 700;
  color: #0F0F0F; margin-bottom: 20px;
}

.prof__loading {
  display: flex; justify-content: center;
  padding: 64px 0;
}
.prof__spinner {
  width: 32px; height: 32px;
  border: 3px solid #E0E0E0;
  border-top-color: #1DA53F;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Card */
.prof__card {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
}

.prof__card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.prof__avatar {
  width: 56px; height: 56px;
  border-radius: 50%;
  background: #1DA53F;
  color: #fff;
  font-size: 22px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.prof__name { font-size: 18px; font-weight: 700; color: #0F0F0F; }
.prof__phone { font-size: 14px; color: #606060; }
.prof__since { font-size: 12px; color: #909090; }

.prof__badges {
  margin-left: auto;
  display: flex; gap: 8px; flex-wrap: wrap;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.3px;
}
.badge--success { background: rgba(29,165,63,.1); color: #1DA53F; }
.badge--warning { background: rgba(245,158,11,.1); color: #d97706; }
.badge--neutral { background: #f2f2f2; color: #606060; }

/* Title row */
.prof__card-title-row {
  display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 16px;
}

.prof__card-title {
  font-size: 16px; font-weight: 700;
  color: #0F0F0F; margin-bottom: 0;
}

.prof__edit-btn {
  padding: 6px 16px;
  border: 1px solid #1DA53F;
  border-radius: 8px;
  background: transparent;
  color: #1DA53F;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: background .15s;
}
.prof__edit-btn:hover { background: rgba(29,165,63,.06); }

/* Fields */
.prof__fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.prof__field { display: flex; flex-direction: column; gap: 4px; }

.prof__label {
  font-size: 12px; font-weight: 600;
  color: #606060; text-transform: uppercase;
  letter-spacing: 0.4px;
}

.prof__value {
  font-size: 15px; color: #0F0F0F;
  padding: 10px 0;
}

.prof__input {
  padding: 10px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px; color: #0F0F0F;
  background: #fff;
}
.prof__input:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}

/* Actions */
.prof__actions {
  display: flex; gap: 10px;
  margin-top: 20px;
}

.prof__btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  transition: background .15s, box-shadow .15s;
  border: none;
}
.prof__btn--primary {
  background: #1DA53F; color: #fff;
}
.prof__btn--primary:hover {
  background: #178A33;
  box-shadow: 0 4px 12px rgba(29,165,63,.25);
}
.prof__btn--primary:disabled { opacity: .7; cursor: default; }
.prof__btn--ghost {
  background: transparent;
  color: #606060;
  border: 1px solid #E0E0E0;
}
.prof__btn--ghost:hover { background: #f8f8f8; }

.prof__hint {
  margin-top: 12px;
  font-size: 13px; color: #909090;
  line-height: 1.4;
}

@media (max-width: 640px) {
  .prof__fields { grid-template-columns: 1fr; }
  .prof__card-header { flex-direction: column; align-items: flex-start; }
  .prof__badges { margin-left: 0; }
}
</style>
